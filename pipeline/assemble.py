#!/usr/bin/env python3
"""
assemble.py
Build a perfectly-synced rough-cut video from the timestamped images + narration.
No manual dragging: every image appears at its timestamp (from 03_segments.json)
and holds until the next one, with narration.mp3 as the soundtrack.

Output is a 1920x1080 H.264 mp4 you import into CapCut for captions/intro/polish.

Usage:
    python pipeline/assemble.py episodes/0001_movie-theater-popcorn
    # writes episodes/0001_movie-theater-popcorn/rough_cut.mp4

Flags:
    --fps 30          output framerate (default 30)
    --out <path>      override output path
    --segments <path> override segments json (default <ep>/03_segments.json)

Requires ffmpeg + ffprobe on PATH (macOS: `brew install ffmpeg`).
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

MIN_DUR = 0.40  # floor so a tiny segment doesn't flash by
SYNC_OFFSET_SEC = 0.40  # shift every image LATER by this much (images were appearing early)


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def find_image(images_dir: Path, index: int) -> Path:
    matches = sorted(images_dir.glob(f"{index:04d}_*.png"))
    if not matches:
        raise FileNotFoundError(f"No image for index {index} in {images_dir}")
    return matches[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", help="episode folder, e.g. episodes/0001_movie-theater-popcorn")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--segments", default=None)
    args = ap.parse_args()

    ep = Path(args.episode)
    seg_path = Path(args.segments) if args.segments else ep / "03_segments.json"
    images_dir = ep / "images"
    audio_path = ep / "audio" / "narration.mp3"
    out_path = Path(args.out) if args.out else ep / "rough_cut.mp4"

    for p in (seg_path, images_dir, audio_path):
        if not p.exists():
            sys.exit(f"Missing required input: {p}")

    segments = json.loads(seg_path.read_text(encoding="utf-8"))
    segments.sort(key=lambda s: s["index"])
    n = len(segments)
    audio_len = audio_duration(audio_path)

    # Shift every image's start LATER by SYNC_OFFSET_SEC, but pin the first image to
    # 0.0 (no blank gap at the top) and let the last image run to the end of audio.
    # Net effect: image 1 holds SYNC_OFFSET_SEC longer, the last image is that much
    # shorter, and every cut in between lands SYNC_OFFSET_SEC later.
    starts = [0.0 if i == 0 else float(seg["seconds"]) + SYNC_OFFSET_SEC
              for i, seg in enumerate(segments)]

    # Duration of each image = gap to the next image's start; last holds to end of audio.
    items = []
    for i, seg in enumerate(segments):
        start = starts[i]
        end = starts[i + 1] if i + 1 < n else audio_len
        dur = max(MIN_DUR, round(end - start, 3))
        items.append((find_image(images_dir, seg["index"]), dur))

    # concat demuxer list file (last entry repeated so its duration is honored)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for img, dur in items:
            f.write(f"file '{img.resolve()}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{items[-1][0].resolve()}'\n")  # demuxer quirk: repeat last
        list_path = f.name

    vf = (
        f"scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,"
        f"fps={args.fps},format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-i", str(audio_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path),
    ]

    print(f"Assembling {n} frames + narration ({audio_len:.1f}s) -> {out_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-2000:])
        sys.exit("ffmpeg failed (see error above)")

    dur = audio_duration(out_path)
    size_mb = out_path.stat().st_size / 1_000_000
    print(f"Done: {out_path}  ({dur:.1f}s, {size_mb:.1f} MB, {args.fps}fps, 1920x1080)")
    print("Next: import this into CapCut for captions, intro card, and thumbnail.")


if __name__ == "__main__":
    main()
