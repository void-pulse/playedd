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
OUTRO = ROOT / "brand" / "assets" / "end_card_main.png"  # silent like/subscribe outro card
OUTRO_SEC = 7.0  # held after narration; art keeps CENTER + TOP-RIGHT clear for YouTube's end screen
MIN_DUR = 0.40  # floor so a tiny segment doesn't flash by
SYNC_OFFSET_SEC = 0.25  # shift every image LATER by this much (FORMATS.md global)
MUSIC_DB = -15.0  # base level of the score (well under the VO); sidechain ducks it further while Jack talks
# Gentle macro-leveling so softer/punchier lines sit at a steadier volume (level only, no timing change).
# Long window + modest max-gain = even out slow drift across the read without audible pumping.
VO_LEVEL = "dynaudnorm=f=300:g=21:m=3.0:p=0.90"


def db_to_lin(db: float) -> float:
    return 10 ** (db / 20.0)


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
    ap.add_argument("--no-outro", action="store_true", help="skip the silent like/subscribe end card")
    ap.add_argument("--music", default=None,
                    help="optional score (e.g. music/full_score.mp3), ducked under the VO")
    ap.add_argument("--raw-vo", action="store_true",
                    help="skip the gentle VO leveling (use the locked narration dynamics as-is)")
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

    # Frame-exact timing: snap every cut to an output-frame boundary so durations are exact
    # multiples of 1/fps. This kills the cumulative late-drift that otherwise creeps in when a
    # looped still image is read at the demuxer default rate and rounded per input (cuts ran
    # ~1s late by the back half before this). Each image holds to the NEXT image's snapped start.
    fps = args.fps
    bounds = [round((starts[i + 1] if i + 1 < n else audio_len) * fps) for i in range(n)]
    items = []
    prev = 0  # first image is pinned to frame 0
    for i, seg in enumerate(segments):
        dur_frames = max(round(MIN_DUR * fps), bounds[i] - prev)
        items.append((find_image(images_dir, seg["index"]), dur_frames / fps))
        prev = prev + dur_frames

    # Silent like/subscribe outro card, held OUTRO_SEC past the narration. The card art keeps the
    # CENTER + TOP-RIGHT clear for YouTube's end-screen subscribe button + recommended-video card.
    use_outro = OUTRO.exists() and not args.no_outro
    if use_outro:
        items.append((OUTRO, round(OUTRO_SEC * fps) / fps))
    total = sum(dur for _, dur in items)

    # Video via the concat FILTER (the concat demuxer silently drops still-image durations).
    scale_body = (f"scale=1920:1080:force_original_aspect_ratio=decrease,"
                  f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,setsar=1,fps={args.fps},format=yuv420p")
    vin, vparts = [], []
    for k, (img, dur) in enumerate(items):
        vin += ["-framerate", str(args.fps), "-loop", "1", "-t", f"{dur:.5f}", "-i", str(img)]
        vparts.append(f"[{k}:v]{scale_body}[v{k}]")
    vparts.append("".join(f"[v{k}]" for k in range(len(items))) + f"concat=n={len(items)}:v=1[v]")
    aidx = len(items)

    music_path = Path(args.music) if args.music else None
    if music_path and not music_path.exists():
        sys.exit(f"Missing music: {music_path}")

    vo_pre = "" if args.raw_vo else f",{VO_LEVEL}"
    extra_inputs = []
    if music_path:
        # VO (leveled) at full level + a sidechain copy; the score is ducked under the VO
        # (sidechaincompress) so it dips while Jack talks and breathes in the gaps, then fades out.
        midx = aidx + 1
        mlin = db_to_lin(MUSIC_DB)
        fade_st = max(0.0, audio_len - 3.0)
        vparts.append(
            f"[{aidx}:a]aresample=44100{vo_pre},apad,atrim=0:{total:.3f},asetpts=N/SR/TB,asplit=2[vo][vosc];"
            f"[{midx}:a]aresample=44100,apad,atrim=0:{total:.3f},asetpts=N/SR/TB,volume={mlin:.4f},"
            f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_st:.3f}:d=3.0[musv];"
            f"[musv][vosc]sidechaincompress=threshold=0.06:ratio=8:attack=20:release=350[duck];"
            f"[vo][duck]amix=inputs=2:normalize=0:duration=first:dropout_transition=0[a]"
        )
        extra_inputs = ["-i", str(music_path)]
    else:
        vparts.append(f"[{aidx}:a]aresample=44100{vo_pre},apad,atrim=0:{total:.3f},asetpts=N/SR/TB[a]")

    cmd = [
        "ffmpeg", "-y", *vin, "-i", str(audio_path), *extra_inputs,
        "-filter_complex", ";".join(vparts),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-r", str(args.fps), "-t", f"{total:.3f}",
        "-movflags", "+faststart", str(out_path),
    ]

    print(f"Assembling {n} frames + narration ({audio_len:.1f}s)"
          f"{' + score' if music_path else ''} + outro card -> {out_path}")
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
