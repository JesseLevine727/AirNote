#!/usr/bin/python3
"""Export ONLY F.Cu/B.Cu to router; final native board retains four copper layers."""
from pathlib import Path
import pcbnew as p,re
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'airnote.kicad_pcb'))
if list(b.GetTracks()):raise RuntimeError('Run generate_hardware.py and prepare_layout.py first: routing input must be clean')
for x,y in [(89.4,81.4),(90.6,81.4),(89.4,82.6),(90.6,82.6),(119,101)]:
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.GetNetsByName()['GND']);b.Add(v)
p.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
# This temporary in-memory layer count prevents ANY inner-layer route; does not save 2-layer PCB.
b.SetCopperLayerCount(2)
p.ExportSpecctraDSN(b,str(ROOT/'outputs'/'airnote-route.dsn'))
f=ROOT/'outputs'/'airnote-route.dsn';s=f.read_text()
s=s.replace('(width 200)','(width 150)').replace('(clearance 200)','(clearance 127)')
# Use existing 0.45/0.20 mm via padstack for all ordinary routing as well.
s=s.replace('(use_via "Via[0-1]_600:300_um")','(use_via "Via[0-1]_450:200_um")')
# Wider amplifier supply and bridge speaker routes, with a separate net class.
power=['+5V','VBUS_RAW','SPK_P','SPK_N']
idx=s.index('(class kicad_default');end=s.index('(circuit',idx)
head=s[idx:end]
for net in power:head=re.sub(r'(?<!\S)'+re.escape(net)+r'(?!\S)','',head)
s=s[:idx]+head+s[end:]
idx=s.index('  (wiring')
# Insert class before network closing bracket.
prefix=s[:idx];cut=prefix.rfind('  )')
cls='    (class power_audio '+' '.join(power)+' (circuit (use_via "Via[0-1]_450:200_um")) (rule (width 300) (clearance 127)))\n'
s=prefix[:cut]+cls+prefix[cut:]+s[idx:]
f.write_text(s)
assert '(layer In' not in s
print('Prepared two-signal-layer DSN; native PCB remains four layers.')
