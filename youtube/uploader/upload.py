#!/usr/bin/env python3
"""
upload.py — Playedd episode uploader + scheduler (YouTube Data API v3).

Reads episodes/<ep>/upload.json (the machine-readable upload spec: main video +
teaser shorts with full metadata) and:

  1. uploads the MAIN video      videos.insert, categoryId 27 (Education),
                                 selfDeclaredMadeForKids=false, PRIVATE
  2. sets its thumbnail          thumbnails.set       (if spec has one)
  3. uploads its captions        captions.insert      (narration.srt, if present)
  4. uploads each SHORT, auto-replacing the {MAIN_URL} placeholder in short
     descriptions with the main video's real URL
  5. schedules the drip          status.publishAt: main at --main-at, shorts at
                                 +N, +2N... days (STRATEGY.md: episode first,
                                 teasers dripped after), all at the same UTC time

Everything uploads PRIVATE. With publishAt set, YouTube flips each video public
automatically at its time — BUT ONLY once the API project has passed Google's
audit; unaudited projects' uploads stay locked private (flip manually in Studio
until then).

Idempotent: youtube/uploader/state.json records every uploaded video id keyed by
file path; re-runs skip them. Stops cleanly on quotaExceeded (one full episode =
main 1600 + 4 shorts 6400 + thumbnail 50 + captions 400 = ~8450 of the default
10,000/day — one episode per day fits, two doesn't).

Usage:
    python youtube/uploader/upload.py --episode episodes/0006_why-are-you-lazy --dry-run
    python youtube/uploader/upload.py --episode episodes/0006_why-are-you-lazy \
        --main-at 2026-06-12T15:00:00Z --shorts-start-days 2 --shorts-every-days 2
Manual (flagged): pin the CTA comment on each Short as it goes live (API can't pin);
flip public in Studio if the project is still unaudited.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path(__file__).resolve().parent / "state.json"
CATEGORY_EDUCATION = "27"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"uploads": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_spec(episode: Path) -> dict:
    spec_path = episode / "upload.json"
    if not spec_path.exists():
        sys.exit(f"missing {spec_path} — write the episode upload spec first")
    return json.loads(spec_path.read_text(encoding="utf-8"))


def validate(spec: dict) -> list[str]:
    problems = []
    items = [("main", spec["main"])] + [(f"short {i+1}", s) for i, s in enumerate(spec.get("shorts", []))]
    for label, item in items:
        f = ROOT / item["file"]
        if not f.exists() or f.stat().st_size == 0:
            problems.append(f"{label}: missing/empty file {item['file']}")
        if not item.get("title") or len(item["title"]) > 100:
            problems.append(f"{label}: bad title length {len(item.get('title',''))}")
        if len(item.get("description", "")) > 4800:
            problems.append(f"{label}: description too long")
        if sum(len(t) for t in item.get("tags", [])) > 470:
            problems.append(f"{label}: tags too long")
    thumb = spec["main"].get("thumbnail")
    if thumb and not (ROOT / thumb).exists():
        problems.append(f"main: thumbnail not found {thumb}")
    caps = spec["main"].get("captions")
    if caps and not (ROOT / caps).exists():
        problems.append(f"main: captions not found {caps}")
    return problems


def drip_times(main_at: str | None, n_shorts: int, start_days: float,
               every_days: float) -> tuple[str | None, list[str | None]]:
    if not main_at:
        return None, [None] * n_shorts
    t0 = datetime.fromisoformat(main_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    shorts = [(t0 + timedelta(days=start_days + every_days * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
              for i in range(n_shorts)]
    return t0.strftime("%Y-%m-%dT%H:%M:%SZ"), shorts


def insert_video(yt, item: dict, publish_at: str | None, state: dict) -> str | None:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at
    body = {"snippet": {"title": item["title"], "description": item["description"],
                        "tags": item.get("tags", []), "categoryId": CATEGORY_EDUCATION},
            "status": status}
    media = MediaFileUpload(str(ROOT / item["file"]), mimetype="video/mp4",
                            chunksize=8 * 1024 * 1024, resumable=True)
    print(f"uploading {Path(item['file']).name} ...")
    try:
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
    except HttpError as e:
        if e.resp.status == 403 and b"quota" in e.content.lower():
            print("QUOTA EXCEEDED — stopping cleanly; re-run tomorrow to continue.")
            return None
        print(f"  ERROR: {e}")
        return None
    vid = resp["id"]
    state["uploads"][item["file"]] = {
        "video_id": vid, "url": f"https://youtu.be/{vid}", "title": item["title"],
        "uploaded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publish_at": publish_at,
    }
    save_state(state)
    print(f"  -> https://youtu.be/{vid}  (PRIVATE{', publishAt ' + publish_at if publish_at else ''})")
    return vid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True, help="episode dir, e.g. episodes/0006_why-are-you-lazy")
    ap.add_argument("--dry-run", action="store_true", help="validate spec + files; no API calls")
    ap.add_argument("--main-at", default=None,
                    help="ISO8601 UTC publishAt for the main video (e.g. 2026-06-12T15:00:00Z)")
    ap.add_argument("--shorts-start-days", type=float, default=2.0,
                    help="first short publishes N days after the main")
    ap.add_argument("--shorts-every-days", type=float, default=2.0,
                    help="gap between shorts after the first")
    ap.add_argument("--skip-shorts", action="store_true")
    args = ap.parse_args()

    episode = ROOT / args.episode
    spec = load_spec(episode)
    problems = validate(spec)
    if problems:
        print("VALIDATION FAILED:")
        [print("  -", p) for p in problems]
        sys.exit(1)
    shorts = [] if args.skip_shorts else spec.get("shorts", [])
    main_at, short_times = drip_times(args.main_at, len(shorts),
                                      args.shorts_start_days, args.shorts_every_days)
    state = load_state()

    print(f"episode: {episode.name}  (main + {len(shorts)} shorts)  spec OK")
    if args.dry_run:
        m = spec["main"]
        mark = "SKIP(dup)" if m["file"] in state["uploads"] else "UPLOAD"
        print(f"  [{mark}] MAIN  {Path(m['file']).name}")
        print(f"          title: {m['title']}")
        print(f"          publishAt: {main_at}  thumbnail: {m.get('thumbnail')}  captions: {m.get('captions')}")
        for s, ts in zip(shorts, short_times):
            mark = "SKIP(dup)" if s["file"] in state["uploads"] else "UPLOAD"
            print(f"  [{mark}] SHORT {Path(s['file']).name}  publishAt: {ts}")
            print(f"          title: {s['title']}")
        print("dry run complete — no API calls made.")
        return

    from googleapiclient.discovery import build
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from auth import get_credentials
    yt = build("youtube", "v3", credentials=get_credentials(interactive=True))

    # 1) main video
    m = spec["main"]
    if m["file"] in state["uploads"]:
        main_id = state["uploads"][m["file"]]["video_id"]
        print(f"main already uploaded -> https://youtu.be/{main_id}")
    else:
        main_id = insert_video(yt, m, main_at, state)
        if not main_id:
            sys.exit(1)
        # 2) thumbnail
        if m.get("thumbnail"):
            yt.thumbnails().set(videoId=main_id,
                                media_body=str(ROOT / m["thumbnail"])).execute()
            print(f"  thumbnail set: {m['thumbnail']}")
        # 3) captions
        if m.get("captions"):
            from googleapiclient.http import MediaFileUpload
            yt.captions().insert(part="snippet", body={"snippet": {
                "videoId": main_id, "language": "en", "name": "English"}},
                media_body=MediaFileUpload(str(ROOT / m["captions"]),
                                           mimetype="application/octet-stream")).execute()
            print(f"  captions uploaded: {m['captions']}")

    main_url = state["uploads"][m["file"]]["url"]

    # 4) shorts, with {MAIN_URL} substituted
    for s, ts in zip(shorts, short_times):
        if s["file"] in state["uploads"]:
            print(f"short already uploaded -> {state['uploads'][s['file']]['url']}")
            continue
        s = dict(s)
        s["description"] = s["description"].replace("{MAIN_URL}", main_url)
        if not insert_video(yt, s, ts, state):
            break
        time.sleep(1)

    print("\nuploaded so far (this episode):")
    for item in [spec["main"], *shorts]:
        u = state["uploads"].get(item["file"])
        if u:
            print(f"  {u['url']}  publishAt={u.get('publish_at')}  {u['title']}")
    print("\nMANUAL: pin the CTA comment on each Short as it goes live; if the API "
          "project is unaudited, videos stay locked private — flip them in Studio.")


if __name__ == "__main__":
    main()
