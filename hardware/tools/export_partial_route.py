#!/usr/bin/python3
"""Export partial native routes for targeted completion on outer signal layers."""
from pathlib import Path
import pcbnew as p,re
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/'airnote.kicad_pcb'))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'airnote.kicad_pcb'),b,True)
b.SetCopperLayerCount(2);p.ExportSpecctraDSN(b,str(R/'outputs/airnote-route-local.dsn'))
f=R/'outputs/airnote-route-local.dsn';s=f.read_text().replace('(width 200)','(width 150)').replace('(clearance 200)','(clearance 127)').replace('(use_via "Via[0-1]_600:300_um")','(use_via "Via[0-1]_450:200_um")')
f.write_text(s);print('Exported partial routes; locked segments',s.count('(type protect)'))
