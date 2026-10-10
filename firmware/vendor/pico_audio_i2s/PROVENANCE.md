# I2S transport provenance

Source: Raspberry Pi pico-extras at
`52fd7a786ce47c989afeaee67e0c6aebee56ed2d`,
`src/rp2_common/pico_audio_i2s/audio_i2s.c` and `audio_i2s.pio`.
The BSD-3-Clause license is retained. The public header and supporting audio
pool library come from the same pinned dependency.

The only transport change is a counter at the actual consumer-buffer
starvation branch and its accessor. The ISR and accessor both run on core 1;
the application copies the counter to its critical-section-protected telemetry.
This exposes underruns instead of inferring them from producer timing.
Two silent buffers are primed before I2S starts. Hardware timing and the
instrument's acoustic response still require measurement.
