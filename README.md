# AirNote

A touchless musical instrument built around a fully integrated RP2040,
VL53L1X distance sensor and MAX98357A speaker amplifier. One hand selects
eleven pentatonic notes over two octaves. The design uses a four-layer PCB
and factory assembly, with an external 8 ohm speaker.

**Engineering prototype — not released for fabrication or physically validated.**
Use [the independent review status](reviews/REVIEW_STATUS.md) for current
failures, passes and pending evidence. A schematic check or firmware build
does not establish that the assembled instrument works.

## Open the design

Open [hardware/airnote.kicad_pro](hardware/airnote.kicad_pro) in KiCad 9.0.9
or newer. The project contains three schematic sheets and the PCB. Project
libraries accompany the files. The generated schematic can also be read in
[hardware/outputs/airnote-schematic.pdf](hardware/outputs/airnote-schematic.pdf).

[View the PCB render](hardware/outputs/airnote-board.png). Some parts, including
the volume pot, mute switch and amplifier, have no installed 3D body model;
the render shows their footprints. Use the BOM and assembly drawing for the
fitted-part list, and verify mechanical dimensions from their drawings.

The [BOM](hardware/bom.csv) identifies exact proposed components. Supplier
availability, pricing, chosen stackup and optical-sensor assembly support
still require confirmation. Manufacturing outputs remain engineering review
artifacts until their release checks are complete.

## Try the sound

[Listen to the synthesized scale](artifacts/synth-preview.wav). This WAV is
rendered by the same software oscillator used in firmware; it is **not a
recording of the PCB, amplifier or speaker**.

## Build and verify

Run from this directory. Native behavioral tests need CMake and a C++17
compiler; the device build additionally needs `arm-none-eabi-gcc`, Python 3
and Git. KiCad's Python module is used by the hardware tools.

```sh
cmake -S . -B build/host
cmake --build build/host -j 4
ctest --test-dir build/host --output-on-failure

python3 tools/fetch_dependencies.py
cmake -S firmware -B build/firmware
cmake --build build/firmware -j 8
```

The firmware build produces `build/firmware/airnote.uf2` and `airnote.elf`.
The captured build is also available as [artifacts/airnote.uf2](artifacts/airnote.uf2),
with source and binary checksums in `artifacts/firmware-evidence.json`.
The SDK may fetch/build its own `picotool` utility on the first build. Runtime
dependencies are pinned in `tools/fetch_dependencies.py`; the vendored sensor
and audio transport adaptations retain their licenses and provenance.

To regenerate the software sound preview:

```sh
build/host/render_demo artifacts/synth-preview.wav
```

Independent reviewer tests and artifact checks live in `reviews/`. The
reviewer owns those checks separately from the implementation. Their result
reports distinguish logic/net-mapping evidence from routing and physical tests.

## Documents

- [Requirements, targets and three-agent workflow](docs/requirements.md)
- [Bring-up, programming, equipment and calibration procedure](docs/bringup.md)
- [Power and thermal allocations](docs/power_budget.md)
- [Fabrication and sourcing plan (JLCPCB)](docs/fabrication_plan.md)
- [Draft factory assembly brief](docs/assembly_request.md)
- [Independent review checklist](reviews/CHECKLIST.md)
- [Current review status](reviews/REVIEW_STATUS.md)
- [Exact part list](hardware/bom.csv)
- [Firmware pin assignment](firmware/include/boards/airnote.h)

Normal PLAY operation uses a specified 5 V adapter; programming/USB diagnostics
use the hardware MUTE position. Firmware also latches a USB host mute, starts
peripherals only after configuration or a deliberate adapter PLAY sequence,
and parks audio after USB suspend/deconfiguration until power-cycle. These
policies do not replace current/inrush/suspend measurements. The initial
distance correction is zero and has not been calibrated to a physical board.

The overseer coordinates the specification and integration, the implementer
creates the hardware, and the reviewer independently checks the artifacts and
tests. Neither factory assembly nor clean ERC/DRC counts as physical validation.
