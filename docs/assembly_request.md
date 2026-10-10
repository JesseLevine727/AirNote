# Assembly feasibility and quotation brief — draft

> **Update 2026-10-10:** JLCPCB Standard PCBA has been chosen. Its published
> capabilities and parts catalog answer most of the questions below without
> a manual inquiry; see [fabrication_plan.md](fabrication_plan.md). Answered:
> procurement (1), stackup and geometry (4), THT assembly. Partly answered:
> optical handling (2; Standard reflow and no wash, liner removed by us) and
> exposed-pad vias (3; open by default, POFV optional). Still to confirm on
> the actual order: rotations in JLC's placement preview (5), and
> edge-rail handling (rev 0.2 adds three global fiducials). JLC's inspection and functional-test options (6)
> were not researched; plan on doing all bring-up and testing ourselves.

Project: AirNote V1 engineering prototype, fully integrated RP2040 /
VL53L1X / MAX98357A instrument. This brief is prepared for a future supplier
inquiry. **It has not been sent, no quotation has been obtained, and no order
is authorized by this document.** The current PCB is not released for manufacture.

## Proposed job

- Nominal 90 x 70 mm board, four copper layers, proposed 1.6 mm finished
  thickness. Confirm the actual outline and drill data from the reviewed files.
- Outer signal routing and two ground-reference inner layers. The final
  stackup must be selected with the supplier before USB geometry is approved.
- Proposed 0.127 mm (5 mil) minimum track/clearance; drill, annular-ring and
  solder-mask capabilities must be checked against the actual design rules.
- Components on the front; mixed fine-pitch SMT and through-hole controls /
  connectors. Quote fully assembled prototypes including the specified pot,
  switches and connectors, or identify any parts left for manual assembly.
- Request estimates for 2 and 5 assembled units; quantity is not committed.
- Exact proposed part numbers: `hardware/bom.csv`. Test pads and mechanical
  holes are PCB features, not purchasable components. No substitutions without
  a documented pinout, package, voltage and firmware compatibility review.

## Explicit capability confirmations

1. Can you procure the exact RP2040, QSPI flash, crystal, regulator, optical
   sensor and TQFN amplifier listed in the BOM? Identify minimum quantities,
   excess-part charges, lead times, and customer-supplied items.
2. Confirm assembly of the VL53L1CXV0FY/1 optical LGA using the manufacturer's
   moisture handling, dry-reflow, cleaning/contamination and protective-liner
   instructions. Do not assume a normal board-wash process is acceptable.
   Reference: https://www.st.com/resource/en/datasheet/vl53l1x.pdf, section 11.
3. Confirm exposed-pad stencil strategy and whether vias under exposed pads
   require filling/capping or another controlled treatment. Review the exact
   amplifier land pattern and the RP2040 footprint, not just the package names.
4. Provide the stackup, copper weights, dielectric properties and proposed
   geometry for the USB 2.0 differential routing. State any impedance-service
   setup costs. The schematic alone does not determine this geometry.
5. Confirm polarity/rotation interpretation against the assembly drawing,
   through-hole pot dimensions, USB connector orientation and optical clearance.
6. State whether inspection includes AOI/X-ray and whether you offer firmware
   loading, current-limited power-on, sensor offset calibration or functional
   tests. Quote those separately; factory assembly inspection is not a full
   instrument acceptance test.

## Package to supply after review

One identified revision of Gerbers, drill files, schematic PDF, BOM, component
placements, assembly drawing and board views; source KiCad files if requested.
Include amplifier MUTE during programming, matched UF2/checksum, and a clear
statement of which bring-up/calibration tests the factory is expected to run.

Before ordering engineering first articles, close CAD/circuit blockers,
confirm the factory process, and explicitly disposition unresolved electrical
risks with a restricted bring-up plan. Reconcile the quote with the exported
design and record the chosen fabrication/assembly rules in the KiCad project.
Physical performance and USB current measurements follow assembly; they are
required for validated release, not represented as already completed tests.
Track both stages in `reviews/REVIEW_STATUS.md`.
