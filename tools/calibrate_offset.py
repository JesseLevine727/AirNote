#!/usr/bin/env python3
"""Estimate a prototype application offset from AirNote USB CDC logs."""
import argparse
import csv
import statistics
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('log', type=Path)
p.add_argument('--target-mm', type=float, required=True)
args = p.parse_args()
if not 100 <= args.target_mm <= 500:
    p.error('target must be within 100..500 mm')
valid, total, sequences = [], 0, []
for row in csv.reader(args.log.read_text().splitlines()):
    if len(row) != 9 or row[0] != 'sample':
        continue
    try:
        sequence, raw, status, error = int(row[1]), int(row[3]), int(row[5]), int(row[6])
    except ValueError:
        continue
    total += 1
    sequences.append(sequence)
    if status == 0 and error == 0:
        valid.append(raw)
if len(valid) < 100:
    raise SystemExit(f'Need >=100 valid samples; found {len(valid)} of {total}')
if any(b != a + 1 for a, b in zip(sequences, sequences[1:])):
    raise SystemExit('Sequence gaps or resets detected; capture a continuous fixture log')
if len(valid) / total < 0.99:
    raise SystemExit(f'Valid sample rate {len(valid)/total:.1%} is below 99%; fix setup first')
spread = statistics.stdev(valid)
if spread > 5:
    raise SystemExit(f'Unstable fixture: sample standard deviation {spread:.2f} mm >5 mm')
offset = round(args.target_mm - statistics.mean(valid))
if abs(offset) > 30:
    raise SystemExit(f'Offset {offset} mm exceeds prototype guard; investigate fixture/optics')
print(f'valid={len(valid)}/{total}, mean_raw_mm={statistics.mean(valid):.3f}, stdev_mm={spread:.3f}')
print(f'Proposed application correction: -DAIRNOTE_OFFSET_MM={offset}')
print('Not full ST calibration. Record board ID and verify residuals across the full range.')
