#!/usr/bin/env python3
"""
generate_sfx.py
Generate the channel's reusable SFX kit via the ElevenLabs Sound Effects API.

Auto-length is OFF: each effect uses a fixed duration_seconds so the kit is
predictable. casino_ambience loops. Files land in assets/sfx/<name>.mp3 (repo
root, reused across episodes). Atomic writes (temp -> rename): a mid-run quota
failure can never truncate a completed effect.

Usage:
    python pipeline/generate_sfx.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
SFX_DIR = ROOT / "assets" / "sfx"

# name -> (prompt, duration_seconds, loop)
SFX = [
    ("slot_jackpot.mp3", "retro slot machine jackpot win, celebratory bells and cascading coins", 3.0, False),
    ("coin_drop.mp3", "single coin dropping on a felt table", 1.0, False),
    ("casino_ambience.mp3", "casino floor ambience, distant slot chimes and low crowd murmur", 10.0, True),
    ("record_scratch.mp3", "sharp comedic record scratch, abrupt stop", 1.0, False),
    ("bass_thud.mp3", "deep ominous bass thud, single impact", 2.0, False),
    ("whoosh.mp3", "soft UI whoosh transition", 1.0, False),
    ("card_riffle.mp3", "playing card shuffle riffle", 2.0, False),
    ("cha_ching.mp3", "cash register cha-ching", 1.0, False),
]


def credit_count(client):
    try:
        sub = client.user.subscription.get()
        return getattr(sub, "character_count", None)
    except Exception:
        return None


def main():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")

    SFX_DIR.mkdir(parents=True, exist_ok=True)

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)

    start_credits = credit_count(client)
    done = 0
    for name, prompt, duration, loop in SFX:
        out_path = SFX_DIR / name
        print(f"[{done + 1:02d}/{len(SFX)}] {name}: {duration:.0f}s loop={loop} ...")
        audio = client.text_to_sound_effects.convert(
            text=prompt,
            duration_seconds=duration,   # explicit -> auto-length OFF
            loop=loop,
            prompt_influence=0.3,
        )
        tmp = out_path.with_suffix(".mp3.tmp")
        try:
            with open(tmp, "wb") as f:
                for chunk in audio:      # request happens here; may raise (e.g. quota)
                    if chunk:
                        f.write(chunk)
            os.replace(tmp, out_path)
        except BaseException:
            tmp.unlink(missing_ok=True)  # never leave a partial effect
            raise
        done += 1

    end_credits = credit_count(client)
    used = (end_credits - start_credits) if (start_credits is not None and end_credits is not None) else None
    print(f"\nDone. {done}/{len(SFX)} effects -> {SFX_DIR}")
    if used is not None:
        print(f"Credits used (character_count delta): {used}")
    else:
        print("Credits used: unavailable (subscription endpoint did not report a count)")


if __name__ == "__main__":
    main()
