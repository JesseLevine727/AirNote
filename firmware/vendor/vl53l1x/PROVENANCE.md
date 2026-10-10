# VL53L1X driver provenance

Source: https://github.com/pololu/vl53l1x-arduino

Pinned revision: `8f21d608af00b42dc8776cfdf5ce935b45d2387d`.

The BSD-3-Clause license and original ST/Pololu notices are retained in
`LICENSE.txt`. The changes to the original driver are an initialization
guard against zero oscillator calibration before timing divisions and a const
accessor for the sensor stream counter read in the same burst as range/status.
The application rejects repeated frames so a stuck-ready sensor cannot
indefinitely sustain a note. Pico SDK
integration lives separately in `include/compat` and `src/wire.cpp`.

The application additionally checks sticky transport failures, configures
both I2C/GPIO AVDD modes, uses a 100 ms driver timeout and 2 ms transport
timeouts, and treats only `RangeValid` results as playable. These are software
checks, not evidence that a manufactured sensor meets the instrument targets.
