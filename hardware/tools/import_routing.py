#!/usr/bin/python3
"""Import checked router session, add copper reference planes, save native PCB."""
from pathlib import Path
import pcbnew as p,json
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'airnote.kicad_pcb'))
assert p.ImportSpecctraSES(b,str(ROOT/'outputs'/'airnote-routed.ses'))
for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.GetNetsByName()['GND']);z.SetLocalClearance(p.FromMM(.2));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.25));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(50.5,50.5),(139.5,50.5),(139.5,119.5),(50.5,119.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
summary={'tracks':len([x for x in b.GetTracks() if not isinstance(x,p.PCB_VIA)]),'vias':len([x for x in b.GetTracks() if isinstance(x,p.PCB_VIA)]),'zones':len(list(b.Zones())),'track_layers':sorted({b.GetLayerName(x.GetLayer()) for x in b.GetTracks() if not isinstance(x,p.PCB_VIA)})}
(ROOT/'reports'/'routing-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
