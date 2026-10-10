# Third-party software

The built firmware incorporates Raspberry Pi Pico SDK 2.3.1, Pico Extras
audio support and its USB dependency TinyUSB. Their licenses accompany this
source tree in `licenses/`. The sensor driver and instrumented I2S transport
retain their notices and provenance in `vendor/`.

- Pico SDK: `079c6f39023649b154152db30f1d781e884879bc` (BSD-3-Clause and source-file notices).
- Pico Extras: `52fd7a786ce47c989afeaee67e0c6aebee56ed2d` (BSD-3-Clause).
- TinyUSB SDK submodule: `86ad6e56c1700e85f1c5678607a762cfe3aa2f47` (MIT).
- ST/Pololu VL53L1X driver: `8f21d608af00b42dc8776cfdf5ce935b45d2387d` (BSD-3-Clause).

The host-only UF2 build utility picotool is pinned to
`2041936441b48a3cc53ae3da9e805229fe8f4e18` in `firmware/CMakeLists.txt`.

Retain these notices with any redistributed firmware binaries. The compiler
also supplies its standard runtime libraries under their respective licenses
and applicable runtime exceptions.
