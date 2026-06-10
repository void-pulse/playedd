# Playedd — Autonomous BUILD command (canonical, verbatim-safe)

This is the corrected "build only" prompt. Safe to run as-is. The only substantive fix vs. the
original is **Step 1's pick rule**: anchor it to the PRODUCTION QUEUE (ep12+) and explicitly skip
already-published episodes. The old "lowest-numbered `01_script.md` under `episodes/`" rule
false-positived on ep1–5 (they predate the API uploader, so they aren't in `state.json` and look
"unbuilt") and could trigger a rebuild of an already-published episode.

The standing `playedd-daily-build` scheduled task already uses this logic.

---

```
Autonomous Playedd BUILD — build only. Work in the repo (/Users/curtisholmes/Projects/YT-Playedd; use .venv/bin/python).

1. PICK: Take the NEXT un-built episode from the PRODUCTION QUEUE in content/ideas/wonder_slate.md —
   the lowest-numbered queue entry (ep12 and up) that is NOT already built+scheduled in
   youtube/uploader/state.json. SKIP anything already published or already scheduled (ep1–11 are
   published or in the uploader; do NOT rebuild them). Do NOT just scan episodes/ for the
   "lowest-numbered 01_script.md" — ep1–5 have scripts but no state.json entry and will
   false-positive as unbuilt. The chosen episode must have a finished 01_script.md; if the next
   queue entry has no script yet, STOP ("buffer empty — waiting on scripts").

2. If that episode is missing 02_storyboard.md or 03_worker_brief.md, GENERATE them first from
   brand/SCRIPT_PLAYBOOK.md + IMAGE_STYLE.md, using a recent episode's 02/03 (e.g. ep11/ep12) as the
   template. One bold idea per frame; obey the IMAGE_STYLE anti-patterns (no redundant
   X-out-and-restate; don't over-name/describe Stan).

3. BUFFER GATE: if 5+ episodes are already BUILT AND SCHEDULED ahead (a main mp4 in state.json with a
   future publishAt), SKIP the build today (shorts/maintenance only) and stop. Else build per
   03_worker_brief.md: Jack VO (klOYed7ULfdFRLhrPHYE, eleven_multilingual_v2, stability 0.50 /
   style 0.05 / similarity 0.80, request stitching + fixed seed 50505, 0.92x read); doodle frames
   (parse_timestamps --merge-short ~4.0 → ~90–110 frames; generate_images --resume to fill fal
   timeouts); frame-exact assembly (assemble.py --music) with ducked score + voice leveling; the
   main mp4 + 4 teaser shorts (end on logo + arrow "FOR FULL BREAKDOWN"; build the short image list
   as a zsh array `imgs=(<dir>/images/*.png)` then pass `--images $imgs` — an unquoted plain var
   does NOT word-split in zsh); 3 distinct A/B thumbnails; upload.json (teaser-style description per
   FORMATS.md). If the beat slugs aren't in generate_music.py MOODS, write <ep>/music_moods.json
   first. Aim narration ~8 min (~1,350–1,450 words; the locked 0.92x read runs long — trim if over
   ~9 min).

4. SCHEDULE via youtube/uploader/upload.py --episode <ep> --main-at <next open Tue/Sat 18:00Z>
   --shorts-start-hours 2 --shorts-every-days 2; attach captions (narration.srt) + the chosen
   thumbnail. Next open slot = the next Tue/Sat after the latest scheduled main in state.json.

5. Leave one-time reminders (with the real video IDs) for Studio-only steps: related-video links on
   the teaser shorts once the main is public; end screen (Playedd logo DIRECTLY ABOVE the outro
   arrow + "Best for viewer" video top-right); thumbnail A/B pick; pinned comment. Mark the episode
   built in the wonder_slate.md PRODUCTION QUEUE. Commit + push (conventional; rm -f .git/index.lock
   if needed). Don't touch already-built episodes.
```

---

**Today this resolves to SKIP** (Step 3: ep7–ep11 = 5 built+scheduled ahead). The next real build is
**ep12 (Deja Vu)**, which already has its scripts and will be picked up automatically when the buffer
drops below 5 (~Jun 16).
