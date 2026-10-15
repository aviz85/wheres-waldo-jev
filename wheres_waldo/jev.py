"""Minimal client for the TypeSafe Jev API (`box` and `noul` questions)."""
import base64, io, os, time
import requests

URL = os.environ.get("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
MODEL = os.environ.get("JEV_MODEL", "jev-preview")
PRICE_PER_TOKEN = 42 / 1e9  # approx. $42 per 1B tokens


def api_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise SystemExit("Set TYPESAFE_API_KEY (see .env.example).")
    return key


def image_asset(im):
    buf = io.BytesIO(); im.save(buf, "PNG")
    return {"type": "image", "format": "png", "data_base64": base64.b64encode(buf.getvalue()).decode()}


def ask(state, assets, questions):
    """POST one request. Returns (json, latency_seconds)."""
    t = time.time()
    r = requests.post(URL, timeout=300, json={"model": MODEL, "state": state, "assets": assets, "questions": questions},
                      headers={"Authorization": f"Bearer {api_key()}", "TypeSafe-Danger-Zone-Images": "true"})
    r.raise_for_status()
    return r.json(), time.time() - t


def cost(usage):
    return (usage.get("input_tokens", 0) + usage.get("output_tokens", 0)) * PRICE_PER_TOKEN
