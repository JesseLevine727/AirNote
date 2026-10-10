# Independent review — AirNote rev 0.2

Reviewed artifact: commit `f187767`, PCB SHA256 `52b4bbc073e0d8ea3d90a4f6ff3984c31e7b3e20a18f3a391a13dbab2314860a`. Previous review: `0d1927e` (PCB `b73600b2…7d0`, commit `78444e8`).

**Static review: no open FAIL.** The two rev 0.2 failures are closed: MFG-05 (the J1 via-to-slot web) and MFG-11 (revision marking and order metadata). No CAD, export or order-file finding blocks a first-article order.

What remains is order-time confirmation (MFG-01), JLC placement-preview rotation checks (MFG-12), and the finish and via-covering choices on the order form. Everything physical stays **PENDING**. The design is not validated on hardware.

## Native and independent checks at f187767

- **KiCad.** KiCad 9.0.9 reports ERC 0. DRC reports 0 violations, 0 unconnected and 0 schematic parity, with all severities and all track errors.
- **Custom rules.** They still load (probe in `layout-review.json`). Saved zone fills equal an in-memory refill.
- **Pin and sourcing audit.** 922 checks, 0 failures.
- **Netlist.** A fresh schematic netlist equals the exported one. Components and all 73 nets are identical to 78444e8. The schematic files changed only in the title-block revision. On the PCB, all 272 pad-to-net assignments are unchanged and no footprint moved.
- **`layout-review.json`.** 25 checks, 0 failures, including the drill-web check that failed at 78444e8.
- **`export-review.json`.** 75 checks, 0 failures.

## Changes verified

- **MFG-05.** The GND via at (67.798, 56.124) is removed. No via-to-via web is under 0.2 mm, and no via-to-pad-hole web is under 0.45 mm. All four J1 shell pads lie entirely inside GND fill on all four layers. The via-in-pad set is still only the five exposed-pad vias.
- **MFG-11.**
  - The silkscreen reads "v0.2 ENGINEERING PROTOTYPE"; I confirmed this in the Gerber render.
  - The PCB title block reads 0.2, and the Gerber job Revision is "0.2".
  - The three schematic title blocks read 0.2. That is a field-only change.
  - Finish "None" stays by overseer disposition: ENIG or lead-free HASL is chosen on the order form. I agree.
  - The export README is rewritten.
- **+5V widening (PCB-06).**
  - F1→U3 is 0.4 mm, 36.6 mm long, with no vias (≈0.05 Ω).
  - F1→U5 is 0.4 mm on F.Cu and B.Cu, with 0.3 mm pad-width stubs at U5 pins 7 and 8 (≈0.12 Ω, series upper bound). Two vias in parallel feed C21 at U5, and the C21–C22 link is 0.4 mm.
  - The remaining narrow parts are as disclosed: a single via near SW2/C19, and the 0.15 mm U3 EN tie, which carries no load.
- **No regressions from the widening.**
  - Only the +5V and GND copper changed.
  - Every primary bypass path is identical (`final-trace-paths.txt`).
  - The F.Cu and B.Cu GND pours keep the same island count (11 and 2), and In1/In2 are still single fills.
  - The USB pair still has its 0.500 mm pour pull-back, 85% coupling and 0.23 mm skew.
  - The crystal neighbourhood is unchanged.
  - The closest new spacing is +5V to SW1 pad 1 at 0.127 mm. That is the design minimum and above JLC's 0.09 mm.
- **C15 via.** It is now at (95.343, 66.943). Its drill edge is 0.150 mm outside the pad and its annulus 0.025 mm clear.
- **JLC order package (MFG-12, MFG-13).**
  - **BOM.** 26 lines with 58 parts, each exactly once. There is no TP, H or FID. LCSC number, footprint and comment agree with bom.csv.
  - **CPL.** The same 58 parts, in the `Designator,Mid X,Mid Y,Layer,Rotation` format. Positions equal the KiCad anchor with Y negated, rotations equal the PCB, and Layer is Top.
  - **Gerber zip.** 11 Gerbers, 2 drill files and the job file, all byte-identical to the loose files. All 40 manifest hashes match.
  - **Order-number marker.** The bottom-side marker is 1.0 × 0.9 mm with a 0.15 mm stroke, which meets JLC's minimum. It is mirrored and reads correctly from the bottom, and it is ≥8 mm from bottom pads and vias.
- **Export README.**
  - Its order-form settings agree with `docs/fabrication_plan.md`: 4 layers, 1.6 mm, JLC04161H-7628, no impedance control, 1/0.5 oz, Standard PCBA top side, 2 of 5 boards, no washing, liner left on, and a POFV-or-tented choice.
  - The 0.20/0.45 mm vias carry no surcharge, because JLC charges extra only below a 0.45 mm via diameter.
  - The anchor notes for J1, J2 and J3 match the footprints.

## Overseer dispositions (recorded, not passes)

These are the overseer's dispositions of my earlier concerns. I agree with all of them; the wording correction is noted in REVIEW_STATUS.md.
- **Accepted for first articles:** D1's distance from J1, the RV1 round tab holes (check fit on the first article), the fiducial pour margin, and the I2S traces and XTAL_OUT routing near the crystal.
- **Fixed:** +5V width and the C15 via.
- **Re-check on the order day:** low stock on J1 and RV1.
- **Chosen on the order form:** the surface finish.

## Minor observations (no action required)

- **Export README wording.** It calls J1's 1.20 mm shell stakes "through-board", but they do not protrude through the 1.6 mm board. The RV1 note gives the pad-field centre (73.15, 105.5), while the body and shaft centre is (76.0, 105.5).
- **C15 move distance.** The fabrication plan says the via moved 0.7 mm. It actually moved 0.36 mm and now sits 0.70 mm from the pad centre.
- **+5V under J1.** The 0.4 mm +5V trace runs under J1's body at y = 54.1, with mask as the only insulation. The route existed before at 0.15 mm, and GCT's drawing shows no keep-out.

## Physical validation

Every physical criterion remains **PENDING**:
- assembly, and the rails and current;
- crystal startup and frequency;
- USB on both plug orientations, and inrush and suspend;
- calibration, notes and latency;
- audio and endurance.

Use `docs/bench-results-template.csv`.

Evidence:
- `drc-final.json`, `erc-final.json`
- `artifact-audit.json`, `layout-review.json`, `export-review.json`
- `final-trace-paths.txt`, `gerber-top-review.svg`, `gerber-bottom-review.svg`, `gerber-inner1-review.svg`
- `power-budget-review.json`, `host-test-evidence.json`, `firmware-static-review.json`
- `final-review-evidence.json`

Path figures are approximate centreline estimates, not a signal-integrity model.
