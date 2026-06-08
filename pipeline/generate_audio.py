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
    --voice NARRATOR_A|...           which voice from VOICE_IDS below (default NARRATOR_D = Drew, the locked Playedd voice)
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
# A beat label on its own line: [LABEL], optionally wrapped in markdown emphasis
# (**[LABEL]**, *[LABEL]*, __[LABEL]__). Both the bare and bold house styles parse.
LABEL_LINE = re.compile(r"^[ \t]*(?:\*{1,2}|_{1,2})?\[([^\]]+)\](?:\*{1,2}|_{1,2})?[ \t]*$", flags=re.M)
BREAK_TAG = re.compile(r"<break[^>]*>")
BREAK_SPLIT = re.compile(r'<break\s+time="([0-9.]+)s"\s*/?>', flags=re.I)

# Assembly defaults (post-process; see assemble()). atempo is a pitch-preserving
# time-stretch, so 0.92 = the channel's slightly-slower read with Drew's timbre
# unchanged. BEAT_GAP is the real silence inserted between beats AND at every <break>
# point: pauses are silence in the mix, never <break> tags sent to ElevenLabs (whose
# <break> rendering glitches with a clipped onset of the next phrase).
DEFAULT_TEMPO = 0.92
BEAT_GAP = 0.6
SR = 44100
# Per-piece edge handling before the silence gap is inserted. Strip ONLY true digital
# silence (<= SILENCE_DB) so a word's natural decay is always preserved — an aggressive
# trim (e.g. -40 dB) ate the soft tail of words ending in a vowel/fricative while
# hard-consonant endings survived. A short de-click micro-fade (DECLICK_S) at each seam
# edge prevents a click where the piece meets the inserted silence. Speech is never
# trimmed into; the pause is always inserted silence, never carved out of the word.
SILENCE_DB = -55.0
DECLICK_S = 0.01


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


def split_on_breaks(tts: str) -> list:
    """Split a section's TTS on <break time="Xs"/> tags into (clean_text, gap_after)
    pieces. The break becomes REAL silence at assembly instead of being sent to
    ElevenLabs, whose <break> rendering can glitch (a clipped onset of the next
    phrase). gap_after is the break duration in seconds; the last piece is 0.0."""
    parts = BREAK_SPLIT.split(tts)          # [text, dur, text, dur, ...]
    texts, durs = parts[0::2], parts[1::2]
    segs = []
    for i, t in enumerate(texts):
        clean = to_plain(t).strip()
        if not clean:
            continue
        segs.append((clean, float(durs[i]) if i < len(durs) else 0.0))
    return segs


def build_segments(sections: list, beat_gap: float) -> list:
    """Flatten sections into an ordered list of synth segments, each tagged with the
    silence gap that follows it: a within-beat <break> gap, the inter-beat gap at a
    section boundary, or 0.0 at the very end. Seam context (prev/next) is the adjacent
    segment so a split read keeps continuous prosody."""
    flat = []
    n_sec = len(sections)
    for si, sec in enumerate(sections):
        segs = split_on_breaks(sec["tts"]) or [(to_plain(sec["tts"]).strip(), 0.0)]
        n = len(segs)
        for k, (text, gap) in enumerate(segs):
            if k < n - 1:
                gap_after = gap             # within-beat paragraph pause
            elif si < n_sec - 1:
                gap_after = beat_gap        # between beats
            else:
                gap_after = 0.0             # end of narration
            flat.append({"sec_index": sec["index"], "slug": sec["slug"],
                         "label": sec["label"], "k": k, "nsegs": n,
                         "text": text, "gap_after": gap_after})
    for j, seg in enumerate(flat):
        prev_seg = flat[j - 1] if j > 0 else None
        # Cross-context (previous_text/next_text) is carried ONLY across a zero-gap, truly
        # continuous join. At any deliberate pause — every beat boundary, and any in-beat
        # <break> — drop it on BOTH sides: the trailing piece ends on a clean terminal
        # cadence (no anticipatory breath) and the leading piece starts clean (no
        # continuation onset breath). Each beat renders as a standalone take; the pauses
        # are inserted silence (between beats) or ElevenLabs ellipses (within a beat).
        seg["prev"] = prev_seg["text"] if (prev_seg is not None and prev_seg["gap_after"] == 0) else None
        seg["next"] = flat[j + 1]["text"] if (j + 1 < len(flat) and seg["gap_after"] == 0) else None
    return flat


def seg_file(chunks_dir: Path, seg: dict) -> Path:
    """Chunk filename. Single-segment beats keep the legacy NN_slug.mp3 name (so
    unchanged chunks are reused and never re-billed); split beats add a _k suffix."""
    num = seg["sec_index"] + 1
    if seg["nsegs"] == 1:
        return chunks_dir / f"{num:02d}_{seg['slug']}.mp3"
    return chunks_dir / f"{num:02d}_{seg['slug']}_{seg['k'] + 1}.mp3"


def atomic_replace_from_tmp(tmp: Path, final: Path) -> None:
    os.replace(tmp, final)


def synth_segment(client, voice_id, model, seg, out_path, voice_settings=VOICE_SETTINGS, seed=None) -> None:
    """Synthesize one segment to out_path via temp-then-rename (crash-safe). No
    <break> tags are ever sent to ElevenLabs; pauses are real silence added later.
    Adjacent-segment text is passed as previous_text/next_text so a split read keeps
    continuous prosody across the silence. A fixed seed holds tone steady across chunks."""
    kwargs = dict(
        voice_id=voice_id,
        model_id=model,
        text=seg["text"],
        voice_settings=voice_settings,
        previous_text=seg["prev"],
        next_text=seg["next"],
    )
    if seed is not None:
        kwargs["seed"] = seed
    audio = client.text_to_speech.convert(**kwargs)
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


def _ffdur(path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def tail_breath_cut(path, speech_db=-30.0, protect_s=0.090, floor_db=-55.0):
    """Return a cut time if a piece ends with a truncated breath plateau AFTER the word's
    decay, else None. POSITION-based, not level-based (breath and soft word-decay share a
    level, so no amplitude trim can separate them): find the last point speech drops away
    and stays down to EOF, always preserve `protect_s` (~90ms) of natural decay past it,
    and cut only if there is still content above `floor_db` after that — i.e. a real breath.
    A tail that decays cleanly to the floor returns None and is left for the -55 edge trim."""
    dur = _ffdur(path)
    if dur <= 0:
        return None
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path),
                          "-af", f"silencedetect=n={speech_db}dB:d=0.06", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = re.findall(r"silence_start: ([0-9.]+)", log)
    ends = re.findall(r"silence_end: ([0-9.]+)", log)
    if not starts:
        return None                       # speech runs to EOF, no trailing low region
    last_start = float(starts[-1])
    last_end = dur if len(ends) < len(starts) else float(ends[-1])
    if last_end < dur - 0.05:
        return None                       # speech resumed after the last dip, runs to EOF
    keep_until = last_start + protect_s
    if keep_until >= dur - 0.02:
        return None                       # < ~90ms of tail after the word; nothing to cut
    seg = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{keep_until:.3f}", "-i", str(path),
                          "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[0-9.]+) dB", seg)
    if m and float(m.group(1)) > floor_db:
        return round(keep_until, 3)        # breath plateau above the floor -> cut at word+90ms
    return None


def assemble(narration_mp3: Path, items: list, tempo: float) -> None:
    """Stitch segment files in order: time-stretch each by `tempo` (atempo is
    pitch-preserving), then add `gap` seconds of REAL silence after it. Speech is
    stretched; the silence gaps stay exact (added after the stretch). This is the
    single assembly path: the inter-beat gaps and the within-beat <break> pauses are
    identical silence, which is why neither glitches. Atomic temp-then-rename.

    `items` is a list of (segment_path, gap_after_seconds)."""
    inputs = []
    for p, _ in items:
        inputs += ["-i", str(p)]
    # Per piece, before inserting the gap: strip ONLY true digital silence (<= SILENCE_DB)
    # off the head, then the tail, so the word's natural decay is fully preserved; then a
    # DECLICK_S micro-fade at each edge to kill seam clicks. Pass forward = head; reverse,
    # do the same = tail; reverse back. Speech is never trimmed into.
    edge = (f"silenceremove=start_periods=1:start_threshold={SILENCE_DB}dB:start_duration=0,"
            f"afade=t=in:st=0:d={DECLICK_S},"
            f"areverse,"
            f"silenceremove=start_periods=1:start_threshold={SILENCE_DB}dB:start_duration=0,"
            f"afade=t=in:st=0:d={DECLICK_S},"
            f"areverse")
    filt, labels, trims = [], [], []
    for i, (p, gap) in enumerate(items):
        cut = tail_breath_cut(p)
        pre = f"[{i}:a]aformat=sample_rates={SR}:channel_layouts=mono"
        if cut is not None:               # drop a truncated breath, preserving word + 90ms
            pre += f",atrim=0:{cut:.3f},asetpts=N/SR/TB"
            trims.append(f"{p.name}@{cut:.2f}s")
        chain = f"{pre},{edge}"
        if abs(tempo - 1.0) > 1e-3:
            chain += f",atempo={tempo:.4f}"
        if gap > 0:
            chain += f",apad=pad_dur={gap}"
        chain += f"[a{i}]"
        filt.append(chain)
        labels.append(f"[a{i}]")
    if trims:
        print("  time-protected breath trims (word + 90ms kept): " + ", ".join(trims))
    filt.append("".join(labels) + f"concat=n={len(items)}:v=0:a=1[out]")
    tmp = narration_mp3.with_suffix(narration_mp3.suffix + ".tmp")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt),
           "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k",
           "-ar", str(SR), "-ac", "1", "-f", "mp3", str(tmp)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"ffmpeg assemble failed:\n{result.stderr[-1500:]}")
    atomic_replace_from_tmp(tmp, narration_mp3)


def write_followalong(script_dir: Path, sections: list[dict]) -> Path:
    """Full break-stripped prose, written only after a successful render."""
    full = "\n\n".join(to_plain(s["tts"]) for s in sections).strip() + "\n"
    out = script_dir / "narration.txt"
    tmp = out.with_suffix(".txt.tmp")
    tmp.write_text(full, encoding="utf-8")
    os.replace(tmp, out)
    return out


def do_dry_run(script_path: Path, sections: list, flat: list, voice_label: str,
               voice_id: str, tempo: float, beat_gap: float) -> None:
    def preview(s, n=78):
        s = (s or "").replace("\n", " ")
        return (s[:n] + "...") if len(s) > n else s

    chunks_dir = script_path.parent / "chunks"
    print("DRY RUN — no API calls made\n")
    print(f"Episode : {script_path}")
    print(f"Voice   : {voice_label} ({voice_id})  [resolved, NOT called]")
    print(f"Sections: {len(sections)}   Segments: {len(flat)}   "
          f"tempo={tempo}x   beat_gap={beat_gap}s\n")
    total = 0
    for seg in flat:
        total += len(seg["text"])
        tag = seg["label"] + (f" [{seg['k'] + 1}/{seg['nsegs']}]" if seg["nsegs"] > 1 else "")
        print(f"  {tag:<22} {seg_file(chunks_dir, seg).name:<26} "
              f"chars={len(seg['text']):<5} gap_after={seg['gap_after']}s")
        print(f"     prev -> {repr(preview(seg['prev']))}")
        print(f"     next -> {repr(preview(seg['next']))}")
    split = sum(1 for s in flat if s["nsegs"] > 1)
    print(f"\nTOTALS: segments={len(flat)}  chars={total}  "
          f"(split-from-breaks segments: {split})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="path to 01_script.md")
    ap.add_argument("--voice", default="NARRATOR_D", choices=list(VOICE_IDS.keys()))  # Drew = locked Playedd voice
    ap.add_argument("--voice-id", default=None, help="raw voice id, overrides --voice")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--stability", type=float, default=None, help="override voice stability (brand default 0.40)")
    ap.add_argument("--style", type=float, default=None, help="override voice style (brand default 0.15)")
    ap.add_argument("--similarity", type=float, default=None, help="override similarity_boost (brand default 0.80)")
    ap.add_argument("--seed", type=int, default=None, help="fixed ElevenLabs seed for tone consistency across chunks")
    ap.add_argument("--section", default=None,
                    help="regenerate only this section label (case-insensitive), then re-stitch")
    ap.add_argument("--tempo", type=float, default=DEFAULT_TEMPO,
                    help=f"post-process read speed (atempo, pitch-preserved). Channel "
                         f"default {DEFAULT_TEMPO}; pass 1.0 for full speed (e.g. shorts)")
    ap.add_argument("--beat-gap", type=float, default=BEAT_GAP,
                    help=f"seconds of real silence between beats (default {BEAT_GAP})")
    ap.add_argument("--reassemble", action="store_true",
                    help="re-stitch from existing chunks only (no synthesis, no API calls); "
                         "use after changing --tempo/--beat-gap or the trim")
    ap.add_argument("--dry-run", action="store_true", help="parse + report, no API calls")
    args = ap.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        sys.exit(f"Script not found: {script_path}")
    sections = parse_sections(script_path)
    if not sections:
        sys.exit("No [LABEL] sections found in script. Check 01_script.md.")
    flat = build_segments(sections, args.beat_gap)

    voice_id = args.voice_id or VOICE_IDS.get(args.voice)

    if args.dry_run:
        do_dry_run(script_path, sections, flat, args.voice, voice_id, args.tempo, args.beat_gap)
        return

    if not voice_id and not args.reassemble:
        sys.exit(f"No voice id for {args.voice}. Fill it into VOICE_IDS (or pass --voice-id).")

    ep_dir = script_path.parent
    chunks_dir = ep_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    audio_dir = ep_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    narration_mp3 = audio_dir / "narration.mp3"

    if not args.reassemble:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")

        # Which segments to (re)generate?
        if args.section:
            want = args.section.strip().lower()
            if want not in {s["label"].lower() for s in sections}:
                labels = ", ".join(s["label"] for s in sections)
                sys.exit(f"No section matching '{args.section}'. Available: {labels}")
            targets = [seg for seg in flat if seg["label"].lower() == want]
        else:
            targets = flat

        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=api_key)

        vs = dict(VOICE_SETTINGS)
        if args.stability is not None: vs["stability"] = args.stability
        if args.style is not None: vs["style"] = args.style
        if args.similarity is not None: vs["similarity_boost"] = args.similarity
        print(f"Voice settings: {vs}  seed={args.seed}")

        for seg in targets:
            out_path = seg_file(chunks_dir, seg)
            tag = seg["label"] + (f" [{seg['k'] + 1}/{seg['nsegs']}]" if seg["nsegs"] > 1 else "")
            print(f"[{tag}] -> {out_path.name} ({len(seg['text'])} chars) ...")
            synth_segment(client, voice_id, args.model, seg, out_path, vs, args.seed)

        # Remove stale chunk files for regenerated beats (post-synth, so a failed run
        # never orphans a good chunk). Also cleans up a beat changing single<->split.
        expected = {seg_file(chunks_dir, s).name for s in flat}
        for idx, slug in {(s["sec_index"], s["slug"]) for s in targets}:
            for old in chunks_dir.glob(f"{idx + 1:02d}_{slug}*.mp3"):
                if old.name not in expected:
                    old.unlink()
    else:
        print("Reassemble only — no synthesis, no API calls.")

    # Assemble: every segment file must exist (atomic writes left prior ones intact).
    seg_files = [seg_file(chunks_dir, s) for s in flat]
    missing = [f.name for f in seg_files if not (f.exists() and f.stat().st_size > 0)]
    if missing:
        sys.exit("Cannot stitch — missing/empty chunks: " + ", ".join(missing) +
                 "\nRun a full generation (no --section) first.")

    assemble(narration_mp3, [(seg_file(chunks_dir, s), s["gap_after"]) for s in flat], args.tempo)
    txt = write_followalong(ep_dir, sections)
    print(f"\nStitched -> {narration_mp3}  "
          f"(tempo={args.tempo}x, beat_gap={args.beat_gap}s, {len(flat)} segments)")
    print(f"Follow-along -> {txt}")
    print("Next: upload narration.mp3 to TurboScribe, export SRT, then run parse_timestamps.py")


if __name__ == "__main__":
    main()
