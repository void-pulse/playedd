#!/usr/bin/env python3
"""
generate_music_bed.py
One cohesive ~180s instrumental bed for an episode draft (looped + ducked by the
assembler). Reuses generate_music's SHARED_PREFIX so it matches the channel sound.
Skips if the bed already exists. Atomic temp -> rename.

Usage:
    python pipeline/generate_music_bed.py episodes/0004_why-everything-you-own-is-designed-to-die
"""
import importlib.util, os, sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
spec = importlib.util.spec_from_file_location("gm", ROOT / "pipeline" / "generate_music.py")
gm = importlib.util.module_from_spec(spec); spec.loader.exec_module(gm)

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: generate_music_bed.py episodes/<ep>")
    ep = Path(sys.argv[1])
    out = ep / "music" / "draft_bed.mp3"
    if out.exists() and out.stat().st_size > 0:
        print(f"bed exists -> {out} (skip)"); return
    out.parent.mkdir(parents=True, exist_ok=True)
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    prompt = gm.SHARED_PREFIX + "wry and investigative, a steady quiet ticking pulse with a knowing undertow, loopable"
    print(f"composing ~180s bed -> {out.name} ...")
    audio = client.music.compose(prompt=prompt, music_length_ms=180000, model_id="music_v1", force_instrumental=True)
    tmp = out.with_suffix(".mp3.tmp")
    with open(tmp, "wb") as f:
        for ch in audio:
            if ch:
                f.write(ch)
    tmp.replace(out)
    print(f"bed -> {out}  ({gm.ffdur(out):.1f}s)")

if __name__ == "__main__":
    main()
