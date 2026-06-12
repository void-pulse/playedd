#!/usr/bin/env python3
"""analytics.py — pull reach/retention per video for the Playedd channel.

Answers the only question that matters when a Short freezes at a few views:
is it a DISTRIBUTION block (almost no impressions = not entering the feed) or a
RETENTION problem (lots of impressions, people swipe)? Prints, per video:
impressions, views, impression CTR, average view %, and a plain-English verdict.

Needs the yt-analytics.readonly scope (re-auth via auth.py if the token predates it).

Usage:
    python youtube/uploader/analytics.py                 # all videos in state.json
    python youtube/uploader/analytics.py VIDEOID [VIDEOID ...]
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auth import get_credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

STATE = Path(__file__).resolve().parent / "state.json"


def video_ids_from_state():
    import json
    d = json.loads(STATE.read_text())
    out = []
    for path, v in d.get("uploads", {}).items():
        vid = v.get("video_id")
        if vid:
            out.append((vid, v.get("title", path)))
    return out


def verdict(impr, views, ctr):
    if impr is None:
        return "no analytics yet (too new, or not served)"
    if impr < 50:
        return "DISTRIBUTION BLOCK — barely shown in feed (not a hook problem)"
    if ctr is not None and views and ctr < 2:
        return "shown but few tap in — thumbnail/first-frame issue"
    return "being served — performance is a retention/hook question"


def main():
    creds = get_credentials(interactive=False)
    yt = build("youtube", "v3", credentials=creds)
    ya = build("youtubeAnalytics", "v2", credentials=creds)

    ids = [(v, v) for v in sys.argv[1:]] or video_ids_from_state()
    if not ids:
        sys.exit("no video ids")

    # only PUBLIC videos have meaningful reach data
    meta = yt.videos().list(part="status,snippet", id=",".join(i for i, _ in ids)).execute()
    pub = {it["id"]: it for it in meta.get("items", [])
           if it["status"]["privacyStatus"] == "public"}

    start = (date.today() - timedelta(days=120)).isoformat()
    end = date.today().isoformat()
    print(f"Reach per PUBLIC video (last 120d, through {end}):\n")
    for vid, title in ids:
        if vid not in pub:
            continue
        try:
            r = ya.reports().query(
                ids="channel==MINE", startDate=start, endDate=end,
                metrics="views,impressions,impressionsClickThroughRate,averageViewPercentage",
                filters=f"video=={vid}").execute()
            rows = r.get("rows", [])
            if rows:
                views, impr, ctr, avp = rows[0]
            else:
                views = impr = ctr = avp = None
        except Exception as e:
            print(f"  {title[:48]:48}  analytics error: {str(e)[:80]}")
            continue
        t = (title or "")[:48]
        if impr is None:
            print(f"  {t:48}  no data yet")
        else:
            print(f"  {t:48}  impr={int(impr):>6}  views={int(views):>5}  "
                  f"CTR={ctr:>5.1f}%  avgView={avp:>5.1f}%")
        print(f"  {'':48}  -> {verdict(impr, views, ctr)}\n")


if __name__ == "__main__":
    main()
