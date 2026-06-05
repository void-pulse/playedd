#!/usr/bin/env python3
"""
generate_music.py
Per-beat instrumental score via the ElevenLabs Music API.

One cohesive cue per [LABEL] beat: beat timings come from the rendered audio
chunks in episodes/<ep>/chunks/ (their durations + cumulative starts). Each cue
runs ~beat duration + 2s (a crossfade tail for assemble.py). A shared prompt
prefix keeps the 10 cues sonically cohesive; only the mood line changes.

Atomic writes (temp -> rename): a mid-run quota failure can never truncate a
completed cue, and music/cues.json records every cue finished so far.

Usage:
    python pipeline/generate_music.py episodes/0003_casino-why-you-lose
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SHARED_PREFIX = (
    "Instrumental background score for a wry investigative explainer video. "
    "Minimal electronic palette, sparse muted synth and soft low bass, around 90 BPM, "
    "low energy, sits underneath a voiceover, loopable, no vocals, no dramatic swells. Mood: "
)

MOODS = {
    "cold_open": "curious and slightly tense, a question hanging in the air",
    "setup": "steady and methodical, a quiet ticking pulse, matter-of-fact",
    "the_turn": "something dawning, slightly off-kilter, the floor tilting",
    "the_science": "clinical and mechanical, precise, cold lab curiosity",
    "the_tracking": "cold and watchful, quietly menacing, surveillance unease",
    "the_building": "starts low and claustrophobic, opens into spacious and grand",
    "the_senses": "hazy and seductive, slightly woozy, perfumed with an undertow",
    "human_layer": "melancholy and hollow, the world going quiet, weightless",
    "payoff": "resolving with a sad clarity, the truth settling",
    "button": "wry and knowing, a small final sting",
}

TAIL_MS = 2000           # crossfade tail added to each cue
MIN_MS, MAX_MS = 10_000, 300_000   # ElevenLabs Music length bounds


def ffdur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def credit_count(client):
    """Best-effort current credit usage (character_count) for delta reporting."""
    try:
        sub = client.user.subscription.get()
        return getattr(sub, "character_count", None)
    except Exception:
        return None


def write_manifest(music_dir: Path, cues: list) -> Path:
    out = music_dir / "cues.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cues, indent=2), encoding="utf-8")
    os.replace(tmp, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", help="episode folder, e.g. episodes/0003_casino-why-you-lose")
    ap.add_argument("--model", default="music_v1")
    args = ap.parse_args()

    ep = Path(args.episode)
    chunks_dir = ep / "chunks"
    chunk_files = sorted(chunks_dir.glob("*.mp3"))
    if not chunk_files:
        sys.exit(f"No audio chunks in {chunks_dir}. Run generate_audio.py first.")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")

    music_dir = ep / "music"
    music_dir.mkdir(exist_ok=True)

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)

    start_credits = credit_count(client)
    cues = []
    cumulative = 0.0
    for i, cf in enumerate(chunk_files):
        m = re.match(r"(\d+)_(.+)\.mp3$", cf.name)
        if not m:
            sys.exit(f"Unexpected chunk name: {cf.name}")
        beat = m.group(2)
        if beat not in MOODS:
            sys.exit(f"No mood defined for beat '{beat}'. Add it to MOODS.")
        dur = ffdur(cf)
        length_ms = max(MIN_MS, min(MAX_MS, round(dur * 1000) + TAIL_MS))
        prompt = SHARED_PREFIX + MOODS[beat]
        out_path = music_dir / f"{i + 1:02d}_{beat}.mp3"
        print(f"[{i + 1:02d}/{len(chunk_files)}] {beat}: beat={dur:.1f}s "
              f"cue_len={length_ms / 1000:.1f}s -> {out_path.name} ...")

        audio = client.music.compose(
            prompt=prompt,
            music_length_ms=length_ms,
            model_id=args.model,
            force_instrumental=True,
        )
        tmp = out_path.with_suffix(".mp3.tmp")
        try:
            with open(tmp, "wb") as f:
                for chunk in audio:   # request happens here; may raise (e.g. quota)
                    if chunk:
                        f.write(chunk)
            os.replace(tmp, out_path)
        except BaseException:
            tmp.unlink(missing_ok=True)        # never leave a partial cue
            write_manifest(music_dir, cues)    # persist what completed
            raise

        cues.append({
            "n": i + 1, "beat": beat,
            "start_sec": round(cumulative, 3),
            "duration_sec": round(dur, 3),
            "file": out_path.name,
            "prompt": prompt,
        })
        write_manifest(music_dir, cues)        # incremental: survives a later failure
        cumulative += dur

    manifest = write_manifest(music_dir, cues)
    end_credits = credit_count(client)
    used = (end_credits - start_credits) if (start_credits is not None and end_credits is not None) else None
    print(f"\nDone. {len(cues)} cues -> {music_dir}")
    print(f"Manifest -> {manifest}")
    if used is not None:
        print(f"Credits used (character_count delta): {used}")
    else:
        print("Credits used: unavailable (subscription endpoint did not report a count)")


if __name__ == "__main__":
    main()
