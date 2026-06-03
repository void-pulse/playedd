#!/usr/bin/env python3
"""
generate_audio.py
Turn a script into narration audio via ElevenLabs, with channel-tuned settings.

Usage:
    python pipeline/generate_audio.py episodes/<ep>/01_script.md --voice NARRATOR_A
    # writes episodes/<ep>/audio/narration.mp3

Flags:
    --voice NARRATOR_A|NARRATOR_B   which voice from VOICE_IDS below (default NARRATOR_A)
    --voice-id <raw id>             use a raw ElevenLabs voice id directly
    --model eleven_multilingual_v2  (default) or eleven_v3
    --with-timestamps               also save audio/alignment.json (character-level
                                    timing). Lets you skip TurboScribe entirely later.

Setup:
    pip install -r requirements.txt
    Set ELEVENLABS_API_KEY in .env
    Fill in your chosen voice IDs in VOICE_IDS below (see brand/VOICE.md).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Fill these in after you audition voices (brand/VOICE.md). Raw ElevenLabs voice IDs.
VOICE_IDS = {
    "NARRATOR_A": "",  # e.g. Declassified / Cover Story narrator
    "NARRATOR_B": "",  # e.g. They Built It First / Wait That's Real narrator
}

# Channel-tuned, natural-narration settings (see brand/VOICE.md).
VOICE_SETTINGS = {
    "stability": 0.40,
    "similarity_boost": 0.80,
    "style": 0.15,
    "use_speaker_boost": True,
}


def load_script(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # Drop a trailing SOURCES section so it doesn't get narrated.
    text = re.split(r"\n#+\s*SOURCES", text, flags=re.I)[0]
    # Strip markdown headings/inline tags that shouldn't be spoken.
    text = re.sub(r"^\s*#.*$", "", text, flags=re.M)        # headings
    text = re.sub(r"\[HUMAN LAYER\]", "", text)              # inline marker
    text = re.sub(r"\*\*|\*|`", "", text)                    # md emphasis
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="path to 01_script.md")
    ap.add_argument("--voice", default="NARRATOR_A", choices=list(VOICE_IDS.keys()))
    ap.add_argument("--voice-id", default=None, help="raw voice id, overrides --voice")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--with-timestamps", action="store_true")
    args = ap.parse_args()

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")

    voice_id = args.voice_id or VOICE_IDS.get(args.voice)
    if not voice_id:
        sys.exit(f"No voice id for {args.voice}. Fill it into VOICE_IDS in this file "
                 f"(or pass --voice-id). See brand/VOICE.md.")

    script_path = Path(args.script)
    text = load_script(script_path)
    if not text:
        sys.exit("Script is empty after cleaning. Check 01_script.md.")

    out_dir = script_path.parent / "audio"
    out_dir.mkdir(exist_ok=True)
    out_mp3 = out_dir / "narration.mp3"

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)

    print(f"Generating narration with voice={args.voice} ({voice_id}), model={args.model} ...")

    if args.with_timestamps:
        # Character-level alignment, lets you build the timeline without TurboScribe.
        resp = client.text_to_speech.convert_with_timestamps(
            voice_id=voice_id,
            model_id=args.model,
            text=text,
            voice_settings=VOICE_SETTINGS,
        )
        import base64
        audio_b64 = resp.audio_base_64 if hasattr(resp, "audio_base_64") else resp["audio_base64"]
        out_mp3.write_bytes(base64.b64decode(audio_b64))
        align = getattr(resp, "alignment", None) or resp.get("alignment")
        (out_dir / "alignment.json").write_text(
            json.dumps(align, default=lambda o: o.__dict__, indent=2), encoding="utf-8"
        )
        print(f"Saved {out_mp3} and audio/alignment.json")
    else:
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=args.model,
            text=text,
            voice_settings=VOICE_SETTINGS,
        )
        with open(out_mp3, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        print(f"Saved {out_mp3}")
        print("Next: upload narration.mp3 to TurboScribe, export SRT, then run parse_timestamps.py")


if __name__ == "__main__":
    main()
