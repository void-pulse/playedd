# Playedd — status / orchestrator briefing (updated 2026-06-10)

## Headline: the publishing model changed (this is the big one)
We found why the channel wasn't growing. **Videos published via the YouTube API (auto-publish on a scheduled publishAt) get almost no reach — they never enter the Shorts feed.** Videos published **natively in Studio** hit the feed and do real numbers.

**Proof (same video, same channel, only the publish method differs):**
- `dead-stars` short: **5 views** on API auto-publish → **540+** the moment Logan published it in Studio.
- `cleopatra`: **444 views in under an hour** (Studio). `sharks`: 387. `Why are you LAZY?` short: 423.
- API-auto-published long-form (`Why Are You LAZY?` main): **5 views**.
- Subs: 17 → 20+ and climbing.

**Mechanism:** ~all Short views come from the Shorts feed; a native publish seeds the video into the feed, the API/scheduled-flip path doesn't (so it only gets channel-page trickle ≈ 5 views).

## New operating model
- 🤖 **Automation BUILDS everything** (script → Jack VO → phone-safe doodle frames → frame-exact assembly → main mp4 + 4 teaser shorts + 3 thumbnails) **AND UPLOADS PRIVATE.**
- ❌ **Never auto-publish via the API.** No publishAt, no scheduled auto-flip.
- 👤 **Logan PUBLISHES each video in Studio** — that's the reach lever. A **noon reminder** lists exactly what to publish + Studio links + best times + a pinned-comment suggestion.
- Publish each ONCE and leave it (repeated private↔public toggling scrambles a Short's distribution).

→ The build command's "SCHEDULE" step is now "UPLOAD PRIVATE + record planned date" (see brand/BUILD_COMMAND.md, updated).

## Cadence & volume
- **Long-form:** ~2/week, Tue/Sat. Build is buffer-gated (build only when <5 already built+queued ahead).
- **Wonder shorts:** ramped to **~3/day** (numbers game toward big view totals), phone-safe, uploaded private for manual publish.

## Other changes landed
- **Phone-safe portrait frames:** text/subject kept centered, clear of the top ~15% (notch/title), bottom ~12%, and side edges. (The old setting filled edge-to-edge and clipped text on phones.)
- **Shorts CTA end card** redesigned: bigger Playedd logo, short thick curved arrow pointing down-left to the link row.
- **Style rules:** no redundant X-out-and-restate; don't over-name/over-describe Stan.
- **Build-command Step 1 pick fixed:** anchor to the production queue (ep12+); skip already-published ep1–5 (they predate the uploader and false-positived as "unbuilt").

## Current backlog state
- ep6–ep11 built; **ep12 (Deja Vu)** mid-build, parked behind the buffer gate (auto-resumes ~Jun 16).
- Some already-uploaded videos are still set to API auto-publish (ep7 Jun 13, etc.). These are being switched to Private / manual-publish so they don't strand themselves at ~5 views. (Pending: hold the existing scheduled ones Private + flip the uploaders to private-by-default.)

## Standing automation (scheduled tasks)
- **playedd-daily-build** — Mon/Thu, buffer-gated long-form build.
- **playedd-daily-wonder-shorts-lane** — Tue/Fri, builds to keep ~3/day queued, private.
- **playedd-daily-publish-community** — **noon**, the publish reminder (what to publish + links + times + pins) + ops + `brand/LOGAN_TODO.md`.
- **playedd-weekly-ops-health** — Sunday, schedule audit + commit + spend log.
- Per-launch Studio reminders (related-video, end screens, pins).

## Net
The only recurring human step is **Logan publishing the day's videos in Studio off the noon list.** Build, upload-private, reminders, and ops are automated.
