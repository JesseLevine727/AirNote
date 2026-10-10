# Independent review status

Date: 2026-10-10. Status: **REV 0.2 STATIC REVIEW: NO OPEN FAIL. NOT RELEASED; ORDER-TIME AND PHYSICAL ITEMS PENDING**.

Reviewed artifact: commit `f187767`, PCB `52b4bbc073e0d8ea3d90a4f6ff3984c31e7b3e20a18f3a391a13dbab2314860a`. Previous review: commit `0d1927e` covering PCB `b73600b2…7d0` (commit `78444e8`). See [FINAL_REVIEW.md](FINAL_REVIEW.md).

**First-article gate (static review).** No static FAIL is open. MFG-05 and MFG-11 are closed. A first-article order is not blocked by any CAD, export or order-file finding.

Before paying, four things remain:
- the MFG-01 supplier items;
- the MFG-12 check of rotations and anchors in JLC's placement preview;
- the finish and POFV choices on the order form;
- the overseer dispositions listed below.

**Physical items.** Everything under BENCH-01 and every "PENDING (physical)" part stays pending until boards exist. None of it is a prerequisite for ordering first articles.

| ID | Status | Finding / evidence | Owner |
|---|---|---|---|
| ARCH-01 | PASS | Unchanged. | Overseer |
| CIR-01 | PASS (limited scope) | `artifact-audit.json` reports 922 checks and 0 failures. A fresh schematic netlist equals `outputs/airnote.net.xml`. Components and nets equal 78444e8 (73 nets). The three schematic files differ only in title-block rev "0.1 DRAFT" → "0.2". | Reviewer |
| CIR-02 | PASS (static code) / PENDING (physical) | Unchanged; firmware is unchanged. | Overseer / reviewer |
| CIR-03 | PASS (arithmetic) / PENDING (electrical) | Unchanged; the power docs are unchanged. The inrush figure of 57.4 µC is an accepted deviation, not a pass. `power-budget-review.json` is updated to f187767. | Overseer / reviewer |
| FW-01..04 | As before | Firmware is unchanged since c298357. The host-suite evidence still matches. | Reviewer |
| PCB-01 | PASS | KiCad 9.0.9 ERC reports 0. DRC reports 0 violations, 0 unconnected and 0 parity (`--severity-all --all-track-errors --schematic-parity`). Saved fills equal an in-memory refill. | Implementer / reviewer |
| PCB-02 | PASS | Unchanged. In1 and In2 are each still a single fill. | Reviewer |
| PCB-03 | PASS | `final-trace-paths.txt`: every primary bypass path is identical to 78444e8, including U3.1→C16 4.03 mm and U5.7→C21 1.30 mm. Only far cross-paths moved by about 0.6 mm. | Reviewer |
| PCB-04 | PASS (static) / PENDING (impedance, operation) | Re-run on f187767. USB copper is unchanged. Pull-back from the pour is 0.500 mm and In1 coverage is unchanged. Coupling is 84.9%/85.7%, and skew is 0.23 mm (worst 2.8 mm ≈ 17 ps). | Reviewer |
| PCB-05 | PASS | Unchanged. | Reviewer |
| PCB-06 | PASS | +5V is now 0.4 mm. F1→U3 is 36.6 mm, no vias, ≈0.047 Ω. F1→U5 is 92 mm at 0.4 mm with 0.3 mm pin stubs, ≈0.12 Ω (series upper bound), with 2 parallel vias at U5 and a 0.4 mm C21–C22 link. The single via near SW2/C19 and the 0.15 mm U3 EN tie (no load) are as stated. VBUS_RAW is unchanged. | Implementer / reviewer |
| PCB-07 | PASS | Regression vs 0d1927e: only the +5V and GND copper changed. Pad-to-net assignments are identical (272 pads), and no footprint moved. | Reviewer |
| PCB-08 | PASS (layout) / PENDING (oscillator) | Unchanged. XIN is 4.0 mm, there are no crystal vias, and the hull contents are unchanged. | Reviewer |
| PCB-09 | PASS | The custom-rule probe still loads the rules and flags all 38 USB 0.25 mm tracks. | Reviewer |
| PCB-10 | PASS | Stackup unchanged; the Gerber job matches. | Reviewer |
| MFG-01 | PENDING (order time) | Quote, stock on the day (J1 C5184243, RV1 C5710902), optical-sensor handling (no-wash, liner), POFV/tented choice and finish choice. | Overseer / user / supplier |
| MFG-02 | PASS | `export-review.json` reports 75 checks and 0 failures. 118 plated and 6 non-plated holes match. The 40-entry manifest matches. Job Revision is "0.2". Vias are tented; the three fiducials are present. | Reviewer |
| MFG-03 | PASS (footprint) / PENDING (mechanics) | Unchanged. | Reviewer |
| MFG-04 | PASS | Unchanged. | Reviewer |
| MFG-05 | **PASS (closed)** | The via at (67.798, 56.124) is gone. The drill-web check finds no violation (via-via ≥0.2 mm; via-pad hole ≥0.45 mm). All four J1 S1 pads are 100% inside the GND fill on all four layers. | Implementer / reviewer |
| MFG-06..10 | PASS | Unchanged. The fiducial and via-in-pad checks were re-run: still only the five exposed-pad vias. | Reviewer |
| MFG-11 | **PASS (closed)** | Silkscreen reads "v0.2 ENGINEERING PROTOTYPE" (Gerber render inspected). The PCB title block is AirNote / 0.2, and the job Revision is "0.2". The three schematic title blocks read 0.2, a field-only change. Finish "None" is an overseer disposition: it is chosen on the order form, and I agree. The export README is rewritten. | Implementer / overseer |
| MFG-12 | PASS (coherence) / PENDING (JLC preview) | JLC BOM has 26 lines and 58 parts, each exactly once, with no TP/H/FID. LCSC number, footprint and comment agree with bom.csv. The CPL has the same 58 parts; X/Y equal the KiCad anchor with Y negated, rotations equal the PCB, Layer is Top, and the headers are JLC's. The Gerber zip holds 14 files, byte-identical to the loose files. KiCad rotations are uncorrected, so check them in JLC's placement preview. | Overseer / user |
| MFG-13 | PASS | The B.Silkscreen marker `JLCJLCJLCJLC` at (70, 90) is 1.0 × 0.9 mm with a 0.15 mm stroke, which meets JLC's 1.0 mm / 0.15 mm minimum. It is mirrored and reads correctly from the bottom (Gerber render). It is ≥8.1 mm from any bottom pad or via and ≥25.9 mm from the fiducials. | Reviewer |
| CIR/DOC | PASS | `hardware/README.md` USB figures now match `layout-review.json`. | Reviewer |
| BENCH-01 | PENDING (physical) | All physical measurements. | User / reviewer |

## Overseer dispositions of earlier concerns (recorded, not passes)

These are from `docs/fabrication_plan.md`, "Review dispositions (rev 0.2)".

- **+5V 0.15 mm → fixed.** Verified under PCB-06. I agree.
- **C15 via drill at the pad edge → fixed.** The drill edge is now 0.150 mm outside the pad, and the annulus is 0.025 mm clear. I agree.
  - Wording: the plan says "moved 0.7 mm along the pad axis". The via actually moved 0.36 mm, from (95.45, 66.60) to (95.34, 66.94), and now sits 0.70 mm from the pad centre.
- **D1 about 15 mm from J1 → accepted for first articles.** I agree. ESD robustness is not an acceptance test.
- **RV1 Ø2.2 round tab holes vs 1.8 × 2.2 slots → accepted.** I agree; check the fit on the first article. The round hole covers the slot's 2.2 mm dimension, not its 2.84 mm diagonal; the tab cross-section is what has to fit.
- **Fiducial pour 0.1 mm outside the mask opening → accepted.** I agree.
- **I2S under the crystal on B.Cu, and XTAL_OUT between Y1's pads → accepted.** I agree.
- **Low stock on J1 and RV1 → re-check on the order day.** I agree; this is tracked under MFG-01.
- **Finish left `None` in CAD → chosen on the order form** (ENIG recommended, lead-free HASL acceptable). I agree.

## Minor observations (no action required for first articles)

- **Export README wording.**
  - "J1 is SMT with through-board shell stakes" is inaccurate. The 1.20 mm stakes sit in plated slots and do not pass through the 1.6 mm board.
  - The RV1 anchor note gives the pad-field centre (73.15, 105.5). The body and shaft centre (F.Fab) is (76.0, 105.5).
- **+5V under J1.** The 0.4 mm +5V trace runs under the J1 receptacle body at y = 54.1, insulated only by mask. This existed before at 0.15 mm. GCT's drawing shows no keep-out. Low risk.
- **+5V to SW1 pad.** +5V is 0.127 mm from SW1 pad 1 (BOOTSEL_SW). That is exactly the design minimum and above JLC's 0.09 mm.

## Reproducible independent checks

```sh
/usr/bin/python3 reviews/audit_artifacts.py
/usr/bin/python3 reviews/inspect_trace_paths.py > reviews/final-trace-paths.txt
# shapely + gerbonara==1.6.3 in a venv created with --system-site-packages (for pcbnew):
<venv>/bin/python reviews/inspect_layout.py      # AIRNOTE_PREVIOUS=<commit> selects the regression baseline (default 0d1927e)
<venv>/bin/python reviews/inspect_exports.py
kicad-cli pcb drc --format json --severity-all --all-track-errors --schematic-parity --exit-code-violations -o reviews/drc-final.json hardware/airnote.kicad_pcb
kicad-cli sch erc --format json --severity-all --exit-code-violations -o reviews/erc-final.json hardware/airnote.kicad_sch
```

## Actionable findings history

- **MFG-05.** Opened at 78444e8 (J1 via-to-slot web 0.13 mm); closed at f187767.
- **MFG-11.** Opened at 78444e8 (v0.1 silk, `rev?`, stale export README); closed at f187767. The finish is dispositioned to the order form.
- **MFG-03.** RV1 -4015F footprint fit verified at 78444e8.
- **U2.** Corrected to W25Q16JVSNIQ at 78444e8.
- **PCB-09.** Custom rules enforced from 78444e8.
- **Rev 0.1 items.** USB pair, IOVDD22 and crystal were corrected at 78444e8.
- **Earlier items.** FW-02, CIR-04, MFG-04, PCB-02 and CIR-03 as previously recorded.
