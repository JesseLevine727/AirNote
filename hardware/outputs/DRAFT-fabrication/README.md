# DRAFT — engineering review only

These files are generated from the routed AirNote prototype. They are not an approved production release. No factory order is authorized by this export.

Use `airnote-fitted-bom.csv` and `airnote-fitted-positions.csv` for component review. The full position file includes PCB test pads and is retained only for traceability. Through-hole parts remain in the fitted list and need assembly-service confirmation. Gerbers contain F.Cu / In1.Cu / In2.Cu / B.Cu in that order, two ground reference planes, paste/mask/silkscreen and the board outline; PTH and NPTH drill files are separate.

The generated Gerber job currently contains KiCad defaults (three 0.48 mm dielectric gaps, finish `None`, revision `rev?`). These are explicit placeholders; they are not a supplier stackup or an impedance specification.

Outstanding release gates: fabricator-approved stackup and USB geometry; manufacturer/assembler approval of 0.127 mm clearance and 0.45/0.20 mm vias; optical VL53L1X dry/no-wash/MSL process and calibration; MCU/amplifier exposed-pad via treatment and paste; exact MPN availability, origin/rotation checks, soldering of through-hole controls, and a sourced PCBA quote. Physical bring-up, USB current/inrush/suspend tests, sound and distance-response metrics are pending.

See `hardware/README.md`, `docs/bringup.md`, `docs/power_budget.md` and `reviews/REVIEW_STATUS.md` for evidence and limitations. Confirm the current CAD and export hashes in `hardware/reports/final-artifact-hashes.json` before any later release.
