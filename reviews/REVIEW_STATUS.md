# Independent review status

Date: 2026-10-10. Status: **REV 0.2 REVIEWED — TWO FAILS OPEN (MFG-05, MFG-11); NOT RELEASED FOR FABRICATION**.

Reviewed artifact: commit `78444e8`, PCB `b73600b23573f1bac7330f827d21ea167084af3bd38f8e93b8ca05c0155987d0`. Previous reviewed PCB: `c35f7d922f362b58a088193dba98902f71df68bcac94774f78b6f83b8618e9cc` (commits `c298357`/`14e63ae`). See [FINAL_REVIEW.md](FINAL_REVIEW.md) for the disposition and evidence boundaries.

This status covers the fully integrated RP2040 / VL53L1X / MAX98357A design. No physical board has been built or tested.

| ID | Status | Finding / evidence | Owner |
|---|---|---|---|
| ARCH-01 | PASS | Fully integrated hardware with factory assembly; four layers. Unchanged. | Overseer |
| CIR-01 | PASS (limited scope) | `artifact-audit.json`: 922 checks, 0 failures. Covers critical pins, passive values, schematic/PCB pads and firmware pins. bom.csv, schematic and footprint MPN/LCSC fields agree for every fitted part, and all 26 MPN-to-LCSC pairs match the live LCSC listings. A fresh schematic netlist equals `outputs/airnote.net.xml`. | Reviewer |
| CIR-02 | PASS (static code) / PENDING (physical) | Unchanged; firmware is unchanged since `c298357`. | Overseer / reviewer |
| CIR-03 | PASS (arithmetic) / PENDING (electrical) | `power-budget-review.json` updated to the current docs. Inrush charge recomputed from the netlist: 0.53 + 30.45 + 25.08 + 1.32 = 57.4 µC, against the 50 µC USB-IF guideline. Inrush and suspend are overseer-accepted first-article deviations, not passes. | Overseer / reviewer |
| FW-01 | PASS (host logic) | Independent ASan/UBSan suite rebuilt and re-run on this revision: 1,056,569 assertions pass. | Reviewer |
| FW-02 | PASS | Unchanged (firmware hashes in `firmware-static-review.json` still match). | Overseer / reviewer |
| FW-03 | PASS (static) | Unchanged. | Reviewer |
| FW-04 | PASS (static policy) / PENDING (electrical) | Unchanged. | Reviewer |
| PCB-01 | PASS (native checks) | KiCad 9.0.9, independent run: ERC 0. DRC 0 violations, 0 unconnected, 0 parity, with `--severity-all --all-track-errors --schematic-parity`. Saved zone fills equal an in-memory refill. | Implementer / reviewer |
| PCB-02 | PASS | Signals on F.Cu/B.Cu only. In1.Cu and In2.Cu are each one continuous GND fill. | Implementer / reviewer |
| PCB-03 | PASS | Bypass paths are equal or better than the previous revision (`final-trace-paths.txt`). IOVDD22→C6 6.07→2.94 mm; DVDD23→C11 1.49→1.07 mm; all other primary pairs unchanged. | Implementer / reviewer |
| PCB-04 | PASS (static layout) / PENDING (impedance, USB operation) | `layout-review.json`: six USB nets in USB_DIFF, F.Cu only, 0 vias; 85–86% of each polarity at exactly 0.40 mm pitch. F.Cu GND pull-back 0.500 mm. In1 has no void under the pair footprint + 0.3 mm. ≥0.201 mm to other nets. Skew through D1 is 0.23 mm (DP 60.76, DM 60.53 mm); the worst plug orientation is 2.8 mm ≈ 17 ps, against an 83 ns full-speed bit. The ±2 mm per-section mismatch is immaterial at full speed. R8/R9 are 3.3/3.5 mm from U1. CC1/CC2 5.1 k pull-downs are intact. | Implementer / reviewer |
| PCB-05 | PASS | USBLC6-2SC6 crossover. ST datasheet Fig. 1/7/8: pins 1/6 = I/O1 and 3/4 = I/O2, joined inside the package; 2 = GND, 5 = VBUS. PCB nets match: 1 DP, 6 DP_ESD, 3 DM, 4 DM_ESD, 2 GND, 5 VBUS_RAW. Two 0.15 mm traces in the 0.95 mm pad gap keep 0.205 mm to the pads. DRC and the Gerber render show no crossing. | Implementer / reviewer |
| PCB-06 | PASS (with concern) | VBUS_RAW main path: J1 A4/B9 → F1 is 0.4 mm F.Cu, 5.5 mm, 0 vias, ≈8 mΩ (was ~30 mm of 0.3 mm via TP1/D1). The west pad's 0.3 mm path with 2 vias runs in parallel. Concern: +5V after F1 is still 0.15 mm (unchanged): ≈0.12 Ω to U3 and ≈0.31 Ω to U5. That is adequate for the 210 mA allocation (IPC-2221 ≈0.6 A at 10 °C rise) but thin. | Implementer |
| PCB-07 | PASS | Rerouted non-USB nets (BOOTSEL_SW, CC1, SENSOR_XSHUT, QSPI_D0, +3V3, +1V1, SWCLK, RUN, I2C_SCL, VBUS_RAW) keep ≥0.15 mm. New vias are tented, and the +1V1 pad-ring via is tented. The crystal network has no vias, and the only foreign F.Cu copper inside its hull is the IOVDD22 bypass branch. Other-net F.Cu track within 0.5 mm of the USB pair fell from ≈22 mm to 3.6 mm. | Implementer / reviewer |
| PCB-08 | PASS (layout, load caps) / PENDING (oscillator margin) | XIN pin 20 → Y1.1 4.0–4.1 mm, 0 vias (was 7.79 mm, 2 vias). XOUT → R1 0.6 mm. C1/C2 ≈1 mm from Y1. ABM8-272-T3 CL 10 pF with 15 pF caps plus ~3 pF stray gives 10.5 pF, the RP2040 design guide §2.3 values. Startup and frequency are bench tests. | Implementer / reviewer |
| PCB-09 | PASS | Custom rules are now enforced. A temporary copy with the USB max width lowered to 0.2 mm flags all 38 USB 0.25 mm tracks under rule "USB_DIFF width". A unit-less copy with an impossible rule produced no rule hits, confirming the old file was discarded. | Reviewer |
| PCB-10 | PASS | PCB stackup and Gerber job both equal JLC04161H-7628: 0.035 / 0.2104 PP εr 4.4 / 0.0152 / 1.065 core εr 4.6 / 0.0152 / 0.2104 / 0.035, mask 0.01, 1.606 mm. | Implementer / reviewer |
| MFG-01 | PENDING | No quote or order. 2026-10-10 stock snapshot: J1 C5184243 has LCSC 0 / JLC 1,569; RV1 C5710902 has LCSC 123. Optical-sensor process, exposed-pad via treatment and finish are still to be confirmed. | Overseer / supplier |
| MFG-02 | PASS (export coherence) | `export-review.json`: 70 checks, 0 failures. 118 plated and 6 non-plated holes match the PCB. Fitted BOM/CPL equal the bom.csv fitted set (no FID/TP/H). Manifest (37 files) matches. Gerber job stackup equals the PCB. No via has its own mask opening; the five exposed-pad vias sit inside their pads' openings. Three fiducials are present in copper and mask. | Reviewer |
| MFG-03 | PASS (footprint fit) / PENDING (mechanics) | RV1 PTV09A-4015F-B103 = Bourns configuration 4 (horizontal/rear mount, bushingless), 15 mm F shaft. Bourns gives one rear-mount PCB layout, and the -1 and -4 front views are identical (10.0 body, 11.4 across tabs, 5.0 pin span, pins 7.0 from the tab line). The footprint matches: Ø1.0 pins at 2.5 mm, Ø2.2 tab holes 8.8 mm apart at +7.0 mm. LCSC C5710902 is that part. Knob, panel and the missing bushing need a first-article fit check. | Implementer / reviewer |
| MFG-04 | PASS | MAX98357A ADI 90-0031 land pattern. Unchanged; audit re-run. | Reviewer |
| MFG-05 | **FAIL** | GND via at (67.798, 56.124) mm, drill 0.20, sits 0.132 mm (drill to drill) from J1's rear-right shell-stake slot S1 (68.32, 56.78; 0.6 × 1.7 mm). JLC publishes 0.2 mm via-to-via and 0.45 mm pad-hole spacing. KiCad's 0.25 mm hole-to-hole rule did not flag this same-net pair. It is pre-existing: the previous review missed it. Fix: delete the via. The four S1 pads are solid in GND fill on all four layers and the via has no track. Alternatively, move it so the drill-to-slot web is ≥0.45 mm. | Implementer |
| MFG-06 | PASS | U2 W25Q16JVSNIQ: Winbond Rev G, "SN = 8-pin SOIC 150-mil" (E 3.80–4.00, HE 5.80–6.20, e 1.27), on the SOIC-8 3.9 × 4.9 footprint. Pin 1 is /CS. LCSC C2456211. | Reviewer |
| MFG-07 | PASS | J1 USB4105-GF-A-120: GCT drawing B4, "120 = 1.20mm" shell stake (default 0.95). Land pattern verified: slots 8.64 apart, rear 0.6 × 1.7, front 0.6 × 1.4, pegs Ø0.65 at 5.78 mm, 1.15 mm pads. Stakes do not protrude through 1.6 mm; this is the longest option. Retention is to be confirmed at assembly. | Reviewer |
| MFG-08 | PASS | J2 C32713271: 1 × 5, 2.54 mm, 0.64 mm square pin (0.91 mm diagonal) in Ø1.0 holes; vendor board range 1.2–1.6 mm. | Reviewer |
| MFG-09 | PASS | Passives: 100 nF X7R 50 V, 1 µF X5R 50 V, 4.7 µF X5R 25 V 0805 and 15 pF C0G 50 V. Every 5 V/VBUS capacitor is ≥25 V, an improvement on the old 10 V parts. AP2112 is stable with 1 µF X5R/X7R. DC-bias derating of the higher-rated parts at ≤5 V is moderate. All LCSC numbers resolve to the stated MPN/value/package. | Reviewer |
| MFG-10 | PASS | FID1–3 (1 mm Cu / 2 mm mask) at (53.5, 61.5), (61.5, 116.5) and (130, 53.5), 3.5 mm from the edges. The pattern is not 180° symmetric (FID1 has no counterpart). The pour starts 1.1 mm from centre, outside the mask opening. All three are excluded from BOM/CPL. | Reviewer |
| MFG-11 | **FAIL** (order package, non-electrical) | (a) Silkscreen reads "v0.1 ENGINEERING PROTOTYPE" on rev 0.2. (b) Gerber job Revision "rev?" and Finish "None" (no title-block revision; finish not chosen). (c) `outputs/DRAFT-fabrication/README.md` is stale: it still describes "three 0.48 mm dielectric gaps" and says the full position file includes test pads; it does not. Fix: set the silk and title-block revision to 0.2, select the finish at order time, and refresh that README. | Implementer / overseer |
| BENCH-01 | PENDING | All physical measurements; no board exists. | User / reviewer |

The procedure is in [CHECKLIST.md](CHECKLIST.md). No failed or pending criterion counts as a pass. An engineering first-article order needs MFG-05 and MFG-11 closed, supplier confirmation (MFG-01) and the overseer's dispositions of the concerns in FINAL_REVIEW.md. Physical measurements follow first-article assembly.

## Reproducible independent checks

```sh
/usr/bin/python3 reviews/audit_artifacts.py
/usr/bin/python3 reviews/inspect_trace_paths.py > reviews/final-trace-paths.txt
# shapely and gerbonara==1.6.3 in a venv created with --system-site-packages (for pcbnew):
<venv>/bin/python reviews/inspect_layout.py      # exits 1 while MFG-05 is open
<venv>/bin/python reviews/inspect_exports.py
kicad-cli pcb drc --format json --severity-all --all-track-errors --schematic-parity --exit-code-violations -o reviews/drc-final.json hardware/airnote.kicad_pcb
kicad-cli sch erc --format json --severity-all --exit-code-violations -o reviews/erc-final.json hardware/airnote.kicad_sch
g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer -I firmware/include firmware/src/instrument.cpp reviews/test_instrument_independent.cpp -o /tmp/airnote-independent-tests && /tmp/airnote-independent-tests
```

Every JSON output records the exact hashes it inspected. None of these runs the sensor, USB or audio hardware.

## Actionable findings history

- **MFG-05, open (rev 0.2 review):** the J1 shell stitching via is too close to the S1 slot. It is pre-existing from rev 0.1.
- **MFG-11, open (rev 0.2 review):** revision marking and order metadata.
- **MFG-03, re-examined:** RV1 changed from -1020F to -4015F. Bourns' single rear-mount layout and identical -1/-4 front views show the existing footprint fits. `audit_artifacts.py` now expects -4015F.
- **U2, corrected by overseer:** W25Q16JVSSIQ (208-mil) was on a 150-mil footprint in rev 0.1. W25Q16JVSNIQ is now confirmed against Winbond's package code table.
- **PCB-09, corrected:** the unit-less rule file was silently discarded by KiCad. Rev 0.2 adds units, and the reviewer independently confirmed the rules now load.
- **PCB-04 (rev 0.1 items), corrected:** USB is routed as a coupled pair over the JLC stackup. IOVDD22 and the crystal are now within targets.
- **Earlier items, unchanged:** FW-02 frozen-frame qualification; CIR-04 volume-pot pull-down; MFG-04 ADI land pattern; PCB-02 outer-layer routing; CIR-03 inrush/suspend dispositions.
