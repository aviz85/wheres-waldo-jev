#!/usr/bin/env python3
"""Summarize results.json files: accuracy per mode and confidence calibration.

  python summarize.py results/round1_results.json results/round2_results.json
"""
import json, statistics, sys
from collections import defaultdict

rows = [r for f in sys.argv[1:] for r in json.load(open(f))]
by = defaultdict(list)
for r in rows: by[r["mode"]].append(r)
for m, R in by.items():
    lat = [r["latency_ms"] for r in R if r.get("latency_ms")]
    print(f"{m:8s} {sum(r['hit'] for r in R)}/{len(R)}  median latency {statistics.median(lat) if lat else '-'} ms")
single = by.get("single", [])
for lo, hi in [(0.7, 1.01), (0.3, 0.7), (0, 0.3)]:
    R = [r for r in single if lo <= (r.get("confidence") or 0) < hi]
    if R: print(f"single, confidence [{lo}, {min(hi, 1)}): {sum(r['hit'] for r in R)}/{len(R)} correct")
