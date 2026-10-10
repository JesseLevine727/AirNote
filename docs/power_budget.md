# AirNote prototype power budget

This is the design allocation for the present 120 MHz firmware and its
restricted audio amplitude. It sets bench acceptance limits; it is not a
measured current result or proof of USB compliance. Increasing oscillator
amplitude, amplifier gain or processor load requires a new review.

## Current and thermal allocations

| Load | Design allocation | Basis and verification |
| --- | ---: | --- |
| RP2040 including its internal core regulator | 100 mA from 3.3 V | Engineering allowance, not a datasheet maximum; measure both active cores with the actual firmware. |
| QSPI flash | 10 mA from 3.3 V | Engineering allowance; include programming/erase and continuous execute-in-place activity. |
| VL53L1X | 40 mA from 3.3 V | ST reports peaks up to 40 mA at nominal test conditions; verify the shared 3.3 V implementation. |
| Pull-ups, LED, volume divider and margin | 5 mA from 3.3 V | Conservative allocation for the installed resistors and indicator. |
| Amplifier | 50 mA from 5 V | Allocation for the initial approximately 0.1 W sine output, including conversion losses and quiescent current; not valid for arbitrary full-scale firmware. |
| Input/regulator overhead and margin | 5 mA from 5 V | Allocation beyond the load totals. |

The resulting allocation is **155 mA on 3.3 V and 210 mA at the 5 V input**
in PLAY. Computer diagnostics keeps the amplifier shut down and targets
<=170 mA after configuration, below the firmware's 250 mA USB request.
Before configuration the target is <=100 mA, with sensor and audio held off.
The 100 mA MCU allocation does not itself prove that the complete
preconfiguration load meets that target.

The sensor peak figure is specified under ST's nominal voltage and temperature
conditions, not as a guaranteed 3.3 V board maximum. Measure rail transients
during ranging as well as average input current. See the
[VL53L1X electrical characteristics](https://www.st.com/resource/en/datasheet/vl53l1x.pdf).

At 155 mA, the 3.3 V LDO dissipates approximately
`(5.0 - 3.3) * 0.155 = 0.264 W`. At a 5.25 V input this becomes 0.302 W.
Using the datasheet's SOT25 junction-to-ambient figure of 184 degrees C/W
gives an indicative rise of 49–56 degrees C. That estimate depends strongly
on PCB copper and airflow. Measure temperature and rail regulation during
the endurance run; the regulator's 600 mA rating does not make that current
thermally usable in this layout. See the
[AP2112 thermal and electrical data](https://www.diodes.com/assets/Datasheets/AP2112.pdf).

## Initial audio level

The firmware limits sine peak amplitude to 8192 out of 32768, or -12.04 dBFS.
With the floating GAIN pin selecting 9 dB, the manufacturer's gain relation
gives `-12.04 + 2.1 + 9 = -0.94 dBV`, approximately 0.90 V RMS and 0.10 W
into a nominal 8 ohm load. The corresponding sine current is approximately
112 mA RMS or 159 mA peak at the speaker. These calculations assume nominal
gain and a resistive load; a real speaker's impedance varies with frequency.
The gain relation and pin configuration are in the
[MAX98357A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf).

The 50 mA amplifier input allocation allows 0.25 W at 5 V. It must be checked
at the actual load and all eleven pitches. Use an 8 ohm speaker rated at least
1 W; output power and acoustic loudness are separate measurements.

## USB release blockers

Nominal direct input capacitance is 5.9 uF: C18 on raw VBUS plus C16, C21 and
C22 after the PTC. The PTC is not a controlled inrush limiter. Charging the
downstream 3.3 V and 1.1 V capacitance adds source charge; a count of only
the capacitors labelled 5 V therefore cannot establish USB inrush compliance.

The present firmware holds the sensor in reset and delays the audio core
until USB configuration or a deliberate MUTE-to-PLAY sequence on the specified
adapter. USB suspend/deconfiguration disables the amplifier and sensor and
parks the audio core. **Core 0 and the regulator still run; no compliant
suspend current has been demonstrated.** A validated low-power strategy and
input-charge/current measurements are required before a USB-compliant release.
For a first-article build, these open risks need an explicit engineering
disposition and restricted power-on plan; the physical measurements themselves
follow assembly. The current files have not passed that first-article gate.

Record source voltage, current waveform, cable, board revision and firmware
hash for connection, ROM BOOTSEL, unconfigured application, configured
diagnostics, suspend, resume and maximum-volume PLAY. Resolve any failure
with circuitry/firmware changes and repeat the affected measurements.

PLAY uses the specified regulated 5 V adapter rated at least 1 A. That adapter
rating is available capacity, not the board's expected draw. USB host detection
and a 500 mA PTC do not establish available source current or protocol compliance.
