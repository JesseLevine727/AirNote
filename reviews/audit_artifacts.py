#!/usr/bin/python3
"""Independent circuit-pin and schematic/PCB consistency audit.

Use /usr/bin/python3 for Ubuntu's pcbnew module. Critical expected connections
come from manufacturer pin tables recorded in CHECKLIST.md, not the CAD builder.
This does not prove routing continuity, PCB geometry, USB compliance, or hardware.
"""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
checks = []

def check(name, ok, detail=""):
    checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

def nc(net):
    return net is None or net == "" or net.startswith("unconnected-")

netlist_path = ROOT / "hardware/outputs/airnote.net.xml"
board_path = ROOT / "hardware/airnote.kicad_pcb"
tree = ET.parse(netlist_path).getroot()
components = {c.attrib["ref"]: c for c in tree.find("components")}
nets = {}
for net in tree.find("nets"):
    for pin in net.findall("node"):
        nets[(pin.attrib["ref"], pin.attrib["pin"])] = net.attrib["name"]

expected = {
    "U1": {"1":"+3V3","10":"+3V3","22":"+3V3","33":"+3V3","42":"+3V3",
           "49":"+3V3","44":"+3V3","45":"+1V1","23":"+1V1","50":"+1V1",
           "43":"ADC_3V3","48":"+3V3","57":"GND","19":"GND","26":"RUN",
           "46":"USB_DM_MCU","47":"USB_DP_MCU","20":"XIN","21":"XOUT",
           "24":"SWCLK","25":"SWDIO","52":"QSPI_CLK","56":"QSPI_CS",
           "53":"QSPI_D0","55":"QSPI_D1","54":"QSPI_D2","51":"QSPI_D3",
           "2":"I2C_SDA","3":"I2C_SCL","4":"SENSOR_XSHUT","5":"SENSOR_IRQ",
           "13":"I2S_DATA","14":"I2S_BCLK","15":"I2S_LRCLK",
           "17":"AMP_ENABLE","18":"MUTE_N","37":"STATUS_LED","38":"VOLUME_ADC"},
    "U2": {"1":"QSPI_CS","2":"QSPI_D1","3":"QSPI_D2","4":"GND",
           "5":"QSPI_D0","6":"QSPI_CLK","7":"QSPI_D3","8":"+3V3"},
    "U3": {"1":"+5V","2":"GND","3":"+5V","4":None,"5":"+3V3"},
    "U4": {"1":"+3V3","2":"GND","3":"GND","4":"GND","5":"SENSOR_XSHUT",
           "6":"GND","7":"SENSOR_IRQ","8":None,"9":"I2C_SDA","10":"I2C_SCL",
           "11":"+3V3","12":"GND"},
    "U5": {"1":"I2S_DATA","2":None,"3":"GND","4":"AMP_SD","5":None,"6":None,
           "7":"+5V","8":"+5V","9":"SPK_P","10":"SPK_N","11":"GND",
           "12":None,"13":None,"14":"I2S_LRCLK","15":"GND","16":"I2S_BCLK","17":"GND"},
    "J1": {"A1":"GND","A12":"GND","B1":"GND","B12":"GND","S1":"GND",
           "A4":"VBUS_RAW","A9":"VBUS_RAW","B4":"VBUS_RAW","B9":"VBUS_RAW",
           "A5":"CC1","B5":"CC2","A6":"USB_DP","B6":"USB_DP",
           "A7":"USB_DM","B7":"USB_DM","A8":None,"B8":None},
    "R6": {"1":"CC1","2":"GND"}, "R7": {"1":"CC2","2":"GND"},
    "R8": {"1":"USB_DP_ESD","2":"USB_DP_MCU"},
    "R9": {"1":"USB_DM_ESD","2":"USB_DM_MCU"},
    "D1": {"1":"USB_DP","2":"GND","3":"USB_DM","4":"USB_DM_ESD",
           "5":"VBUS_RAW","6":"USB_DP_ESD"},
    "R14": {"1":"AMP_ENABLE","2":"AMP_SD"},
    "R15": {"1":"AMP_SD","2":"GND"},
    "R19": {"1":"VOLUME_ADC","2":"GND"},
    "SW3": {"1":"GND","2":"AMP_SD","3":None,"4":"GND","5":"MUTE_N","6":None},
    "J3": {"1":"SPK_P","2":"SPK_N"},
    "J2": {"1":"+3V3","2":"GND","3":"SWDIO","4":"SWCLK","5":"RUN"},
    "SW1": {"1":"BOOTSEL_SW","2":"GND"},
    "SW2": {"1":"RUN","2":"GND"},
    "RV1": {"1":"GND","2":"VOLUME_RAW","3":"+3V3"},
    "D2": {"1":"GND","2":"LED_A"},
}
for ref, pins in expected.items():
    for pin, want in pins.items():
        actual = nets.get((ref,pin))
        check(f"manufacturer pin map {ref}.{pin}", nc(actual) if want is None else actual==want,
              f"expected={want!r}; actual={actual!r}")

for ref,want in {"R1":"1k","R2":"10k","R3":"1k","R4":"10k",
    "R6":"5.1k","R7":"5.1k","R8":"27","R9":"27","R10":"10k",
    "R11":"10k","R12":"5.1k","R13":"5.1k","R14":"10k","R15":"100k",
    "R16":"10k","R17":"1k","R18":"1k","R19":"1M",
    "C1":"15p","C2":"15p","C10":"100n","C11":"100n","C14":"1u",
    "C19":"100n","C21":"100n"}.items():
    actual=components[ref].findtext("value")
    check(f"critical passive value {ref}",actual==want,f"expected={want}; actual={actual}")

board = pcbnew.LoadBoard(str(board_path))
footprints = {f.GetReference():f for f in board.GetFootprints()}
check("four copper layers",board.GetCopperLayerCount()==4)
for ref, component in components.items():
    if ref.startswith("#"): continue
    fp = footprints.get(ref)
    check(f"component present on PCB {ref}",fp is not None)
    if fp is None: continue
    check(f"component value agreement {ref}",fp.GetValue()==component.findtext("value"))
    pad_numbers = {pad.GetNumber() for pad in fp.Pads()}
    for (node_ref,number),net in nets.items():
        if node_ref == ref and not nc(net):
            check(f"connected schematic pin has a physical pad {ref}.{number}",number in pad_numbers)
    for pad in fp.Pads():
        number = pad.GetNumber()
        if not number: continue
        expected_net = nets.get((ref,number))
        actual_net = pad.GetNetname()
        ok = nc(actual_net) if nc(expected_net) else expected_net == actual_net
        check(f"schematic/PCB pad assignment {ref}.{number}",ok,
              f"schematic={expected_net!r}; pcb={actual_net!r}")

amp = footprints["U5"]
ep = next(p for p in amp.Pads() if p.GetNumber()=="17")
check("MAX98357A official center land dimensions",
      abs(pcbnew.ToMM(ep.GetSize().x)-1.23)<0.001 and abs(pcbnew.ToMM(ep.GetSize().y)-1.23)<0.001)
for number in range(1, 17):
    pad = next(p for p in amp.Pads() if p.GetNumber()==str(number))
    offset = [-0.75, -0.25, 0.25, 0.75][(number-1)%4]
    side = (number-1)//4
    want_position = [(-1.425, offset), (offset, 1.425),
                     (1.425, -offset), (-offset, -1.425)][side]
    want_size = (0.80, 0.30) if side%2==0 else (0.30, 0.80)
    position, size = pad.GetFPRelativePosition(), pad.GetSize()
    check(f"MAX98357A official perimeter land {number}",
          all(abs(pcbnew.ToMM(actual)-want)<0.001 for actual,want in
              zip((position.x,position.y,size.x,size.y),want_position+want_size)))
check("volume ADC has 1 Mohm open-wiper discharge path",components["R19"].findtext("value")=="1M")
pot_mpn = components["RV1"].find("fields/field[@name='MPN']")
check("potentiometer MPN matches selected body variant",pot_mpn is not None and pot_mpn.text=="PTV09A-1020F-B103")

header = (ROOT/"firmware/include/boards/airnote.h").read_text()
for macro, want in {"PICO_DEFAULT_I2C_SDA_PIN":0,"PICO_DEFAULT_I2C_SCL_PIN":1,
    "AIRNOTE_XSHUT_PIN":2,"AIRNOTE_SENSOR_IRQ_PIN":3,"AIRNOTE_I2S_DATA_PIN":10,
    "AIRNOTE_I2S_BCLK_PIN":11,"AIRNOTE_I2S_LRCLK_PIN":12,"AIRNOTE_AMP_ENABLE_PIN":14,
    "AIRNOTE_MUTE_N_PIN":15,"PICO_DEFAULT_LED_PIN":25,"AIRNOTE_VOLUME_PIN":26}.items():
    match = re.search(r"^#define\s+"+macro+r"\s+(\d+)\b",header,re.M)
    check(f"firmware pin assignment {macro}",bool(match and int(match[1])==want))

sources = [netlist_path, board_path, ROOT/"firmware/include/boards/airnote.h"]
result = {"scope":"pin assignment and artifact consistency only; not routing or hardware validation",
          "sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
          "checks":checks,"failed":sum(x["status"]=="FAIL" for x in checks),
          "physical_tests":"PENDING"}
(ROOT/"reviews/artifact-audit.json").write_text(json.dumps(result,indent=2)+"\n")
for c in checks:
    if c["status"]=="FAIL": print(c)
print(f"{len(checks)} checks; {result['failed']} failures. Routing and hardware validation are separate.")
sys.exit(bool(result["failed"]))
