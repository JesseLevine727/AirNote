# Independent review status

Date: 2026-10-10. Status: **DRAFT SNAPSHOT REVIEWED — NOT RELEASED FOR FABRICATION**.

Final reviewed PCB: `c35f7d922f362b58a088193dba98902f71df68bcac94774f78b6f83b8618e9cc`. See [FINAL_REVIEW.md](FINAL_REVIEW.md) for the final disposition and evidence boundaries.

This status concerns the fully integrated RP2040 / VL53L1X / MAX98357A design, not the earlier module-carrier concept. No physical board has been tested.

| ID | Status | Finding / evidence needed | Owner |
|---|---|---|---|
| ARCH-01 | PASS | User selected fully integrated hardware with factory assembly; four layers preferred. | Overseer |
| CIR-01 | PASS (limited scope) | `artifact-audit.json`: independent critical-pin, passive-value, connected-pad-existence, schematic/PCB pad-assignment and firmware-pin checks; no failures on recorded hashes. Exact physical package/mechanical and copper review remain separate. | Reviewer |
| CIR-02 | PASS (static code) / PENDING (physical) | `start_sensor()` uses init(true), explicitly configures/readbacks register 0x2F in addition to 0x2E, and releases open-drain XSHUT to external pull-up. Actual startup, I/O waveform and calibration unmeasured. | Overseer / reviewer |
| CIR-03 | PASS (allocation arithmetic) / PENDING (electrical) | `power-budget-review.json`: current/thermal/audio calculations and engineering-allocation wording checked. USB input charge, preconfiguration/suspend current and actual board load remain unmeasured. | Implementer / overseer |
| FW-01 | PASS (host logic) | Independent ASan/UBSan suite in `test_instrument_independent.cpp`: note centers, invalid/glitch qualification, hysteresis, stale cutoff, timer wrap, amplitude, mute release, volume and synthesized pitch within +/-5 cents. ARM build evidence maintained by overseer. | Reviewer |
| FW-02 | PASS (corrected and retested) | First review found a repeated valid sensor result could refresh freshness indefinitely. `FrameTracker` now rejects repeated burst-coherent stream counters; counter wrap/restart and stuck-ready behavior independently tested. | Overseer / reviewer |
| FW-03 | PASS (static instrumentation review) | Vendored I2S transport diff adds only a counter/accessor at the actual consumer-buffer starvation branch. ISR/accessor run on audio core; telemetry copied under critical section. Physical I2S integrity remains pending. | Reviewer |
| FW-04 | PASS (static policy) / PENDING (electrical) | Staged sensor/audio startup, host latch, suspend/deconfiguration shutdown and LED-off gating inspected. Audio DMA/PIO permanently parks until power cycle after shutdown. Measured USB current/inrush and compliance remain unresolved; see `firmware-static-review.json`. | Reviewer |
| PCB-01 | PASS (native CAD checks only) | Independent final ERC/DRC: zero violations, zero unconnected and zero schematic-parity issues. Outer-layer routing and continuous inner GND fills confirmed. Overall electrical-layout approval remains open under PCB-04. | Implementer / reviewer |
| PCB-03 | PASS (specific bypass corrections) | Core/regulator/sensor/amp bypasses corrected; IOVDD33 and flash bypasses also shortened. C21 passive-land drill removed. Final paths and limitations are in `final-trace-paths.txt`; residual IOVDD22 is covered by PCB-04. | Implementer / reviewer |
| PCB-04 | PENDING (engineering disposition) | USB paired geometry and factory stackup need further work. IOVDD22 bypass remains approximately 6–7 mm; XIN-to-crystal is approximately 7.79 mm with vias in its net. These require explicit first-article disposition and relevant bench validation; no blanket layout approval. | Overseer / reviewer |
| MFG-01 | PENDING | Exact assembler, confirmed component procurement, quote and optical-sensor reflow/handling support. | Overseer / supplier |
| MFG-02 | PASS (export coherence only) | Actual Gerber/drill parsing and render inspection completed. Drills/slots and fitted-component positions match the PCB; source/export hashes recorded in `export-review.json`. Factory process, stackup, finish and final release remain pending. | Reviewer |
| BENCH-01 | PENDING | All physical functionality, calibration, power, timing, noise and endurance measurements; no board available. | User / reviewer |

The source-backed review procedure is in [CHECKLIST.md](CHECKLIST.md). No failed or pending criterion counts as a pass. An engineering first-article order requires closed CAD/circuit blockers, confirmed supplier capability and an explicit disposition of open USB/power risks with a restricted bring-up plan. That gate has not passed. Measurements requiring a physical board follow first-article assembly and must pass before a validated release; they are not a circular prerequisite to creating the first board.

## Reproducible independent checks

```sh
/usr/bin/python3 reviews/audit_artifacts.py
g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer -I firmware/include firmware/src/instrument.cpp reviews/test_instrument_independent.cpp -o /tmp/airnote-independent-tests
/tmp/airnote-independent-tests
```

The JSON audit records exact inspected hashes. The native suite is intentionally independent of production I2C/PIO execution: it cannot establish physical performance or bus timing.

## Actionable findings during initial review

- **FW-02, corrected:** successful reads of a frozen sensor frame previously refreshed the note timestamp. Fixed by overseer with stream-counter qualification and independently retested.
- **CIR-04, corrected:** initial open volume-pot wiper left the ADC floating. Regenerated netlist/PCB include R19 = 1 Mohm from VOLUME_ADC to ground. Physical response to a disconnected wiper remains unmeasured.
- **MFG-03, corrected part selection:** RV1 now uses PTV09A-1020F-B103 matching the PTV09A-1 named footprint, removing the initial -4 versus -1 body ambiguity. Supplier availability and physical mechanical fit remain pending.
- **MFG-04, corrected:** project footprint `AirNote:MAX98357A_T1633_ADI_90-0031` now has the official ADI 0.80 x 0.30 mm perimeter lands, 2.85 mm opposite center spacing and 1.23 mm EP. Independent audit verifies all 16 perimeter land positions/sizes and EP size. Factory paste/thermal-via processing remains separate.
- **CIR-03, unresolved release gate:** initial direct 5 V capacitance exceeded the baseline USB input-capacitance allowance even before output-capacitor charging. Amplifier capacitor reduced from 10 uF to 4.7 uF; effective input charge, preconfiguration current and suspend behavior still require analysis/measurement. PTC hold current does not establish an inrush limit.
- **PCB-02, corrected:** final signal tracks use only F.Cu/B.Cu; both inner layers contain continuous GND fills. Explicit 0.127 mm native clearance rules and final independent DRC agree. This is a prototype geometry choice, not supplier capability approval.
- **CAD presentation, corrected:** crystal/USB label spacing and title-block text were revised; the regenerated controller PDF was visually inspected. Native 3D render still lacks several mechanical bodies, as disclosed in the final review.
