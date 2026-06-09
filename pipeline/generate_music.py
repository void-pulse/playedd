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
    "Instrumental upbeat, curious explainer score for a wondrous video about time, memory, and "
    "noticing the world. Bright, warm, and gently propulsive: light pizzicato and plucked strings, "
    "soft rounded synth arpeggios, warm piano, a light steady rhythmic pulse with soft mallets, "
    "major key, optimistic and inquisitive, around 100 BPM, moderate energy with a gentle forward "
    "momentum, sits comfortably beneath a calm voiceover, no vocals, no heavy or aggressive drums, "
    "no harsh synths, no big EDM drops. Playful, bright, and modern like a feel-good explainer "
    "score. Mood: "
)

# One cue per ep5 beat. The arc honors the head-fake (reveal_1 is the tempting-but-weak idea,
# reveal_2 is the real warm discovery) and the no-mortality rule (human_layer is reassurance).
MOODS = {
    "cold_open": "wistful and nostalgic, a warm endless-summer memory, a soft question in the air",
    "setup": "gently curious, the quiet feeling of noticing something odd, light and inquisitive",
    "the_turn": "something quietly dawning, a hopeful lift as the mystery opens up",
    "reveal_1": "light and tentative, a plausible idea offered then gently doubted, a small question mark",
    "reveal_2": "warm discovery, the real insight arriving, strings opening with quiet wonder",
    "reveal_3": "tender and nostalgic, the glow of first times, intimate and warm",
    "reveal_4": "curious and speculative, an intriguing maybe, weightless and open-ended",
    "human_layer": "reassuring and grounding, warm and intimate, a steadying calm",
    "payoff": "hopeful and expansive, gently uplifting, a sense of possibility opening wide",
    "button": "warm and resolved, a soft closing wonder, settling with a gentle smile",
}

TAIL_MS = 2000           # crossfade tail added to each cue
MIN_MS, MAX_MS = 10_000, 300_000   # ElevenLabs Music length bounds
CROSSFADE_S = 1.5        # acrossfade overlap at each cue boundary (tail covers it)


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


def build_acrossfade_filter(n: int, crossfade_s: float) -> str:
    """filter_complex chaining n audio inputs with acrossfade, then apad on the tail.
    apad lets a later `-t <target>` both trim (if longer) and pad-with-silence (if
    shorter) to an exact duration. Final output label is [out]."""
    if n < 1:
        raise ValueError("need at least one input")
    if n == 1:
        return "[0:a]apad[out]"
    parts = []
    prev = "[0:a]"
    for i in range(1, n):
        if i == n - 1:
            parts.append(f"{prev}[{i}:a]acrossfade=d={crossfade_s},apad[out]")
        else:
            parts.append(f"{prev}[{i}:a]acrossfade=d={crossfade_s}[a{i}]")
            prev = f"[a{i}]"
    return ";".join(parts)


def stitch_full_score(music_dir: Path, narration_mp3: Path, cues: list) -> Path:
    """Crossfade the cue files (script order) into full_score.mp3, trimmed/padded to
    EXACTLY narration_mp3's duration. Atomic temp -> rename."""
    cue_files = [music_dir / c["file"] for c in cues]
    missing = [f.name for f in cue_files if not (f.exists() and f.stat().st_size > 0)]
    if missing:
        sys.exit("Cannot stitch full score — missing/empty cues: " + ", ".join(missing))
    if not narration_mp3.exists():
        sys.exit(f"Need {narration_mp3} to align the full score to the narration length.")

    target = ffdur(narration_mp3)
    out = music_dir / "full_score.mp3"
    tmp = out.with_suffix(".mp3.tmp")

    cmd = ["ffmpeg", "-y"]
    for f in cue_files:
        cmd += ["-i", str(f)]
    cmd += [
        "-filter_complex", build_acrossfade_filter(len(cue_files), CROSSFADE_S),
        "-map", "[out]",
        "-t", f"{target:.3f}",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-f", "mp3",          # .tmp extension hides the muxer; specify it
        str(tmp),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"ffmpeg full-score stitch failed:\n{result.stderr[-1500:]}")
    os.replace(tmp, out)
    print(f"Full score -> {out}  (aligned to narration: {target:.1f}s, "
          f"{CROSSFADE_S}s crossfades)")
    return out


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
    ap.add_argument("--stitch", action="store_true",
                    help="stitch already-generated cues into full_score.mp3 (no API calls)")
    args = ap.parse_args()

    ep = Path(args.episode)
    music_dir = ep / "music"
    narration_mp3 = ep / "audio" / "narration.mp3"

    # --stitch: no generation, no API. Stitch existing cues per music/cues.json.
    if args.stitch:
        manifest_path = music_dir / "cues.json"
        if not manifest_path.exists():
            sys.exit(f"No {manifest_path}. Generate the cues first.")
        cues = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not cues:
            sys.exit(f"{manifest_path} is empty. Generate the cues first.")
        stitch_full_score(music_dir, narration_mp3, cues)
        return

    chunks_dir = ep / "chunks"
    chunk_files = sorted(chunks_dir.glob("*.mp3"))
    if not chunk_files:
        sys.exit(f"No audio chunks in {chunks_dir}. Run generate_audio.py first.")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")

    music_dir.mkdir(exist_ok=True)

    # Per-episode mood overrides: <ep>/music_moods.json (beat -> mood line) wins over the
    # built-in MOODS, so each episode's beat structure scores correctly without editing this
    # shared file. Falls back to MOODS for any beat the episode file doesn't define.
    moods = dict(MOODS)
    moods_file = ep / "music_moods.json"
    if moods_file.exists():
        moods.update(json.loads(moods_file.read_text(encoding="utf-8")))
        print(f"Loaded per-episode moods: {moods_file}")

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
        if beat not in moods:
            sys.exit(f"No mood defined for beat '{beat}'. Add it to MOODS or {moods_file.name}.")
        dur = ffdur(cf)
        length_ms = max(MIN_MS, min(MAX_MS, round(dur * 1000) + TAIL_MS))
        prompt = SHARED_PREFIX + moods[beat]
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

    # Auto-stitch the cohesive full score (free, no API). Re-runnable via --stitch.
    if narration_mp3.exists():
        stitch_full_score(music_dir, narration_mp3, cues)
    else:
        print(f"{narration_mp3} not found; skipping full_score stitch. "
              f"Run with --stitch once narration.mp3 exists.")


if __name__ == "__main__":
    main()
