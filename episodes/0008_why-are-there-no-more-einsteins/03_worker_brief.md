# Claude Code Worker Brief — Build ep8 (Why Are There No More Einsteins?)

Build ep8 end to end from the locked script, same pipeline as ep5-ep7. Episode dir: `episodes/0008_why-are-there-no-more-einsteins/`. Follow brand/STRATEGY.md, VOICE.md, IMAGE_STYLE.md, FORMATS.md, CHARACTER.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Features **Stan** (modern everyman) and **doodle-Einstein** (one-off historical figure).
- `02_storyboard.md` — visual anchors, one bold idea per frame, character notes.
- `00_idea.md` — context, register, myth-risk, the 4 teaser-short angles.

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed.

## Main video steps (same as ep5-ep7)
1. `generate_audio.py` (Jack config, chunked by beat). LOCK audio before timestamping.
2. Timestamp -> `narration.srt` + segments json. Proof captions (no em dashes; "E=mc²" reads cleanly; "nineteen oh five" / numbers sensible).
3. Per-timestamp SCENE descriptions -> `04_scenes.json`, anchored to `02_storyboard.md`. Stan consistent every frame; doodle-Einstein recognizable (wild hair + mustache) and clearly NOT Stan. One bold metaphor per frame.
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate cluttered/broken/off-model frames.
5. `assemble.py` (frame-exact timing; the ep5 drift fix). Upbeat ducked score + voice leveling. -> `0008_why-are-there-no-more-einsteins.mp4`.
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR. No CTA text on the main video.
7. `upload.md`: title "Why Are There No More Einsteins?", description per FORMATS template (teaser hook that withholds the payoff, "what you'll learn" that intrigues without spoiling, honest-sourcing line, comment-bait "could you name a single living genius? try it", SOURCES from 01_script.md, hashtags), Education category, search-intent tags, synthetic-content disclosure.
8. **Thumbnails: produce 3 DISTINCT options for A/B testing** (one bold idea each, big caps, high contrast). Concepts: (a) Stan shrugging up at a giant Einstein silhouette + red "?", caps "WHERE'D THEY GO?"; (b) doodle-Einstein at the patent desk scribbling E=mc², caps "A CLERK DID THIS?"; (c) a glowing lineup Einstein/Newton/Da Vinci then a blank empty spot, caps "WHO'S NEXT?".

## Shorts (4 teasers — withhold the payoff, drive to the full video, end on Playedd logo + up-arrow + "FOR FULL BREAKDOWN")
Each ~15-25s, native 9:16 (`--portrait`), one idea per frame, Jack VO. Drip over the week+ after the main video.
1. **Name a living genius:** "Quick, name a living genius like Einstein. ...You can't, can you? Where did they go?" Tease (don't answer).
2. **The patent clerk:** "Einstein rewrote all of physics in ONE year, as a stalled patent clerk, in his spare time." Awe + tease "so why none now?"
3. **GPS:** "Your GPS would be wrong by 2km every day without a theory a bored clerk wrote for fun." Tease the bigger question.
4. **The twist:** "There are people as brilliant as Einstein alive right now. Here's why you'll never know their names." (do NOT reveal teams / burden-of-knowledge)

## Guardrails
- REGISTER: neutral + wonder, UPLIFTING landing. NEVER imply people got dumber. Keep the awe + the hopeful, slightly profound close.
- NOT a biography. Einstein's feats are the awe-setup; the episode is the "why none now / what about us" question (history + psychology).
- ACCURACY (see 01_script.md flags): 1905 papers (atoms/photoelectric=Nobel/relativity/E=mc²), patent clerk, thesis rejected; GPS ~2km/day; lone-genius partly a myth (but don't say Einstein "wasn't a genius"); burden of knowledge = Bloom 2020 (frame as research); genius = "partly genetic" (don't pin an exact %).
- Minimize em dashes. Critic pass on the final cut (hook in 2s, retention, clutter, Stan + Einstein consistency, captions) with specific fixes.
- Do NOT touch ep4 / ep5 / ep6 / ep7. Do NOT publish. Commit + push (conventional). If git complains about a lock: `rm -f .git/index.lock` first.
