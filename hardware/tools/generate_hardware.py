#!/usr/bin/python3
"""Generate editable KiCad 9 sources and placement from an explicit pin/net manifest.
Run with /usr/bin/python3 (distribution pcbnew bindings). Does not order boards.
"""
from pathlib import Path
import sys,copy,uuid,json,csv,math,shutil
sys.path.insert(0,str(Path(__file__).parent))
from sexpr import *
import pcbnew as pcb
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',required=True,help='New isolated directory; must not be the canonical hardware directory')
args=parser.parse_args();SOURCE_ROOT=Path(__file__).resolve().parents[1];ROOT=Path(args.output_dir).resolve()
if ROOT==SOURCE_ROOT:raise SystemExit('Refusing to overwrite the canonical routed board. Choose an isolated --output-dir.')
if (ROOT/'airnote.kicad_pcb').exists():raise SystemExit('Output already contains a PCB; choose a fresh directory.')
ROOT.mkdir(parents=True,exist_ok=True)
shutil.copytree(SOURCE_ROOT/'libraries',ROOT/'libraries',dirs_exist_ok=True)
LIB=Path('/usr/share/kicad/symbols'); FP=Path('/usr/share/kicad/footprints')
A=atom
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'airnote-v0.1/'+s))
def n(v):return A(round(float(v),4))
def form(k,*v):return [A(k),*v]
def fx(size=1.0,hide=False):
 v=form('effects',form('font',form('size',n(size),n(size))))
 if hide:v.append(form('hide',A('yes')))
 return v
libs={};syms={}
def symbol(libid):
 if libid in syms:return copy.deepcopy(syms[libid])
 lib,name=libid.split(':')
 if lib=='AirNote':
  base=symbol('Audio:'+name);base[1]=libid
  for u in children(base,'symbol'):
   for pin in children(u,'pin'):
    if child(pin,'number')[1]=='17':pin[1]=A('passive')
  syms[libid]=base;return copy.deepcopy(base)
 if lib not in libs:libs[lib]=parse((LIB/(lib+'.kicad_sym')).read_text())
 s=copy.deepcopy(next(x for x in children(libs[lib],'symbol') if x[1]==name))
 ex=child(s,'extends')
 if ex:
  base=symbol(lib+':'+ex[1]); old=base[1].split(':')[-1]
  for u in children(base,'symbol'):u[1]=name+u[1][len(old):]
  props={p[1]:p for p in children(s,'property')}
  base=[x for x in base if not(isinstance(x,list) and x[0]=='property' and x[1] in props)]
  base.extend(props.values());s=base
 s[1]=libid;syms[libid]=s;return copy.deepcopy(s)
def pins(libid,unit=1):
 out=[]
 for u in children(symbol(libid),'symbol'):
  ix=int(u[1].rsplit('_',2)[-2])
  if ix not in (0,unit):continue
  out.extend(children(u,'pin'))
 return out
components=[]
def add(ref,lib,val,fp,mpn,nets,page,sch,xy,rot=0,unit=1,desc='',manufacturer=''):
 c=dict(ref=ref,lib=lib,value=val,footprint=fp,mpn=mpn,nets={str(k):v for k,v in nets.items()},page=page,sch=sch,xy=xy,rot=rot,unit=unit,description=desc,manufacturer=manufacturer,uuid=uid(ref))
 components.append(c);return c
rnum=0;cnum=0
def resistor(val,a,b,page,sch,xy,rot=0):
 global rnum;rnum+=1
 code={'27':'27R','1k':'1K','10k':'10K','100k':'100K','5.1k':'5K1','470':'470R','1M':'1M','1':'1R','100':'100R'}[val]
 return add('R'+str(rnum),'Device:R',val,'Resistor_SMD:R_0603_1608Metric','RC0603FR-07'+code+'L',{1:a,2:b},page,sch,xy,rot,manufacturer='Yageo')
def cap(val,a,b,page,sch,xy,rot=0):
 global cnum;cnum+=1
 mpns={'100n':'GRM188R71C104KA01D','1u':'GRM188R71A105KA61D','4.7u':'GRM21BR71A475KA73L','10u':'GRM21BR61A106KE19L','15p':'GRM1885C1H150JA01D','10n':'GRM188R71H103KA01D'}
 size='0805_2012Metric' if val in ('4.7u','10u') else '0603_1608Metric'
 return add('C'+str(cnum),'Device:C',val,'Capacitor_SMD:C_'+size,mpns[val],{1:a,2:b},page,sch,xy,rot,manufacturer='Murata')
# Core board coordinates in mm; outline 90 x 70, origin (50,50).
cn={19:'GND',26:'RUN',46:'USB_DM_MCU',47:'USB_DP_MCU',56:'QSPI_CS',52:'QSPI_CLK',53:'QSPI_D0',55:'QSPI_D1',54:'QSPI_D2',51:'QSPI_D3',20:'XIN',21:'XOUT',24:'SWCLK',25:'SWDIO',48:'+3V3',43:'ADC_3V3',1:'+3V3',10:'+3V3',22:'+3V3',33:'+3V3',42:'+3V3',49:'+3V3',57:'GND',44:'+3V3',45:'+1V1',23:'+1V1',50:'+1V1',2:'I2C_SDA',3:'I2C_SCL',4:'SENSOR_XSHUT',5:'SENSOR_IRQ',13:'I2S_DATA',14:'I2S_BCLK',15:'I2S_LRCLK',17:'AMP_ENABLE',18:'MUTE_N',37:'STATUS_LED',38:'VOLUME_ADC'}
add('U1','MCU_RaspberryPi:RP2040','RP2040','Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm','RP2040',cn,'core',(81.28,96.52),(90,82),manufacturer='Raspberry Pi')
add('U2','Memory_Flash:W25Q16JVSS','W25Q16JVSSIQ','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','W25Q16JVSSIQ',{1:'QSPI_CS',6:'QSPI_CLK',5:'QSPI_D0',2:'QSPI_D1',3:'QSPI_D2',7:'QSPI_D3',8:'+3V3',4:'GND'},'core',(190.5,58.42),(89,69),manufacturer='Winbond')
add('Y1','Device:Crystal_GND24','12MHz ABM8-272-T3','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm','ABM8-272-T3',{1:'XIN',3:'XTAL_OUT',2:'GND',4:'GND'},'core',(193.04,116.84),(92,91),manufacturer='Abracon')
resistor('1k','XOUT','XTAL_OUT','core',(203.2,142.24),(89,90),90)
cap('15p','XIN','GND','core',(172.72,116.84),(89,93),0)
cap('15p','XTAL_OUT','GND','core',(218.44,116.84),(95,93),0)
resistor('10k','+3V3','QSPI_CS','core',(162.56,58.42),(92.5,69.0),0)
resistor('1k','QSPI_CS','BOOTSEL_SW','core',(241.3,58.42),(96,68),90)
add('SW1','Switch:SW_Push','BOOTSEL','Button_Switch_SMD:SW_SPST_TL3342','TL3342F160QG',{1:'BOOTSEL_SW',2:'GND'},'core',(269.24,58.42),(99,59),manufacturer='E-Switch')
resistor('10k','+3V3','RUN','core',(243.84,93.98),(84,91),0)
add('SW2','Switch:SW_Push','RESET','Button_Switch_SMD:SW_SPST_TL3342','TL3342F160QG',{1:'RUN',2:'GND'},'core',(269.24,93.98),(109,59),manufacturer='E-Switch')
add('J2','Connector_Generic:Conn_01x05','SWD 3V3 GND DIO CLK RUN','Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical','TSW-105-07-G-S',{1:'+3V3',2:'GND',3:'SWDIO',4:'SWCLK',5:'RUN'},'core',(304.8,132.08),(112,84),manufacturer='Samtec')
# Every RP2040 supply pin has local decoupling.
for i,(xy,net) in enumerate([((85.2,78),'+3V3'),((85.2,84.6),'+3V3'),((87.2,86.8),'+3V3'),((93.6,86.8),'+3V3'),((94.8,82),'+3V3'),((94.8,77.2),'+3V3'),((92.8,76.6),'+3V3'),((87,77),'+1V1'),((94.4,74.6),'+1V1'),((97,79),'ADC_3V3')]):
 cap('100n',net,'GND','core',(48.26+27.94*(i%5),177.8+38.1*(i//5)),xy,0)
cap('1u','+3V3','GND','core',(208.28,177.8),(97,84.5),0)
cap('1u','+1V1','GND','core',(236.22,177.8),(97,82),0)
cap('100n','+3V3','GND','core',(264.16,177.8),(85,68),0)
resistor('1','+3V3','ADC_3V3','core',(292.1,177.8),(96,76),90)
# USB and power page.
add('J1','Connector:USB_C_Receptacle_USB2.0_16P','USB-C USB2.0','AirNote:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal','USB4105-GF-A',{'A1':'GND','A12':'GND','B1':'GND','B12':'GND','A4':'VBUS_RAW','A9':'VBUS_RAW','B4':'VBUS_RAW','B9':'VBUS_RAW','A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM','S1':'GND'},'power',(55.88,71.12),(64,53.675),180,manufacturer='GCT')
resistor('5.1k','CC1','GND','power',(104.14,45.72),(67,61),90)
resistor('5.1k','CC2','GND','power',(132.08,45.72),(67,63.5),90)
add('D1','Power_Protection:USBLC6-2SC6','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6','USBLC6-2SC6',{1:'USB_DP',6:'USB_DP_ESD',3:'USB_DM',4:'USB_DM_ESD',2:'GND',5:'VBUS_RAW'},'power',(121.92,88.9),(72,62),manufacturer='STMicroelectronics')
resistor('27','USB_DP_ESD','USB_DP_MCU','power',(175.26,66.04),(96,72),90)
resistor('27','USB_DM_ESD','USB_DM_MCU','power',(205.74,66.04),(96,73.8),90)
add('F1','Device:Polyfuse','500mA hold PTC','Fuse:Fuse_1206_3216Metric','1206L050YR',{1:'VBUS_RAW',2:'+5V'},'power',(111.76,139.7),(68,55.5),90,manufacturer='Littelfuse')
add('U3','Regulator_Linear:AP2112K-3.3','AP2112K-3.3','Package_TO_SOT_SMD:SOT-23-5','AP2112K-3.3TRG1',{1:'+5V',2:'GND',3:'+5V',5:'+3V3'},'power',(177.8,139.7),(74,71),manufacturer='Diodes Inc.')
cap('1u','+5V','GND','power',(144.78,157.48),(70.5,71),0)
cap('1u','+3V3','GND','power',(208.28,157.48),(77.5,71),0)
cap('100n','VBUS_RAW','GND','power',(78.74,139.7),(70,59),0)
# Sensor and instrument page.
add('U4','Sensor_Distance:VL53L1CXV0FY1','VL53L1CXV0FY/1','Sensor_Distance:ST_VL53L1x','VL53L1CXV0FY/1',{1:'+3V3',11:'+3V3',2:'GND',3:'GND',4:'GND',6:'GND',12:'GND',5:'SENSOR_XSHUT',7:'SENSOR_IRQ',9:'I2C_SDA',10:'I2C_SCL'},'instrument',(68.58,66.04),(119, sixty:=60),manufacturer='STMicroelectronics')
cap('100n','+3V3','GND','instrument',(101.6,45.72),(117.5,63.5),0)
cap('4.7u','+3V3','GND','instrument',(129.54,45.72),(120.5,63.5),0)
resistor('10k','+3V3','SENSOR_XSHUT','instrument',(101.6,81.28),(114.5,63),90)
resistor('10k','+3V3','SENSOR_IRQ','instrument',(129.54,81.28),(114.5,66),90)
resistor('5.1k','+3V3','I2C_SDA','instrument',(40.64,111.76),(111,66),90)
resistor('5.1k','+3V3','I2C_SCL','instrument',(68.58,111.76),(111,68.5),90)
add('U5','AirNote:MAX98357A','MAX98357AETE+T','AirNote:MAX98357A_T1633_ADI_90-0031','MAX98357AETE+T',{1:'I2S_DATA',16:'I2S_BCLK',14:'I2S_LRCLK',4:'AMP_SD',3:'GND',11:'GND',15:'GND',17:'GND',7:'+5V',8:'+5V',9:'SPK_P',10:'SPK_N'},'instrument',(220.98,68.58),(119,101),manufacturer='Analog Devices')
# 9dB gain: pin2 intentionally floating, explicit NC.
cap('100n','+5V','GND','instrument',(187.96,38.1),(121.8,100),0)
cap('4.7u','+5V','GND','instrument',(218.44,38.1),(125,100),0)
add('J3','Connector_Generic:Conn_01x02','SPEAKER 8ohm >=1W','Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical','B2B-PH-K-S(LF)(SN)',{1:'SPK_P',2:'SPK_N'},'instrument',(279.4,66.04),(132,104),manufacturer='JST')
resistor('10k','AMP_ENABLE','AMP_SD','instrument',(177.8,111.76),(113.5,103),90)
resistor('100k','AMP_SD','GND','instrument',(205.74,111.76),(114,106),0)
resistor('10k','+3V3','MUTE_N','instrument',(276.86,111.76),(110,108),0)
add('SW3','Switch:SW_DPDT_x2','MUTE / PLAY','Button_Switch_SMD:SW_DPDT_CK_JS202011JCQN','JS202011JCQN',{1:'GND',2:'AMP_SD',3:None,4:'GND',5:'MUTE_N',6:None},'instrument',(243.84,134.62),(121,113),unit=1,manufacturer='C&K')
add('SW3','Switch:SW_DPDT_x2','MUTE / PLAY','Button_Switch_SMD:SW_DPDT_CK_JS202011JCQN','JS202011JCQN',{1:'GND',2:'AMP_SD',3:None,4:'GND',5:'MUTE_N',6:None},'instrument',(276.86,134.62),(121,113),unit=2,manufacturer='C&K')
add('RV1','Device:R_Potentiometer','10k LINEAR VOLUME','Potentiometer_THT:Potentiometer_Bourns_PTV09A-1_Single_Vertical','PTV09A-1020F-B103',{1:'GND',2:'VOLUME_RAW',3:'+3V3'},'instrument',(66.04,165.1),(69,108),manufacturer='Bourns')
resistor('1k','VOLUME_RAW','VOLUME_ADC','instrument',(109.22,165.1),(86,108),90)
cap('100n','VOLUME_ADC','GND','instrument',(137.16,165.1),(90,108),0)
add('D2','Device:LED','GREEN STATUS','LED_SMD:LED_0603_1608Metric','LTST-C190KGKT',{1:'GND',2:'LED_A'},'instrument',(190.5,165.1),(95,112),manufacturer='Lite-On')
resistor('1k','STATUS_LED','LED_A','instrument',(162.56,165.1),(91,112),90)
resistor('1M','VOLUME_ADC','GND','instrument',(137.16,200.66),(93,108),0)
# Test points and mechanicals.
for i,(net,xy) in enumerate([('VBUS_RAW',(61,65)),('+5V',(68,67)),('+3V3',(77,75)),('+1V1',(98,87)),('GND',(107,90)),('I2C_SDA',(108,73)),('I2C_SCL',(111,73)),('I2S_DATA',(107,98)),('I2S_BCLK',(107,101)),('I2S_LRCLK',(107,104)),('AMP_SD',(112,112))],1):
 add('TP'+str(i),'Connector:TestPoint',net,'TestPoint:TestPoint_Pad_D1.5mm','TEST_PAD_1.5MM',{1:net},'power',(40.64+27.94*((i-1)%6),190.5+20.32*((i-1)//6)),xy,desc='Bare PCB pad; no fitted component')
# Source generation.
rootid=uid('sheet-core'); sheetids={p:uid('sheet-'+p) for p in ['core','power','instrument']}
for page,file in [('core','airnote'),('power','power'),('instrument','instrument')]:
 cs=[c for c in components if c['page']==page]
 sch=form('kicad_sch',form('version',A('20250114')),form('generator','eeschema'),form('generator_version','9.0'),form('uuid',sheetids[page]),form('paper','A3'),form('title_block',form('title',{'core':'AirNote - RP2040 controller','power':'AirNote - USB and power','instrument':'AirNote - sensor, audio and controls'}[page]),form('date','2026-10-10'),form('rev','0.1 DRAFT'),form('company','AirNote side project')))
 sch.append(form('lib_symbols',*(symbol(z) for z in sorted({c['lib'] for c in cs}|({'power:PWR_FLAG'} if page=='power' else set())))))
 for c in cs:
  x,y=c['sch'];ref=c['ref'];u=c['unit'];lib=symbol(c['lib']);suuid=uid(ref+'unit'+str(u))
  inst=form('symbol',form('lib_id',c['lib']),form('at',n(x),n(y),n(0)),form('unit',A(str(u))),form('in_bom',A('no' if ref.startswith('TP') else 'yes')),form('on_board',A('yes')),form('dnp',A('no')),form('uuid',suuid))
  for key,val,dy,hide in [('Reference',ref,-5.08,False),('Value',c['value'],-2.54,False),('Footprint',c['footprint'],0,True),('MPN',c['mpn'],0,True),('Datasheet',next((p[2] for p in children(lib,'property') if p[1]=='Datasheet'),''),0,True)]:
   lp=next((p for p in children(lib,'property') if p[1]==key),None)
   if lp and key in ('Reference','Value'):
    ax,ay,aa=map(float,child(lp,'at')[1:]);ef=copy.deepcopy(child(lp,'effects'))
    if ref=='Y1':ax=0;ay=17.78 if key=='Reference' else 15.24
    inst.append(form('property',key,val,form('at',n(x+ax),n(y-ay),n(aa)),ef))
   else:inst.append(form('property',key,val,form('at',n(x+3.81),n(y+dy),n(0)),fx(1.0,hide)))
  path='/'+rootid if page=='core' else '/'+rootid+'/'+uid('hier-'+page)
  inst.append(form('instances',form('project','airnote',form('path',path,form('reference',ref),form('unit',A(str(u)))))))
  seen=set()
  for p in pins(c['lib'],u):
   num=child(p,'number')[1];px,py,pa=map(float,child(p,'at')[1:]);px+=x;py=y-py
   inst.append(form('pin',num,form('uuid',uid(ref+'pin'+num))))
   net=c['nets'].get(num); key=(px,py,net)
   if key in seen:continue
   seen.add(key)
   if net is None:
    sch.append(form('no_connect',form('at',n(px),n(py)),form('uuid',uid(ref+'NC'+num))))
   else:
    dx,dy={0:(-7.62,0),180:(7.62,0),90:(0,5.08),270:(0,-5.08)}[int(pa)]
    ex,ey=px+dx,py+dy
    sch.append(form('wire',form('pts',form('xy',n(px),n(py)),form('xy',n(ex),n(ey))),form('stroke',form('width',A('0')),form('type',A('default'))),form('uuid',uid(ref+'wire'+num))))
    # Global labels connect sheet boundaries explicitly; orientation points toward wire.
    ang={0:180,180:0,90:270,270:90}[int(pa)]
    sch.append(form('global_label',net,form('shape',A('input')),form('at',n(ex),n(ey),n(ang)),form('effects',form('font',form('size',n(1),n(1))),form('justify',A('right' if ang in (180,270) else 'left'))),form('uuid',uid(ref+'label'+num))))
  sch.append(inst)
 if page=='power':
  for i,net in enumerate(['+5V','GND','ADC_3V3']):
   x=254+30.48*i;y=177.8;ref='#FLG0'+str(i+1)
   ins=form('symbol',form('lib_id','power:PWR_FLAG'),form('at',n(x),n(y),n(0)),form('unit',A('1')),form('in_bom',A('no')),form('on_board',A('yes')),form('dnp',A('no')),form('uuid',uid(ref)),form('property','Reference',ref,form('at',n(x),n(y),n(0)),fx(1,True)),form('property','Value','PWR_FLAG',form('at',n(x),n(y-5.08),n(0)),fx(1)),form('instances',form('project','airnote',form('path','/'+rootid+'/'+uid('hier-power'),form('reference',ref),form('unit',A('1'))))))
   sch.append(ins)
   sch.append(form('global_label',net,form('shape',A('input')),form('at',n(x),n(y),n(0)),fx(.9),form('uuid',uid(ref+'label'))))
 if page=='core':
  for p,x,y in [('power',322.58,198.12),('instrument',322.58,228.6)]:
   sh=form('sheet',form('at',n(x),n(y)),form('size',n(60.96),n(17.78)),form('stroke',form('width',n(.15)),form('type',A('default'))),form('fill',form('color',A('0'),A('0'),A('0'),A('0'))),form('uuid',uid('hier-'+p)),form('property','Sheetname',p.title(),form('at',n(x),n(y-1.27),n(0)),fx(1.27)),form('property','Sheetfile',p+'.kicad_sch',form('at',n(x),n(y+19.05),n(0)),fx(1.27)),form('instances',form('project','airnote',form('path','/'+rootid,form('page','2' if p=='power' else '3')))))
   sch.append(sh)
  sch.append(form('sheet_instances',form('path','/',form('page','1'))))
 notes={'core':['Reference: Raspberry Pi Hardware design with RP2040, sections 2.1-2.5.','One 100 nF capacitor per MCU supply pin; +1V1 from on-chip regulator.','12 MHz ABM8-272-T3; 1 kohm drive resistor and 15 pF load capacitors.','Prototype only: assembly, factory quote and physical validation pending.'], 'power':['USB wall adapter: regulated 5 V, >=1 A. ONE SUPPLY PATH ONLY.','Computer programming: set hardware switch to MUTE before connection.','USB-C: separate 5.1k Rd on CC1 and CC2; USB 2.0 data only, no PD.','3V3 LDO thermal/current budget and USB rail drop require bench verification.'], 'instrument':['Sensor AVDD and pull-ups = 3.3 V. Driver must explicitly select 2V8 I/O mode.','XSHUT: drive low or release high-Z. Never enable RP2040 internal pull-up.','MAX98357A: GAIN floating = 9 dB; SD high selects LEFT. Duplicate audio on L/R.','Hardware MUTE grounds AMP_SD through switch and drives MUTE_N low.','Speaker is bridge-tied: neither speaker wire may connect to ground.','Optical factory process: dry reflow, no-wash, MSL3, remove liner, offset calibrate.']}
 for i,t in enumerate(notes[page]):sch.append(form('text',t,form('at',n(40.64),n(236.22+i*5.08) if page!='core' else n(233.68+i*5.08),n(0)),form('effects',form('font',form('size',n(1.1),n(1.1))),form('justify',A('left'))),form('uuid',uid(page+'note'+str(i)))))
 (ROOT/(file+'.kicad_sch')).write_text(dump(sch)+'\n')
# BOM and machine-readable independent audit input.
unique={c['ref']:c for c in components}; rows=list(unique.values())
with open(ROOT/'bom.csv','w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Manufacturer','MPN','Footprint','Assembly','Notes'])
 for c in rows:w.writerow([c['ref'],c['value'],c['manufacturer'],c['mpn'],c['footprint'],'PCB only' if c['ref'].startswith('TP') else 'Fit',c['description']])
(ROOT/'pin_net_manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
# Native board, exact library footprint geometry.
b=pcb.BOARD();b.SetCopperLayerCount(4)
for name in sorted({net for c in rows for net in c['nets'].values() if net}):b.Add(pcb.NETINFO_ITEM(b,name))
nets=b.GetNetsByName()
for c in rows:
 lib,name=c['footprint'].split(':');f=pcb.FootprintLoad(str(ROOT/'libraries'/'AirNote.pretty' if lib=='AirNote' else FP/(lib+'.pretty')),name)
 if not f:raise RuntimeError(c['footprint'])
 f.SetReference(c['ref']);f.SetValue(c['value']);f.SetPosition(pcb.VECTOR2I(pcb.FromMM(c['xy'][0]),pcb.FromMM(c['xy'][1])));f.SetOrientationDegrees(c['rot'])
 f.SetPath(pcb.KIID_PATH('/'+rootid+'/'+uid(c['ref']+'unit1') if c['page']=='core' else '/'+rootid+'/'+uid('hier-'+c['page'])+'/'+uid(c['ref']+'unit1')))
 for p in f.Pads():
  net=c['nets'].get(p.GetNumber())
  if net:p.SetNet(nets[net])
 f.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8),pcb.FromMM(.8)));f.Reference().SetTextThickness(pcb.FromMM(.12));f.Value().SetVisible(False)
 b.Add(f)
 # Vendor-independent local footprint snapshots, including exact pin numbering.
 dst=ROOT/'libraries'/'AirNote.pretty'/(name+'.kicad_mod')
 if lib!='AirNote' and not dst.exists():shutil.copy(FP/(lib+'.pretty')/(name+'.kicad_mod'),dst)
# Rounded rectangle approximation: conservative straight outline, 90x70mm.
for start,end in [((50,50),(140,50)),((140,50),(140,120)),((140,120),(50,120)),((50,120),(50,50))]:
 s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(pcb.VECTOR2I(*[pcb.FromMM(x) for x in start]));s.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(x) for x in end]));s.SetLayer(pcb.Edge_Cuts);s.SetWidth(pcb.FromMM(.05));b.Add(s)
for i,(x,y) in enumerate([(54,54),(136,54),(54,116),(136,116)],1):
 f=pcb.FootprintLoad(str(FP/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5');f.SetReference('H'+str(i));f.SetValue('M2.5');f.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));b.Add(f)
for txt,x,y,size in [('AIRNOTE',74,93,2.5),('v0.1 DRAFT', eighty:=80,97,1),('SENSOR - KEEP CLEAR',119,55,1),('MUTE    PLAY',121,117.5,1),('8 OHM SPEAKER',130,109,1),('VOLUME',75,116,1),('5V USB',61, sixty:=60,1)]:
 t=pcb.PCB_TEXT(b);t.SetText(txt);t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)));t.SetTextThickness(pcb.FromMM(.15));t.SetLayer(pcb.F_SilkS);b.Add(t)
# Save base; routing is a distinct reproducible stage.
pcb.SaveBoard(str(ROOT/'airnote.kicad_pcb'),b,True)
pro={'meta':{'filename':'airnote.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.127,'min_track_width':0.15,'min_via_diameter':0.45,'min_through_hole_diameter':0.2,'min_copper_edge_clearance':0.3},'defaults':{'track_width':0.2},'drc_exclusions':[]}},'net_settings':{'meta':{'version':4},'classes':[{'name':'Default','clearance':0.127,'track_width':0.2,'via_diameter':0.5,'via_drill':0.25,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.2,'diff_pair_gap':0.15,'diff_pair_via_gap':0.25}]},'schematic':{},'erc':{}}
(ROOT/'airnote.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "AirNote")(type "KiCad")(uri "${KIPRJMOD}/libraries/AirNote.pretty")(options "")(descr "Pinned standard footprint snapshots")))\n')
print(f'Generated {len(rows)} components, 3 schematic sheets and 4-layer placed PCB.')

local=symbol('AirNote:MAX98357A');local[1]='MAX98357A'
(ROOT/'libraries'/'AirNote.kicad_sym').write_text(dump(form('kicad_symbol_lib',form('version',A('20241209')),form('generator','kicad_symbol_editor'),local))+'\n')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name \"AirNote\")(type \"KiCad\")(uri \"${KIPRJMOD}/libraries/AirNote.kicad_sym\")(options \"\")(descr \"MAX98357A EP pin corrected to passive; datasheet requires GND\")))\n')
