# Claude Code Worker Brief — Build ep6 (Why Are You Lazy?)

Build ep6 end to end from the locked script, same pipeline as ep5. Episode dir: `episodes/0006_why-are-you-lazy/`. Follow brand/STRATEGY.md, brand/VOICE.md, brand/IMAGE_STYLE.md, brand/FORMATS.md, brand/CHARACTER.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Features **Stan**, the recurring everyman.
- `02_storyboard.md` — visual anchors, one bold idea per frame, Stan consistent.
- `00_idea.md` — context, register, myth-risk, the 4 teaser-short angles.

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed (consistency).

## Main video steps (same as ep5, which worked)
1. `generate_audio.py` with the Jack config, chunked by beat. LOCK audio (trim dead air, fix flubs) before timestamping.
2. Timestamp -> `narration.srt` + segments json. Proof captions (spelling, segmentation, no em dashes).
3. Write per-timestamp SCENE descriptions to `04_scenes.json`, anchored to `02_storyboard.md`. **Stan stays visually consistent every frame** (brand/CHARACTER.md). One bold metaphor per frame; cut pacing mapped to voice energy.
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate any cluttered/broken/off-model-Stan frames.
5. `assemble.py` (frame-exact timing — pin input fps to output fps, snap cuts to frame boundaries; the ep5 drift fix) -> `0006_why-are-you-lazy.mp4`. Upbeat per-beat score, ducked, with voice leveling (ep5 settings).
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR (brand/FORMATS.md). No CTA text on the main video.
7. `upload.md`: title "Why Are You Lazy?", description per FORMATS template (hook, what you'll learn, honest-sourcing line, comment-bait "be honest, are you watching this instead of doing something?", SOURCES from 01_script.md, hashtags), Education category, search-intent tags per brand/TAGS.md, synthetic-content disclosure, thumbnail "LAZY?" (Stan on couch).

## Shorts (4 teasers — per brand/STRATEGY.md: WITHHOLD the payoff, drive to the full video, end on Playedd logo + up-arrow + "FOR FULL BREAKDOWN")
Each ~15-25s, native 9:16 (`--portrait`), one idea per frame, Stan featured, Jack VO. Drip them out over the week+ after the main video. Each must stand alone and end on the "?" itch.
1. **The reframe:** Stan can't run; "you're not lazy, your brain is a survival machine built to save energy." Tease that there's a wilder reason it feels like a *sin*. (do NOT reveal the history)
2. **The history bomb:** "Laziness was invented as a SIN, by a monk in the desert 1,600 years ago." Tease, cut to CTA.
3. **The noonday demon:** "The afternoon slump used to be considered a literal demon. It had a name." Tease.
4. **The factory guilt:** "The reason you feel guilty doing nothing is basically a few-hundred-year-old sales pitch." Tease.

## Guardrails
- REGISTER: neutral + wonder, reassuring via mechanism. NEVER shame the viewer. No health advice/prescriptions; the one lever (shrink the first step) stays light and grounded.
- HISTORY ACCURACY: acedia → Evagrius's eight → Gregory's seven deadly sins → "sloth"; Protestant work ethic = Weber's thesis (frame as "a new idea took hold," don't over-claim single cause). "Law of least effort" = brain "tends to" minimize effort, not absolute. DO NOT use the contested "hunter-gatherers barely worked" (Sahlins) claim. Keep "around the fourth century / 1,600 years ago" for the monks; keep the industrial era vague ("a few hundred years").
- Minimize em dashes. Run a critic pass on the final cut (hook in 2s, retention, clutter, Stan consistency, caption accuracy) with specific fixes.
- Do NOT touch ep4 or the published ep5. Do NOT publish. Leave for Logan's review. Commit + push (conventional). If git complains about a lock: `rm -f .git/index.lock` first.
