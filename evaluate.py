#!/usr/bin/env python3
"""Ask Jev to find Waldo in every generated scene and score the answers.

  export TYPESAFE_API_KEY=...
  python evaluate.py data/round2 --modes single tiled2 [--limit 5]

single : one request, `box` question over the whole scene (reference image in the same state).
tiledG : split the scene into a GxG grid (15% overlap), one request with a `noul` (visible?) and a
         `box` question per tile; pick the tile with the highest p_visible * box confidence.
Hit = center of the predicted box inside Waldo's visible box (+/-3px), or, for occluded scenes,
inside his full-body box. Annotated images: green = ground truth, magenta = Jev's box.
"""
import argparse, json, pathlib, uuid
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from wheres_waldo import jev

INS = ("the person in `{t}` who is the same character as `reference_character` (red-and-white horizontally striped "
       "shirt, red-and-white beanie with a white pompom, round glasses, blue trousers). The character may be in a "
       "different pose, rotated, seen from behind, or partially hidden")


def inside(px, gt):
    cx, cy = (px[0] + px[2]) / 2, (px[1] + px[3]) / 2
    return gt[0] - 3 <= cx <= gt[2] + 3 and gt[1] - 3 <= cy <= gt[3] + 3


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u else 0


def tiles(W, H, g):
    tw, th = W / g * 1.15, H / g * 1.15; out = []
    for i in range(g):
        for j in range(g):
            x0 = min(W - tw, max(0, j * W / g - W / g * .075)); y0 = min(H - th, max(0, i * H / g - H / g * .075))
            out.append((round(x0), round(y0), round(x0 + tw), round(y0 + th)))
    return out


def run_one(data, out, name, info, mode):
    im = Image.open(data / f"{name}.png").convert("RGB"); W, H = im.size
    rr = f"ref-{uuid.uuid4()}"; state = {"reference_character": rr}
    assets = {rr: jev.image_asset(Image.open(data / "reference.png").convert("RGB"))}
    if mode == "single":
        rs = f"scn-{uuid.uuid4()}"; state["scene"] = rs; assets[rs] = jev.image_asset(im)
        j, lat = jev.ask(state, assets, {"target": {"type": "box", "instructions": INS.format(t="scene")}})
        a = j["answers"]["target"]; t = (0, 0, W, H); pvis = None
    else:
        g = int(mode[5:]); T = tiles(W, H, g); qs = {}
        for k, tb in enumerate(T):
            r = f"t{k}-{uuid.uuid4()}"; state[f"tile{k}"] = r; assets[r] = jev.image_asset(im.crop(tb))
            qs[f"p{k}"] = {"type": "noul", "instructions": f"Is the character from `reference_character` visible (possibly in another pose or partly hidden) in `tile{k}`?"}
            qs[f"b{k}"] = {"type": "box", "instructions": INS.format(t=f"tile{k}")}
        j, lat = jev.ask(state, assets, qs); A = j["answers"]
        best = max(range(len(T)), key=lambda k: (A[f"p{k}"].get("noul") or 0) * (A[f"b{k}"].get("confidence") or 0))
        a = A[f"b{best}"]; t = T[best]; pvis = A[f"p{best}"].get("noul")
    b = a["box"]; tw, th = t[2] - t[0], t[3] - t[1]
    px = [t[0] + b["left"] * tw, t[1] + b["top"] * th, t[0] + b["right"] * tw, t[1] + b["bottom"] * th]
    gt = info["gt"]; hit = inside(px, gt) or (info.get("occ", "none") != "none" and inside(px, info["full"]))
    d = ImageDraw.Draw(im); d.rectangle(gt, outline=(0, 255, 0), width=3); d.rectangle(px, outline=(255, 0, 255), width=4)
    im.save(out / f"{mode}_{name}.png")
    return dict(name=name, mode=mode, **info, box_px=[round(v) for v in px], hit=hit, iou=round(iou(px, gt), 3),
                confidence=a.get("confidence"), p_visible=pvis, latency_ms=round(lat * 1000), cost_usd=jev.cost(j.get("usage", {})))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("--out", default=None)
    ap.add_argument("--modes", nargs="+", default=["single"]); ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(); data = pathlib.Path(a.data); out = pathlib.Path(a.out or data / "results"); out.mkdir(parents=True, exist_ok=True)
    jev.api_key()
    gts = list(json.load(open(data / "ground_truth.json")).items())[: a.limit]
    rows = []
    for mode in a.modes:
        def safe(item):
            try: return run_one(data, out, item[0], item[1], mode)
            except Exception as e: print("ERR", item[0], e)
        with ThreadPoolExecutor(a.workers) as ex: R = [r for r in ex.map(safe, gts) if r]
        print(f"{mode}: {sum(r['hit'] for r in R)}/{len(R)} hits, cost ${sum(r['cost_usd'] for r in R):.4f}"); rows += R
    json.dump(rows, open(out / "results.json", "w"), indent=1)
