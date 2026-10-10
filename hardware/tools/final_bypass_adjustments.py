#!/usr/bin/python3
"""Move two bypass capacitors closer to their IC pins; preserve unrelated routes."""
from pathlib import Path
import sys,math
sys.path.insert(0,str(Path(__file__).parent));from sexpr import *
import pcbnew as p
R=Path(__file__).resolve().parents[1];path=R/'airnote.kicad_pcb';a=parse(path.read_text());netnames={int(x[1]):x[2]for x in children(a,'net')}
# Remove former leaf branches up to first junction. Keep shared power trunks.
for ref in ['C7','C15']:
 f=next(f for f in children(a,'footprint')if any(q[1]=='Reference'and q[2]==ref for q in children(f,'property')))
 fx,fy=map(float,child(f,'at')[1:3])
 for pad in children(f,'pad'):
  if pad[1]not in ['1','2']:continue
  px,py=map(float,child(pad,'at')[1:3]);cur=(round(fx+px,6),round(fy+py,6));net=int(child(pad,'net')[1]);first=True
  while True:
   candidates=[]
   for t in children(a,'segment'):
    if int(child(t,'net')[1])!=net:continue
    aa=tuple(round(float(v),6)for v in child(t,'start')[1:3]);bb=tuple(round(float(v),6)for v in child(t,'end')[1:3])
    if aa==cur:candidates.append((t,bb))
    elif bb==cur:candidates.append((t,aa))
   if len(candidates)!=1:break
   t,nxt=candidates[0];a.remove(t);cur=nxt;first=False
   if any(tuple(round(float(v),6)for v in child(v,'at')[1:3])==cur for v in children(a,'via')):break
path.write_text(dump(a));b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
for ref,x,y in [('C7',96.,82.5),('C15',94.7,67.1)]:fs[ref].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));fs[ref].SetOrientationDegrees(0)
def wire(net,pts):
 for aa,bb in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(v)for v in aa]));t.SetEnd(p.VECTOR2I(*[p.FromMM(v)for v in bb]));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu);t.SetNet(b.GetNetsByName()[net]);b.Add(t)
for ref,dx,dy in [('C7',.8,0),('C15',0,-.8)]:
 q=next(q for q in fs[ref].Pads()if q.GetNumber()=='2');x,y=p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y);wire('GND',[(x,y),(x+dx,y+dy)])
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x+dx),p.FromMM(y+dy)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(b.GetNetsByName()['GND']);b.Add(v)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b,True)
