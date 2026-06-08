#!/usr/bin/env python3
"""
generate_images.py
Generate one doodle image per timestamp via fal.ai (gpt-image-2), named by
timestamp so they drop into CapCut already in order.

Input: 04_scenes.json  (list of {index, timestamp, seconds, scene})
       produced by feeding 03_segments.json to prompts/03 in Claude Code.

Usage:
    python pipeline/generate_images.py episodes/<ep>/04_scenes.json
    # writes episodes/<ep>/images/0001_0m00s.png, 0002_0m07s.png, ...

Flags:
    --model fal-ai/gpt-image-2     (default) doodle-friendly, follows instructions
            fal-ai/flux/schnell    cheaper/faster fallback, less obedient on "bad" style
    --concurrency 4                parallel requests
    --resume                       skip images that already exist (re-run safe)
    --only 12                      generate only segment index 12 (for fixing one frame)

Setup:
    pip install -r requirements.txt
    Set FAL_KEY in .env  (you've already funded the account with auto top-up)
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "brand" / "IMAGE_STYLE.md"


def load_style_block() -> str:
    text = STYLE_FILE.read_text(encoding="utf-8")
    m = re.search(r"<!-- STYLE_BLOCK_START -->(.*?)<!-- STYLE_BLOCK_END -->", text, flags=re.S)
    if not m:
        sys.exit("Could not find STYLE_BLOCK markers in brand/IMAGE_STYLE.md")
    return m.group(1).strip()


def safe_name(index: int, timestamp: str) -> str:
    # "0:07" -> "0m07s"; zero-pad index so files sort correctly.
    parts = timestamp.split(":")
    if len(parts) == 3:
        h, m, s = parts
        label = f"{int(h)}h{int(m):02d}m{int(s):02d}s"
    else:
        m, s = parts
        label = f"{int(m)}m{int(s):02d}s"
    return f"{index:04d}_{label}.png"


def build_prompt(style_block: str, scene: str) -> str:
    return f"{style_block}\n\nSCENE: {scene}"


def image_args(model: str, prompt: str, portrait: bool = False) -> dict:
    """
    Arg shapes differ slightly per model on fal. Verify against the model's API
    page if a call ever rejects an argument:
      https://fal.ai/models/fal-ai/gpt-image-2
      https://fal.ai/models/fal-ai/flux/schnell
    portrait=True -> native 9:16 vertical (Shorts); default is landscape 16:9.
    """
    if "gpt-image" in model:
        size = {"width": 1080, "height": 1920} if portrait else {"width": 1920, "height": 1080}
        return {
            "prompt": prompt,
            "image_size": size,
            "num_images": 1,
            "quality": "medium",             # medium is the cost/quality sweet spot
        }
    # flux fallback
    return {
        "prompt": prompt,
        "image_size": "portrait_16_9" if portrait else "landscape_16_9",
        "num_images": 1,
        "num_inference_steps": 4,
    }


def extract_url(result: dict) -> str:
    imgs = result.get("images") or result.get("data") or []
    if imgs and isinstance(imgs, list):
        first = imgs[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("image_url")
        return first
    # some endpoints return {"image": {...}}
    if "image" in result and isinstance(result["image"], dict):
        return result["image"].get("url")
    raise RuntimeError(f"No image URL in result: {list(result.keys())}")


def generate_one(fal_client, model, style_block, seg, out_dir, resume, portrait=False):
    out_path = out_dir / safe_name(seg["index"], seg["timestamp"])
    if resume and out_path.exists() and out_path.stat().st_size > 0:
        return seg["index"], "skip", out_path.name
    prompt = build_prompt(style_block, seg["scene"])
    try:
        result = fal_client.subscribe(model, arguments=image_args(model, prompt, portrait), with_logs=False)
        url = extract_url(result)
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return seg["index"], "ok", out_path.name
    except Exception as e:  # noqa
        return seg["index"], f"ERROR: {e}", out_path.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", help="path to 04_scenes.json")
    ap.add_argument("--model", default="fal-ai/gpt-image-2")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--portrait", action="store_true",
                    help="native 9:16 vertical for Shorts (overrides the style block's framing)")
    args = ap.parse_args()

    if not os.getenv("FAL_KEY"):
        sys.exit("FAL_KEY not set. Add it to .env")

    import fal_client

    scenes_path = Path(args.scenes)
    scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
    if args.only is not None:
        scenes = [s for s in scenes if s["index"] == args.only]
        if not scenes:
            sys.exit(f"No segment with index {args.only}")

    out_dir = scenes_path.parent / "images"
    out_dir.mkdir(exist_ok=True)
    style_block = load_style_block()
    if args.portrait:
        # swap the canonical horizontal framing for native vertical 9:16, fill edge to edge
        style_block = re.sub(
            r"Composition: horizontal 16:9 wide YouTube frame\. Clean, centered, readable\. "
            r"Do not crop important objects\. Leave breathing room\.",
            "Composition: VERTICAL 9:16 tall mobile frame (a Short). Compose the subject TALL and "
            "BIG so it fills the whole vertical frame top to bottom and edge to edge — no empty "
            "bands, no margins, no dead white space. Clean and readable.",
            style_block,
        )

    print(f"Model: {args.model} | {len(scenes)} images | concurrency {args.concurrency}")
    ok = skip = err = 0
    with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [
            ex.submit(generate_one, fal_client, args.model, style_block, s, out_dir, args.resume, args.portrait)
            for s in scenes
        ]
        for fut in cf.as_completed(futures):
            idx, status, name = fut.result()
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                err += 1
            print(f"  [{idx:>4}] {status:<8} {name}")

    print(f"\nDone. ok={ok} skipped={skip} errors={err}")
    print(f"Images in {out_dir}")
    if err:
        print("Re-run with --resume to retry only the failures.")
    else:
        print("Next: open CapCut, drop the images folder in filename order, lay narration.mp3 under it.")


if __name__ == "__main__":
    main()
