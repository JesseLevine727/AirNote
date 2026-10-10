# Independent review checklist

Reviewer scope: circuit, firmware behavior, layout, manufacturing exports and evidence. The reviewer writes only `reviews/`; implementer owns `hardware/`, and overseer owns `firmware/` and project requirements.

Status vocabulary: **PASS** means the stated check has recorded evidence; **FAIL** means a specific discrepancy; **PENDING** means the check has not been completed. A clean automated report cannot convert another pending check into a pass. Every review records the artifact revision/hash. Physical performance remains pending until measured on hardware.

## Source baseline and critical connections

Primary sources accessed 2026-10-10:

- [RP2040 hardware design guide](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf), particularly minimal design, flash, crystal and USB sections.
- [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf), pinout, supply requirements and GPIO specifications.
- [VL53L1X datasheet](https://www.st.com/resource/en/datasheet/vl53l1x.pdf), Rev 8, sections 2.3, 3.3, 6.2 and 11.
- [ST optical integration guidance](https://www.st.com/resource/en/application_note/an5231-cover-glass-guidelines-for-the-singlezone-timeofflight-sensor-stmicroelectronics.pdf).
- [MAX98357A/MAX98357B datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf), Rev 16, February 2026, pin table, Table 5, gain, and package sections.
- [USB-IF USB 2.0 specification](https://www.usb.org/document-library/usb-20-specification), chapter 7 power rules; [USB-IF current compliance clarification](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies).
- [Upstream ST VL53L1X driver](https://github.com/stm32duino/VL53L1X/blob/main/src/vl53l1x_class.cpp), configuration register comments for AVDD-level I/O. Review the actual project's pinned driver separately.
- [GCT USB4105 drawing](https://gct.co/files/drawings/usb4105.pdf), revision B4: contact order, duplicate VBUS/GND lands, 0.50 mm signal pitch, 5.78 mm peg spacing, 8.64 mm shell-stake spacing and recommended land/hole sizes checked against the project footprint.
- [C&K JS series datasheet](https://www.ckswitches.com/media/1422/js.pdf), 2026 revision, page 9: JS202011JCQN topology and land layout. KiCad numbers its two rows 1/2/3 and 4/5/6, while this manufacturer drawing uses 1/2/3 and 5/6/7. The central lands are common in each row; this deliberate numbering normalization is acceptable only with the corresponding generic DPDT symbol. Both switched rows in AirNote use the same end for ground. Actual lever direction versus silk still needs assembly verification.

| Device | Critical pin mapping to audit independently |
|---|---|
| RP2040 | IOVDD: 1,10,22,33,42,49; DVDD:23,50; VREG input:44; VREG output:45; USB supply:48; ADC supply:43; exposed ground:57; TESTEN:19; RUN:26; XIN:20; XOUT:21; SWCLK:24; SWDIO:25; USB DM:46; USB DP:47; QSPI CLK:52; CS:56; IO0:53; IO1:55; IO2:54; IO3:51. |
| VL53L1X optical LGA12 | AVDDVCSEL:1; AVSSVCSEL:2; grounds:3,4,6,12; XSHUT:5; interrupt:7; DNC:8; SDA:9; SCL:10; AVDD:11. |
| MAX98357A TQFN16 | DIN:1; GAIN_SLOT:2; grounds:3,11,15; SD_MODE:4; NC:5,6,12,13; VDD:7,8; OUTP:9; OUTN:10; LRCLK:14; BCLK:16; EP:ground. |

RP2040 candidate standard footprint: `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm`. Sensor candidate: `Sensor_Distance:ST_VL53L1x`. These are starting points, not independent dimensional sign-off. MAX98357A TQFN package code is **T1633+4**, outline **21-0136**, land pattern **90-0031**; its [official land pattern](https://mds.analog.com/api/public/content/90-0031.pdf) specifies a 1.23 x 1.23 mm center pad, 0.80 x 0.30 mm perimeter lands, 0.50 mm pitch and 2.85 mm opposite land-center spacing. AirNote now uses a local footprint matching those dimensions, independently checked in `audit_artifacts.py`; factory paste and thermal-via processing remain separate checks.

## Circuit gate

- [ ] Independent datasheet-to-symbol-to-netlist-to-footprint pad audit for every IC, connector and switch, including bottom/top-view orientation and pin 1.
- [ ] Every power/ground pad connected, including hidden/stacked symbol pins and exposed pads. TESTEN grounded. DNC/NC pins treated per datasheet.
- [ ] RP2040 1.1 V regulator output reaches both core supply pins, with local input/output capacitors; individual supply decouplers present and close in layout.
- [ ] Flash MPN voltage/package and boot2 configuration agree. QSPI routes short. BOOTSEL pulldown has the reference series resistance; RESET/RUN and SWD remain accessible.
- [ ] Exact 12 MHz crystal, load capacitance, ESR and drive-limiting network checked. Reference values do not automatically apply to a substituted crystal.
- [ ] USB DP/DM polarity correct, connector's duplicate contacts joined correctly, 27-ohm series resistors near MCU, ESD device polarity/capacitance checked, separate correct CC terminations. Stackup-dependent routing and continuous return path reviewed.
- [ ] Shared 3.3 V sensor supply remains within its operating range with regulator tolerance/ripple. I2C, XSHUT and interrupt levels agree with the configured I/O mode. XSHUT cannot be driven high while its supply is absent. No unintended internal pull-up defeats the chosen open-drain control.
- [ ] Amplifier analog gain, channel-selection voltage and firmware stereo words agree. Current datasheet: directly high SD_MODE selects left; old evaluation-board labels are not authoritative.
- [ ] Hardware audio-off overrides firmware safely, including MCU reset/BOOTSEL and stuck-high firmware. No switch shorts an actively driven GPIO directly to ground. Speaker terminals are isolated from circuit ground.
- [ ] Worst-case source, regulator, trace, protection-device and connector currents documented for PROGRAM and PLAY modes. Adapter/cable restriction and manual PLAY selection explicit; no assumed charger detection.
- [ ] PC preconfiguration draw, descriptor current and suspend behavior have a supported policy. Merely disabling the amplifier does not prove the remaining electronics satisfy a USB power limit.
- [ ] Inrush/input capacitance and amplifier supply bulk capacitance reviewed together. Speaker impedance/power rating, digital amplitude limit and amplifier gain jointly bound audio power.
- [ ] Volume pot open-wiper behavior tends toward silence; ADC input filtering, clamp limits and voltage range checked.
- [ ] KiCad ERC: no unresolved findings. Every justified exclusion has an individual explanation; rules are not globally weakened to hide a violation.

## Firmware gate

- [ ] Pinned dependencies and reproducible build instructions; binary built for exact MCU, flash and crystal.
- [ ] Sensor initialization explicitly selects AVDD-level I/O where applicable: register 0x002E bit 0 for I2C; 0x002F bit 0 for interrupt GPIO. Readback checked; failure cannot enable sound.
- [ ] All hardware transaction waits and sensor boot waits bounded. Sensor missing, NACK, timeout, invalid status, frozen data and disconnect lead to silence within the specified deadline.
- [ ] No stale reading refreshes its validity timestamp. Clock rollover and long uptime arithmetic checked.
- [ ] Quantization, all 11 notes, endpoint mapping, hysteresis, entry/exit behavior and invalid-data recovery covered with independent input traces.
- [ ] Fixed-card stability and human playability are separate requirements; neither is inferred from simulated input.
- [ ] I2S word alignment, bit count, channel order, bit clock/frame ratio and pin assignment independently decoded. MAX98357A uses I2S, not MAX98357B left-justified framing.
- [ ] Audio-buffer ownership is safe across cores and DMA. No blocking sensor transaction can stop the audio service. Underrun behavior is explicit; amp disabled before clocks are stopped.
- [ ] ADC-to-volume mapping is monotonic with a defined silence region. Bounded waveform amplitude and transitions avoid discontinuity/clipping. Hardware mute tested independently of software.
- [ ] Calibration is clearly marked unperformed until measured. Offsets retained or reproducibly configured, reapplied at each sensor initialization, and documented per physical board.
- [ ] Host tests prove only pure logic; firmware build proves compilation, not valid electrical timing or actual response latency.

## Layout and manufacturing gate

- [ ] Four-layer stackup frozen with assembler/fabricator. Signal return paths stay continuous; high-current speaker and amplifier paths avoid sensor/ADC/crystal regions.
- [ ] QFN/LGA escape clearance, copper-to-edge, annular rings, holes, solder-mask webs, thermal pads and paste aperture coverage meet selected process.
- [ ] All module replacements are actual IC circuits; BOM has exact manufacturer MPNs and packages, tolerances, voltage/power ratings and fitted/DNF intent.
- [ ] Courtyards, connector insertion, volume knob, mute/PLAY access, screw heads, standoffs and sensor optical cone checked in 3D and dimensional drawings.
- [ ] Factory confirms optical package handling: MSL3 moisture controls; protective liner handling; clean/no-wash process; dry reflow; temperature/pass limits; no optical contamination. No presumed service availability.
- [ ] Assembly inspection capabilities for hidden QFN/LGA joints are stated. AOI/continuity tests do not imply functional testing.
- [ ] Exact component stock/approved substitutes, quote, assembly capabilities and sourcing lead time confirmed before purchase. Substitutions require a new pin/footprint/electrical review.
- [ ] DRC run after zone refill with no unresolved findings. No unconnected pads requiring routing. Schematic/PCB parity checked independently.
- [ ] Manufacturing export revision frozen: Gerbers, plated/nonplated drills, board outline, stackup notes, BOM, placement files, assembly drawings and programming/calibration instructions agree.
- [ ] Reviewer opens exported Gerbers/drills and checks layer count, holes, outline, solder mask/paste and reference orientation. Export existence is not export correctness.

## Physical gate — all pending until actual boards exist

1. Unpowered inspection and rail checks, then current-limited power with amplifier forced off. Record 5 V, 3.3 V, 1.1 V and quiescent current; investigate unexpected consumption before raising the limit.
2. Flash/readback/reset/recovery; then sensor identity, live range validity and assembly offset calibration; then low-volume audio into the specified load.
3. Verify both hardware-off states while firmware deliberately requests audio. Measure PLAY and PROGRAM supply behavior; test USB plug orientation and permitted cables/sources.
4. Controlled card: each note center for 60 s; target >=99% valid readings and <=1 unintended transition per minute. Record sensor ROI, lighting, background and calibration.
5. Hand playability: low/middle/high note held for >=5 s in >=9/10 attempts after practice. Empty-cone test for 5 min with no notes. Target removal silence <=150 ms in >=99/100 trials.
6. Proposed physical response p95 <=80 ms over 100 independently referenced transitions, with median/max/misses reported. Completed sensor-read timestamps do not measure full gesture latency. This target is provisional until hardware evidence exists.
7. Pitch within +/-5 cents for all 11 notes (current requirement AUDIO-01). Audio amplitude, clipping and supply behavior measured using a suitable differential class-D measurement arrangement or acoustic method appropriate to the metric. Never ground a speaker terminal through a scope/audio input.
8. Thirty minutes at maximum permitted volume while exercising sensing/controls: no reset, hang or buffer underrun; component temperatures within documented limits. Twenty power cycles recover normally.

Physical tests need at least a multimeter and controlled power source. Full electrical/audio and latency verification needs suitable borrowed/owned instruments or an agreed independently timed fixture. Missing equipment leaves the affected criterion pending.
