#!/usr/bin/env python3
"""
auth.py — OAuth2 for the YouTube Data API v3 (Playedd channel).

Reads YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET from .env. First run opens the
browser (loopback flow — Google retired the copy/paste redirect in 2022); approve
with the account that owns the Playedd channel and pick the Playedd channel on
the consent screen. The refresh token lands in youtube/uploader/token.json
(gitignored) and refreshes automatically afterward.

Run directly to (re)authorize:  python youtube/uploader/auth.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

# .upload for videos.insert; the broader scope for thumbnails.set, captions.insert,
# and updating publishAt on existing videos; yt-analytics.readonly for impressions /
# CTR / retention so we can diagnose reach (distribution block vs. weak retention).
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]
TOKEN_PATH = Path(__file__).resolve().parent / "token.json"


def _client_config() -> dict:
    cid = os.getenv("YOUTUBE_CLIENT_ID")
    secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET missing from .env "
                 "(create an OAuth 'Desktop app' client in Google Cloud Console "
                 "with the YouTube Data API v3 enabled, then add both to .env)")
    return {"installed": {
        "client_id": cid, "client_secret": secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }}


def get_credentials(interactive: bool = True) -> Credentials:
    """Load (and auto-refresh) stored credentials; run consent flow if needed."""
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            return creds
    if not interactive:
        sys.exit("No stored YouTube token. Run once: python youtube/uploader/auth.py")

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_config(_client_config(), scopes=SCOPES)
    creds = flow.run_local_server(
        port=8766, open_browser=True, access_type="offline", prompt="consent",
        authorization_prompt_message="\nApprove in the browser tab that just opened "
                                     "(account that owns the PLAYEDD channel):\n{url}\n")
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nToken stored -> {TOKEN_PATH} (gitignored). Future runs are automatic.")
    return creds


if __name__ == "__main__":
    get_credentials(interactive=True)
    print("Auth OK.")
