#!/usr/bin/env python3
"""generate_episode_images.py — MOODY CINEMATIC long-form episode art.

The locked-in LONG-FORM style (2026-06): dark, near-black backgrounds with one
dramatic spotlight/glow, high contrast, thick-outline doodles, TEXT-FREE. A big
step up from the bright flat shorts look — see brand/LONGFORM_STRATEGY.md. First
used on ep17 (childhood amnesia).

Reads <episode>/04_scenes.json ({index, timestamp, scene, ...}) and writes
landscape 16:9 PNGs into <episode>/images/, named so assemble.py finds them.

NOTE: the OLD bright flat doodle style (with baked-in caps) still lives in
pipeline/generate_images.py via brand/IMAGE_STYLE.md's STYLE_BLOCK — that remains
the SHORTS default and is preserved if we ever want to switch episodes back.

Usage:
    python pipeline/generate_episode_images.py episodes/0017_childhood-amnesia [--concurrency 4]
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_images import safe_name  # consistent NNNN_MmSSs.png naming  # noqa: E402

STYLE = ("A flat hand-drawn cartoon doodle illustration with thick black outlines, in a MOODY CINEMATIC style. "
         "Simple doodle characters; the stick figure 'Stan' has a round white head, two dot eyes, a simple line "
         "mouth, thin line limbs, no hair. Deep dark near-black navy/charcoal background with ONE dramatic "
         "spotlight or glow lighting the subject, high contrast, cinematic mood. Horizontal 16:9 wide frame. "
         "ABSOLUTELY NO words, letters, numbers, captions or text anywhere. SCENE: ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", help="episode folder containing 04_scenes.json")
    ap.add_argument("--model", default="fal-ai/gpt-image-2")
    ap.add_argument("--quality", default="medium")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()
    if not os.getenv("FAL_KEY"):
        sys.exit("FAL_KEY not set")
    import fal_client

    ep = Path(args.episode)
    scenes = json.loads((ep / "04_scenes.json").read_text())
    out = ep / "images"; out.mkdir(exist_ok=True)

    def one(s):
        p = out / safe_name(s["index"], s["timestamp"])
        if p.exists() and p.stat().st_size > 0:
            return s["index"], "skip"
        try:
            res = fal_client.subscribe(args.model, with_logs=False, arguments={
                "prompt": STYLE + s["scene"],
                "image_size": {"width": 1536, "height": 864},
                "num_images": 1, "quality": args.quality})
            url = (res.get("images") or [{}])[0].get("url")
            r = requests.get(url, timeout=120); p.write_bytes(r.content)
            return s["index"], "ok"
        except Exception as e:
            return s["index"], f"ERR {str(e)[:70]}"

    ok = skip = err = 0
    with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for idx, st in ex.map(one, scenes):
            print(idx, st, flush=True)
            ok += st == "ok"; skip += st == "skip"; err += st.startswith("ERR")
    print(f"DONE ok={ok} skip={skip} err={err} total={len(scenes)}")


if __name__ == "__main__":
    main()
