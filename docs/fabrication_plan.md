# AirNote fabrication and sourcing plan

Revision 0.2 draft, 2026-10-10. Overseer decision record for the first
engineering articles. **No order has been placed.** Stock, prices and fees
below are a single 2026-10-10 snapshot from JLCPCB/LCSC and will change.

## Supplier and process

| Item | Decision | Reason |
| --- | --- | --- |
| Fabricator / assembler | JLCPCB, parts from JLC/LCSC stock | Single vendor for 4-layer fab, SMT and THT assembly; every fitted part found in stock (see BOM). |
| PCBA service | **Standard PCBA, single-sided (top)** | JLC lists the VL53L1X (C190004) as "Standard only". Economic reflow (255 °C) also exceeds ST's 245 °C maximum peak for the sensor. All parts are on the top side. |
| Stackup | **JLC04161H-7628** (JLC default, no fee) | See table below. Impedance control is not ordered; geometry is calculated instead. |
| Board | 90 × 70 mm, 1.6 mm, 1 oz outer / 0.5 oz inner | Meets Standard PCBA minimum size (70 × 70 mm). |
| Washing | None / no-clean | ST requires a no-wash process for the optical sensor. |
| Sensor liner | Removed by us after assembly | ST ships the VL53L1X with a protective liner; no JLC process for removing it was found. Remove it with tweezers during bring-up, before any optical test. |

### JLC04161H-7628 stackup

| Layer | Material | Thickness | Dk |
| --- | --- | ---: | ---: |
| F.Cu (L1) | 1 oz copper | 0.035 mm | |
| Prepreg | 1 × 7628, RC49% | 0.2104 mm | 4.4 |
| In1.Cu (L2), GND | 0.5 oz copper | 0.0152 mm | |
| Core | | 1.065 mm | 4.6 (JLC calculator DB: 4.38–4.42) |
| In2.Cu (L3), GND | 0.5 oz copper | 0.0152 mm | |
| Prepreg | 1 × 7628 | 0.2104 mm | 4.4 |
| B.Cu (L4) | 1 oz copper | 0.035 mm | |

Solder mask Dk 3.8. Finished thickness 1.59 mm ±10%. Source: JLC impedance
page and calculator templates, https://jlcpcb.com/impedance.

### USB differential geometry

USB 2.0 full speed (12 Mb/s) needs 90 Ω ±15% differential (76.5–103.5 Ω).
The pair is routed on F.Cu over the solid In1.Cu ground at **0.25 mm width,
0.15 mm gap** (0.40 mm pitch, matching the RP2040 USB pin pitch).

| Method | Geometry | Result |
| --- | --- | --- |
| JLC calculator (Si9000 engine), coated microstrip | 0.240 / 0.15 mm | 90.0 Ω |
| Independent 2D finite-difference field solve, 15 µm mask | 0.25 / 0.15 mm | 92.4 Ω (solver validated within 2.5% of Hammerstad–Jensen) |
| Same, without solder mask | 0.25 / 0.15 mm | 102.6 Ω |

Both methods put 0.25/0.15 mm inside the full-speed tolerance. JLC's paid
impedance control (+$33 on this quote) is therefore not ordered. These are
calculations, not a TDR measurement.

The rev 0.2 layout applies this as net class `USB_DIFF`. All six USB nets
are on F.Cu with no vias, and In1.Cu ground is continuous under them.
About 85% of each line's length runs at exactly 0.40 mm pitch (reviewer
measurement). The rest is neck-down at the J1, D1 and U1 pads, including two
runs of about 3 mm through D1's pad gap. Details: `hardware/README.md` and
`reviews/layout-review.json`.

### Design rules versus JLC 4-layer capability

| Rule | AirNote | JLC capability | Status |
| --- | --- | --- | --- |
| Min track / space | 0.15 / 0.127 mm | 0.09 / 0.09 mm | OK, no surcharge |
| Via drill / pad | 0.20 / 0.45 mm | 0.15 / 0.25 mm min; 0.20 with ≥0.45 pad is free | OK, no surcharge |
| Via hole to track | ≈0.25 mm | ≥0.2 mm | OK |
| Solder-mask web | | ≥0.10 mm | Check in final DRC/export review |

Source: https://jlcpcb.com/capabilities/pcb-capabilities.

The custom rules in `hardware/airnote.kicad_dru` were never enforced before
rev 0.2: the file had no units, and KiCad discards a whole rule file with a
unitless value (verified by testing a deliberately impossible rule both
ways). Rev 0.2 adds the units, so DRC now applies these rules and the
USB_DIFF rules, and still passes.

## Surface finish (order-time decision)

Not yet selected; the design files are the same either way. ENIG gives
flatter pads than HASL for the 0.4 mm pitch RP2040 QFN, the VL53L1X LGA and
the MAX98357A TQFN, which reduces bridging and open-joint risk on exactly
the parts that are hardest to rework. Recommendation: ENIG if the price
difference on the order page is small. Lead-free HASL is acceptable.

## Exposed-pad vias (order-time decision)

The RP2040 and MAX98357A exposed pads contain five 0.20 mm thermal/ground
vias. JLC cannot ink-plug vias inside pads; by default they stay **open**
(plated, unfilled), so some solder can wick into them.

- **Open (default, $0):** common on JLC-assembled RP2040 boards with small
  vias. Risk: voiding under the exposed pad. The RP2040 exposed pad is its
  only ground connection, so a poor joint stops the chip working.
- **Epoxy-filled and capped (POFV): about +$21** ($17.32 plus $3.39 required
  electroless copper) on 4-layer. Removes the wicking variable for first articles.

Recommendation: POFV for the first order, since $21 is small next to a
failed batch. This is the user's call at order time; the design files are
the same either way.

## Sourcing summary

Every fitted part was found in JLC/LCSC stock. The rev 0.2 layout carries
the LCSC numbers in `hardware/bom.csv`, on every fitted schematic symbol and
as hidden footprint fields. Changes from the Codex BOM, made for stock or
correctness:

| Ref | Was | Now | Why |
| --- | --- | --- | --- |
| U2 | W25Q16JVSSIQ | W25Q16JVSNIQ (C2456211) | **Correctness:** "SS" is the 208-mil SOIC, but the placed footprint is the 150-mil SOIC-8. "SN" is the same device in the 150-mil package. |
| J1 | USB4105-GF-A (44 in stock) | USB4105-GF-A-120 (C5184243) | Same land pattern; only the shell stake length (1.20 mm) differs. |
| RV1 | PTV09A-1020F-B103 | PTV09A-4015F-B103 (C5710902) | The original isn't carried by LCSC. Same electrical part; bushingless, 15 mm shaft. Low stock: order early. |
| J2 | Samtec TSW-105-07-G-S | Generic 1 × 5 2.54 mm header (C32713271) | Low Samtec stock; identical footprint. |
| Passives | Murata/Yageo MPNs | JLC Basic equivalents | Several exact MPNs out of stock (1 µF had 4, 4.7 µF had 0, 27 Ω under the minimum order). |

Parts cost is about **$13.55 per board** at qty-10 prices, before attrition.

## Rough first-order cost (5 boards, 2 assembled)

From JLC's 2026-09-09 price page; not a quote.

| Item | Approx. |
| --- | ---: |
| 5 × 4-layer PCBs, JLC04161H-7628 | $8 |
| Standard PCBA setup + single-side stencil | $34 |
| Feeder/loading fees: 26 unique parts × $1.53 | $40 |
| Parts for 2 boards (with attrition) | ~$30 |
| THT hand soldering (RV1, J2, J3) | ~$5 |
| POFV (recommended) | $21 |
| **Subtotal before shipping/tax** | **≈ $140** |

Rev 0.2 adds three global fiducials (1 mm copper, 2 mm mask opening).
Whether JLC wants edge rails for this board is still to be confirmed on
the actual quote.

## Before ordering

1. The layout corrections and BOM changes must pass the independent review
   (`reviews/REVIEW_STATUS.md`).
2. Generate JLC-format BOM and placement (CPL) files from the reviewed
   revision. Check every part's rotation in JLC's placement preview before
   paying; the RP2040, VL53L1X, MAX98357A, USB-C and SOT-23 parts most often
   need rotation corrections.
3. Re-check stock for RV1, J1 and the RP2040 on the day of ordering.
4. Decide on POFV and the surface finish (see above).
