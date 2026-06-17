#!/usr/bin/env python3
"""caption_short.py — burn CapCut-style captions into a built Short.

No libass needed. We transcribe the narration with whisper (word-level
timestamps), group the words into punchy 1-2 word chunks, render each chunk as
a transparent PNG (big Permanent Marker caps, white with a thick dark outline,
centered in the phone-safe lower-middle), and overlay each onto the video for
its exact time window with ffmpeg. The active text appears in sync with the
voice — the moving text is what holds the swipe.

Usage:
    python pipeline/caption_short.py shorts_daily/batch01/03_venus/03_venus.mp4 \
        --audio shorts_daily/batch01/03_venus/audio/narration.mp3 \
        --out shorts_daily/batch01/03_venus/03_venus_cap.mp4
If --audio is omitted, the audio is pulled straight from the input video.
If --out is omitted, the input is captioned in place (atomic replace).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "brand" / "assets" / "fonts" / "PermanentMarker.ttf"
W, H = 1080, 1920

WHITE = (255, 255, 255)
INK = (20, 20, 20)
HILITE = (255, 214, 10)   # CapCut-ish pop accent (unused in v1 plain mode)

CY = int(H * 0.60)        # caption vertical center (phone-safe lower-middle)
MAX_W = int(W * 0.86)     # keep text clear of the side edges
START_SIZE = 132
MIN_SIZE = 64
STROKE = 11               # thick dark outline so it reads on any background


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-2000:] + "\n")
        raise SystemExit(f"command failed: {' '.join(map(str, cmd))}")
    return p


def whisper_words(audio: Path, model: str, workdir: Path):
    """Run whisper with word timestamps; return a flat list of (word, start, end)."""
    run(["whisper", str(audio), "--model", model, "--word_timestamps", "True",
         "--output_format", "json", "--output_dir", str(workdir), "--language", "en"])
    js = workdir / (audio.stem + ".json")
    data = json.loads(js.read_text())
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            t = w.get("word", "").strip()
            if t:
                words.append((t, float(w["start"]), float(w["end"])))
    return words


def script_tokens(script_path: Path):
    """Spoken words of the real script — drops # comment lines, ALL [LABEL] section
    tags (episodes have many), SSML <break> tags, and em dashes."""
    txt = script_path.read_text(encoding="utf-8")
    txt = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))
    txt = re.sub(r"\[.*?\]", " ", txt)            # all [LABEL] tags (global, not just leading)
    txt = re.sub(r"<[^>]+>", " ", txt)            # <break .../> SSML
    txt = txt.replace("—", " ").replace("–", " ")
    return [t for t in txt.split() if any(c.isalnum() for c in t)]


def align_to_script(wwords, tokens):
    """Keep whisper's word TIMINGS but replace the recognized text with the true
    script words (fixes mis-hearings like 'crosswalk' -> 'call psychoity')."""
    def norm(s):
        return re.sub(r"[^a-z0-9']", "", s.lower())
    a = [norm(w[0]) for w in wwords]
    b = [norm(t) for t in tokens]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                _, s, e = wwords[i1 + k]
                out.append((tokens[j1 + k], s, e))
        elif tag in ("replace", "insert"):
            m = j2 - j1
            if m == 0:
                continue
            if tag == "replace":
                t0, t1 = wwords[i1][1], wwords[i2 - 1][2]
            else:  # insert: borrow the gap between neighbours
                t0 = wwords[i1 - 1][2] if i1 > 0 else (wwords[0][1] if wwords else 0.0)
                t1 = wwords[i1][1] if i1 < len(wwords) else (wwords[-1][2] if wwords else t0 + 0.4)
            if t1 <= t0:
                t1 = t0 + 0.35 * m
            step = (t1 - t0) / m
            for k in range(m):
                out.append((tokens[j1 + k], t0 + k * step, t0 + (k + 1) * step))
        # tag == "delete": whisper heard extra words; drop them
    return out


def chunk(words, per=2, max_dur=1.1):
    """Group words into <=`per`-word, <=max_dur chunks for punchy on-beat captions."""
    out, cur = [], []
    for tok in words:
        cur.append(tok)
        dur = cur[-1][2] - cur[0][1]
        if len(cur) >= per or dur >= max_dur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    def clean(s):
        s = s.upper()
        for ch in '.,;:"“”«»':
            s = s.replace(ch, "")
        return s.strip()
    return [(clean(" ".join(t[0] for t in g)), g[0][1], g[-1][2]) for g in out]


def fit_font(d, text):
    size = START_SIZE
    while size > MIN_SIZE:
        f = ImageFont.truetype(str(FONT), size)
        if d.textbbox((0, 0), text, font=f, stroke_width=STROKE)[2] <= MAX_W:
            return f
        size -= 4
    return ImageFont.truetype(str(FONT), MIN_SIZE)


def render_chunk_png(text, path):
    """Draw each word with a clear gap so 2-word chunks never visually merge."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = fit_font(d, text)
    words = text.split()
    gap = int(f.size * 0.34)
    widths = [d.textbbox((0, 0), w, font=f, stroke_width=STROKE)[2] for w in words]
    total = sum(widths) + gap * (len(words) - 1)
    bb = d.textbbox((0, 0), text, font=f, stroke_width=STROKE)
    x = (W - total) // 2
    y = CY - (bb[3] - bb[1]) // 2 - bb[1]
    for w, wd in zip(words, widths):
        d.text((x, y), w, font=f, fill=WHITE, stroke_width=STROKE, stroke_fill=INK)
        x += wd + gap
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="built short mp4")
    ap.add_argument("--audio", default=None, help="narration mp3 (defaults to the video's audio)")
    ap.add_argument("--out", default=None, help="output mp4 (defaults to in-place)")
    ap.add_argument("--model", default="base", help="whisper model")
    ap.add_argument("--per", type=int, default=2, help="max words per caption chunk")
    ap.add_argument("--end", type=float, default=None,
                    help="stop captioning at this time (s) so words don't overlap the CTA end card")
    ap.add_argument("--script", default=None,
                    help="path to the script; locks caption TEXT to it (whisper only supplies timing)")
    args = ap.parse_args()

    video = Path(args.video)
    out = Path(args.out) if args.out else video
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        audio = Path(args.audio) if args.audio else None
        if audio is None:
            audio = tdp / "audio.wav"
            run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])

        words = whisper_words(audio, args.model, tdp)
        if not words:
            raise SystemExit("whisper returned no words — nothing to caption")
        if args.script:
            toks = script_tokens(Path(args.script))
            # AUDIO QC: if what the voice actually said diverges hard from the script,
            # the TTS likely glitched/looped (e.g. ElevenLabs hallucinating). Flag loudly.
            def nrm(s):
                return re.sub(r"[^a-z0-9']", "", s.lower())
            ratio = difflib.SequenceMatcher(a=[nrm(w[0]) for w in words],
                                            b=[nrm(t) for t in toks], autojunk=False).ratio()
            if ratio < 0.78:
                sys.stderr.write(
                    f"\n*** AUDIO QC FAIL: voice matches script only {ratio:.0%} — the narration "
                    f"likely glitched (TTS hallucination/loop). Regenerate the audio before shipping. ***\n\n")
                if not os.getenv("CAPTION_FORCE"):
                    raise SystemExit(2)
            words = align_to_script(words, toks)
        chunks = chunk(words, per=args.per)
        if args.end is not None:
            chunks = [(t, s, min(e, args.end)) for (t, s, e) in chunks if s < args.end]

        pngs = []
        for i, (text, s, e) in enumerate(chunks):
            p = tdp / f"cap_{i:03d}.png"
            render_chunk_png(text, p)
            pngs.append((p, s, e))

        # Build the ffmpeg overlay chain: base video + one looped PNG per chunk,
        # each shown only during its [start,end) window.
        cmd = ["ffmpeg", "-y", "-i", str(video)]
        for p, _, _ in pngs:
            cmd += ["-loop", "1", "-i", str(p)]
        fc, last = [], "0:v"
        for idx, (_, s, e) in enumerate(pngs, start=1):
            nxt = f"v{idx}"
            # half-open [s,e) so adjacent captions never both render on a boundary frame
            fc.append(f"[{last}][{idx}:v]overlay=0:0:enable='gte(t,{s:.3f})*lt(t,{e:.3f})'[{nxt}]")
            last = nxt
        filter_complex = ";".join(fc)
        tmp_out = tdp / "out.mp4"
        cmd += ["-filter_complex", filter_complex, "-map", f"[{last}]", "-map", "0:a?",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", str(tmp_out)]
        run(cmd)

        out.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_out, out)
    print(f"captioned -> {out}  ({len(chunks)} caption chunks)")


if __name__ == "__main__":
    main()
