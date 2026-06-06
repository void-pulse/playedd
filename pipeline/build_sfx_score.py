#!/usr/bin/env python3
"""
build_sfx_score.py
Assemble a single dense, level-consistent SFX stem (full_sfx.mp3) for an episode.

Layers (bottom to top):
  - Zoned ambient beds: looped, crossfaded between zones, audible floor with some
    bed running the ENTIRE episode (no dead air).
  - Floor sweeteners: light distant-casino one-shots scattered at randomized
    intervals through the casino-floor zones, reduced gain (below the marked hits).
  - Marked cues (sfx/cues.json): the prominent accents, on top.

Every one-shot (sweetener + marked) is PEAK-NORMALIZED to a uniform level first,
so a card_beep and a crowd_cheer land at the same perceived loudness. A final
limiter lets the whole stem ride under the voice with one fader.

Output length = the episode's music/full_score.mp3.

Usage:
    python pipeline/build_sfx_score.py episodes/0003_casino-why-you-lose
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "assets" / "sfx"

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

PEAK_TARGET_DBFS = -3.0   # peak-normalize every one-shot to this
MARKED_GAIN = 0.75        # prominent accents
SWEET_GAIN = 0.35         # floor sweeteners (below marked, above beds)
SWEET_JACKPOT_GAIN = 0.25 # the "distant" jackpot a touch lower
XF = 2.5
SR = 44100
SEED = 3                  # deterministic sweetener scatter

SWEET_POOL = ["coin_drop.mp3", "chip_clink.mp3", "cha_ching.mp3",
              "slot_reel_spin.mp3", "slot_jackpot.mp3"]


def ffdur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


_peak_cache: dict[str, float] = {}


def peak_gain(fname: str) -> float:
    """Linear gain to bring this file's peak to PEAK_TARGET_DBFS (cached)."""
    if fname in _peak_cache:
        return _peak_cache[fname]
    r = subprocess.run(["ffmpeg", "-i", str(KIT / fname), "-af", "volumedetect",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"max_volume:\s*(-?\d+\.?\d*)\s*dB", r.stderr)
    max_db = float(m.group(1)) if m else 0.0
    gain = 10 ** ((PEAK_TARGET_DBFS - max_db) / 20.0)
    _peak_cache[fname] = gain
    return gain


def beat_starts(segs: list) -> dict:
    starts = {}
    for beat, phrase in BEAT_FIRST.items():
        hit = next((s for s in segs if phrase.lower() in s["text"].lower()), None)
        if not hit:
            sys.exit(f"Beat first-line not found: {beat} -> '{phrase}'")
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
    end = target

    # --- beds: NONE. Ambiance killed entirely; the stem is all SFX one-shots.
    # (The machine-zone drone still appears as a placed one-shot via cues.json,
    # but there is no continuous ambient bed anywhere.) ---
    beds = []

    # --- dense casino sweeteners: one-shots scattered through SETUP..THE SENSES at
    # short randomized gaps, so there's frequent SFX activity over the pictures. ---
    random.seed(SEED)
    z0, z1 = b["setup"], b["human_layer"]
    sweeteners = []
    t = z0 + random.uniform(2.0, 6.0)
    while t < z1 - 2.0:
        snd = random.choice(SWEET_POOL)
        sweeteners.append((snd, round(t, 3)))
        t += random.uniform(8.0, 14.0)   # dense: frequent casino activity

    # --- marked cues (prominent accents) ---
    cues = json.loads((ep / "sfx" / "cues.json").read_text())
    marked = [(c["kit_sound"], float(c["start_sec"])) for c in cues]

    # --- build ffmpeg graph ---
    inputs, chains, labels = [], [], []
    idx = 0

    def add_input(src: Path):
        inputs.extend(["-i", str(src)])

    for fname, start, stop, gain in beds:
        if not (KIT / fname).exists():
            sys.exit(f"Missing bed: {fname}")
        zlen = max(XF * 2, round(stop - start, 3))
        ms = int(round(max(0.0, start) * 1000))
        add_input(KIT / fname)
        chains.append(
            f"[{idx}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"aloop=loop=-1:size=2147483647,atrim=0:{zlen},asetpts=N/SR/TB,"
            f"afade=t=in:st=0:d={XF},afade=t=out:st={round(zlen-XF,3)}:d={XF},"
            f"volume={gain},adelay={ms}|{ms}[b{idx}]")
        labels.append(f"[b{idx}]")
        idx += 1

    def add_oneshot(fname: str, t: float, place_gain: float):
        nonlocal idx
        if not (KIT / fname).exists():
            sys.exit(f"Missing one-shot: {fname}")
        g = round(peak_gain(fname) * place_gain, 4)
        ms = int(round(max(0.0, t) * 1000))
        add_input(KIT / fname)
        chains.append(
            f"[{idx}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"volume={g},adelay={ms}|{ms}[x{idx}]")
        labels.append(f"[x{idx}]")
        idx += 1

    for fname, t in sweeteners:
        gain = SWEET_JACKPOT_GAIN if fname == "slot_jackpot.mp3" else SWEET_GAIN
        add_oneshot(fname, t, gain)
    for fname, t in marked:
        add_oneshot(fname, t, MARKED_GAIN)

    n = len(labels)
    fc = ";".join(chains) + ";" + "".join(labels) + \
        f"amix=inputs={n}:normalize=0:dropout_transition=0,alimiter=limit=0.95,aresample={SR},apad[mix]"

    out = ep / "sfx" / "full_sfx.mp3"
    tmp = out.with_suffix(".mp3.tmp")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[mix]",
           "-t", f"{target:.3f}", "-c:a", "libmp3lame", "-b:a", "192k", "-f", "mp3", str(tmp)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"ffmpeg failed:\n{result.stderr[-1800:]}")
    os.replace(tmp, out)

    def lbl(s): return f"{int(s // 60)}:{int(s % 60):02d}"
    print(f"Beds: {len(beds)} (ambiance killed — all SFX)")
    print(f"Casino sweeteners scattered: {len(sweeteners)} "
          f"(SETUP..THE SENSES, ~8-14s apart, gain {SWEET_GAIN}/{SWEET_JACKPOT_GAIN} jackpot)")
    print(f"Marked cues (peak-normalized, gain {MARKED_GAIN}): {len(marked)}")
    print(f"full_sfx.mp3 -> {out}  ({ffdur(out):.1f}s, target {target:.1f}s)")


if __name__ == "__main__":
    main()
