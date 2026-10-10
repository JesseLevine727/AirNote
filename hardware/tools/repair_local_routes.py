#!/usr/bin/python3
"""Targeted manual bypass and USB layout correction; consumes the existing routed PCB."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def move(ref,x,y,a=0):fs[ref].SetPosition(pt(x,y));fs[ref].SetOrientationDegrees(a)
def wire(net,pts,w=.15,layer=p.F_Cu):
 for aa,bb in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(pt(*aa));t.SetEnd(pt(*bb));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.GetNetsByName()[net]);t.SetLocked(True);b.Add(t)
def via(net,x,y):
 v=p.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.GetNetsByName()[net]);v.SetLocked(True);b.Add(v)
# Supply networks are rerouted around intentional local connections. All USB data nets reroute after moving series resistors.
import sys
sys.path.insert(0,str(ROOT/'tools'))
from sexpr import parse,dump,children,child
path=ROOT/'airnote.kicad_pcb';a=parse(path.read_text());nets={int(n[1]):n[2]for n in children(a,'net')}
for t in list(a):
 if isinstance(t,list)and t[0]in ('segment','via') and nets[int(child(t,'net')[1])]in ['+1V1','+3V3','USB_DP_MCU','USB_DM_MCU','USB_DP','USB_DM','USB_DP_ESD','USB_DM_ESD','ADC_3V3','+5V']:a.remove(t)
path.write_text(dump(a));b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
move('C14',93.0,76.7);move('C8',96.4,76.7);move('R5',100,76,90)
move('C9',89.4,76.7,180);move('C10',87.6,74.85,180)
move('C11',90.6,87.7,270);move('C6',93.25,87.3);move('C7',96.5,89.0)
move('R8',90.6,73.4,270);move('R9',92.3,73.4,270)
move('C19',114.75,59.25,90);move('C21',119.5,104.75,270);move('C22',122.4,104.75,270)
# Short, same-side USB stubs on outer copper. Stackup/coupling still a manufacturing gate.
wire('USB_DP_MCU',[(91,78.5625),(91,77.5),(91.1,77.4),(91.1,74.625),(90.6,74.225)])
wire('USB_DM_MCU',[(91.4,78.5625),(91.4,77.6),(91.5,77.5),(91.5,74.825),(92.3,74.225)])
# DVDD pin23 capacitor, VREG output pin45 capacitor, IOVDD49 local capacitor.
wire('+1V1',[(90.6,85.4375),(90.6,86.925)])
wire('+1V1',[(91.8,78.5625),(91.8,77.125),(92.225,76.7)])
wire('+3V3',[(90.2,78.5625),(90.2,76.725),(90.175,76.7)])
wire('+3V3',[(90.6,78.5625),(90.6,78.05),(90.2,77.65)])
# VREG input44; this bypass also supplies USB_VDD48 through the branch above.
wire('+3V3',[(92.2,78.5625),(92.2,77.85),(92.625,77.425),(94.9,77.425),(95.625,76.7)])
# VL53L1X both supply pads from its nearby 100 nF without a long global detour.
wire('+3V3',[(117.4,59.2),(116.5,59.2),(115.65,60.05),(115.175,60.05),(114.75,60.025)],.2)
wire('+3V3',[(117.4,60.8),(116.3,60.8),(115.65,60.15),(115.175,60.15),(114.75,60.025)],.2)
# MAX98357A dual VDD with immediately adjacent bypass and bulk cap.
wire('+5V',[(119.25,102.425),(119.25,103.725),(119.5,103.975)],.3)
wire('+5V',[(119.75,102.425),(119.75,103.725),(119.5,103.975)],.3)
wire('+5V',[(119.5,103.975),(121.225,103.975),(121.45,103.8),(122.4,103.8)],.3)
# Direct ground return vias adjacent to each local capacitor, never in its pad.
for ref in ['C3','C4','C5','C6','C7','C8','C9','C10','C11','C12','C13','C14','C15','C19','C20','C21','C22']:
 pad=next(q for q in fs[ref].Pads()if q.GetNetname()=='GND');x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)
 dx,dy=(0,.8)if ref in ['C11','C21','C22'] else ((0,-.8)if ref=='C19' else((-.8,0) if ref in ['C9','C10'] else(.8,0)))
 wire('GND',[(x,y),(x+dx,y+dy)],.2);via('GND',x+dx,y+dy)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
print('Local bypass and USB prewires installed; route clearance inspection required.')
