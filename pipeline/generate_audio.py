#!/usr/bin/env python3
"""
generate_audio.py
Turn a script into narration audio via ElevenLabs, with channel-tuned settings.

Per-section chunked generation: each [LABEL] section is synthesized to its own
file under episodes/<ep>/chunks/, then ffmpeg-concatenated into narration.mp3.
This makes single-beat fixes cheap (regenerate one chunk, re-stitch) and makes a
quota'd or glitched run non-destructive (atomic temp-then-rename writes never
truncate an existing good narration.mp3 or chunk).

Usage:
    python pipeline/generate_audio.py episodes/<ep>/01_script.md --voice NARRATOR_D
    # writes episodes/<ep>/chunks/NN_<slug>.mp3 + episodes/<ep>/audio/narration.mp3

Flags:
    --voice NARRATOR_A|...           which voice from VOICE_IDS below (default NARRATOR_A)
    --voice-id <raw id>              raw ElevenLabs voice id, overrides --voice
    --model eleven_multilingual_v2   (default)
    --section "THE BUILDING"         regenerate ONLY that section (case-insensitive
                                     label match), then re-stitch. Other chunks must exist.
    --dry-run                        parse + report sections/chars/breaks/seam context.
                                     Makes ZERO API calls.

Setup:
    pip install -r requirements.txt    (needs ffmpeg + ffprobe on PATH)
    Set ELEVENLABS_API_KEY in .env
    Fill in your chosen voice IDs in VOICE_IDS below (see brand/VOICE.md).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Fill these in after you audition voices (brand/VOICE.md). Raw ElevenLabs voice IDs.
VOICE_IDS = {
    "NARRATOR_A": "2fe8mwpfJcqvj9RGBsC1",  # Keanan - Natural, Teacher
    "NARRATOR_B": "RCvfNaeRVixdBMcmd2Wl",  # Jason Jordan
    "NARRATOR_C": "raMcNf2S8wCmuaBcyI6E",  # Tyler Kurk - Smooth, Pleasant and Clear
    "NARRATOR_D": "q0IMILNRPxOgtBTS4taI",  # Drew
}

# Channel-tuned, natural-narration settings (see brand/VOICE.md).
VOICE_SETTINGS = {
    "stability": 0.40,
    "similarity_boost": 0.80,
    "style": 0.15,
    "use_speaker_boost": True,
}

SOURCES_SPLIT = re.compile(
    r"^[ \t]*(?:#+[ \t]*SOURCES\b|-*[ \t]*SOURCES[ \t]*-*)[ \t]*$",
    flags=re.I | re.M,
)
LABEL_LINE = re.compile(r"^[ \t]*\[([^\]]+)\][ \t]*$", flags=re.M)
BREAK_TAG = re.compile(r"<break[^>]*>")


def slugify(label: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", label.lower())).strip("_")


def _strip_noise(text: str) -> str:
    """Remove SOURCES heading lines, markdown headings, stray inline [tags] and emphasis."""
    text = re.sub(r"^\s*#.*$", "", text, flags=re.M)     # markdown headings
    text = re.sub(r"\[[^\]]*\]", "", text)               # any inline bracketed tag
    text = re.sub(r"\*\*|\*|`", "", text)                # md emphasis
    return text


def section_tts(body: str) -> str:
    """Spoken text for a section: noise stripped, <break> tags PRESERVED."""
    text = _strip_noise(body)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def to_plain(tts_text: str) -> str:
    """Human/seam-context prose: <break> tags removed, gaps collapsed."""
    text = BREAK_TAG.sub("", tts_text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text).strip()
    return text


def parse_sections(path: Path) -> list[dict]:
    """Split a script into [LABEL] sections. Returns ordered list of
    {index, label, slug, tts} with the SOURCES block dropped and labels removed."""
    text = path.read_text(encoding="utf-8")
    text = SOURCES_SPLIT.split(text, maxsplit=1)[0]
    text = re.sub(r"\n[ \t]*-{3,}[ \t]*$", "", text.rstrip())

    matches = list(LABEL_LINE.finditer(text))
    if not matches:
        return []
    sections = []
    for i, m in enumerate(matches):
        label = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        tts = section_tts(text[start:end])
        if tts:
            sections.append({"index": len(sections), "label": label,
                             "slug": slugify(label), "tts": tts})
    return sections


def load_script(path: Path) -> str:
    """Full cleaned TTS text (all sections joined). Kept for compatibility/tooling."""
    return "\n\n".join(s["tts"] for s in parse_sections(path))


def chunk_path(chunks_dir: Path, sec: dict) -> Path:
    return chunks_dir / f"{sec['index'] + 1:02d}_{sec['slug']}.mp3"


def atomic_replace_from_tmp(tmp: Path, final: Path) -> None:
    os.replace(tmp, final)


def synth_chunk(client, voice_id, model, sec, prev_plain, next_plain, out_path) -> None:
    """Synthesize one section to out_path via temp-then-rename (crash-safe)."""
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model,
        text=sec["tts"],
        voice_settings=VOICE_SETTINGS,
        previous_text=prev_plain,
        next_text=next_plain,
    )
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    try:
        with open(tmp, "wb") as f:
            for chunk in audio:   # API request happens here; may raise (e.g. quota)
                if chunk:
                    f.write(chunk)
        atomic_replace_from_tmp(tmp, out_path)
    except BaseException:
        tmp.unlink(missing_ok=True)   # never leave a partial/truncated chunk
        raise


def concat_to(narration_mp3: Path, chunk_files: list[Path]) -> None:
    """ffmpeg-concat chunk_files (in order) into narration_mp3 via temp-then-rename."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for cf in chunk_files:
            f.write(f"file '{cf.resolve()}'\n")
        list_path = f.name
    tmp = narration_mp3.with_suffix(narration_mp3.suffix + ".tmp")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
           "-c", "copy", str(tmp)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            tmp.unlink(missing_ok=True)
            sys.exit(f"ffmpeg concat failed:\n{result.stderr[-1500:]}")
        atomic_replace_from_tmp(tmp, narration_mp3)
    finally:
        Path(list_path).unlink(missing_ok=True)


def write_followalong(script_dir: Path, sections: list[dict]) -> Path:
    """Full break-stripped prose, written only after a successful render."""
    full = "\n\n".join(to_plain(s["tts"]) for s in sections).strip() + "\n"
    out = script_dir / "narration.txt"
    tmp = out.with_suffix(".txt.tmp")
    tmp.write_text(full, encoding="utf-8")
    os.replace(tmp, out)
    return out


def do_dry_run(script_path: Path, sections: list[dict], voice_label: str, voice_id: str) -> None:
    def preview(s, n=90):
        s = s.replace("\n", " ")
        return (s[:n] + "...") if len(s) > n else s

    total_chars = total_breaks = 0
    print("DRY RUN — no API calls made\n")
    print(f"Episode : {script_path}")
    print(f"Voice   : {voice_label} ({voice_id})  [resolved, NOT called]")
    print(f"Sections: {len(sections)}\n")
    for i, sec in enumerate(sections):
        chars = len(sec["tts"])
        breaks = len(BREAK_TAG.findall(sec["tts"]))
        total_chars += chars
        total_breaks += breaks
        prev_plain = to_plain(sections[i - 1]["tts"]) if i > 0 else None
        next_plain = to_plain(sections[i + 1]["tts"]) if i + 1 < len(sections) else None
        print(f"[{i + 1:02d}] {sec['label']:<14} file=chunks/{sec['index'] + 1:02d}_{sec['slug']}.mp3"
              f"  chars={chars}  breaks={breaks}")
        print(f"     previous_text -> {('(none)' if prev_plain is None else repr(preview(prev_plain)))}")
        print(f"     next_text     -> {('(none)' if next_plain is None else repr(preview(next_plain)))}")
    print(f"\nTOTALS: sections={len(sections)}  chars={total_chars}  breaks={total_breaks}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="path to 01_script.md")
    ap.add_argument("--voice", default="NARRATOR_A", choices=list(VOICE_IDS.keys()))
    ap.add_argument("--voice-id", default=None, help="raw voice id, overrides --voice")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--section", default=None,
                    help="regenerate only this section label (case-insensitive), then re-stitch")
    ap.add_argument("--dry-run", action="store_true", help="parse + report, no API calls")
    args = ap.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        sys.exit(f"Script not found: {script_path}")
    sections = parse_sections(script_path)
    if not sections:
        sys.exit("No [LABEL] sections found in script. Check 01_script.md.")

    voice_id = args.voice_id or VOICE_IDS.get(args.voice)

    if args.dry_run:
        do_dry_run(script_path, sections, args.voice, voice_id)
        return

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")
    if not voice_id:
        sys.exit(f"No voice id for {args.voice}. Fill it into VOICE_IDS (or pass --voice-id).")

    ep_dir = script_path.parent
    chunks_dir = ep_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    audio_dir = ep_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    narration_mp3 = audio_dir / "narration.mp3"

    # Which sections to (re)generate?
    if args.section:
        want = args.section.strip().lower()
        targets = [s for s in sections if s["label"].lower() == want]
        if not targets:
            labels = ", ".join(s["label"] for s in sections)
            sys.exit(f"No section matching '{args.section}'. Available: {labels}")
    else:
        targets = sections

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)

    for sec in targets:
        i = sec["index"]
        prev_plain = to_plain(sections[i - 1]["tts"]) if i > 0 else None
        next_plain = to_plain(sections[i + 1]["tts"]) if i + 1 < len(sections) else None
        out_path = chunk_path(chunks_dir, sec)
        print(f"[{i + 1:02d}/{len(sections)}] {sec['label']} -> {out_path.name} "
              f"({len(sec['tts'])} chars) ...")
        synth_chunk(client, voice_id, args.model, sec, prev_plain, next_plain, out_path)

    # Stitch: every chunk must exist (atomic writes left prior chunks intact on failure).
    chunk_files = [chunk_path(chunks_dir, s) for s in sections]
    missing = [cf.name for cf in chunk_files if not (cf.exists() and cf.stat().st_size > 0)]
    if missing:
        sys.exit("Cannot stitch — missing/empty chunks: " + ", ".join(missing) +
                 "\nRun a full generation (no --section) first.")

    concat_to(narration_mp3, chunk_files)
    txt = write_followalong(ep_dir, sections)
    print(f"\nStitched -> {narration_mp3}")
    print(f"Follow-along -> {txt}")
    print("Next: upload narration.mp3 to TurboScribe, export SRT, then run parse_timestamps.py")


if __name__ == "__main__":
    main()
