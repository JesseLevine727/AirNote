#!/usr/bin/python3
"""Complete the remaining QSPI D0 connection using clearance-aware grid search.
This verifies connectivity only; impedance/coupling need final stackup review.
"""
from pathlib import Path
import pcbnew as p, numpy as np, math,heapq,itertools
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'airnote.kicad_pcb'))
import argparse
ap=argparse.ArgumentParser();ap.add_argument('net');ap.add_argument('sx',type=float);ap.add_argument('sy',type=float);ap.add_argument('ex',type=float);ap.add_argument('ey',type=float);args=ap.parse_args()
net=args.net;step=.025;x0=min(args.sx,args.ex)-5;y0=min(args.sy,args.ey)-5;nx=int((abs(args.sx-args.ex)+10)/step)+1;ny=int((abs(args.sy-args.ey)+10)/step)+1
xs=x0+np.arange(nx)*step;ys=y0+np.arange(ny)*step
layers=[p.F_Cu,p.B_Cu];blocked=np.zeros((2,ny,nx),dtype=bool);vblocked=np.zeros((ny,nx),dtype=bool)
clearance=.13;trackwidth=.15;viawidth=.45

def rect(arr,xmin,ymin,xmax,ymax,pad):
 ix0=max(0,int(math.floor((xmin-pad-x0)/step)));ix1=min(nx-1,int(math.ceil((xmax+pad-x0)/step)))
 iy0=max(0,int(math.floor((ymin-pad-y0)/step)));iy1=min(ny-1,int(math.ceil((ymax+pad-y0)/step)))
 if ix1>=ix0 and iy1>=iy0:arr[iy0:iy1+1,ix0:ix1+1]=True

def capsule(arr,ax,ay,bx,by,r):
 ix0=max(0,int((min(ax,bx)-r-x0)/step)-1);ix1=min(nx-1,int((max(ax,bx)+r-x0)/step)+1)
 iy0=max(0,int((min(ay,by)-r-y0)/step)-1);iy1=min(ny-1,int((max(ay,by)+r-y0)/step)+1)
 if ix1<ix0 or iy1<iy0:return
 xx,yy=np.meshgrid(xs[ix0:ix1+1],ys[iy0:iy1+1]);dx=bx-ax;dy=by-ay
 t=np.clip(((xx-ax)*dx+(yy-ay)*dy)/(dx*dx+dy*dy+1e-30),0,1)
 arr[iy0:iy1+1,ix0:ix1+1]|=(xx-ax-t*dx)**2+(yy-ay-t*dy)**2<r*r
for f in b.GetFootprints():
 for q in f.Pads():
  z=q.GetBoundingBox();xx,yy,xe,ye=[p.ToMM(a) for a in [z.GetX(),z.GetY(),z.GetRight(),z.GetBottom()]]
  # Do not put new vias into any component pad.
  rect(vblocked,xx,yy,xe,ye,viawidth/2+clearance)
  if q.GetNetname()==net:continue
  for li,lay in enumerate(layers):
   if q.IsOnLayer(lay):rect(blocked[li],xx,yy,xe,ye,trackwidth/2+clearance)
for q in b.GetTracks():
 if q.GetNetname()==net:continue
 if isinstance(q,p.PCB_VIA):
  ax,ay=p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y);r=p.ToMM(q.GetWidth(p.F_Cu))/2
  for a in blocked:capsule(a,ax,ay,ax,ay,r+trackwidth/2+clearance)
  capsule(vblocked,ax,ay,ax,ay,r+viawidth/2+clearance)
 else:
  ax,ay,bx,by=[p.ToMM(a) for a in [q.GetStart().x,q.GetStart().y,q.GetEnd().x,q.GetEnd().y]];r=p.ToMM(q.GetWidth())/2
  if q.GetLayer() in layers:capsule(blocked[layers.index(q.GetLayer())],ax,ay,bx,by,r+trackwidth/2+clearance)
  capsule(vblocked,ax,ay,bx,by,r+viawidth/2+clearance)
startxyz=(args.sx,args.sy);endxyz=(args.ex,args.ey)
def grid(q):return int(round((q[0]-x0)/step)),int(round((q[1]-y0)/step))
sx,sy=grid(startxyz);ex,ey=grid(endxyz);start=(0,sx,sy);target=(0,ex,ey)
# Roundoff only at pad centers; all grid-to-pad endpoint lines checked by native DRC.
assert not blocked[0,sy,sx],('start obstructed',sx,sy)
assert not blocked[0,ey,ex],('target obstructed',ex,ey)
dirs=[(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
counter=itertools.count();q=[(0,next(counter),start)];g={start:0};prev={}
while q:
 _,_,cur=heapq.heappop(q)
 if cur==target:break
 lay,x,y=cur
 for dx,dy in dirs:
  xx,yy=x+dx,y+dy
  if not(0<=xx<nx and 0<=yy<ny) or blocked[lay,yy,xx]:continue
  if dx and dy and (blocked[lay,y,xx] or blocked[lay,yy,x]):continue
  nxt=(lay,xx,yy);gg=g[cur]+(1.41421356 if dx and dy else 1)
  if gg<g.get(nxt,1e99):g[nxt]=gg;prev[nxt]=cur;h=math.hypot(xx-ex,yy-ey);heapq.heappush(q,(gg+h,next(counter),nxt))
 if not vblocked[y,x] and not blocked[1-lay,y,x]:
  nxt=(1-lay,x,y);gg=g[cur]+20
  if gg<g.get(nxt,1e99):g[nxt]=gg;prev[nxt]=cur;heapq.heappush(q,(gg+math.hypot(x-ex,y-ey),next(counter),nxt))
else:
 print('Visited',len(g),'layers',{c[0]for c in g},'range',min(c[1]for c in g),max(c[1]for c in g),min(c[2]for c in g),max(c[2]for c in g))
 import matplotlib.pyplot as plt
 fig,axs=plt.subplots(1,2,figsize=(15,8))
 for l,ax in enumerate(axs):
  mat=blocked[l].astype(float);mat[vblocked]+=0.5
  for ll,xx,yy in g:
   if ll==l:mat[yy,xx]=3
  ax.imshow(mat,extent=[x0,x0+nx*step,y0+ny*step,y0],interpolation='none');ax.plot([startxyz[0],endxyz[0]],[startxyz[1],endxyz[1]],'ro')
 plt.savefig('/tmp/route-debug.png',dpi=150)
 raise RuntimeError('No clearance-safe route found')
path=[target]
while path[-1]!=start:path.append(prev[path[-1]])
path.reverse();points=[]
for i,c in enumerate(path):
 if i==0 or i==len(path)-1 or c[0]!=path[i-1][0] or c[0]!=path[i+1][0] or (c[1]-path[i-1][1],c[2]-path[i-1][2])!=(path[i+1][1]-c[1],path[i+1][2]-c[2]):points.append(c)
coords=[(l,float(xs[x]),float(ys[y]))for l,x,y in points];coords[0]=(0,*startxyz);coords[-1]=(0,*endxyz)
for aa,bb in zip(coords,coords[1:]):
 l,x,y=aa;ll,xx,yy=bb
 if l!=ll:
  v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(viawidth));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.GetNetsByName()[net]);b.Add(v)
 else:
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetEnd(p.VECTOR2I(p.FromMM(xx),p.FromMM(yy)));t.SetWidth(p.FromMM(trackwidth));t.SetLayer(layers[l]);t.SetNet(b.GetNetsByName()[net]);b.Add(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
print(net,'completion',len(coords),'vertices; routed length mm',sum(math.hypot(aa[1]-bb[1],aa[2]-bb[2]) for aa,bb in zip(coords,coords[1:])))
