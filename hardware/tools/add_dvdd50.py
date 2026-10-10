#!/usr/bin/python3
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/'airnote.kicad_pcb'))
def wire(pts,layer):
 for (x,y),(xx,yy)in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetEnd(p.VECTOR2I(p.FromMM(xx),p.FromMM(yy)));t.SetWidth(p.FromMM(.15));t.SetLayer(layer);t.SetNet(b.GetNetsByName()['+1V1']);t.SetLocked(True);b.Add(t)
for x,y in [(89.75,77.625),(88.375,75.65)]:
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.GetNetsByName()['+1V1']);v.SetLocked(True);b.Add(v)
wire([(89.8,78.5625),(89.8,77.9),(89.75,77.85),(89.75,77.625)],p.F_Cu)
wire([(89.75,77.625),(89.75,77.025),(88.375,75.65)],p.B_Cu)
wire([(88.375,75.65),(88.375,74.85)],p.F_Cu)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'airnote.kicad_pcb'),b,True)
