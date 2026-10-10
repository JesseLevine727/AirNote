#!/usr/bin/python3
"""Preserve native metadata, assign explicit no-connect nets, and normalize through vias."""
from pathlib import Path
import pcbnew as p,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'airnote.kicad_pcb'))
parts={c['ref']:c for c in json.loads((ROOT/'pin_net_manifest.json').read_text())}
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref in parts:
  name=parts[ref]['footprint'];lib,item=name.split(':');f.SetFPID(p.LIB_ID(lib,item))
 if ref.startswith('H'):f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
for v in b.GetTracks():
 if isinstance(v,p.PCB_VIA):v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu)
fs={f.GetReference():f for f in b.GetFootprints()}
r=ET.parse(ROOT/'outputs'/'airnote.net.xml').getroot()
for net in r.findall('nets/net'):
 name=net.attrib['name'].replace('/','{slash}')
 if not name.startswith('unconnected-'):continue
 if name not in b.GetNetsByName():b.Add(p.NETINFO_ITEM(b,name))
 ni=b.GetNetsByName()[name]
 for node in net.findall('node'):
  f=fs.get(node.attrib['ref'])
  if f:
   for pad in f.Pads():
    if pad.GetNumber()==node.attrib['pin']:pad.SetNet(ni)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
pr=ROOT/'airnote.kicad_pro';j=json.loads(pr.read_text());j['net_settings']['meta']={'version':4}
for c in j['net_settings']['classes']:
 if c['name']=='Default':c.update(clearance=.127,track_width=.15,via_diameter=.45,via_drill=.2)
j['board']['design_settings']['rules'].update(min_clearance=.127,min_track_width=.15,min_via_diameter=.45,min_through_hole_diameter=.2,min_via_annular_width=.1)
pr.write_text(json.dumps(j,indent=2)+'\n')
print('Normalized through-vias, library IDs, explicit NC nets and native 5mil rules.')
