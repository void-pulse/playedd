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

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "brand" / "assets" / "avatar_800.png"   # silent Playedd end stamp (no CTA text)
LOGO_SEC = 2.5
MIN_DUR = 0.40  # floor so a tiny segment doesn't flash by
SYNC_OFFSET_SEC = 0.25  # shift every image LATER by this much (FORMATS.md global)


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
    ap.add_argument("--no-logo", action="store_true", help="skip the silent Playedd logo end stamp")
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

    # Silent Playedd logo end stamp: composite the tracked face onto a clean white frame,
    # held LOGO_SEC past the narration. Baked at assemble time so a clean rebuild can't lose it.
    use_logo = LOGO.exists() and not args.no_logo
    tmpdir = Path(tempfile.mkdtemp())
    if use_logo:
        logo_frame = tmpdir / "logo.png"
        lr = subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=white:s=1920x1080", "-i", str(LOGO),
            "-filter_complex",
            "[1:v]colorkey=0xfaf9f4:0.18:0.08,scale=760:760[lg];[0:v][lg]overlay=(W-w)/2:(H-h)/2[out]",
            "-map", "[out]", "-frames:v", "1", str(logo_frame)], capture_output=True, text=True)
        if lr.returncode != 0:
            sys.exit("logo end-stamp composite failed:\n" + lr.stderr[-1500:])
        items.append((logo_frame, LOGO_SEC))
    total = audio_len + (LOGO_SEC if use_logo else 0.0)

    # Video via the concat FILTER (the concat demuxer silently drops still-image durations).
    scale_body = (f"scale=1920:1080:force_original_aspect_ratio=decrease,"
                  f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,setsar=1,fps={args.fps},format=yuv420p")
    vin, vparts = [], []
    for k, (img, dur) in enumerate(items):
        vin += ["-loop", "1", "-t", f"{dur}", "-i", str(img)]
        vparts.append(f"[{k}:v]{scale_body}[v{k}]")
    vparts.append("".join(f"[v{k}]" for k in range(len(items))) + f"concat=n={len(items)}:v=1[v]")
    aidx = len(items)
    vparts.append(f"[{aidx}:a]aresample=44100,apad,atrim=0:{total:.3f},asetpts=N/SR/TB[a]")

    cmd = [
        "ffmpeg", "-y", *vin, "-i", str(audio_path),
        "-filter_complex", ";".join(vparts),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-r", str(args.fps), "-t", f"{total:.3f}",
        "-movflags", "+faststart", str(out_path),
    ]

    print(f"Assembling {n} frames + narration ({audio_len:.1f}s) + silent logo -> {out_path}")
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
