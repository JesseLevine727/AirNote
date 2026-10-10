# Independent review — AirNote engineering draft

Reviewed PCB SHA256: `c35f7d922f362b58a088193dba98902f71df68bcac94774f78b6f83b8618e9cc`.

**Native CAD checks and export-coherence checks pass. The design is not released for fabrication or validated on hardware.**

The independent KiCad 9.0.9 run reports zero ERC violations, zero DRC violations, zero unconnected items and zero schematic/PCB parity issues, including all severities and all track errors. Critical pin/value/footprint checks and firmware pin mapping pass. Host controller/synthesizer tests pass with address/undefined-behavior sanitizers; fresh ARM compilation is recorded by the overseer. None of these checks executes the actual sensor, USB peripheral or audio hardware.

The final PCB has 766 track segments on the two outer layers and 98 through vias. Both inner copper layers have one continuous filled GND region. The bypass corrections are preserved: short direct branches now serve RP2040 core pin 23, its regulator output, the sensor, amplifier, IOVDD pin 33 and flash supply. Capacitor ground connections have nearby vias. The unintended C21 via-in-pad was removed; only the five intentional MCU/amplifier exposed-pad vias remain and need a supported factory process.

Actual Gerber/Excellon exports were parsed with Gerbonara 1.6.3 and front/back/inner-plane views independently inspected. Four copper layers, mask, paste, silkscreen and outline are present. All 114 plated holes/slots and six nonplated holes agree with the PCB within the export's 0.001 mm coordinate resolution. Every fitted-component placement agrees with the BOM and PCB position, side and rotation. Hashes of the inspected source, PDF and export files are recorded in `export-review.json`.

## Open engineering decisions before a first-article order

- **USB geometry and stackup — additional layout work required.** D+/D− were routed separately; equal endpoint connection does not establish controlled differential impedance or appropriate paired geometry. The draft Gerber job contains default 0.48 mm dielectric gaps, `None` finish and `rev?`, explicitly marked as placeholders. Select the actual fabricator stackup and review/reroute USB as a pair before approving a manufacturing package. The current full-speed USB interface has not been tested.
- **IOVDD pin 22 — prototype deviation, not a verified failure.** Its bypass path improved from about 9 mm to approximately 6–7 mm, but remains longer than preferred. A first-article disposition must either shorten it or explicitly accept this residual while requiring rail-transient and maximum-activity testing. It is not covered by a blanket layout pass.
- **Crystal — prototype deviation, margin unverified.** The approximate MCU XIN-to-crystal route is 7.79 mm and the XIN net uses two vias; the whole branched net totals 10.48 mm. Prefer a tighter local route. Otherwise explicitly accept it for first articles and measure startup/recovery over the intended source/temperature conditions. A 12 MHz nominal label and clean DRC do not prove oscillator margin.
- **Power/USB — unresolved compliance and bring-up risks.** The documented 155 mA 3.3 V and 210 mA PLAY input figures are engineering allocations. Arithmetic/source references are checked, but actual input charge, ROM/unconfigured current, configured current, suspend current and regulator temperature remain unmeasured. The firmware reduces peripheral load on suspend while core 0 still runs. Neither the adapter rating nor PTC proves source-current or USB compliance.
- **Factory and mechanics — confirmation required.** Obtain exact stock/quote and approval of optical-package moisture, no-wash/reflow/liner handling, hidden-joint inspection and exposed-pad via processing. Confirm connector/knob/switch mechanics and lever direction. Missing 3D bodies for the pot, switch and amplifier limit the native render's mechanical evidence.

An engineering first-article order requires closed CAD/circuit blockers, supplier capability and explicit disposition of these remaining risks with a restricted bring-up plan. That decision has not passed. Measurements requiring physical hardware happen after first-article assembly; they are not represented as completed or as a circular prerequisite to creating the first board.

## Physical validation

Every physical performance criterion remains **PENDING**: assembly inspection, rails/current, calibration, actual note/pitch output, hand stability, no-target silence, gesture latency, USB behavior and endurance. Use `docs/bench-results-template.csv` to record measurements and provenance. USB-MUTE range logs and adapter-PLAY acoustic measurements are separate runs under the current interlock; predicted software notes do not count as observed speaker output.

Evidence: `drc-final.json`, `erc-final.json`, `artifact-audit.json`, `host-test-evidence.json`, `firmware-static-review.json`, `power-budget-review.json`, `final-trace-paths.txt`, `export-review.json` and `final-review-evidence.json`. Trace-path figures are approximate: the diagnostic omits travel inside copper pads and is not a signal-integrity model.
