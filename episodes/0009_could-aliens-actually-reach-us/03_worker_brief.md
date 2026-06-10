# Claude Code Worker Brief — Build ep9 (Could Aliens Actually Reach Us?)

Build ep9 end to end from the locked script, same pipeline as ep5-ep8. Episode dir: `episodes/0009_could-aliens-actually-reach-us/`. Follow brand/STRATEGY.md, VOICE.md, IMAGE_STYLE.md, FORMATS.md, CHARACTER.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Features **Stan** (stargazer everyman).
- `02_storyboard.md` — visual anchors, one bold idea per frame; space = flat dark bg + star dots OK.
- `00_idea.md` — context, register, myth-risk, the 4 teaser-short angles.

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed.

## Main video steps (same as ep5-ep8)
1. `generate_audio.py` (Jack config, chunked by beat). LOCK audio before timestamping.
2. Timestamp -> `narration.srt` + segments json. Proof captions (no em dashes; numbers/units read cleanly: "4 light-years", "77,000", "1,500").
3. Per-timestamp SCENE descriptions -> `04_scenes.json`, anchored to `02_storyboard.md`. Stan consistent; one bold metaphor per frame; the scale gaps are the point.
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate cluttered/broken frames.
5. `assemble.py` (frame-exact timing; the ep5 drift fix). Upbeat-but-awed ducked score + voice leveling. -> `0009_could-aliens-actually-reach-us.mp4`.
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR. No CTA text on the main video.
7. `upload.md`: title "Could Aliens Actually Reach Us?", **description in the SHORT teaser style** (brand/FORMATS.md: 1-2 line teaser opener that withholds the payoff, 3-4 tease bullets, comment-bait "do you think they're out there?", SOURCES at bottom, AI-disclosure), Education category, search-intent tags, thumbnail (see below).

## Thumbnails — produce 3 DISTINCT options for A/B (brand/FORMATS.md)
(a) tiny Stan waving at a distant alien across a huge starfield, caps "TOO FAR?"; (b) rocket pointed at a far star, "77,000 YEARS"; (c) Stan at a telescope, faint alien, "SO CLOSE?". One bold idea, big caps, high contrast each.

## Shorts (4 teasers — withhold payoff, drive to full, end on logo + arrow "FOR FULL BREAKDOWN")
Each ~15-25s, native 9:16 (`--portrait`), one idea per frame, Jack VO. Drip over the week+ after the main video.
1. "Our fastest spacecraft would take 77,000 years to reach the nearest star." Tease.
2. "Voyager has flown 50 years and is barely one light-day from home. The nearest star is 1,500 light-days away." Tease.
3. "In 1950 a scientist asked one question about aliens that still haunts us: where is everybody?" Tease.
4. "The universe might be full of life, and none of them can ever meet. Here's why." Tease (don't fully reveal).

## Guardrails
- REGISTER: neutral + wonder, land on AWE, not loneliness/doom. The vastness is astonishing, not sad.
- ACCURACY (see 01_script.md flags): "aliens exist" = odds/likely, NOT stated fact; Proxima ~4.24 ly; nothing with mass hits light speed; Voyager ~77,000 yrs to Proxima; ~1 light-day out after ~50 yrs vs ~1,500+ to the star; warp drive needs exotic/negative-energy matter that may not exist (don't imply it's coming); Breakthrough Starshot (~20% c, ~20 yrs, stalled); Fermi 1950.
- Cold open must NOT give away the answer (it teases). Minimize em dashes.
- Critic pass on the final cut (hook in 2s, retention, clutter, Stan consistency, captions) with specific fixes.
- Do NOT touch ep4-ep8. Do NOT publish. Commit + push (conventional). If git complains about a lock: `rm -f .git/index.lock` first.
