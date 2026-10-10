#!/usr/bin/python3
"""Resolve component courtyard overlaps conservatively; route/plane stages follow."""
import pcbnew as p, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'airnote.kicad_pcb'))
def mm(x):return p.ToMM(x)
def xy(f):return mm(f.GetPosition().x),mm(f.GetPosition().y)
def box(f):
 f.BuildCourtyardCaches(); c=f.GetCourtyard(p.F_CrtYd)
 z=c.BBox() if c.OutlineCount() else f.GetBoundingBox(False,False)
 return mm(z.GetX()),mm(z.GetY()),mm(z.GetRight()),mm(z.GetBottom())
def overlap(a,z,gap=.15):return a[0]<z[2]+gap and a[2]+gap>z[0] and a[1]<z[3]+gap and a[3]+gap>z[1]
def pos(f,x,y):f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
fs=list(b.GetFootprints()); fs.sort(key=lambda f:(0 if f.GetReference().startswith(('U','J','Y','H','SW','RV')) else 1, -((box(f)[2]-box(f)[0])*(box(f)[3]-box(f)[1]))))
fixed=[];changes=[]
for f in fs:
 ox,oy=xy(f);r0=f.GetOrientationDegrees();found=False
 for d in sorted([(dx,dy) for dx in range(-80,81) for dy in range(-80,81)],key=lambda z:z[0]**2+z[1]**2):
  x,y=ox+d[0]*.25,oy+d[1]*.25;pos(f,x,y);bb=box(f)
  # USB body can extend beyond board; mounting holes are naturally within.
  inset=0 if f.GetReference()=='J1' else .4
  if bb[0]<50+inset or bb[1]<(47 if f.GetReference()=='J1' else 50+inset) or bb[2]>140-inset or bb[3]>120-inset:continue
  if any(overlap(bb,q) for q in fixed):continue
  fixed.append(bb);found=True;break
 if not found:raise RuntimeError('No place for '+f.GetReference())
 if abs(x-ox)+abs(y-oy)>.01:changes.append([f.GetReference(),[ox,oy],[x,y]])
 f.Reference().SetVisible(False)
# Compact reference text above component, on fabrication layer to keep silkscreen clean.
# Assembly drawing and placement file carry every reference.
for f in fs:
 f.Reference().SetLayer(p.F_Fab);f.Reference().SetVisible(True)
# Silkscreen only intentional user labels.
p.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
(ROOT/'reports'/'placement-adjustments.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Moved',len(changes),'components to nonoverlapping courtyards')
print('DSN export',p.ExportSpecctraDSN(b,str(ROOT/'outputs'/'airnote-unrouted.dsn')))
