#!/usr/bin/env python3
"""animate_short.py — build a FULLY AI-ANIMATED short.

Runs each scene's still doodle through minimax video-01-live (image-to-video, which
keeps the flat hand-drawn style), then assembles the moving clips + the static CTA
end card + narration into a 1080x1920 short. Caption it afterwards with caption_short.

Usage:
    python pipeline/animate_short.py shorts_daily/batch03/06_doorway \
        --cuts 0 5 10 14.5 --out shorts_daily/batch03/06_doorway/06_doorway_anim.mp4 \
        --cta-heading "BECOME A,STAN" --badge "DAILY WONDER #14"
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_short import make_cta_card, ffdur, W, H, FPS  # noqa: E402

MODEL = "fal-ai/minimax/video-01-live/image-to-video"


def animate_one(fal_client, img: Path, scene_text: str, out: Path):
    if out.exists() and out.stat().st_size > 0:
        return out
    prompt = (f"Flat 2D hand-drawn cartoon doodle animation. {scene_text} "
              "Subtle, natural motion. Keep the EXACT flat hand-drawn doodle style with thick "
              "black outlines, flat colors, no 3D, no realism, no camera moves.")
    url = fal_client.upload_file(str(img))
    res = fal_client.subscribe(MODEL, arguments={"prompt": prompt, "image_url": url}, with_logs=False)
    vurl = (res.get("video") or {}).get("url") or res.get("video_url")
    if not vurl:
        raise RuntimeError(f"no video url: {list(res.keys())}")
    r = requests.get(vurl, timeout=240); r.raise_for_status()
    out.write_bytes(r.content)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene_dir", help="short dir containing audio/narration.mp3 + images/ + 04_short_scenes.json")
    ap.add_argument("--cuts", nargs="+", type=float, required=True, help="scene start times (one per image)")
    ap.add_argument("--cta-sec", type=float, default=0.4)
    ap.add_argument("--tail", type=float, default=2.2)
    ap.add_argument("--cta-heading", default="BECOME A,STAN")
    ap.add_argument("--badge", default="")
    ap.add_argument("--bg", default="#FFFFFF")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = Path(args.scene_dir)
    narration = d / "audio" / "narration.mp3"
    imgs = sorted((d / "images").glob("*.png"))
    scenes = json.loads((d / "04_short_scenes.json").read_text())
    scene_text = {s["index"]: s["scene"] for s in scenes}
    if len(imgs) != len(args.cuts):
        sys.exit(f"{len(imgs)} images but {len(args.cuts)} cuts")

    import fal_client
    if not os.getenv("FAL_KEY"):
        sys.exit("FAL_KEY not set")

    work = Path(tempfile.mkdtemp())
    anim_dir = d / "animated"; anim_dir.mkdir(exist_ok=True)

    # 1) animate every scene in parallel
    print(f"animating {len(imgs)} scenes via minimax...", flush=True)
    clips = [None] * len(imgs)
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(animate_one, fal_client, img, scene_text.get(i + 1, ""), anim_dir / f"clip_{i:02d}.mp4"): i
                for i, img in enumerate(imgs)}
        for fut in cf.as_completed(futs):
            i = futs[fut]
            clips[i] = fut.result()
            print(f"  scene {i+1} animated", flush=True)

    # 2) durations from cuts (last scene runs to the image window = narration - cta_sec)
    dur = ffdur(narration)
    window = max(0.5, dur - args.cta_sec)
    starts = list(args.cuts)
    durs = [(starts[k + 1] if k + 1 < len(starts) else window) - starts[k] for k in range(len(starts))]

    # 3) CTA still
    cta = work / "cta.png"
    make_cta_card(args.bg, cta, "", args.cta_heading, args.badge)

    # 4) picture track: each clip trimmed to its dur + scaled cover; CTA still held to the end
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p"
    vin, vparts = [], []
    for k, (clip, du) in enumerate(zip(clips, durs)):
        vin += ["-stream_loop", "-1", "-i", str(clip)]   # loop in case a clip is shorter than its slot
        vparts.append(f"[{k}:v]trim=0:{du:.3f},setpts=PTS-STARTPTS,{cover}[v{k}]")
    n = len(clips)
    vin += ["-loop", "1", "-t", f"{args.cta_sec + args.tail:.3f}", "-i", str(cta)]
    vparts.append(f"[{n}:v]{cover}[v{n}]")
    vparts.append("".join(f"[v{k}]" for k in range(n + 1)) + f"concat=n={n+1}:v=1[v]")
    picture = work / "picture.mp4"
    r = subprocess.run(["ffmpeg", "-y", *vin, "-filter_complex", ";".join(vparts), "-map", "[v]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-r", str(FPS), str(picture)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("picture render failed:\n" + r.stderr[-1800:])

    # 5) mux narration (padded with silence through the CTA tail)
    total = sum(durs) + args.cta_sec + args.tail
    out = Path(args.out)
    r = subprocess.run(["ffmpeg", "-y", "-i", str(picture), "-i", str(narration),
                        "-filter_complex", f"[1:a]apad,atrim=0:{total:.3f},asetpts=N/SR/TB[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("mux failed:\n" + r.stderr[-1800:])
    print(f"ANIMATED SHORT -> {out}  ({total:.1f}s, {n} animated scenes + CTA)")


if __name__ == "__main__":
    main()
