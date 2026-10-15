#!/usr/bin/env python3
"""Generate the Where's Waldo benchmark scenes (no API needed).

  python generate.py --round 1 --out data/round1   # 72 scenes, 30-120 people, poses + occlusion + decoys
  python generate.py --round 2 --out data/round2   # 54 hard scenes, 200-600 people, small Waldo
"""
import argparse, json, pathlib, random
from wheres_waldo.draw import reference
from wheres_waldo.scenes import scene

POSES = ["standard", "mirror_stride", "mirror_wave", "tilt_left", "tilt_right", "lying", "upside_down",
         "arms_up", "wave", "stride", "sitting", "back", "small", "large"]
OCCS = ["bottom25", "bottom50", "bottom75", "side50", "head_only", "behind_person", "edge_cut"]


def round1(out):
    gts, seed = {}, 5000
    for p in POSES:
        for k in range(3):
            seed += 1; gts[f"pose_{p}_{k}"] = scene(out, f"pose_{p}_{k}", pose=p, n=random.Random(seed).choice([30, 60, 90, 120]), seed=seed)
    for o in OCCS:
        for k in range(3):
            seed += 1; gts[f"occ_{o}_{k}"] = scene(out, f"occ_{o}_{k}", occ=o, n=random.Random(seed).choice([30, 60, 90, 120]), seed=seed)
    for p, o in [("tilt_left", "bottom50"), ("arms_up", "side50"), ("sitting", "behind_person"), ("back", "bottom25")]:
        seed += 1; gts[f"combo_{p}_{o}"] = scene(out, f"combo_{p}_{o}", pose=p, occ=o, n=80, seed=seed)
    for p in ["standard", "arms_up", "tilt_right", "stride", "sitting"]:
        seed += 1; gts[f"decoy_{p}"] = scene(out, f"decoy_{p}", pose=p, n=90, ndec=8, seed=seed)
    return gts


def round2(out, count=54):
    poses = ["standard", "lying", "upside_down", "sitting", "back", "arms_up", "tilt_left", "mirror_stride"]
    occs = [None, None, "bottom50", "side50", "head_only", "behind_person"]
    gts, rng = {}, random.Random(7)
    for i in range(count):
        n = [200, 350, 600][i % 3]; s = {200: 2.0, 350: 1.6, 600: 1.3}[n]
        rel = rng.choice([0.3, 0.45, 0.6]); p = rng.choice(poses); o = rng.choice(occs); nd = rng.choice([0, 0, 15])
        g = scene(out, f"h{i:02d}", pose=p, occ=o, n=n, ndec=nd, s=s, seed=9000 + i, tsc=round(2.8 * rel, 2))
        g.update(rel=rel, density=n); gts[f"h{i:02d}"] = g
    return gts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, choices=[1, 2], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=54, help="round 2 only: number of scenes")
    a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    reference(out / "reference.png")
    gts = round1(out) if a.round == 1 else round2(out, a.limit)
    json.dump(gts, open(out / "ground_truth.json", "w"), indent=1)
    print(f"wrote {len(gts)} scenes + reference.png + ground_truth.json to {out}")
