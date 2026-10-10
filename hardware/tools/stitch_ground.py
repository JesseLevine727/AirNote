#!/usr/bin/python3
"""Add grounded through vias to eligible outer copper islands using actual filled polygons."""
from pathlib import Path
import pcbnew as p,math
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/'airnote.kicad_pcb'));zs={z.GetLayer():z.GetFilledPolysList(z.GetLayer())for z in b.Zones()}
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
existing=[(p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y))for t in b.GetTracks()if isinstance(t,p.PCB_VIA)]
added=[]
for layer in [p.F_Cu,p.B_Cu]:
 polys=zs[layer]
 for idx in range(polys.OutlineCount()):
  poly=polys.COutline(idx);box=poly.BBox();xmin,ymin,xmax,ymax=[p.ToMM(a)for a in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]]
  # Skip polygons that already touch a ground via on this layer.
  if any(poly.PointInside(pt(x,y))for x,y in existing):continue
  candidate=None
  for iy in range(int((ymax-ymin)/.1)+1):
   y=ymin+iy*.1
   for ix in range(int((xmax-xmin)/.1)+1):
    x=xmin+ix*.1
    if not poly.PointInside(pt(x,y)):continue
    if any(math.hypot(x-xx,y-yy)<.65 for xx,yy in existing+added):continue
    # Entire via plus process clearance inside poured GND on both sides and both planes.
    probes=[pt(x+.35*math.cos(a*math.pi/4),y+.35*math.sin(a*math.pi/4))for a in range(8)]
    if all(z.Contains(q)for z in zs.values()for q in probes):candidate=(x,y);break
   if candidate:break
  if candidate:
   x,y=candidate;v=p.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.GetNetsByName()['GND']);b.Add(v);added.append(candidate)
  else:print('No stitching site polygon',b.GetLayerName(layer),idx,(xmin,ymin,xmax,ymax))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'airnote.kicad_pcb'),b,True);print('Added stitching vias',added)
