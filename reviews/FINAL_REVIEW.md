# Independent review — AirNote rev 0.2

Reviewed artifact: commit `78444e8`, PCB SHA256 `b73600b23573f1bac7330f827d21ea167084af3bd38f8e93b8ca05c0155987d0`. Previous: `c35f7d922f362b58a088193dba98902f71df68bcac94774f78b6f83b8618e9cc`.

**The rev 0.2 layout corrections pass static review. Two manufacturing findings fail: MFG-05 (a via-to-slot drill web) and MFG-11 (revision marking and order metadata). The design is not released for fabrication and is not validated on hardware.**

The KiCad 9.0.9 native checks are clean on an independent run: ERC 0; DRC 0 violations, 0 unconnected and 0 parity, with all severities and all track errors. The custom rules are now loaded. A temporary copy with the USB maximum width lowered flagged every 0.25 mm USB track, while a unit-less copy produced no rule hits. The saved zone fills equal an in-memory refill. The pin, footprint and sourcing audit runs 922 checks with no failures. Its sourcing checks confirm that every fitted part's MPN and LCSC number agree across bom.csv, the schematic and the footprints, and that all 26 MPN-to-LCSC pairs resolve on LCSC to the stated part. The firmware is unchanged; the independent host suite was rebuilt and passes.

## Layout changes reviewed

- **USB pair (PCB-04, PCB-05).** All six USB nets are in USB_DIFF on F.Cu, with no vias, over continuous In1 GND. There is no In1 void under the pair plus 0.3 mm; the only gaps within 0.6 mm are antipads of adjacent vias. The F.Cu GND pour is held back exactly 0.5 mm. About 85% of each polarity runs at exactly 0.40 mm pitch. The overseer's 93% figure was not reproduced; the uncoupled parts are J1 fan-out and duplicate-contact joins, D1 pad entries and the staggered R8/R9.
  - **Neck-down.** The 0.15 mm neck-down starts at the pads. Two 0.15 mm runs of about 3 mm pass through D1's pad gap.
  - **D1 crossover.** ST's USBLC6-2 datasheet joins pins 1–6 and 3–4 internally (Figures 1, 7 and 8). The nets land correctly: DP on 1, DP_ESD on 6, DM on 3, DM_ESD on 4, GND on 2 with its own via, VBUS on 5. The two gap traces keep 0.205 mm to the pads, and nothing crosses.
  - **Lengths and skew.** Pad edge to pad edge: J1→D1 13.80 mm DP / 15.61 mm DM; D1→R 43.66 / 41.40 mm; R→U1 3.30 / 3.53 mm. End-to-end skew is 0.23 mm. The duplicate-contact joins give 2.8 mm with the plug on A6/A7 and 0.8 mm on B6/B7, about 17 ps worst case. At full speed (83 ns bit, ≥4 ns edges) neither that nor the ±2 mm per-section mismatch matters.
  - **Stubs, terminations and placement.** The stubs are 2.0–2.6 mm. R8/R9 are 3.3–3.5 mm from U1, and the CC1/CC2 5.1 kΩ pull-downs are intact. D1 is about 14–16 mm along the pair from J1; closer is better for ESD, but this is acceptable.
  - **Impedance.** Not measured. A Hammerstad-based check of 0.25 / 0.15 mm over 0.21 mm of εr 4.4 gives roughly 95 Ω without mask. That agrees with the overseer's 90–92 Ω coated estimates; full speed is tolerant.
- **Crystal and supply pins (PCB-03, PCB-08).**
  - **Crystal.** XIN pin 20 → Y1.1 is 4.0–4.1 mm with no vias (previously 7.79 mm with two vias). XOUT → R1 is 0.6 mm, and C1/C2 sit about 1 mm from Y1.
  - **Supply pins.** IOVDD22 → C6 is 2.94 mm (was 6.07 mm) and DVDD23 → C11 is 1.07 mm. Every other primary bypass path is unchanged.
  - **Load capacitors.** ABM8-272-T3 (CL 10 pF, ESR 50 Ω) with 15 pF capacitors and a 1 kΩ resistor is exactly the RP2040 hardware design guide §2.3 network: 7.5 pF + ~3 pF stray = 10.5 pF. A ±0.5 pF error is a few ppm, against USB full speed's ±2500 ppm. This is the correct choice; keep it.
  - **Nearby copper.** The only foreign F.Cu copper inside the network's outline is the IOVDD22 bypass branch, a decoupled supply. XTAL_OUT runs between Y1's pad columns, 0.175 mm from the XIN pad. That adds an estimated <0.1 pF XIN–XOUT shunt, which is acceptable. I2S_DATA and I2S_LRCLK pass under the crystal on B.Cu, behind two GND planes.
  - **Bench.** Startup time and frequency remain bench tests.
- **VBUS (PCB-06).** J1's A4/B9 VBUS pad now reaches F1 over 5.5 mm of 0.4 mm F.Cu with no vias (≈8 mΩ, IPC-2221 ≈1.2 A at 10 °C rise). This is an improvement. The B4/A9 pad is a parallel 0.3 mm path through TP1, a B.Cu link and two vias. After F1, +5V is unchanged at 0.15 mm: ≈0.12 Ω to U3 and ≈0.31 Ω with two vias to U5. That is adequate for the 210 mA PLAY allocation (IPC-2221 ≈0.6 A; drop <40 mV), but it is the thinnest link in the power path and should be widened before raising audio amplitude or gain.
- **Other reroutes (PCB-07).** Every changed non-USB net keeps 0.15 mm minimum width. New vias are tented, including the +1V1 via between the RP2040 exposed pad and its pad ring. Other-net F.Cu track within 0.5 mm of the USB pair fell from about 22 mm to 3.6 mm. SENSOR_XSHUT, a static line, runs about 0.56 mm from the pair for about 14 mm.
- **Stackup (PCB-10).** The PCB stackup and the Gerber job both equal JLC04161H-7628 as described in `docs/fabrication_plan.md`.

## Sourcing and mechanical changes

- **RV1 (MFG-03), PASS for footprint fit.** In the Bourns PTV09 code, "-4" is terminal configuration 4: horizontal/rear mount, bushingless. "-1" is also rear mount, with a sleeve bushing. The datasheet has a single "recommended PCB layout (horizontal/rear mount)", and the -1 and -4 front views give identical body, tab and pin dimensions. So the PTV09A-1 rear-mount footprint is correct for -4015F.
  - **Footprint vs layout.** The footprint matches: pins Ø1.0 at 2.5 mm, tab holes 8.8 mm apart (10.6 mm outside-to-outside), 7.0 mm from the pins. KiCad uses Ø2.2 round tab holes where Bourns shows 1.8 × 2.2 slots. That is the same for -1 and is left for the first-article fit check.
  - **Mechanics.** With no bushing or nut and a 15 mm F shaft, the knob sits about 5 mm lower and needs a 6 mm F-shaft knob.
- **U2 (MFG-06).** Winbond Rev G gives "SN = 8-pin SOIC 150-mil" and "SS = 8-pin SOIC 208-mil". W25Q16JVSNIQ fits the 3.9 mm footprint, so this correction is right.
- **J1 (MFG-07).** GCT's drawing gives "120 = 1.20mm" shell stake, against the 0.95 mm default. That is the longest option for a 1.6 mm board; the land pattern is unchanged and was verified.
- **J2 (MFG-08).** The 0.64 mm square pin fits the Ø1.0 holes.
- **Passives (MFG-09).** Ratings are 50 V/25 V, X7R/X5R/C0G. They are improved over rev 0.1 for the 5 V rails, and DC-bias derating is modest.
- **Fiducials (MFG-10).** The three fiducials are correctly excluded from BOM/CPL, asymmetric and clear of copper.

## Failures

- **MFG-05, FAIL.** The GND via at (67.798, 56.124) mm, 0.20 mm drill, is 0.132 mm (drill to drill) from J1's S1 slot at (68.32, 56.78). JLC publishes 0.2 mm via hole spacing and 0.45 mm pad hole spacing. KiCad did not flag it. It existed in rev 0.1. **Fix:** delete it. It has no track, and all four S1 pads are solid in GND on every layer.
- **MFG-11, FAIL (order package).** Three items:
  - The silkscreen says "v0.1 ENGINEERING PROTOTYPE".
  - The Gerber job shows Revision "rev?" and Finish "None"; the PCB has no title-block revision.
  - `hardware/outputs/DRAFT-fabrication/README.md` still describes 0.48 mm placeholder dielectrics and a test-pad position file.

  **Fix:** mark revision 0.2 on silk and in the title block, record the chosen finish, and refresh that README.

## Concerns for overseer disposition (not failures)

1. **+5V is 0.15 mm** from F1 to U3 and U5. See PCB-06.
2. **Via drill at C15's GND pad edge.** The via at (95.45, 66.6) mm has its drill edge 0.005 mm inside the C15 GND pad outline. That carries a low risk of solder wicking or tombstoning; nudge the via 0.15 mm away.
3. **README figures differ from measurement.** The coupling fraction is 93% claimed vs 85% measured. Neck-down is described as "within about 1 mm", but two 3 mm runs pass through D1. Orientation skew is given as 1.6/0.9 mm vs 2.8/0.8 mm measured. All are immaterial electrically.
4. **Sourcing risk.** J1 shows 0 LCSC stock (JLC 1,569) and RV1 shows 123. Recheck on the order day, as the plan states.
5. **Fiducial pour margin.** The fiducial pour edge is only 0.1 mm outside each 2 mm mask opening. It is acceptable but tight; JLC may add rails.

## Physical validation

Every physical criterion remains **PENDING**: assembly, rails and current, crystal startup and frequency, USB enumeration and signal quality on both plug orientations, inrush and suspend, calibration, notes, latency, audio and endurance. Use `docs/bench-results-template.csv`.

Evidence:
- `drc-final.json`, `erc-final.json`
- `artifact-audit.json`, `layout-review.json`, `export-review.json`
- `final-trace-paths.txt`, `gerber-top-review.svg`, `gerber-bottom-review.svg`, `gerber-inner1-review.svg`
- `power-budget-review.json`, `host-test-evidence.json`, `firmware-static-review.json`
- `final-review-evidence.json`

Path lengths are approximate centreline figures, not a signal-integrity model.
