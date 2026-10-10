#!/usr/bin/python3
"""Remove unlocked routes that conflict with newly placed local bypass geometry."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).parent))
from sexpr import *
R=Path(__file__).resolve().parents[1];p=R/'airnote.kicad_pcb';a=parse(p.read_text());j=json.loads((R/'reports/drc-repair.json').read_text())
tracks={child(t,'uuid')[1]:t for t in a if isinstance(t,list) and t[0]in ('segment','via')};bad=set()
for v in j['violations']:
 if v['type'] in ['clearance','shorting_items','tracks_crossing','hole_clearance','hole_to_hole','solder_mask_bridge','track_dangling']:
  for i in v['items']:
   t=tracks.get(i['uuid'])
   if t and not child(t,'locked'):bad.add(int(child(t,'net')[1]))
removed=0
for t in list(a):
 if isinstance(t,list)and t[0]in ('segment','via') and int(child(t,'net')[1])in bad and not child(t,'locked'):a.remove(t);removed+=1
p.write_text(dump(a));print('Ripped conflicting nets',bad,'segments',removed)
