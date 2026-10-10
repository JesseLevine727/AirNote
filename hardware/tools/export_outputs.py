#!/usr/bin/python3
"""Validate canonical sources and regenerate review/DRAFT exports without modifying CAD."""
from pathlib import Path
import subprocess,csv,hashlib,json,shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs';D=O/'DRAFT-fabrication';Q=R/'reports'
for p in [O,D,Q]:p.mkdir(parents=True,exist_ok=True)
def cli(*a):subprocess.run(['kicad-cli',*map(str,a)],check=True)
cli('sch','erc','--format','json','--exit-code-violations','--output',Q/'erc-final.json',R/'airnote.kicad_sch')
cli('pcb','drc','--format','json','--schematic-parity','--exit-code-violations','--output',Q/'drc-final.json',R/'airnote.kicad_pcb')
cli('sch','export','netlist','--format','kicadxml','--output',O/'airnote.net.xml',R/'airnote.kicad_sch')
cli('sch','export','pdf','--output',O/'airnote-schematic.pdf',R/'airnote.kicad_sch')
cli('pcb','export','gerbers','--output',str(D)+'/', '--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','--subtract-soldermask',R/'airnote.kicad_pcb')
cli('pcb','export','drill','--output',str(D)+'/', '--excellon-units','mm','--excellon-separate-th','--generate-map','--generate-report','--map-format','pdf',R/'airnote.kicad_pcb')
cli('pcb','export','pos','--output',D/'airnote-all-positions.csv','--format','csv','--units','mm','--side','both','--exclude-dnp',R/'airnote.kicad_pcb')
with (R/'bom.csv').open()as f:bom=list(csv.DictReader(f))
fit={row['Reference']for row in bom if row['Assembly']=='Fit'}
for out,rows in [(D/'airnote-fitted-bom.csv',[row for row in bom if row['Reference']in fit])]:
 with out.open('w')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (D/'airnote-all-positions.csv').open()as f:positions=list(csv.DictReader(f))
with (D/'airnote-fitted-positions.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=list(positions[0]));w.writeheader();w.writerows(row for row in positions if row['Ref']in fit)
# JLCPCB order package. Rotations are KiCad's, uncorrected: check them in JLC's placement preview.
import re,zipfile,tempfile
nat=lambda s:[int(x) if x.isdigit() else x for x in re.split(r'(\d+)',s)]
jlc=[row for row in bom if row['Reference']in fit and not re.match(r'(TP|H|FID)\d',row['Reference'])]
groups={}
for row in jlc:groups.setdefault(row['LCSC'],[]).append(row)
with (D/'airnote-jlc-bom.csv').open('w',newline='')as f:
 w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
 for lcsc,rows in sorted(groups.items(),key=lambda kv:min((nat(r['Reference'])for r in kv[1]))):
  refs=sorted((r['Reference']for r in rows),key=nat);by={r['Reference']:r for r in rows};fpn={r['Footprint'].split(':')[-1]for r in rows}
  assert lcsc and len(fpn)==1,(lcsc,fpn)
  w.writerow([' / '.join(dict.fromkeys(by[r]['Value']for r in refs)),','.join(refs),fpn.pop(),lcsc])
with tempfile.TemporaryDirectory()as tmp:
 cli('pcb','export','pos','--output',Path(tmp)/'front.csv','--format','csv','--units','mm','--side','front','--exclude-dnp',R/'airnote.kicad_pcb')
 with (Path(tmp)/'front.csv').open()as f:front=[row for row in csv.DictReader(f)if row['Ref']in{r['Reference']for r in jlc}]
assert sorted(r['Ref']for r in front)==sorted(r['Reference']for r in jlc),'CPL/BOM part sets differ'
with (D/'airnote-jlc-cpl.csv').open('w',newline='')as f:
 w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
 for row in sorted(front,key=lambda r:nat(r['Ref'])):w.writerow([row['Ref'],row['PosX'],row['PosY'],'Top',row['Rot']])
gerb=sorted(p for p in D.iterdir() if p.suffix in ['.gtl','.g1','.g2','.gbl','.gtp','.gbp','.gto','.gbo','.gts','.gbs','.gm1','.drl','.gbrjob'])
assert len(gerb)==14,[p.name for p in gerb]
with zipfile.ZipFile(D/'airnote-jlc-gerbers.zip','w')as z:
 for p in gerb:
  zi=zipfile.ZipInfo(p.name,(1980,1,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o644<<16;z.writestr(zi,p.read_bytes())
cli('pcb','export','pdf','--output',O/'airnote-assembly.pdf','--layers','F.Fab,Edge.Cuts','--mode-single','--exclude-value','--sketch-pads-on-fab-layers',R/'airnote.kicad_pcb')
# Multi-page CLI accepts a directory and chooses the board basename.
copper=O/'copper';copper.mkdir(exist_ok=True)
cli('pcb','export','pdf','--output',copper,'--layers','F.Cu,In1.Cu,In2.Cu,B.Cu','--common-layers','Edge.Cuts','--mode-multipage',R/'airnote.kicad_pcb')
shutil.move(copper/'airnote.pdf',O/'airnote-copper.pdf');copper.rmdir()
cli('pcb','render','--output',O/'airnote-board.png','--width','1800','--height','1200','--side','top','--quality','high','--background','opaque',R/'airnote.kicad_pcb')
import pcbnew as pcb
board=pcb.LoadBoard(str(R/'airnote.kicad_pcb'));tracks=list(board.GetTracks())
summary={'status':'final locally checked engineering prototype; factory and physical gates remain open','board_sha256':hashlib.sha256((R/'airnote.kicad_pcb').read_bytes()).hexdigest(),'tracks':sum(not isinstance(t,pcb.PCB_VIA)for t in tracks),'vias':sum(isinstance(t,pcb.PCB_VIA)for t in tracks),'zones':len(list(board.Zones())),'track_layers':sorted({board.GetLayerName(t.GetLayer())for t in tracks if not isinstance(t,pcb.PCB_VIA)}),'copper_layers':board.GetCopperLayerCount(),'minimum_track_width_mm':min(pcb.ToMM(t.GetWidth())for t in tracks if not isinstance(t,pcb.PCB_VIA)),'unconnected_items_in_final_native_DRC':0}
(Q/'routing-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
files=[p for p in R.glob('*.kicad_*')if p.suffix in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru']]+[R/'bom.csv',R/'pin_net_manifest.json',Q/'erc-final.json',Q/'drc-final.json',Q/'routing-summary.json']+list(D.glob('*'))+[O/x for x in ['airnote-schematic.pdf','airnote-board.png','airnote-assembly.pdf','airnote-copper.pdf','airnote.net.xml']]
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(files)if p.is_file()}
(Q/'final-artifact-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(f'Validated canonical project; generated DRAFT export set for {len(fit)} fitted components ({len(groups)} JLC BOM lines, {len(front)} CPL parts, {len(gerb)} files in the Gerber zip). No manufacturing approval implied.')
