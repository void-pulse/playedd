#!/usr/bin/env python3
"""
parse_timestamps.py
Turn a TurboScribe export (SRT, VTT, or simple timestamped TXT) into a clean
segments JSON that the rest of the pipeline understands.

Each segment = one image in the final video. The 'seconds' field is when that
image should appear; the next segment's 'seconds' is when it should leave.

Usage:
    python pipeline/parse_timestamps.py episodes/<ep>/02_narration.srt
    # writes episodes/<ep>/03_segments.json

Optional:
    --out path/to/segments.json    (override output location)
    --merge-short 1.5              (merge segments shorter than N seconds into the next,
                                    so you don't pay for an image that flashes by)
"""
import argparse
import json
import re
import sys
from pathlib import Path

# TurboScribe injects a promo line into free-tier exports. Strip it so it never
# becomes narration text or an image prompt. Case-insensitive, tolerant of spacing.
WATERMARK_RE = re.compile(
    r"\(\s*Transcribed by TurboScribe\.\s*Go Unlimited to remove this message\.\s*\)",
    re.IGNORECASE,
)


def strip_watermark(text: str) -> str:
    """Remove the TurboScribe watermark parenthetical and any whitespace it leaves behind."""
    cleaned = WATERMARK_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)  # collapse a gap left mid-line
    return cleaned.strip()


def hms_to_seconds(ts: str) -> float:
    """Accepts HH:MM:SS,mmm / HH:MM:SS.mmm / MM:SS / M:SS."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0.0, parts[0], parts[1]
    else:
        h, m, s = 0.0, 0.0, parts[0]
    return h * 3600 + m * 60 + s


def seconds_to_label(sec: float) -> str:
    m = int(sec // 60)
    s = int(round(sec % 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d}"


def parse_srt_or_vtt(text: str):
    """Handles both SRT and VTT. Returns list of (start_seconds, text)."""
    # Normalize line endings, strip a VTT header if present.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"^WEBVTT.*?\n\n", "", text, flags=re.S)
    blocks = re.split(r"\n\s*\n", text.strip())
    time_re = re.compile(
        r"(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)\s*-->\s*"
        r"(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)"
    )
    out = []
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip() != ""]
        if not lines:
            continue
        # Drop a leading numeric index line if present (SRT).
        if re.fullmatch(r"\d+", lines[0].strip()):
            lines = lines[1:]
        if not lines:
            continue
        m = time_re.search(lines[0])
        if not m:
            continue
        start = hms_to_seconds(m.group(1))
        caption = " ".join(lines[1:]).strip()
        caption = re.sub(r"<[^>]+>", "", caption)  # strip vtt tags
        caption = strip_watermark(caption)
        if caption:
            out.append((start, caption))
    return out


def parse_plain_txt(text: str):
    """
    Fallback for a simple 'M:SS some text' per-line format.
    Returns list of (start_seconds, text).
    """
    out = []
    line_re = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.*\S)\s*$")
    for line in text.splitlines():
        m = line_re.match(line)
        if m:
            caption = strip_watermark(m.group(2))
            if caption:
                out.append((hms_to_seconds(m.group(1)), caption))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="TurboScribe export: .srt, .vtt, or .txt")
    ap.add_argument("--out", default=None)
    ap.add_argument("--merge-short", type=float, default=0.0,
                    help="merge segments shorter than this many seconds")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        sys.exit(f"File not found: {in_path}")

    raw = in_path.read_text(encoding="utf-8", errors="ignore")
    ext = in_path.suffix.lower()

    if ext in (".srt", ".vtt"):
        pairs = parse_srt_or_vtt(raw)
    elif ext == ".txt":
        pairs = parse_plain_txt(raw) or parse_srt_or_vtt(raw)
    else:
        # Try both, srt-style first.
        pairs = parse_srt_or_vtt(raw) or parse_plain_txt(raw)

    if not pairs:
        sys.exit("Could not parse any timestamped lines. Check the file format.")

    pairs.sort(key=lambda p: p[0])

    # Optional merge of very short segments into the following one.
    if args.merge_short > 0:
        merged = []
        i = 0
        while i < len(pairs):
            start, txt = pairs[i]
            j = i + 1
            while j < len(pairs) and (pairs[j][0] - start) < args.merge_short:
                txt = (txt + " " + pairs[j][1]).strip()
                j += 1
            merged.append((start, txt))
            i = j
        pairs = merged

    segments = [
        {
            "index": idx + 1,
            "timestamp": seconds_to_label(start),
            "seconds": round(start, 2),
            "text": txt,
        }
        for idx, (start, txt) in enumerate(pairs)
    ]

    out_path = Path(args.out) if args.out else in_path.with_name("03_segments.json")
    out_path.write_text(json.dumps(segments, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Parsed {len(segments)} segments -> {out_path}")
    print("Next: feed 03_segments.json to prompts/03 in Claude Code to write 04_scenes.json")


if __name__ == "__main__":
    main()
