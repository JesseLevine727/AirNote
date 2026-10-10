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

The board is 90 × 70 mm with four M2.5 mounting holes and three global fiducials (FID1 53.5/61.5, FID2 61.5/116.5, FID3 130.0/53.5 mm; 1 mm copper, 2 mm mask opening, board-only, excluded from BOM and position files). Signals route on F.Cu and B.Cu; In1.Cu and In2.Cu are ground reference planes. There are also outer ground pours. Minimum designed track/clearance is 0.15/0.127 mm; through vias are 0.45 mm copper with 0.20 mm drill. These are copper-path estimates from `reviews/inspect_trace_paths.py`, not measured supply integrity: IOVDD pin 22 to C6 about 2.9 mm (C6 GND pad via about 0.4 mm from the pad), DVDD pin 23 to C11 about 1.1 mm, IOVDD pin 33 to C7 about 1.6 mm and flash VCC to C15 about 3.1 mm. Crystal startup and oscillator margin remain bench checks.

The +5V rail after F1 is 0.4 mm wide (rev 0.2 review follow-up). F1 → U3 input and C16 is now 36.6 mm of 0.4 mm F.Cu with no vias, about 0.05 Ω estimated; it was 0.15 mm and about 0.12 Ω. F1 → U5 VDD/PVDD is 0.4 mm on F.Cu and on the B.Cu run, about 0.12 Ω estimated; it was 0.15 mm and about 0.31 Ω. At U5 the B.Cu-to-F.Cu change now has two vias in parallel. The C21/C22 bulk link is 0.4 mm. Three short sections stay narrower:

- The U5 pin 7/8 stubs are 0.3 mm, the pad width.
- The U3 EN tie (pin 3 to pin 1) is 0.15 mm; it carries no load current.
- The single F.Cu-to-B.Cu via beside SW2 and C19 has no room for a second via without rerouting RUN and SENSOR_XSHUT.

Resistances are copper estimates, not measurements.

The MCU is RP2040 with W25Q16JVSNIQ flash and a 12 MHz crystal. VL53L1CXV0FY/1 uses 3.3 V AVDD, 3.3 V I2C pull-ups and explicit 2V8-mode initialization. MAX98357AETE+T drives an external 8 Ω speaker; neither speaker terminal may connect to ground. Its GAIN pin floats for 9 dB, and SD high selects LEFT; firmware sends the same sample in both channels. A 10 kΩ resistor between GP14 and AMP_SD limits contention when the hardware MUTE switch forces shutdown. A separate switch pole makes GP15 low in MUTE. The volume potentiometer has a 1 MΩ ADC pull-down so an open wiper tends toward silence.

| Function | RP2040 GPIO |
|---|---:|
| I2C SDA / SCL | 0 / 1 |
| VL53L1X XSHUT / interrupt | 2 / 3 |
| I2S data / bit clock / LR clock | 10 / 11 / 12 |
| Amplifier enable / active-low mute sense | 14 / 15 |
| Status LED / volume ADC | 25 / 26 |

Use a regulated USB 5 V supply rated at least 1 A for PLAY. Set MUTE before connecting a computer for programming. The 250 mA USB descriptor is a declaration, not a measurement. USB inrush, configured current, suspend current, regulator temperature and actual speaker power remain physical test gates. See [calculated power budget](../docs/power_budget.md) and [bring-up procedure](../docs/bringup.md).

Factory assembly is required for the optical LGA and MCU/amp exposed-pad packages. Before release, the assembler must confirm the exact MPN supply, four-layer stackup, optical-device dry/no-wash process, MSL handling, sensor liner removal, post-reflow offset calibration, paste stencil and exposed-pad via fill/cap or equivalent validated process. The board includes thermal vias in the MCU and amplifier exposed pads. The external speaker, mating cable and power adapter are not PCBA BOM items. Through-hole controls/connectors require an assembly quote as well. Verify actual switch lever direction against MUTE/PLAY silkscreen during bring-up. No parts or boards have been ordered and no quoted total cost is available.

## Layout and sourcing notes

### Stackup

The board stackup is JLCPCB JLC04161H-7628, the chosen stackup per `docs/fabrication_plan.md` (1.6 mm nominal; KiCad sum 1.606 mm including 0.01 mm masks): F.Cu 0.035 / 7628 prepreg 0.2104 mm, εr 4.4 / In1.Cu 0.0152 / core 1.065 mm, εr 4.6 / In2.Cu 0.0152 / 7628 prepreg 0.2104 mm, εr 4.4 / B.Cu 0.035, solder mask both sides (εr 3.8). Re-check the stackup code on the order form. The copper finish is deliberately left unset in CAD (`None` in the Gerber job) because it is chosen on the order form: ENIG recommended, lead-free HASL acceptable. That is the user's decision.

### USB geometry

USB_DP, USB_DM, USB_DP_ESD, USB_DM_ESD, USB_DP_MCU and USB_DM_MCU are net class `USB_DIFF`: 0.25 mm traces, 0.15 mm pair gap (about 90 Ω differential on this stackup by the overseer's 2D field-solver estimate; USB full speed tolerates 90 Ω ±15%), 0.2 mm clearance to other nets, and a custom rule that keeps the outer GND pour 0.5 mm away so the pair is edge-coupled microstrip rather than coplanar. Neck-down to 0.15 mm happens at the J1, D1 and U1 pads, including two runs of about 3 mm through D1's pad gap. About 85% of each polarity runs at exactly 0.40 mm pitch. The uncoupled remainder is the J1 fan-out and duplicate-contact joins, the D1 pad entries and the staggered R8/R9. The whole path is on F.Cu with **zero vias**, over continuous In1.Cu GND (a script samples the trace footprint plus 0.1 mm and finds no In1 void or antipad under it).

- J1: the duplicated contacts are joined by short 0.15 mm stubs: DP (A6–B6) behind the pad row under the receptacle body, DM (A7–B7) in front of it. The pair leaves from B6/A7.
- D1 (USBLC6-2SC6) is about 15 mm along the pair from J1. The schematic order J1 → D1 → R8/R9 → U1 needs the pair to swap sides twice; both swaps happen inside D1 without vias. USB_DM runs through the gap between D1's pad columns to pin 3, and USB_DP_ESD leaves pin 6 through the same gap, using D1's internal pin 1–6 and 3–4 links as the crossovers. VBUS_RAW (pin 5) and GND (pin 2, own via) leave from the outer pad ends.
- R8/R9 sit side by side about 3 mm above U1 pins 47/46. The R → U1 section is matched within 0.23 mm (3.30 / 3.53 mm).
- Lengths, pad edge to pad edge, along the B6 and A7 trunks (reviewer's measurement, `reviews/layout-review.json`): J1 → D1 13.80 mm DP / 15.61 mm DM; D1 → R8/R9 43.66 / 41.40 mm; R8/R9 → U1 3.30 / 3.53 mm.
  - The per-section difference of about ±2 mm in the first two sections comes from where the D1 crossover puts the gap run (before the package for DM, after it for DP).
  - Through D1, the J1 → U1 totals are 60.76 mm DP and 60.53 mm DM, a 0.23 mm skew.
  - The USB-C duplicate-contact joins add orientation-dependent skew: up to about 2.8 mm with the plug on A6/A7 and 0.8 mm on B6/B7. That is about 17 ps, negligible against the 83 ns full-speed bit time.
- The pair is about 60 mm long (previously about 50 mm, routed as separate nets). It goes around the east side of the flash and approaches U1 from the north.
- USB impedance and differential behaviour are **not measured**. These are layout checks only. Request impedance control or an impedance coupon from the fabricator if the actual differential impedance matters.

### Crystal and RP2040 supply pins

Y1 (rotated −90°) sits directly below U1 pins 20/21. XIN is about 4.0–4.1 mm from pin 20 to Y1 pin 1 on F.Cu with no vias. XOUT runs about 0.8 mm straight into R1 (1 kΩ). XTAL_OUT runs about 4.1 mm from R1 pin 2, down the gap between Y1's pad columns, to Y1 pin 3. C1 and C2 are about 1 mm from Y1 pins 1 and 3 and have their own GND vias. Y1 GND pads 2 and 4 each have a GND via. U1 pin 19 GND, C5 and the F.Cu GND pour surround the network. No unrelated signal runs on F.Cu between the crystal network and U1 or under the crystal. The JLC listing for this crystal gives CL = 10 pF. C1/C2 stay at 15 pF: with about 3 pF stray that is about 10.5 pF, the RP2040 hardware design guide values. Frequency offset and startup margin must be measured at bring-up.

### Sourcing

`bom.csv` and every fitted schematic symbol carry an `LCSC` part number, and fitted footprints carry hidden `MPN`/`LCSC` fields for BOM/CPL generation. Passives use JLC Basic parts. R8/R9 (27 Ω, C25190) are JLC Extended. **Correction:** U2 is now W25Q16JVSNIQ, the 150-mil SOIC-8 that matches the placed SOIC-8_3.9x4.9 footprint. The previous W25Q16JVSSIQ is the 208-mil package, a part/footprint mismatch. Other substitutions:

- J1 is USB4105-GF-A-120 (same land pattern, 1.20 mm shell stakes).
- J2 is a generic straight 1x5 2.54 mm header (C32713271).
- RV1 is PTV09A-4015F-B103 (bushingless, 15 mm flat shaft). Bourns gives one recommended layout for all rear-mount PTV09 configurations, so the existing footprint is unchanged. The knob sits about 5 mm lower than with -1020F.

### Rev 0.2 review fixes

- The J1 shell stitching via at (67.80, 56.12) is removed (MFG-05). Its drill was 0.13 mm from the S1 shell slot, and the S1 pads are solid in GND on every layer.
- The reviewer's drill-web check (`reviews/inspect_layout.py`) now passes: via to via ≥ 0.2 mm, via to pad hole ≥ 0.45 mm.
- The C15 GND-pad via moved to (95.34, 66.94); its drill edge is 0.15 mm outside the pad.
- The board is marked rev 0.2: silkscreen "v0.2 ENGINEERING PROTOTYPE", PCB title block AirNote / 0.2 / 2026-10-10 (the Gerber job revision reads 0.2), and schematic title blocks rev 0.2.
- B.Silkscreen carries `JLCJLCJLCJLC` at (70, 90) so JLC prints its order number there.
- The JLC order files are generated by `tools/export_outputs.py`. See [the export README](outputs/DRAFT-fabrication/README.md) for upload steps.

## Re-export and regeneration

With KiCad 9 CLI installed, run from the repository root:

```sh
/usr/bin/python3 hardware/tools/export_outputs.py
```

This runs ERC and DRC, refuses failed checks, and regenerates PDF, render, Gerbers, drills, fitted BOM/positions, the JLC order files and an SHA-256 artifact manifest. It does not edit the canonical schematic or PCB. Position coordinates use KiCad's absolute origin in millimeters, with exported Y convention; the assembler must confirm rotations/origin. Test pads, mounting holes and fiducials are excluded from the position files. The export also writes the JLCPCB order package: `airnote-jlc-bom.csv`, `airnote-jlc-cpl.csv` (KiCad rotations, uncorrected) and `airnote-jlc-gerbers.zip`, all hashed in the artifact manifest.

`generate_hardware.py` creates only an initial schematic/placement in a **fresh separate directory**:

```sh
/usr/bin/python3 hardware/tools/generate_hardware.py --output-dir /tmp/airnote-rebuild
```

It intentionally refuses the canonical `hardware/` directory or an existing PCB output. The generator does **not** reproduce the final routed board: subsequent placement and local routing corrections live in the canonical editable PCB. Its output is a design-development starting point, not a replacement manufacturing source. Other scripts in `tools/` record the development routing stages and can overwrite a working PCB; do not rerun those on the canonical design. Historical router sessions and intermediate `reports/*.kicad_pcb` boards are development evidence, not order candidates. Use only `*-final.json` reports and the current artifact hashes for the final checkpoint. The custom rules in `airnote.kicad_dru` now carry explicit units; the earlier unit-less file was rejected by KiCad, so those rules had not been applied before.

Project-local libraries include a datasheet-correct MAX98357A exposed-pad symbol and exact ADI 90-0031 land pattern. J1's local footprint differs from the installed KiCad footprint only in two unplated peg-hole layer masks: `F&B.Cu` becomes `*.Cu`, matching KiCad's four-layer normalization. Pad locations, dimensions, drills, shell slots and contact mapping are unchanged. Standard native library footprints are embedded in the PCB and additional snapshots are retained locally.

References: [RP2040 hardware design guide](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf), [official reference source](https://datasheets.raspberrypi.com/rp2040/Minimal-KiCAD.zip), [ST VL53L1X datasheet](https://www.st.com/resource/en/datasheet/vl53l1x.pdf), [MAX98357A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf), [ADI land pattern 90-0031](https://mds.analog.com/api/public/content/90-0031.pdf), [Bourns potentiometer drawing](https://www.bourns.com/docs/product-datasheets/ptv09.pdf). The downloaded Raspberry Pi source retains its original license in `reference/`; KiCad library snapshots originate from the installed KiCad libraries and retain their upstream licensing.
