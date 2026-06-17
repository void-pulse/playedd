#!/usr/bin/env python3
"""
upload_shorts.py — uploader for STANDALONE shorts (no parent episode).

Reads a batch manifest (shorts_daily/<batch>/upload_manifest.json: list of
{file, title, description, tags, publishAt}) and uploads each PRIVATE with its
publishAt. Same idempotent state.json ledger as the episode uploader.

Usage:
    python youtube/uploader/upload_shorts.py --manifest shorts_daily/batch01/upload_manifest.json [--dry-run]
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload import load_state, save_state, insert_video  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--schedule", action="store_true",
                    help="ACTUALLY use the manifest's publishAt. DEFAULT OFF = upload PRIVATE with no "
                         "publishAt (publish natively in Studio — API auto-publish gets ~0 reach).")
    args = ap.parse_args()
    records = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    problems = [r["file"] for r in records if not (ROOT / r["file"]).exists()]
    if problems:
        sys.exit(f"missing files: {problems}")
    state = load_state()
    pending = [r for r in records if r["file"] not in state["uploads"]]
    print(f"{len(records)} records; pending {len(pending)}")
    if args.dry_run:
        for r in records:
            mark = "SKIP(dup)" if r["file"] in state["uploads"] else "UPLOAD"
            print(f"  [{mark}] {r['publishAt']}  {r['title']}")
        return
    from googleapiclient.discovery import build
    from auth import get_credentials
    yt = build("youtube", "v3", credentials=get_credentials(interactive=False))
    for r in pending:
        pub = r.get("publishAt") if args.schedule else None   # private-by-default
        if not insert_video(yt, r, pub, state):
            break
        time.sleep(1)
    print("\nall scheduled standalone shorts:")
    for r in records:
        u = state["uploads"].get(r["file"])
        if u:
            print(f"  {u.get('publish_at')}  {u['url']}  {u['title']}")


if __name__ == "__main__":
    main()
