#!/usr/bin/python3
"""Review exported placement/drill geometry against native PCB; parse Gerbers.

Requires pcbnew (system Python) and gerbonara==1.6.3. This checks coherence,
not supplier capability, controlled impedance, assembly yield or hardware.
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
for row in rows:
 f=parts[row['Ref']];p=f.GetPosition()
 check('Placement '+row['Ref'],abs(float(row['PosX'])-p.x/1e6)<1e-5 and abs(float(row['PosY'])+p.y/1e6)<1e-5 and abs((float(row['Rot'])-f.GetOrientationDegrees()+180)%360-180)<1e-5 and row['Side']=='top' and f.GetLayer()==pcbnew.F_Cu)
source_paths=[ROOT/'hardware/airnote.kicad_pcb',ROOT/'hardware/airnote.kicad_sch',ROOT/'hardware/power.kicad_sch',ROOT/'hardware/instrument.kicad_sch',ROOT/'hardware/airnote.kicad_pro',ROOT/'hardware/airnote.kicad_dru',ROOT/'hardware/bom.csv',ROOT/'hardware/outputs/airnote.net.xml',ROOT/'hardware/outputs/airnote-schematic.pdf',ROOT/'hardware/outputs/airnote-assembly.pdf']
source_paths+=sorted(p for p in OUT.iterdir() if p.is_file())
result={'status':'PASS export-coherence checks only' if all(c['status']=='PASS' for c in checks) else 'FAIL','gerbonara_version':gerbonara.__version__,'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'checks':checks,'parsed_layers':layer_geometry,'parser_warnings':warnings_seen,'physical_tests':'PENDING','limitations':['Copper Gerbers, mask/paste and split drill sets were parsed; front/back independent render review is recorded separately.','The Gerber job stackup/finish/revision metadata are placeholders pending a factory-specific release.','Zero geometry discrepancies do not approve USB impedance/routing, remaining layout concerns, optical assembly process or actual operation.']}
(ROOT/'reviews/export-review.json').write_text(json.dumps(result,indent=2)+'\n')
for c in checks:
 if c['status']=='FAIL':print(c)
print(result['status'],len(checks),'checks')
raise SystemExit(any(c['status']=='FAIL' for c in checks))
