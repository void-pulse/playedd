#!/usr/bin/env python3
"""
build_sfx_score.py
Assemble a single continuous SFX stem (full_sfx.mp3) for an episode:
zoned ambient beds (looped, low, crossfaded between zones) with every one-shot
cue from sfx/cues.json overlaid ON TOP at its exact timestamp, at full punch.

Beds ride ~20-26 dB under the hits, so the whole stem can be dropped under the
voice with one fader. Output length = the episode's music/full_score.mp3.

Beat zone boundaries are derived by finding each [LABEL] beat's first line in
03_segments.json (see BEAT_FIRST).

Usage:
    python pipeline/build_sfx_score.py episodes/0003_casino-why-you-lose
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "assets" / "sfx"

# Each beat's first spoken line (a substring unique enough to find in 03_segments.json).
BEAT_FIRST = {
    "cold_open": "Can you actually beat the casino",
    "setup": "First, the part you already know",
    "the_turn": "The slickest trick on the floor",
    "the_science": "None of this is accident",
    "the_tracking": "Now it gets personal",
    "the_building": "The games are rigged in your",
    "the_senses": "Quick myth check",
    "human_layer": "And here's the answer to the",
    "payoff": "So that's why you keep going",
    "button": "if you're feeling smug because",
}

HIT = 0.85          # one-shot gain (full punch)
XF = 2.5            # crossfade / fade length between zones
SR = 44100


def ffdur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def beat_starts(segs: list) -> dict:
    starts = {}
    for beat, phrase in BEAT_FIRST.items():
        hit = next((s for s in segs if phrase.lower() in s["text"].lower()), None)
        if not hit:
            sys.exit(f"Beat first-line not found in segments: {beat} -> '{phrase}'")
        starts[beat] = float(hit["seconds"])
    return starts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    args = ap.parse_args()
    ep = Path(args.episode)

    full_score = ep / "music" / "full_score.mp3"
    if not full_score.exists():
        sys.exit(f"Need {full_score} to set the target length.")
    target = ffdur(full_score)

    segs = json.loads((ep / "03_segments.json").read_text())
    b = beat_starts(segs)
    end = target  # last boundary

    # --- zoned ambient beds: (file, start, stop, gain) ---
    beds = [
        ("tension_bed.mp3",         0.0,                b["setup"],        0.035),  # cold open: light swell
        ("casino_floor_walla.mp3",  b["setup"],         b["the_building"], 0.060),  # SETUP..THE TRACKING
        ("slot_machine_chorus.mp3", b["the_turn"],      b["the_tracking"], 0.050),  # under TURN+SCIENCE
        ("casino_lounge.mp3",       b["the_building"] - XF, b["human_layer"], 0.060),  # crossfade from walla
        ("machine_zone_drone.mp3",  b["human_layer"],   b["payoff"],       0.045),  # HUMAN LAYER (very low)
        ("tension_bed.mp3",         b["human_layer"],   b["payoff"],       0.040),  # HUMAN LAYER (very low)
        ("tension_bed.mp3",         b["button"],        end,               0.035),  # button: light swell
    ]
    # --- one-shots from cues.json (full punch, exact timestamps) ---
    cues = json.loads((ep / "sfx" / "cues.json").read_text())
    shots = [(c["kit_sound"], float(c["start_sec"])) for c in cues]

    # --- build ffmpeg graph ---
    inputs, chains, labels = [], [], []
    idx = 0
    for fname, start, stop, gain in beds:
        src = KIT / fname
        if not src.exists():
            sys.exit(f"Missing bed: {src}")
        zlen = max(XF * 2, round(stop - start, 3))
        ms = int(round(max(0.0, start) * 1000))
        inputs += ["-i", str(src)]
        chains.append(
            f"[{idx}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"aloop=loop=-1:size=2147483647,atrim=0:{zlen},asetpts=N/SR/TB,"
            f"afade=t=in:st=0:d={XF},afade=t=out:st={round(zlen-XF,3)}:d={XF},"
            f"volume={gain},adelay={ms}|{ms}[b{idx}]")
        labels.append(f"[b{idx}]")
        idx += 1
    for fname, t in shots:
        src = KIT / fname
        if not src.exists():
            sys.exit(f"Missing one-shot kit sound: {src}")
        ms = int(round(max(0.0, t) * 1000))
        inputs += ["-i", str(src)]
        chains.append(
            f"[{idx}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"volume={HIT},adelay={ms}|{ms}[s{idx}]")
        labels.append(f"[s{idx}]")
        idx += 1

    n = len(labels)
    fc = ";".join(chains) + ";" + "".join(labels) + \
        f"amix=inputs={n}:normalize=0:dropout_transition=0,alimiter=limit=0.95,aresample={SR},apad[mix]"

    out = ep / "sfx" / "full_sfx.mp3"
    tmp = out.with_suffix(".mp3.tmp")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc,
           "-map", "[mix]", "-t", f"{target:.3f}",
           "-c:a", "libmp3lame", "-b:a", "192k", "-f", "mp3", str(tmp)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"ffmpeg failed:\n{result.stderr[-1800:]}")
    os.replace(tmp, out)

    # --- report ---
    def lbl(sec):
        return f"{int(sec // 60)}:{int(sec % 60):02d}"
    print("Zone map (beat starts derived from 03_segments.json):")
    for beat in BEAT_FIRST:
        print(f"  {beat:<12} starts {lbl(b[beat])}")
    print("\nBed zones:")
    for fname, start, stop, gain in beds:
        print(f"  {fname:<24} {lbl(max(0,start))}-{lbl(stop)}  gain={gain}")
    print(f"\nOne-shots overlaid: {len(shots)} cues at full punch ({HIT})")
    print(f"full_sfx.mp3 -> {out}  ({ffdur(out):.1f}s, target {target:.1f}s)")


if __name__ == "__main__":
    main()
