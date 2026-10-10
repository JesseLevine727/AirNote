# AirNote V1 requirements and workflow

Revision 0.2, 2026-10-10. User-selected architecture: fully integrated PCB with
factory assembly. All physical acceptance results are **PENDING** until an
assembled board is measured. Fabricator, stackup (JLC04161H-7628), PCBA
service and sourcing are recorded in [fabrication_plan.md](fabrication_plan.md);
no quote has been accepted and no order has been placed.

## Product behavior

One open palm above the upward-facing optical sensor selects one monophonic
note. Closer means higher pitch. The playing interval is 100–500 mm, indoors
without direct sunlight, with the empty sensing cone looking beyond 500 mm.
V1 uses the C-major pentatonic notes C4, D4, E4, G4, A4, C5, D5, E5, G5, A5,
C6. A volume knob controls level; a hardware switch mutes the amplifier. A
status LED indicates a playing note or a sensor fault. This is an optical
instrument, not a capacitive theremin.

The firmware uses eleven equal distance bands, 5 mm hysteresis, and two
consecutive valid observations to change notes. An invalid sample never
refreshes the last valid timestamp. Stale data expires after 100 ms; a valid
out-of-range reading silences the voice immediately, followed by the short
audio release envelope. These settings are starting values for hand trials.

## Architecture

- RP2040, 2 MiB external QSPI flash, 12 MHz crystal, internal 1.1 V core
  regulator and external 3.3 V supply.
- VL53L1X on the PCB, nominally sharing the 3.3 V rail with the MCU. Firmware
  explicitly configures I2C and GPIO AVDD-level modes; XSHUT is driven low or
  released to its external pull-up.
- MAX98357A in TQFN-16, I2S, 9 dB gain, two-terminal differential speaker
  output for an external 8 ohm speaker rated at least 1 W.
- USB-C for 5 V power and USB 2.0 programming/diagnostics. BOOTSEL, reset and
  SWD allow recovery even when application firmware is broken.
- Physical mute/PLAY switch independently grounds amplifier shutdown and
  tells the MCU the switch state.

Normal PLAY operation uses a specified, regulated 5 V adapter rated at least
1 A. Computer programming/diagnostics uses the physical MUTE position. There
is one power-input connector; the SWD 3V3 pin is a voltage reference/output,
not a second power input. Firmware host detection is an additional mute
interlock, **not source-current detection**. USB input capacitance/inrush,
startup, current advertisement/configuration and suspend compliance must be
reviewed before a manufacturing release; a fuse does not establish compliance.

## Agent responsibilities

| Role | Responsibility |
| --- | --- |
| Overseer | Maintain this specification, integrate hardware/firmware, assign work, resolve trade-offs and maintain evidence status. |
| Implementer | Create and correct KiCad circuits, board, BOM and manufacturing outputs against the specification. |
| Reviewer | Independently audit source documents, pin mapping, circuit/layout and behavior; return actionable failures; never infer physical success from static checks. |

The implementer cannot approve their own deliverables. Review findings are
PASS, FAIL or PENDING and identify their evidence and artifact revision. Failed
findings return to implementation and receive a targeted retest. Unavailable
measurements remain pending. The overseer coordinates firmware implementation
and integration alongside the hardware implementer.

## Acceptance matrix

| ID | Requirement and measurement | Target | Current evidence |
| --- | --- | --- | --- |
| FUNC-01 | Fixed matte target normal to sensor at each note-zone centre; 60 s each; record lighting, background and raw samples | Correct note >=99% of the interval; valid range samples >=99% | Host controller tests only; hardware PENDING |
| FUNC-02 | Real open palm, selected low/middle/high notes, ten attempts each after practice | Sustain selected note for 5 s in >=9/10 trials at each pitch | PENDING |
| PERF-01 | Independently time physical target transitions and resulting audio, 100 transitions across directions/notes | p95 <=80 ms, no missed transitions; report median/max | PENDING; sensor timestamps alone are insufficient |
| FUNC-03 | Remove target to empty cone, 100 trials | Audio silent within 150 ms in >=99 trials | Software timeout/envelope tested; physical PENDING |
| FUNC-04 | Empty sensing cone in the defined indoor setup for 5 min | No unintended notes | PENDING |
| AUDIO-01 | Measure all 11 steady reference notes acoustically or with appropriate differential filtered measurement | Frequency within +/-5 cents of equal temperament | Synthesizer software checked; physical PENDING |
| AUDIO-02 | Volume sweep and sustained maximum allowed digital amplitude | Monotonic usable volume to silence; output and current within speaker/supply budgets | PENDING |
| CTRL-01 | Hardware mute operated 50 times, including firmware hung/not flashed | Every operation disables amplifier independently | Circuit audit and physical PENDING |
| PWR-01 | Measure startup, idle, programmed/diagnostic and maximum-volume rails/current | Within frozen component limits and agreed source budget; no reset/droop violation | PENDING |
| REL-01 | 30 min repeated playing at maximum allowed volume, then 20 power cycles | No hangs/resets/unintended sound; successful startup every cycle | PENDING |
| FW-01 | Native behavioral tests and reproducible ARM build | Tests pass and target ELF/UF2 build | Logs in artifacts/ when captured |
| CAD-01 | ERC, schematic-to-PCB parity, DRC and independent pad/net/footprint audit | No unresolved functional/clearance errors; no unrouted nets; warnings individually justified | See reviews/REVIEW_STATUS.md |
| MFG-01 | Factory procurement, stackup, optical handling, assembly rotations and export review | Exact BOM available; assembler confirms sensor process; coherent manufacturing revision | PENDING |

The nominal sensor setup is short-distance mode, 20 ms timing budget, 25 ms
intermeasurement period and 8x8 ROI. Real cadence, field of view, stability
and full gesture-to-audio latency must be measured together. A quoted sensor
timing budget is not an instrument response-time result.

## Release gates

1. Specification/architecture: pin map, supply strategy, exact parts and test
   methods reviewed; supplier support and quote explicitly tracked.
2. Schematic: datasheet-to-symbol-to-footprint mapping, voltage/clock/boot
   compatibility, decoupling, ratings and startup states independently checked.
3. Layout: routed board, ground/current paths, USB geometry against chosen
   stackup, optical/mechanical clearance, exposed pads and test access checked.
4. Manufacturing: Gerbers, drills, BOM, placement file, assembly drawing and
   calibration/programming notes independently inspected for the same revision.
5. Hardware validation: staged bring-up and every physical acceptance test
   performed on the assembled board with measured evidence.

An engineering first-article order and a validated design release are separate
decisions. Before a first-article order, close CAD/circuit errors, confirm the
supplier process, and explicitly disposition unresolved electrical risks with
a restricted bring-up plan. The present USB power questions are still open;
an unqualified order-ready claim is therefore premature. Measurements that
require a physical board are performed on those first articles, then inform
any revision and the eventual validated release. No order has been placed.

“Fabrication-ready” and “hardware-validated” are different statuses. A clean
ERC/DRC report, factory visual inspection or working firmware simulation does
not establish the physical instrument's performance.

## Primary references

- [RP2040 hardware design](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf)
- [VL53L1X datasheet](https://www.st.com/resource/en/datasheet/vl53l1x.pdf)
- [MAX98357A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf)
- [Pico SDK](https://github.com/raspberrypi/pico-sdk)
- [Pico I2S audio implementation](https://github.com/raspberrypi/pico-extras)
- [Pololu sensor driver](https://github.com/pololu/vl53l1x-arduino)

