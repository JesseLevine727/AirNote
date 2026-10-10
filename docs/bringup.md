# AirNote staged bring-up and calibration

This is a procedure to execute on the first manufactured board, not a record
of completed tests. No PCB or lab equipment is currently confirmed available.

## Equipment

Minimum assembly checks need a multimeter, magnification and the specified
5 V supply. Prefer a current-limited bench supply with a USB breakout for
first power. Functional tests need an 8 ohm >=1 W speaker, a ruler and matte
target, a computer/data cable for firmware and logs, and mounting standoffs.
Borrow an oscilloscope/logic analyser and a suitable audio/timing fixture to
verify rail droop, buses and end-to-end response. Choose the latency method
before declaring that requirement testable. Phone video alone is generally
too coarse to establish the proposed p95 latency target accurately.

## Before power

1. Confirm the PCB/assembly/firmware revision and BOM. Inspect polarity,
   package orientation, exposed-pad joints, USB connector and optical window.
   The factory must follow the sensor manufacturer's no-contamination process.
2. Put the physical switch in MUTE and the volume at minimum. Leave the speaker
   disconnected initially. Check for hard shorts on VBUS/5V/3V3/1V1 to GND;
   allow capacitors to charge before interpreting resistance measurements.
3. Verify the hardware mute switch shorts AMP_SD to GND in MUTE without
   shorting the MCU GPIO directly (there is a series resistor).
4. Remove the VL53L1X protective liner (the clear film over the optical
   window) with plastic tweezers. JLC assembles the sensor with it in place
   and has no removal step; ranging through it gives wrong distances.

## First power and firmware

1. Apply current-limited 5 V, initially with a conservative 100 mA limit.
   Never make the first connection to a computer port (see the inrush and
   suspend disposition in `docs/power_budget.md`). Without a bench supply,
   use a USB power meter on a phone charger, then a powered hub for the computer.
   If the supply limits, switch off and investigate before raising it.
   Measure 5V, 3V3 and 1V1 at the test pads identified in the assembly drawing.
   TP1 is raw USB VBUS, TP2 is fused 5V, TP3 is 3V3, TP4 is 1V1 and TP5 is
   GND; not every test-point reference is printed on the silkscreen. Compare to the component
   datasheets and frozen power budget, not just a nominal label.
2. Verify AMP_SD remains low before firmware is installed. Hold BOOTSEL while
   connecting the USB data cable or resetting; the RP2040 ROM should expose
   its RPI-RP2 drive. Copy the matching `airnote.uf2`. Keep MUTE selected.
   The ROM drive enumerating is also the first check of the 12 MHz crystal
   and the USB pair. The crystal's load capacitors (15 pF) follow the
   Raspberry Pi reference rather than the crystal's 10 pF CL rating, so a
   small frequency offset is expected. Tens of ppm do not matter here: USB
   full speed allows ±2500 ppm and the ±5 cent pitch target is about
   ±2900 ppm. If the drive does not appear, check the crystal with an
   oscilloscope (×10 probe on the XOUT side of R1) before suspecting USB.
3. Read USB CDC diagnostics. Firmware must identify the sensor, explicitly
   configure AVDD-level I/O, start short-mode ranging and recover from a
   bounded communication failure. Log sequence numbers; gaps indicate lost
   diagnostic records and must not disappear from an analysis.
4. Use SWD if boot recovery fails. Its 3V3 pin is a target-voltage reference;
   do not feed a second power supply through it.

## Sensor calibration

ST specifies offset calibration after assembly/reflow. The initial firmware
has `AIRNOTE_OFFSET_MM=0`; this means no measured application correction has
been supplied, not proof that the board has zero offset.

Use the ST procedure in the [sensor API documentation](https://www.st.com/resource/en/user_manual/um2356-vl53l1x-api-user-manual-stmicroelectronics.pdf)
for final calibration. For the initial exposed-sensor engineering prototype,
the included `tools/calibrate_offset.py` estimates a constant application-level
distance correction from >=100 valid samples at a measured target distance.
It is not a replacement for full optical calibration or a cover-glass process.
Record board ID, fixture distance, lighting, sample spread, raw log and result.

Rebuild the board's firmware using the measured signed correction:

```sh
cmake -S firmware -B build/firmware -DAIRNOTE_OFFSET_MM=<measured_integer_mm>
cmake --build build/firmware -j 8
```

Check residual errors at 100, 200, 300, 400 and 500 mm. An offset that fixes one
point does not establish performance over the playing interval. Do not add
cover glass to V1 without revisiting optical geometry and calibration.

## Audio and playing

Disconnect computer USB and use the specified 5 V adapter. Connect the speaker
only between OUTP and OUTN. Neither speaker terminal is ground: ordinary
grounded oscilloscope clips or an audio input must not be connected directly
across these switching outputs. Use acoustic capture or a properly configured
differential/filtered measurement.

At boot, observe MUTE for >=30 ms before switching to PLAY. The firmware stays
muted after it detects a USB host until the next power-cycle. Hardware MUTE
works independently of that interlock. Source current is not inferred from
absence of USB enumeration.

Start quietly, verify fixed tones and gain, and measure supply current and
temperature. The initial sine amplitude ceiling is 8192/32768 (-12 dBFS);
with nominal amplifier gain this is a calculation, not measured output power.
Only adjust it after checking speaker, supply and distortion limits.

Execute every physical test in `requirements.md`. Copy
`bench-results-template.csv` for each board and record pass/fail/pending,
board identity, firmware hash, setup and raw evidence in a new bench record.
The logged maximum audio-producer gap is a diagnostic, not end-to-end latency.
The separate `underruns` field counts the I2S driver's actual consumer-buffer
starvation events. Both audio cores and DMA run during muted USB diagnostics;
acoustic validation also needs a separate PLAY-mode run.

The USB host interlock prevents simultaneous computer diagnostics and audible
PLAY. For the fixed-target test, capture raw sensor validity at each position
in USB MUTE, then repeat the same fixture positions and duration on the adapter
while measuring the actual acoustic note. Keep those runs separately identified;
an offline note prediction from a USB log is not a measurement of speaker output.
Use an external timing fixture and microphone for the physical response test.

Startup holds the sensor in XSHUT and delays audio-core startup until USB is
configured or the user deliberately selects PLAY on the specified adapter.
On detected USB suspend the amplifier and sensor stop, and the audio core
aborts DMA, disables I2S and parks until power-cycle. After resume the sensor
can restart for diagnostics; the audio engine remains parked. These measures
reduce load but do not establish USB suspend-current compliance. The current
USB descriptor requests 250 mA after configuration. Preconfiguration, inrush
and suspend measurements remain manufacturing-release blockers.

