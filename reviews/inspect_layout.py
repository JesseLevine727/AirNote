#!/usr/bin/python3
"""Independent layout inspection for the AirNote rev 0.2 PCB.

Read-only with respect to hardware/: the canonical board is loaded into memory,
zone refills happen in memory only, and the custom-rule probe runs kicad-cli
on a copy in a temporary directory. Writes reviews/layout-review.json.

Requires KiCad 9 pcbnew (system Python), networkx and shapely, for example:
    /usr/bin/python3 -m venv --system-site-packages /tmp/rv && /tmp/rv/bin/pip install shapely
    /tmp/rv/bin/python reviews/inspect_layout.py
Run from the repository root. Geometry is approximate (track centerlines,
pad-interior travel removed only at section endpoints). This is not a field
solver, a DRC replacement, or evidence of physical behaviour.
"""
import collections, hashlib, json, math, shutil, subprocess, tempfile
from pathlib import Path
import networkx as nx
import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / 'hardware/airnote.kicad_pcb'
import os
# Previously reviewed revision for the regression comparison (override with AIRNOTE_PREVIOUS=<commit>).
PREVIOUS = os.environ.get('AIRNOTE_PREVIOUS', '0d1927e')
mm = lambda v: v / 1e6
checks = []
def check(name, status, detail):
    checks.append({'check': name, 'status': status, 'detail': detail})
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

board = pcbnew.LoadBoard(str(PCB))
fps = {f.GetReference(): f for f in board.GetFootprints()}
tracks = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
vias = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

def pad_poly(pad, layer=pcbnew.F_Cu):
    ps = pcbnew.SHAPE_POLY_SET(); pad.TransformShapeToPolygon(ps, layer, 0, 5000, pcbnew.ERROR_INSIDE)
    o = ps.Outline(0); return Polygon([(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())])
def seg(t): return ((mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)))
def track_geo(t): a, b = seg(t); return LineString([a, b]).buffer(mm(t.GetWidth()) / 2)
def pad(ref, num): return next(p for p in fps[ref].Pads() if p.GetNumber() == num)
def zone_fill(layer_name):
    out = []
    for z in board.Zones():
        layer = board.GetLayerID(layer_name)
        if z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer):
            ps = z.GetFilledPolysList(layer)
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i)
                holes = [[(mm(ps.Hole(i, h).CPoint(k).x), mm(ps.Hole(i, h).CPoint(k).y)) for k in range(ps.Hole(i, h).PointCount())] for h in range(ps.HoleCount(i))]
                out.append((z.GetNetname(), Polygon([(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())], holes)))
    return out

# ---------------------------------------------------------------- net graph
def net_graph(net):
    """Weighted graph of a net's tracks/vias/pads. Edge attrs: length (mm), r (relative ohms: mm/width)."""
    ts = [t for t in tracks if t.GetNetname() == net]; vs = [v for v in vias if v.GetNetname() == net]
    pads = [(r, p) for r, f in fps.items() for p in f.Pads() if p.GetNetname() == net]
    key = lambda p, l: (round(p[0], 6), round(p[1], 6), l)
    nodes = {key(pt, t.GetLayer()) for t in ts for pt in seg(t)}
    rad = collections.defaultdict(float)
    for t in ts:
        for pt in seg(t): rad[key(pt, t.GetLayer())] = max(rad[key(pt, t.GetLayer())], mm(t.GetWidth()) / 2)
    for v in vs:
        for l in (pcbnew.F_Cu, pcbnew.B_Cu):
            n = key((mm(v.GetPosition().x), mm(v.GetPosition().y)), l); nodes.add(n); rad[n] = mm(v.GetWidth(l)) / 2
    g = nx.Graph(); g.add_nodes_from(nodes)
    for t in ts:
        (ax, ay), (bx, by) = seg(t); dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy); w = mm(t.GetWidth()); hit = []
        for n in nodes:
            if n[2] != t.GetLayer(): continue
            u = 0 if L == 0 else max(0, min(1, ((n[0] - ax) * dx + (n[1] - ay) * dy) / (L * L)))
            q = (ax + u * dx, ay + u * dy); d = math.dist(n[:2], q)
            if d <= w / 2 + rad[n] + 1e-5:
                pk = key(q, t.GetLayer()); hit.append((u, pk))
                if pk != n: g.add_edge(n, pk, length=d, r=d / w, w=w)
        hit.sort()
        for (_, n1), (_, n2) in zip(hit, hit[1:]):
            d = math.dist(n1[:2], n2[:2]); g.add_edge(n1, n2, length=d, r=d / w, w=w)
    for v in vs:
        p = (mm(v.GetPosition().x), mm(v.GetPosition().y))
        # barrel: 1.6 mm, ~20 um plating, expressed in the same mm/width-of-35um-copper units
        barrel = 1.6 * 0.035 / (math.pi * mm(v.GetDrillValue()) * 0.020)
        g.add_edge(key(p, pcbnew.F_Cu), key(p, pcbnew.B_Cu), length=0, r=barrel, via=1)
    for r, p in pads:
        pn = (r, p.GetNumber())
        for n in nodes:
            if p.IsOnLayer(n[2]) and p.HitTest(pcbnew.VECTOR2I(round(n[0] * 1e6), round(n[1] * 1e6))):
                g.add_edge(pn, n, length=0, r=0)
    return g

def section(net, a, z, weight='length'):
    """Path length between two pads, excluding travel inside the two end pads."""
    g = net_graph(net)
    path = nx.shortest_path(g, a, z, weight=weight)
    pts = [n[:2] for n in path if len(n) == 3]
    line = LineString(pts) if len(pts) > 1 else None
    ends = unary_union([pad_poly(pad(*a)), pad_poly(pad(*z))])
    length = line.difference(ends).length if line is not None else 0.0
    nv = sum(1 for u, v in zip(path, path[1:]) if g.edges[u, v].get('via'))
    rel_r = sum(g.edges[u, v]['r'] for u, v in zip(path, path[1:]))
    widths = [g.edges[u, v]['w'] for u, v in zip(path, path[1:]) if g.edges[u, v].get('w') and g.edges[u, v]['length'] > 1e-3]
    return length, nv, rel_r, (min(widths) if widths else None)

# ---------------------------------------------------------------- hashes / previous
previous_pcb = tempfile.NamedTemporaryFile(suffix='.kicad_pcb', delete=False)
previous_pcb.write(subprocess.run(['git', 'show', f'{PREVIOUS}:hardware/airnote.kicad_pcb'], cwd=ROOT, capture_output=True, check=True).stdout); previous_pcb.close()
result = {'scope': 'static layout inspection; approximate geometry; no physical validation',
          'sha256': {str(p.relative_to(ROOT)): sha(p) for p in [PCB, ROOT / 'hardware/airnote.kicad_pro', ROOT / 'hardware/airnote.kicad_dru']},
          'previous_revision': {'commit': PREVIOUS, 'pcb_sha256': sha(previous_pcb.name)}}

# ---------------------------------------------------------------- custom rules loaded
with tempfile.TemporaryDirectory() as tmp:
    for name in ['airnote.kicad_pcb', 'airnote.kicad_pro', 'airnote.kicad_dru']:
        shutil.copy(ROOT / 'hardware' / name, Path(tmp) / name)
    dru = Path(tmp) / 'airnote.kicad_dru'
    dru.write_text(dru.read_text().replace('(max 0.25mm)', '(max 0.2mm)'))
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '-o', str(Path(tmp) / 'probe.json'), str(Path(tmp) / 'airnote.kicad_pcb')], capture_output=True)
    probe = json.loads((Path(tmp) / 'probe.json').read_text())
usb = ['USB_DP', 'USB_DM', 'USB_DP_ESD', 'USB_DM_ESD', 'USB_DP_MCU', 'USB_DM_MCU']
wide_usb = sum(1 for t in tracks if t.GetNetname() in usb and abs(mm(t.GetWidth()) - 0.25) < 1e-6)
flagged = sum(1 for v in probe['violations'] if "USB_DIFF width" in v['description'])
check('Custom rules file is parsed and USB_DIFF rule matches the pair (probe: max width lowered to 0.2 mm on a temporary copy)',
      'PASS' if flagged == wide_usb > 0 else 'FAIL', {'usb_0.25mm_tracks': wide_usb, 'probe_violations_naming_USB_DIFF_width': flagged})
classes = {n: board.FindNet(n).GetNetClassName() for n in usb}
check('All six USB nets are in net class USB_DIFF', 'PASS' if set(classes.values()) == {'USB_DIFF'} else 'FAIL', classes)

# ---------------------------------------------------------------- stackup
stack = (PCB.read_text().split('(stackup', 1)[1].split('(copper_finish', 1)[0])
import re
thick = [float(x) for x in re.findall(r'\(thickness ([\d.]+)\)', stack)]
check('Stackup equals JLC04161H-7628 (mask 0.01, Cu 0.035, PP 0.2104 Dk4.4, Cu 0.0152, core 1.065 Dk4.6, Cu 0.0152, PP 0.2104, Cu 0.035, mask 0.01)',
      'PASS' if thick == [0.01, 0.035, 0.2104, 0.0152, 1.065, 0.0152, 0.2104, 0.035, 0.01] and stack.count('(epsilon_r 4.4)') == 2 and '(epsilon_r 4.6)' in stack else 'FAIL',
      {'thicknesses_mm': thick, 'copper_finish': re.search(r'\(copper_finish "([^"]*)"', PCB.read_text())[1]})

# ---------------------------------------------------------------- USB geometry
useg = {n: [t for t in tracks if t.GetNetname() == n] for n in usb}
check('USB nets: F.Cu only, zero vias', 'PASS' if all(t.GetLayer() == pcbnew.F_Cu for n in usb for t in useg[n]) and not any(v.GetNetname() in usb for v in vias) else 'FAIL',
      {n: {'segments': len(useg[n]), 'length_mm': round(sum(mm(t.GetLength()) for t in useg[n]), 3), 'widths': sorted({round(mm(t.GetWidth()), 3) for t in useg[n]})} for n in usb})
P, M = ['USB_DP', 'USB_DP_ESD', 'USB_DP_MCU'], ['USB_DM', 'USB_DM_ESD', 'USB_DM_MCU']
coupling = {}
for fam, other in [(P, M), (M, P)]:
    partner = unary_union([LineString(seg(t)) for n in other for t in useg[n]])
    tot = exact = 0
    for n in fam:
        for t in useg[n]:
            a, b = seg(t); L = math.dist(a, b); k = max(1, int(L / 0.02))
            for i in range(k):
                u = (i + .5) / k; p = Point(a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1])); tot += L / k
                if abs(partner.distance(p) - 0.40) <= 0.011: exact += L / k
    coupling[fam[0] + ' family'] = {'length_mm': round(tot, 2), 'at_0.40mm_pitch_mm': round(exact, 2), 'fraction': round(exact / tot, 3)}
check('USB coupling: fraction of each polarity family at 0.40 mm centre pitch (>=0.80 expected; doc claims 0.93)', 'PASS' if all(v['fraction'] >= 0.80 for v in coupling.values()) else 'FAIL', coupling)
own_pads = {n: [(r + '.' + p.GetNumber(), pad_poly(p)) for r, f in fps.items() for p in f.Pads() if p.GetNetname() == n] for n in usb}
neck = []
for n in usb:
    for t in useg[n]:
        if mm(t.GetWidth()) < 0.249:
            a, b = seg(t)
            near = min(min(pg.distance(Point(e)) for _, pg in own_pads[n]) for e in (a, b))
            far = max(min(pg.distance(Point(e)) for _, pg in own_pads[n]) for e in (a, b))
            neck.append({'net': n, 'from': a, 'to': b, 'length_mm': round(math.dist(a, b), 3), 'nearest_end_to_own_pad_mm': round(near, 3), 'farthest_end_to_own_pad_mm': round(far, 3)})
check('USB neck-down (0.15 mm) segments all start at or within 1.05 mm of an own-net pad', 'PASS' if all(x['nearest_end_to_own_pad_mm'] <= 1.05 for x in neck) else 'FAIL',
      {'segments': neck, 'note': 'The D1 pad-gap runs (USB_DM 3.05 mm, USB_DP_ESD 2.95 mm) extend about 2.7-2.8 mm from their own pad but stay inside D1 pad rows.'})
usbgeo = unary_union([track_geo(t) for n in usb for t in useg[n]])
fcu = zone_fill('F.Cu')
pour = min(usbgeo.distance(g) for net, g in fcu if net == 'GND')
check('F.Cu GND pour pull-back from USB copper >= 0.5 mm', 'PASS' if pour >= 0.499 else 'FAIL', {'minimum_mm': round(pour, 3)})
plane = {}
for ln in ['In1.Cu', 'In2.Cu']:
    fill = unary_union([g for net, g in zone_fill(ln) if net == 'GND'])
    plane[ln] = {f'+{m}mm_uncovered_mm2': round(usbgeo.buffer(m).difference(fill).area, 4) for m in (0.1, 0.3, 0.6)}
check('In1.Cu GND fill continuous under USB copper footprint + 0.3 mm', 'PASS' if plane['In1.Cu']['+0.3mm_uncovered_mm2'] == 0 else 'FAIL',
      {'coverage': plane, 'note': 'Residual +0.6 mm gaps are antipads of nearby QSPI_CS, QSPI_D0, CC2 and I2C_SDA vias (0.43-0.57 mm from pair copper).'})
other = []
for t in board.GetTracks():
    if t.GetNetname() in usb: continue
    if isinstance(t, pcbnew.PCB_VIA): other.append((t.GetNetname(), Point(mm(t.GetPosition().x), mm(t.GetPosition().y)).buffer(mm(t.GetWidth(pcbnew.F_Cu)) / 2)))
    elif t.GetLayer() == pcbnew.F_Cu: other.append((t.GetNetname(), track_geo(t)))
for f in board.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() not in usb and p.IsOnLayer(pcbnew.F_Cu): other.append((f.GetReference() + '.' + p.GetNumber() + ' ' + p.GetNetname(), pad_poly(p)))
clear = {n: sorted((round(unary_union([track_geo(t) for t in useg[n]]).distance(g), 3), name) for name, g in other)[0] for n in usb}
check('USB copper to other-net F.Cu copper >= 0.2 mm', 'PASS' if min(c[0] for c in clear.values()) >= 0.2 else 'FAIL', clear)
# section lengths
sec = {
    'DP J1.B6->D1.1': ('USB_DP', ('J1', 'B6'), ('D1', '1')), 'DM J1.A7->D1.3': ('USB_DM', ('J1', 'A7'), ('D1', '3')),
    'DP J1.A6->D1.1': ('USB_DP', ('J1', 'A6'), ('D1', '1')), 'DM J1.B7->D1.3': ('USB_DM', ('J1', 'B7'), ('D1', '3')),
    'DP D1.6->R8.1': ('USB_DP_ESD', ('D1', '6'), ('R8', '1')), 'DM D1.4->R9.1': ('USB_DM_ESD', ('D1', '4'), ('R9', '1')),
    'DP R8.2->U1.47': ('USB_DP_MCU', ('R8', '2'), ('U1', '47')), 'DM R9.2->U1.46': ('USB_DM_MCU', ('R9', '2'), ('U1', '46'))}
L = {k: round(section(*v)[0], 3) for k, v in sec.items()}
dp = L['DP J1.B6->D1.1'] + L['DP D1.6->R8.1'] + L['DP R8.2->U1.47']; dm = L['DM J1.A7->D1.3'] + L['DM D1.4->R9.1'] + L['DM R9.2->U1.46']
eeff = 2.7 + 1.7 / math.sqrt(1 + 12 * 0.2104 / 0.25)   # Hammerstad microstrip estimate, w=0.25, h=0.2104, er=4.4
ps_per_mm = math.sqrt(eeff) / 0.299792458
plug_a = (L['DP J1.A6->D1.1'] + dp - L['DP J1.B6->D1.1']) - dm
plug_b = dp - (L['DM J1.B7->D1.3'] + dm - L['DM J1.A7->D1.3'])
skews = {'B6/A7 trunks DP-DM_mm': round(dp - dm, 3), 'plug on A6/A7 DP-DM_mm': round(plug_a, 3), 'plug on B6/B7 DP-DM_mm': round(plug_b, 3),
         'estimated_ps_per_mm': round(ps_per_mm, 2), 'worst_case_ps': round(max(abs(dp - dm), abs(plug_a), abs(plug_b)) * ps_per_mm, 1),
         'full_speed_bit_time_ns': 83.33}
check('USB end-to-end skew through D1 <= 1 mm on the B6/A7 trunks; worst plug orientation recorded', 'PASS' if abs(dp - dm) <= 1.0 else 'FAIL',
      {'sections_pad_edge_to_pad_edge_mm': L, 'totals_mm': {'DP': round(dp, 3), 'DM': round(dm, 3)}, 'skew': skews})
d1 = {p.GetNumber(): (p.GetNetname(), round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)) for p in fps['D1'].Pads()}
want = {'1': 'USB_DP', '6': 'USB_DP_ESD', '3': 'USB_DM', '4': 'USB_DM_ESD', '2': 'GND', '5': 'VBUS_RAW'}
opp = abs(d1['1'][1] - d1['6'][1]) < 1e-3 and abs(d1['3'][1] - d1['4'][1]) < 1e-3
check('D1 USBLC6-2SC6: I/O1 = pins 1/6 (DP/DP_ESD), I/O2 = pins 3/4 (DM/DM_ESD), GND 2, VBUS 5; 1 opposite 6 and 3 opposite 4',
      'PASS' if all(d1[k][0] == v for k, v in want.items()) and opp else 'FAIL', d1)
for r, cc in (('R6', 'CC1'), ('R7', 'CC2')):
    nets = {p.GetNumber(): p.GetNetname() for p in fps[r].Pads()}
    check(f'{r} 5.1 kohm pull-down {cc} to GND', 'PASS' if nets == {'1': cc, '2': 'GND'} and fps[r].GetValue() == '5.1k' else 'FAIL', nets)
u1 = fps['U1'].GetPosition()
check('R8/R9 placed near U1 (series section <= 4 mm)', 'PASS' if max(L['DP R8.2->U1.47'], L['DM R9.2->U1.46']) <= 4.0 else 'FAIL',
      {'R8.2->U1.47_mm': L['DP R8.2->U1.47'], 'R9.2->U1.46_mm': L['DM R9.2->U1.46'], 'centre_distance_to_U1_mm': {r: round(math.dist((mm(fps[r].GetPosition().x), mm(fps[r].GetPosition().y)), (mm(u1.x), mm(u1.y))), 2) for r in ('R8', 'R9')}})

# ---------------------------------------------------------------- crystal
xin = section('XIN', ('U1', '20'), ('Y1', '1')); xout = section('XOUT', ('U1', '21'), ('R1', '1')); xo = section('XTAL_OUT', ('R1', '2'), ('Y1', '3'))
xn = ['XIN', 'XOUT', 'XTAL_OUT']
check('XIN pin 20 -> Y1.1 <= 4.1 mm and crystal nets have no vias', 'PASS' if xin[0] <= 4.1 and not any(v.GetNetname() in xn for v in vias) else 'FAIL',
      {'XIN_mm': round(xin[0], 3), 'XOUT_to_R1_mm': round(xout[0], 3), 'R1_to_Y1.3_mm': round(xo[0], 3)})
xgeo = unary_union([pad_poly(p) for r, f in fps.items() for p in f.Pads() if p.GetNetname() in xn] + [pad_poly(p) for p in fps['Y1'].Pads()] +
                   [track_geo(t) for t in tracks if t.GetNetname() in xn])
hull = xgeo.convex_hull; foreign = collections.defaultdict(list)
for t in board.GetTracks():
    n = t.GetNetname()
    if n in xn or n == 'GND': continue
    g = Point(mm(t.GetPosition().x), mm(t.GetPosition().y)).buffer(mm(t.GetWidth(pcbnew.F_Cu)) / 2) if isinstance(t, pcbnew.PCB_VIA) else track_geo(t)
    lname = 'via' if isinstance(t, pcbnew.PCB_VIA) else board.GetLayerName(t.GetLayer())
    if g.intersects(hull.buffer(1.0)):
        foreign[lname].append((n, round(g.distance(xgeo), 3), 'inside hull' if g.intersects(hull) else 'within 1 mm'))
fcu_inside = sorted({n for n, d, w in foreign['F.Cu'] if w == 'inside hull'})
check('Crystal network: only non-GND F.Cu copper inside its hull is the IOVDD22 (+3V3) bypass branch', 'PASS' if fcu_inside in ([], ['+3V3']) else 'FAIL',
      {k: sorted(set(v)) for k, v in foreign.items()})
g3 = net_graph('+3V3')
iovdd = nx.shortest_path_length(g3, ('U1', '22'), ('C6', '1'), weight='length')
check('IOVDD pin 22 -> C6 copper path <= 3.0 mm', 'PASS' if iovdd <= 3.0 else 'FAIL', {'mm': round(iovdd, 3)})

# ---------------------------------------------------------------- power path
def ipc2221_external_A(width_mm, dT=10.0, oz=1.0):
    area_mil2 = (width_mm / 0.0254) * (1.378 * oz); return 0.048 * dT ** 0.44 * area_mil2 ** 0.725
rho_per_mm = 1.72e-8 / (1e-3 * 0.035e-3) * 1e-3  # ohm per mm per mm-width at 35 um
power = {}
for label, net, a, z in [('J1 east VBUS pad (A4/B9) -> F1.1', 'VBUS_RAW', ('J1', 'A4'), ('F1', '1')),
                         ('J1 west VBUS pad (A9/B4) -> F1.1', 'VBUS_RAW', ('J1', 'A9'), ('F1', '1')),
                         ('F1.2 -> U3.1 (LDO input)', '+5V', ('F1', '2'), ('U3', '1')),
                         ('F1.2 -> U5.7 (amplifier VDD)', '+5V', ('F1', '2'), ('U5', '7'))]:
    length, nv, rel, wmin = section(net, a, z, weight='r')
    power[label] = {'length_mm': round(length, 2), 'vias': nv, 'min_width_mm': wmin, 'est_dc_resistance_ohm': round(rel * rho_per_mm, 3)}
widths = {n: sorted({round(mm(t.GetWidth()), 3) for t in tracks if t.GetNetname() == n}) for n in ('VBUS_RAW', '+5V')}
main = power['J1 east VBUS pad (A4/B9) -> F1.1']
check('VBUS_RAW main path J1 -> F1 is >= 0.4 mm F.Cu with no vias', 'PASS' if main['vias'] == 0 and main['min_width_mm'] >= 0.399 else 'FAIL',
      {'paths': power, 'widths_mm': widths,
       'ipc2221_external_10C_rise_A': {str(w): round(ipc2221_external_A(w), 2) for w in (0.15, 0.3, 0.4)},
       'note': 'Series-path estimates: parallel vias/branches are not credited, so resistances are upper bounds.'})
p3, p5 = power['F1.2 -> U3.1 (LDO input)'], power['F1.2 -> U5.7 (amplifier VDD)']
check('+5V main paths: F1 -> U3 >= 0.4 mm; F1 -> U5 >= 0.3 mm (pad-width stub)', 'PASS' if p3['min_width_mm'] >= 0.399 and p5['min_width_mm'] >= 0.299 else 'FAIL',
      {'F1->U3': p3, 'F1->U5': p5, 'vias_on_+5V': [(round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3)) for v in vias if v.GetNetname() == '+5V'],
       'narrow_+5V_segments_mm': sorted({(round(mm(t.GetWidth()), 3),) + tuple(round(x, 3) for pt in seg(t) for x in pt) for t in tracks if t.GetNetname() == '+5V' and mm(t.GetWidth()) < 0.399})})

# ---------------------------------------------------------------- vias in pads and drill webs
vip = []
for v in vias:
    c = Point(mm(v.GetPosition().x), mm(v.GetPosition().y)); ann = c.buffer(mm(v.GetWidth(pcbnew.F_Cu)) / 2)
    for r, f in fps.items():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) and pad_poly(p).intersects(ann):
                pg = pad_poly(p)
                vip.append({'via': (round(c.x, 3), round(c.y, 3)), 'net': v.GetNetname(), 'pad': f'{r}.{p.GetNumber()}',
                            'drill_centre_inside_pad': pg.contains(c),
                            'drill_edge_inside_pad_mm': round(mm(v.GetDrillValue()) / 2 - pg.exterior.distance(c), 3) if not pg.contains(c) else None})
ep = sorted(x['pad'] for x in vip if x['drill_centre_inside_pad'])
check('Via-in-pad set: only the five exposed-pad vias have drills inside pads', 'PASS' if ep == ['U1.57'] * 4 + ['U5.17'] else 'FAIL', vip)
webs = []
for v in vias:
    c = (mm(v.GetPosition().x), mm(v.GetPosition().y)); r = mm(v.GetDrillValue()) / 2
    for ref, f in fps.items():
        for p in f.Pads():
            if not p.GetDrillSize().x: continue
            h = p.GetEffectiveHoleShape(); s = h.GetSeg(); a, b = (mm(s.A.x), mm(s.A.y)), (mm(s.B.x), mm(s.B.y))
            web = LineString([a, b]).distance(Point(c)) if a != b else math.dist(a, c)
            web -= mm(h.GetWidth()) / 2 + r
            if web < 0.45: webs.append({'via': c, 'net': v.GetNetname(), 'hole': f'{ref}.{p.GetNumber()}', 'web_mm': round(web, 3)})
    for v2 in vias:
        c2 = (mm(v2.GetPosition().x), mm(v2.GetPosition().y))
        if c < c2 and math.dist(c, c2) - r - mm(v2.GetDrillValue()) / 2 < 0.2:
            webs.append({'via': c, 'via2': c2, 'web_mm': round(math.dist(c, c2) - r - mm(v2.GetDrillValue()) / 2, 3)})
check('Drill-to-drill webs meet JLC published spacing (via-via 0.2 mm; pad hole 0.45 mm)', 'PASS' if not webs else 'FAIL',
      {'violations': webs, 'source': 'https://jlcpcb.com/capabilities/pcb-capabilities (accessed 2026-10-10)',
       'note': 'KiCad min_hole_to_hole (0.25 mm) did not report the same-net via/pad-slot pair found at J1 in rev 0.2 (78444e8); this check is independent of it.'})

# ---------------------------------------------------------------- fiducials
bb = board.GetBoardEdgesBoundingBox(); edge = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
fill = unary_union([g for n, g in fcu])
fid = {}
for r in sorted(x for x in fps if x.startswith('FID')):
    f = fps[r]; c = (mm(f.GetPosition().x), mm(f.GetPosition().y)); p = f.Pads()[0]
    fid[r] = {'xy': c, 'copper_dia': mm(p.GetSize().x), 'mask_opening_dia': mm(p.GetSize().x) + 2 * mm(p.GetLocalSolderMaskMargin() or 0),
              'min_edge_mm': round(min(c[0] - edge[0], c[1] - edge[1], edge[2] - c[0], edge[3] - c[1]), 2),
              'pour_from_centre_mm': round(fill.distance(Point(c)), 3), 'excluded_bom_pos': f.IsExcludedFromBOM() and f.IsExcludedFromPosFiles()}
cx, cy = (edge[0] + edge[2]) / 2, (edge[1] + edge[3]) / 2
rot = [(2 * cx - v['xy'][0], 2 * cy - v['xy'][1]) for v in fid.values()]
asym = max(min(math.dist(q, v['xy']) for v in fid.values()) for q in rot)
check('Three fiducials, excluded from BOM/CPL, >=3 mm from edge, no copper inside the mask opening, not 180-degree symmetric',
      'PASS' if len(fid) == 3 and all(v['excluded_bom_pos'] and v['min_edge_mm'] >= 3 and v['pour_from_centre_mm'] > v['mask_opening_dia'] / 2 for v in fid.values()) and asym > 3 else 'FAIL',
      {'fiducials': fid, 'max_mismatch_after_180deg_rotation_mm': round(asym, 2)})

# ---------------------------------------------------------------- zone fill freshness (in memory only)
def areas():
    return {f'{z.GetNetname()} {board.GetLayerName(l)}': round(z.GetFilledPolysList(l).Area() / 1e12, 4) for z in board.Zones() for l in z.GetLayerSet().Seq() if z.HasFilledPolysForLayer(l)}
saved = areas(); pcbnew.ZONE_FILLER(board).Fill(board.Zones()); refilled = areas()
check('Saved zone fills equal an in-memory refill with the loaded rules', 'PASS' if saved == refilled else 'FAIL', {'saved_mm2': saved, 'refilled_mm2': refilled})

# ---------------------------------------------------------------- regression summary vs previous revision
def summary(path):
    b = pcbnew.LoadBoard(path); d = collections.defaultdict(lambda: {'segs': set(), 'vias': set()})
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA): d[t.GetNetname()]['vias'].add((round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)))
        else:
            a, z = seg(t); d[t.GetNetname()]['segs'].add((t.GetLayerName(), round(mm(t.GetWidth()), 3)) + tuple(sorted([tuple(round(x, 3) for x in a), tuple(round(x, 3) for x in z)])))
    return d, {f.GetReference(): (round(mm(f.GetPosition().x), 3), round(mm(f.GetPosition().y), 3), f.GetOrientationDegrees()) for f in b.GetFootprints()}
old, oldfp = summary(previous_pcb.name); new, newfp = summary(str(PCB))
changed = {}
for net in sorted(set(old) | set(new)):
    a, b = old.get(net, {'segs': set(), 'vias': set()}), new.get(net, {'segs': set(), 'vias': set()})
    if a != b:
        ln = lambda s: round(sum(math.dist(x[2], x[3]) for x in s), 2)
        changed[net] = {'length_mm': [ln(a['segs']), ln(b['segs'])], 'vias': [len(a['vias']), len(b['vias'])],
                        'widths_mm': [sorted({x[1] for x in a['segs']}), sorted({x[1] for x in b['segs']})],
                        'layers': [sorted({x[0] for x in a['segs']}), sorted({x[0] for x in b['segs']})]}
prev_board = pcbnew.LoadBoard(previous_pcb.name)
padnets = lambda b: {(f.GetReference(), p.GetNumber(), round(mm(p.GetPosition().x) - mm(f.GetPosition().x), 4), round(mm(p.GetPosition().y) - mm(f.GetPosition().y), 4)): p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
pn_old, pn_new = padnets(prev_board), padnets(board)
diff_pads = sorted(set(pn_old.items()) ^ set(pn_new.items()))
check('Pad-to-net assignments unchanged from the previous revision', 'PASS' if not diff_pads else 'FAIL', {'pads': len(pn_new), 'differences': diff_pads[:40]})
moved = {r: [oldfp.get(r), newfp.get(r)] for r in sorted(set(oldfp) | set(newfp)) if oldfp.get(r) != newfp.get(r)}
nonusb_min = min(min(v['widths_mm'][1] or [9]) for n, v in changed.items() if n not in usb)
check('Rerouted non-USB nets keep >= 0.15 mm width (no new necking)', 'PASS' if nonusb_min >= 0.15 else 'FAIL', {'changed_nets': changed, 'moved_footprints': moved})
Path(previous_pcb.name).unlink()

result['checks'] = checks
result['failed'] = sum(c['status'] == 'FAIL' for c in checks)
result['physical_tests'] = 'PENDING'
(ROOT / 'reviews/layout-review.json').write_text(json.dumps(result, indent=1, default=list) + '\n')
for c in checks: print(c['status'], '-', c['check'])
print(f"{len(checks)} checks; {result['failed']} failures. Static geometry only.")
raise SystemExit(bool(result['failed']))
