# AirNote hardware — engineering prototype

Open **airnote.kicad_pro** in KiCad 9. The three editable schematic sheets and routed four-layer PCB are the canonical design. The current native checks report **0 ERC violations; 0 DRC violations, 0 unconnected items and 0 schematic/PCB parity issues**. These are software checks; a physical board has not been built or tested.

- [Schematic PDF](outputs/airnote-schematic.pdf)
- [Board render](outputs/airnote-board.png)
- [Assembly drawing, including component references](outputs/airnote-assembly.pdf)
- [Four copper layers](outputs/airnote-copper.pdf)
- [Exact component BOM](bom.csv)
- [Draft fabrication and assembly exports](outputs/DRAFT-fabrication/)
- [Native ERC](reports/erc-final.json) and [DRC](reports/drc-final.json)
- [Independent review](../reviews/REVIEW_STATUS.md)

The render is illustrative: some exact component 3D models are absent, while their electrical footprints and assembly references remain present.

The board is 90 × 70 mm with four M2.5 mounting holes. Signals route on F.Cu and B.Cu; In1.Cu and In2.Cu are ground reference planes. There are also outer ground pours. Minimum designed track/clearance is 0.15/0.127 mm; through vias are 0.45 mm copper with 0.20 mm drill. USB, QSPI and bypass connections received local layout corrections after the initial router pass. The retained IOVDD pin22-to-C6 branch is about 6.66 mm; closer placement conflicted with the existing crystal fanout. IOVDD33-to-C7 is about 1.99 mm and flash VCC-to-C15 about 3.63 mm. These are copper path estimates, not measured supply integrity. Crystal startup and oscillator margin also remain bench checks. USB impedance and differential coupling have **not** been validated against a fabricator stackup. The nominal KiCad stackup is a placeholder until that review.

The MCU is RP2040 with W25Q16JVSSIQ flash and a 12 MHz crystal. VL53L1CXV0FY/1 uses 3.3 V AVDD, 3.3 V I2C pull-ups and explicit 2V8-mode initialization. MAX98357AETE+T drives an external 8 Ω speaker; neither speaker terminal may connect to ground. Its GAIN pin floats for 9 dB, and SD high selects LEFT; firmware sends the same sample in both channels. A 10 kΩ resistor between GP14 and AMP_SD limits contention when the hardware MUTE switch forces shutdown. A separate switch pole makes GP15 low in MUTE. The volume potentiometer has a 1 MΩ ADC pull-down so an open wiper tends toward silence.

| Function | RP2040 GPIO |
|---|---:|
| I2C SDA / SCL | 0 / 1 |
| VL53L1X XSHUT / interrupt | 2 / 3 |
| I2S data / bit clock / LR clock | 10 / 11 / 12 |
| Amplifier enable / active-low mute sense | 14 / 15 |
| Status LED / volume ADC | 25 / 26 |

Use a regulated USB 5 V supply rated at least 1 A for PLAY. Set MUTE before connecting a computer for programming. The 250 mA USB descriptor is a declaration, not a measurement. USB inrush, configured current, suspend current, regulator temperature and actual speaker power remain physical test gates. See [calculated power budget](../docs/power_budget.md) and [bring-up procedure](../docs/bringup.md).

Factory assembly is required for the optical LGA and MCU/amp exposed-pad packages. Before release, the assembler must confirm the exact MPN supply, four-layer stackup, optical-device dry/no-wash process, MSL handling, sensor liner removal, post-reflow offset calibration, paste stencil and exposed-pad via fill/cap or equivalent validated process. The board includes thermal vias in the MCU and amplifier exposed pads. The external speaker, mating cable and power adapter are not PCBA BOM items. Through-hole controls/connectors require an assembly quote as well. Verify actual switch lever direction against MUTE/PLAY silkscreen during bring-up. No parts or boards have been ordered and no quoted total cost is available.

## Re-export and regeneration

With KiCad 9 CLI installed, run from the repository root:

```sh
/usr/bin/python3 hardware/tools/export_outputs.py
```

This runs ERC and DRC, refuses failed checks, and regenerates PDF, render, Gerbers, drills, fitted BOM/positions and an SHA-256 artifact manifest. It does not edit the canonical schematic or PCB. Position coordinates use KiCad's absolute origin in millimeters, with exported Y convention; the assembler must confirm rotations/origin. The full position file is retained for traceability, while `airnote-fitted-positions.csv` omits test pads and board-only holes.

`generate_hardware.py` creates only an initial schematic/placement in a **fresh separate directory**:

```sh
/usr/bin/python3 hardware/tools/generate_hardware.py --output-dir /tmp/airnote-rebuild
```

It intentionally refuses the canonical `hardware/` directory or an existing PCB output. The generator does **not** reproduce the final routed board: subsequent placement and local routing corrections live in the canonical editable PCB. Its output is a design-development starting point, not a replacement manufacturing source. Other scripts in `tools/` record the development routing stages and can overwrite a working PCB; do not rerun those on the canonical design. Historical router sessions and intermediate `reports/*.kicad_pcb` boards are development evidence, not order candidates. Use only `*-final.json` reports and the current artifact hashes for the final checkpoint.

Project-local libraries include a datasheet-correct MAX98357A exposed-pad symbol and exact ADI 90-0031 land pattern. J1's local footprint differs from the installed KiCad footprint only in two unplated peg-hole layer masks: `F&B.Cu` becomes `*.Cu`, matching KiCad's four-layer normalization. Pad locations, dimensions, drills, shell slots and contact mapping are unchanged. Standard native library footprints are embedded in the PCB and additional snapshots are retained locally.

References: [RP2040 hardware design guide](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf), [official reference source](https://datasheets.raspberrypi.com/rp2040/Minimal-KiCAD.zip), [ST VL53L1X datasheet](https://www.st.com/resource/en/datasheet/vl53l1x.pdf), [MAX98357A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf), [ADI land pattern 90-0031](https://mds.analog.com/api/public/content/90-0031.pdf), [Bourns potentiometer drawing](https://www.bourns.com/docs/product-datasheets/ptv09.pdf). The downloaded Raspberry Pi source retains its original license in `reference/`; KiCad library snapshots originate from the installed KiCad libraries and retain their upstream licensing.
