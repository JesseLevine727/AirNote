#!/usr/bin/python3
"""Review exported placement/drill geometry against native PCB; parse Gerbers.

Requires pcbnew (system Python) and gerbonara==1.6.3, e.g. a venv created with
--system-site-packages. Also checks the Gerber job stackup against the PCB, via
tenting in the mask layers, fiducial exclusion and the implementer's artifact
hash manifest, and renders the review SVGs. This checks coherence, not supplier
capability, controlled impedance, assembly yield or hardware.
"""
import collections,csv,hashlib,json,math,warnings
from pathlib import Path
import pcbnew
import gerbonara
from gerbonara import LayerStack
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/outputs/DRAFT-fabrication'
board=pcbnew.LoadBoard(str(ROOT/'hardware/airnote.kicad_pcb'))
checks=[]
def check(name,passed,details=''):
 checks.append({'check':name,'status':'PASS' if passed else 'FAIL','details':details})
def rounded(values):return tuple(round(v,5) for v in values)
with warnings.catch_warnings(record=True) as caught:
 warnings.simplefilter('always')
 stack=LayerStack.open(OUT)
 # Force eager access to every parsed layer and both drill files.
 layer_geometry={str(k):{'objects':len(v.objects),'bounds':v.bounding_box()} for k,v in stack.graphic_layers.items()}
 warnings_seen=[str(w.message) for w in caught]
check('Four copper layers parsed',sum(k[1]=='copper' for k in stack.graphic_layers)==4)
check('Top and bottom mask/paste/silk plus outline present',all(k in stack.graphic_layers for k in [('top','mask'),('bottom','mask'),('top','paste'),('bottom','paste'),('top','silk'),('bottom','silk'),('mechanical','outline')]))
check('Bottom paste empty for all-top assembly',len(stack.graphic_layers[('bottom','paste')].objects)==0)
source_holes={True:collections.Counter(),False:collections.Counter()}
for v in board.GetTracks():
 if isinstance(v,pcbnew.PCB_VIA):
  p=v.GetPosition();d=v.GetDrillValue()/1e6
  source_holes[True][rounded((p.x/1e6,-p.y/1e6,d,d))]+=1
for f in board.GetFootprints():
 for p in f.Pads():
  d=p.GetDrillSize()
  if not d.x:continue
  pos=p.GetPosition();plated=p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH
  source_holes[plated][rounded((pos.x/1e6,-pos.y/1e6,min(d.x,d.y)/1e6,max(d.x,d.y)/1e6))]+=1
for plated,drill in [(True,stack.drill_pth),(False,stack.drill_npth)]:
 exported=collections.Counter()
 for o in drill.objects:
  d=o.aperture.diameter
  if hasattr(o,'x1'):
   x,y=(o.x1+o.x2)/2,(o.y1+o.y2)/2;length=math.hypot(o.x2-o.x1,o.y2-o.y1)+d
  else:x,y,length=o.x,o.y,d
  exported[rounded((x,y,d,length))]+=1
 # KiCad's metric Excellon output rounds coordinates to 0.001 mm.
 # Match one-to-one within half that resolution, rather than comparing
 # the PCB's nanometre coordinates to the rounded export as exact floats.
 unmatched=list(source_holes[plated].elements());extra=[];max_difference=0
 for hole in exported.elements():
  candidates=[(max(abs(a-b) for a,b in zip(hole,source)),i) for i,source in enumerate(unmatched)]
  difference,index=min(candidates,default=(math.inf,-1))
  if difference<=0.00051:max_difference=max(max_difference,difference);unmatched.pop(index)
  else:extra.append(hole)
 check(('Plated' if plated else 'Nonplated')+' drill centers/sizes/slot lengths match PCB',not unmatched and not extra,{'source_count':source_holes[plated].total(),'export_count':exported.total(),'coordinate_tolerance_mm':0.00051,'maximum_difference_mm':max_difference,'missing':unmatched,'extra':extra})
parts={f.GetReference():f for f in board.GetFootprints()}
bom=list(csv.DictReader((ROOT/'hardware/bom.csv').open()))
want={r['Reference'] for r in bom if r['Assembly']=='Fit'}
rows=list(csv.DictReader((OUT/'airnote-all-positions.csv').open()))
check('Placement list matches fitted BOM references',{r['Ref'] for r in rows}==want)
fitted_bom={r['Reference'] for r in csv.DictReader((OUT/'airnote-fitted-bom.csv').open())}
fitted_cpl={r['Ref'] for r in csv.DictReader((OUT/'airnote-fitted-positions.csv').open())}
check('Exported fitted BOM and fitted CPL list exactly the fitted bom.csv references (no FID/TP/H)',fitted_bom==want==fitted_cpl,{'bom_only':sorted(fitted_bom-want),'cpl_only':sorted(fitted_cpl-want),'missing':sorted(want-fitted_bom)})
manifest=json.loads((ROOT/'hardware/reports/final-artifact-hashes.json').read_text())
bad=[k for k,v in manifest.items() if hashlib.sha256((ROOT/'hardware'/k).read_bytes()).hexdigest()!=v]
check('Implementer hash manifest matches every listed file',not bad and manifest.get('airnote.kicad_pcb')==hashlib.sha256((ROOT/'hardware/airnote.kicad_pcb').read_bytes()).hexdigest(),{'entries':len(manifest),'mismatches':bad})
job=json.loads((OUT/'airnote-job.gbrjob').read_text())
job_thk=[m.get('Thickness') for m in job['MaterialStackup'] if 'Thickness' in m]
pcb_text=(ROOT/'hardware/airnote.kicad_pcb').read_text()
import re
pcb_thk=[float(x) for x in re.findall(r'\(thickness ([\d.]+)\)',pcb_text.split('(stackup',1)[1].split('(copper_finish',1)[0])]
check('Gerber job stackup equals the PCB stackup (JLC04161H-7628) and four layers',job_thk==pcb_thk and job['GeneralSpecs']['LayerNumber']==4,{'job':job_thk,'pcb':pcb_thk,'board_thickness':job['GeneralSpecs']['BoardThickness']})
order_package={'gbrjob_revision':job['GeneralSpecs']['ProjectId']['Revision'],'gbrjob_finish':job['GeneralSpecs']['Finish']}
from gerbonara.graphic_objects import Flash
pad_xy={(round(p.GetPosition().x/1e6,3),round(-p.GetPosition().y/1e6,3)) for f in board.GetFootprints() for p in f.Pads()}
via_xy=[(round(v.GetPosition().x/1e6,3),round(-v.GetPosition().y/1e6,3)) for v in board.GetTracks() if isinstance(v,pcbnew.PCB_VIA)]
via_xy=[xy for xy in via_xy if xy not in pad_xy]  # a via at a pad centre (U5 exposed pad) shares that pad's opening
for side in ['top','bottom']:
 centres={(round(o.x,3),round(o.y,3)) for o in stack.graphic_layers[(side,'mask')].objects if isinstance(o,Flash)}
 exposed=[xy for xy in via_xy if xy in centres]
 check(f'All {len(via_xy)} vias tented on {side} mask (no mask flash at a via centre)',not exposed,{'exposed':exposed})
fid_flash=sorted({o.attrs.get('.P',('?',))[0] for o in stack.graphic_layers[('top','copper')].objects if isinstance(o,Flash) and o.attrs.get('.P',('',))[0].startswith('FID') and abs(o.aperture.diameter-1.0)<1e-6})
fid_mask=sorted({o.attrs.get('.C',('?',))[0] for o in stack.graphic_layers[('top','mask')].objects if isinstance(o,Flash) and o.attrs.get('.C',('',))[0].startswith('FID')})
check('Three fiducials present in top copper (1 mm) and top mask Gerbers',fid_flash==fid_mask==['FID1','FID2','FID3'],{'copper':fid_flash,'mask':fid_mask})
# JLC order package: BOM/CPL agree with bom.csv and the PCB; zip equals the loose files.
import zipfile
jbom=list(csv.DictReader((OUT/'airnote-jlc-bom.csv').open()))
bom_by={r['Reference']:r for r in bom}
jlc_want={r for r in want if not re.match(r'(TP|H|FID)\d',r)}
jrefs=[d for row in jbom for d in row['Designator'].split(',')]
check('JLC BOM: every fitted part exactly once; no TP/H/FID',sorted(jrefs)==sorted(jlc_want) and len(jrefs)==len(set(jrefs)),{'lines':len(jbom),'parts':len(jrefs),'missing':sorted(jlc_want-set(jrefs)),'extra':sorted(set(jrefs)-jlc_want)})
bad=[(d,row['LCSC Part #'],bom_by[d]['LCSC'],row['Footprint'],bom_by[d]['Footprint'],row['Comment']) for row in jbom for d in row['Designator'].split(',') if d in bom_by and (row['LCSC Part #']!=bom_by[d]['LCSC'] or row['Footprint']!=bom_by[d]['Footprint'].split(':')[-1] or row['Comment']!=' / '.join(dict.fromkeys(bom_by[x]['Value'] for x in row['Designator'].split(','))))]
check('JLC BOM: LCSC number, footprint and value equal bom.csv for every designator',not bad,{'mismatches':bad})
jcpl=list(csv.DictReader((OUT/'airnote-jlc-cpl.csv').open()))
check('JLC CPL: same designator set as JLC BOM, each once',sorted(r['Designator'] for r in jcpl)==sorted(jrefs),{'rows':len(jcpl)})
badp=[]
for r in jcpl:
 f=parts[r['Designator']];p=f.GetPosition()
 if not (abs(float(r['Mid X'])-p.x/1e6)<1e-5 and abs(float(r['Mid Y'])+p.y/1e6)<1e-5 and abs((float(r['Rotation'])-f.GetOrientationDegrees()+180)%360-180)<1e-5 and r['Layer']=='Top' and f.GetLayer()==pcbnew.F_Cu): badp.append(r)
check('JLC CPL: positions (KiCad anchor, Y negated), rotations and Top layer equal the PCB',not badp,{'mismatches':badp})
with zipfile.ZipFile(OUT/'airnote-jlc-gerbers.zip') as z:
 names=sorted(z.namelist());diff=[n for n in names if z.read(n)!=(OUT/n).read_bytes()]
loose=sorted(p.name for p in OUT.iterdir() if p.suffix in ['.gtl','.g1','.g2','.gbl','.gtp','.gbp','.gto','.gbo','.gts','.gbs','.gm1','.drl','.gbrjob'])
check('JLC Gerber zip: 11 Gerbers + 2 drills + job, byte-identical to the loose files',names==loose and len(names)==14 and not diff,{'zip':names,'differing':diff})
# Review renders (actual Gerber/Excellon content, not native CAD plots).
(ROOT/'reviews/gerber-top-review.svg').write_text(str(stack.to_pretty_svg(side='top')))
(ROOT/'reviews/gerber-bottom-review.svg').write_text(str(stack.to_pretty_svg(side='bottom')))
(ROOT/'reviews/gerber-inner1-review.svg').write_text(str(stack.graphic_layers[('inner_1','copper')].to_svg()))
for row in rows:
 f=parts[row['Ref']];p=f.GetPosition()
 check('Placement '+row['Ref'],abs(float(row['PosX'])-p.x/1e6)<1e-5 and abs(float(row['PosY'])+p.y/1e6)<1e-5 and abs((float(row['Rot'])-f.GetOrientationDegrees()+180)%360-180)<1e-5 and row['Side']=='top' and f.GetLayer()==pcbnew.F_Cu)
source_paths=[ROOT/'hardware/airnote.kicad_pcb',ROOT/'hardware/airnote.kicad_sch',ROOT/'hardware/power.kicad_sch',ROOT/'hardware/instrument.kicad_sch',ROOT/'hardware/airnote.kicad_pro',ROOT/'hardware/airnote.kicad_dru',ROOT/'hardware/bom.csv',ROOT/'hardware/outputs/airnote.net.xml',ROOT/'hardware/outputs/airnote-schematic.pdf',ROOT/'hardware/outputs/airnote-assembly.pdf']
source_paths+=sorted(p for p in OUT.iterdir() if p.is_file())
result={'status':'PASS export-coherence checks only' if all(c['status']=='PASS' for c in checks) else 'FAIL','gerbonara_version':gerbonara.__version__,'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'checks':checks,'parsed_layers':layer_geometry,'parser_warnings':warnings_seen,'order_package_open_items':order_package,'physical_tests':'PENDING','limitations':['Copper Gerbers, mask/paste and split drill sets were parsed; front/back/In1 renders are written to reviews/gerber-*-review.svg and inspected separately.','The Gerber job stackup matches JLC04161H-7628; Finish stays "None" by overseer disposition (chosen on the order form).','Zero geometry discrepancies do not approve USB impedance/routing, remaining layout concerns, optical assembly process or actual operation.']}
(ROOT/'reviews/export-review.json').write_text(json.dumps(result,indent=2)+'\n')
for c in checks:
 if c['status']=='FAIL':print(c)
print(result['status'],len(checks),'checks')
raise SystemExit(any(c['status']=='FAIL' for c in checks))
