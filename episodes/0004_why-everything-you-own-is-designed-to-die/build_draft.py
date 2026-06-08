#!/usr/bin/env python3
"""
build_draft.py  —  reproducible ep4 episode assembler.

Self-contained: regenerate images (generate_images), audio (generate_audio), sfx
(generate_sfx) and the music bed, then run this. Reads sfx_cues.json (the SFX manifest)
and narration.json (whisper segment + word timestamps). Produces draft_ep4.mp4.

Design notes (hard-won):
- SFX land on the exact WORD they illustrate (word-level times) — not the picture cut.
- The Playedd logo face is COMPOSITED onto the final frame here, at assemble time, from the
  tracked asset brand/assets/avatar_800.png — a clean image regen can never revert to a figure.
- Audio is rendered first against a full-length silent anchor (can't end early / deadlock),
  then muxed. Video uses the concat FILTER (the concat demuxer silently drops still frames).
- Looped inputs use FINITE -stream_loop counts; amix uses duration=first (anchor is first).

Usage:  python episodes/0004_.../build_draft.py
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

EP = Path(__file__).resolve().parent
ROOT = EP.parents[1]
W, H, FPS = 1920, 1080, 30
SYNC_OFFSET, MIN_DUR, TAIL, MUSIC_DB, SR = 0.40, 0.20, 2.5, -22.0, 44100

def ffdur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(p)],capture_output=True,text=True).stdout.strip())
def db(x): return round(10**(x/20.0),4)
def nrm(t): return re.sub(r"[^a-z0-9 ]"," ",t.lower()).split()
def nw(w): return re.sub(r"[^a-z0-9]","",w.lower())

CUEMAP = json.loads((EP/"sfx_cues.json").read_text())
WJSON = json.loads((EP/"narration.json").read_text())
WORDS = [(nw(w["word"]),float(w["start"]),float(w["end"])) for s in WJSON["segments"] for w in s.get("words",[])]

# Image timing comes from narration.srt (the segmentation the approved cut was timed on).
# narration.json (a separate whisper run) segments differently — keep it ONLY for word-SFX times.
def _parse_srt(p):
    out=[]
    for b in re.split(r"\n\s*\n", p.read_text().replace("\r","")):
        L=[l for l in b.split("\n") if l.strip()]
        if len(L)<2: continue
        m=re.search(r"(\d+):(\d+):([\d.,]+)\s*-->", L[1] if re.fullmatch(r"\d+",L[0].strip()) else L[0])
        if not m: continue
        out.append((int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3).replace(",",".")),
                    nrm(" ".join(L[2:] if re.fullmatch(r"\d+",L[0].strip()) else L[1:]))))
    return out
_srt=EP/"narration.srt"
if not _srt.exists(): sys.exit("narration.srt required for image timing (the approved cut's segmentation)")
SEGS = _parse_srt(_srt)

def seg_time(fw):
    fw=fw[:8]; best,bt=-1,0.0
    for st,sw in SEGS:
        sc=sum(1 for w in fw if w in sw)
        if sc>best: best,bt=sc,st
    return bt
def word_time(phrase, target):
    pw=[nw(x) for x in phrase.split()]; tw=nw(target)
    for i in range(len(WORDS)-len(pw)+1):
        if all(WORDS[i+j][0]==pw[j] for j in range(len(pw))):
            for j in range(len(pw)):
                if WORDS[i+j][0]==tw: return WORDS[i+j][1]
            return WORDS[i][1]
    for w,s,e in WORDS:
        if w==tw: return s
    return None

narration=EP/"audio"/"narration.mp3"; vo_len=ffdur(narration); total=round(vo_len+TAIL,3)
scenes=sorted(json.loads((EP/"04_scenes.json").read_text()), key=lambda s:s["index"])
imgs={}
for s in scenes:
    m=sorted((EP/"images").glob(f"{s['index']:04d}_*.png"))
    if not m: sys.exit(f"missing image idx {s['index']} — run generate_images first")
    imgs[s["index"]]=m[0]

# ---- logo end card: composite the tracked Playedd face onto the final frame (reproducible) ----
LOGO=CUEMAP.get("logo")
logo_tmp=None
if LOGO and LOGO["frame"] in imgs:
    asset=ROOT/LOGO["asset"]
    if not asset.exists(): sys.exit(f"logo asset missing: {asset}")
    base=imgs[LOGO["frame"]]
    logo_tmp=Path(tempfile.mktemp(suffix=".png"))
    fc=(f"[1:v]colorkey={LOGO['colorkey']},scale={LOGO['size']}:{LOGO['size']}[lg];"
        f"[0:v][lg]overlay={LOGO['x']}:{LOGO['y']}[out]")
    r=subprocess.run(["ffmpeg","-y","-i",str(base),"-i",str(asset),"-filter_complex",fc,
        "-map","[out]","-frames:v","1",str(logo_tmp)],capture_output=True,text=True)
    if r.returncode!=0: sys.exit("logo composite failed:\n"+r.stderr[-1500:])
    imgs[LOGO["frame"]]=logo_tmp
    print(f"composited logo onto frame {LOGO['frame']}")

prev=0.0
for s in scenes:
    t=max(seg_time(nrm(s["text"])), prev+0.2)
    s["t"]=0.0 if s is scenes[0] else round(t+SYNC_OFFSET,3); prev=t
n=len(scenes); items=[]
for i,s in enumerate(scenes):
    end=scenes[i+1]["t"] if i+1<n else total
    items.append((s["index"], imgs[s["index"]], max(MIN_DUR, round(end-s["t"],3))))
T={s["index"]: s["t"] for s in scenes}

# ---------- PASS 1: audio mix against a full-length silent anchor ----------
SFXD=ROOT/"assets"/"sfx"
loops=lambda need,fp: str(int(need/ffdur(fp))+1)
AUD=Path(tempfile.mktemp(suffix=".wav"))
music=EP/CUEMAP["music"]["file"]
ai=["-f","lavfi","-t",f"{total}","-i","anullsrc=r=44100:cl=stereo","-i",str(narration),
    "-stream_loop",loops(total,music),"-i",str(music)]
af=lambda i: f"[{i}:a]aformat=sample_rates={SR}:channel_layouts=stereo"
ap=[f"{af(0)},atrim=0:{total}[anchor]",
    f"{af(1)},apad,atrim=0:{total},asetpts=N/SR/TB[vo]",
    f"{af(2)},atrim=0:{total},asetpts=N/SR/TB,volume={db(CUEMAP['music']['gain_db'])},afade=t=out:st={round(total-2.0,3)}:d=2.0[mus]"]
lab=["[anchor]","[vo]","[mus]"]; src=3
for b in CUEMAP["beds"]:
    fp=SFXD/(b["sfx"]+".mp3")
    if not fp.exists(): sys.exit(f"missing bed {fp}")
    st=T.get(b["from"],0.0); en=T.get(b["to"],st+6)+1.0; dur=round(en-st,3); fo=round(min(3.0,dur*0.5),3)
    ai+=["-stream_loop",loops(dur,fp),"-i",str(fp)]
    ap.append(f"{af(src)},atrim=0:{dur},volume={db(b['gain'])},afade=t=in:d=1.0,afade=t=out:st={round(dur-fo,3)}:d={fo},adelay={int(st*1000)}:all=1,apad,atrim=0:{total}[b{src}]")
    lab.append(f"[b{src}]"); src+=1
placed=[]
for c in CUEMAP["cues"]:
    fp=SFXD/(c["sfx"]+".mp3")
    if not fp.exists(): sys.exit(f"missing sfx {fp}")
    wt=word_time(c["phrase"],c["word"])
    if wt is None: placed.append((c["sfx"],c["word"],"NOT FOUND")); continue
    at=max(0.0, round(wt+c.get("lead",-0.05),3))
    ai+=["-i",str(fp)]
    ap.append(f"{af(src)},volume={db(c['gain'])},adelay={int(at*1000)}:all=1,apad,atrim=0:{total}[s{src}]")
    lab.append(f"[s{src}]"); placed.append((c["sfx"],c["word"],at)); src+=1
ap.append("".join(lab)+f"amix=inputs={len(lab)}:normalize=0:duration=first:dropout_transition=0,alimiter=limit=0.95:level=false[a]")
r=subprocess.run(["ffmpeg","-y",*ai,"-filter_complex",";".join(ap),"-map","[a]","-ac","2","-ar",str(SR),"-c:a","pcm_s16le","-t",f"{total}",str(AUD)],capture_output=True,text=True)
if r.returncode!=0: AUD.unlink(missing_ok=True); sys.exit("audio pass failed:\n"+r.stderr[-2500:])
print(f"audio rendered: {ffdur(AUD):.1f}s (target {total}s); {sum(1 for _,_,a in placed if a!='NOT FOUND')} cues on-word, {len(CUEMAP['beds'])} beds")

# ---------- PASS 2: video via concat FILTER (demuxer drops still frames) + mux ----------
out=EP/"draft_ep4.mp4"; tmp=out.with_suffix(".mp4.tmp")
SCALE=(f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:white,setsar=1,fps={FPS},format=yuv420p")
vin=[]; vfp=[]
for k,(idx,img,du) in enumerate(items):
    vin+=["-loop","1","-t",f"{du}","-i",str(img)]
    vfp.append(f"[{k}:v]{SCALE}[v{k}]")
vfp.append("".join(f"[v{k}]" for k in range(len(items)))+f"concat=n={len(items)}:v=1[v]")
aidx=len(items)
r=subprocess.run(["ffmpeg","-y",*vin,"-i",str(AUD),"-filter_complex",";".join(vfp),
    "-map","[v]","-map",f"{aidx}:a","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
    "-c:a","aac","-b:a","192k","-r",str(FPS),"-t",f"{total}","-movflags","+faststart","-f","mp4",str(tmp)],capture_output=True,text=True)
AUD.unlink(missing_ok=True)
if logo_tmp: logo_tmp.unlink(missing_ok=True)
if r.returncode!=0: tmp.unlink(missing_ok=True); sys.exit("video/mux pass failed:\n"+r.stderr[-2500:])
tmp.replace(out)
print(f"DRAFT -> {out}  ({ffdur(out):.1f}s, {len(items)} frames)")
