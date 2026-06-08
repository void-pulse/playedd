# Claude Code Worker Brief — Build ep5 (Why Does Time Speed Up as You Get Older?)

You are the Playedd build worker. Build ep5 end to end from the locked script. Repo: void-pulse/playedd. Episode dir: `episodes/0005_why-time-speeds-up-as-you-age/`. Follow the brand docs (brand/*.md). Conventional commits. Heavy artifacts (audio/images/mp4) stay gitignored; commit scripts/manifests/srt/json.

## Inputs (already in the episode dir)
- `01_script.md` — LOCKED narration. Do not rewrite. Beats tagged [COLD OPEN]…[BUTTON].
- `02_storyboard.md` — visual anchors. One bold idea per frame.
- `00_idea.md` — context, register, myth-risk.

## Voice
- ElevenLabs **Jack**, voice ID `klOYed7ULfdFRLhrPHYE`.
- Settings (brand/VOICE.md → ep5 render config): model `eleven_multilingual_v2`, stability **0.50**, style **0.05**, similarity **0.80**, speaker boost **on**.
- Generate in scene-sized chunks with **request stitching** (pass previous/next text) and a **fixed seed** for the whole episode so tone does not drift. This is the consistency requirement.

## Steps
1. **Narration audio.** Run `pipeline/generate_audio.py` with the Jack config above, chunked by beat. Then LOCK the audio: trim dead air, fix any flubs, finalize the performance BEFORE timestamping (FORMATS production rule). Output to `audio/`.
2. **Timestamp.** Run TurboScribe (or the parse step) on the locked audio to get word/line timestamps. Produce `narration.srt` (sidecar) and the segments json. Proof captions: correct spelling, sensible segmentation, no em-dash artifacts.
3. **Storyboard → scenes.** Write per-timestamp SCENE descriptions to the scenes json, anchored to `02_storyboard.md`. Map cut pacing to the voice energy (fast lines = quick cuts, slow lines = holds). Enforce ONE bold metaphor per frame; no clutter.
4. **Images.** Run `pipeline/generate_images.py` (model `fal-ai/gpt-image-2`, reads STYLE_BLOCK from brand/IMAGE_STYLE.md). 16:9 landscape, timestamp-named files so they sort in order. Review for broken/clutter frames and regenerate the weak ones.
5. **Assemble.** Run `pipeline/assemble.py` (SYNC_OFFSET_SEC 0.25). Output `0005_why-time-speeds-up-as-you-age.mp4`.
6. **End stamp = silent Playedd LOGO.** Do NOT render the old "YOU'RE BEING PLAYED" CTA text. If `build_draft.py` / `build_short.py` still contain that CTA, remove it and swap in the logo asset (brand change applies channel-wide).
7. **Short.** Build a native 9:16 vertical short (`--portrait`) from the strongest 30-45s beat (the head-fake or the novelty payoff). Logo end stamp, no CTA.
8. **Publish kit.** Draft `upload.md`: title "Why Does Time Speed Up as You Get Older?", description per FORMATS template (hook question, what you'll learn, honest-sourcing credibility line, comment-bait "what year did this start for you?", SOURCES from 01_script.md, hashtags), Education category, tags per brand/TAGS.md (search-intent first), "altered/synthetic content" disclosure note. Thumbnail per 02_storyboard.md ("WHERE'D IT GO?").

## Guardrails
- REGISTER: neutral + wonder, gently empowering. NEVER add a mortality / "life slipping away" framing. (brand/VOICE.md emotional register.)
- Keep the head-fake intact (proportional theory = obvious-but-weak; memory/novelty = the real answer; Bejan = debated).
- Minimize em dashes everywhere (AI tell).
- Run a critic pass on the assembled cut: hook in first 2s, retention, any clutter frames, caption accuracy. Specific fixes, not "looks good."
- Do NOT touch ep4. Do NOT publish; leave for Logan's review.
