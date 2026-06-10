# Playedd YouTube uploader + scheduler (Data API v3)

## One-time setup (Logan, ~5 min)
1. console.cloud.google.com → new project (e.g. "playedd-uploader") → enable **YouTube Data API v3**.
2. OAuth consent screen: External, add yourself as a test user.
3. Credentials → Create credentials → **OAuth client ID → Desktop app** → copy both values into `.env`:
   `YOUTUBE_CLIENT_ID=...` and `YOUTUBE_CLIENT_SECRET=...`
4. `python youtube/uploader/auth.py` → browser opens → approve with the **Playedd channel** account.
   Token lands in `token.json` (gitignored); everything after is automatic.

## Per episode
The build pipeline writes `episodes/<ep>/upload.json` (main + 4 shorts, full metadata;
short descriptions carry `{MAIN_URL}`, auto-replaced with the real main-video link).

    python youtube/uploader/upload.py --episode episodes/0006_why-are-you-lazy --dry-run
    python youtube/uploader/upload.py --episode episodes/0006_why-are-you-lazy \
        --main-at 2026-06-12T15:00:00Z          # shorts auto-drip +2d, +4d, +6d, +8d

Uploads main (+ thumbnail if set in the spec, + narration.srt captions), then the 4
shorts. Everything goes up **PRIVATE** with `publishAt` set — YouTube flips each public
automatically at its time. Idempotent via `state.json`; quota fits ~1 episode/day
(main 1600 + 4 shorts 6400 + captions 400 + thumbnail 50 ≈ 8450 of 10,000).

## Caveats
- **API audit:** until Google audits/approves the API project, API uploads stay locked
  private even past their publishAt (flip manually in Studio meanwhile). Apply for the
  audit once; after approval scheduling is fully hands-off.
- **Pinned comments:** the API can't pin — pin the CTA comment per Short manually.
- `thumbnail` is null in the ep6-ep9 specs until Logan picks winners (options are in
  each episode's `thumbnails/`); set the path and re-run (thumbnails.set works
  post-upload via the same script re-run only for new uploads — or set it in Studio).
