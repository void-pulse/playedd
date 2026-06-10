# Claude Code Worker Brief — Build ep10 (Where Do Your Thoughts Come From?)

Build ep10 end to end from the locked script, same pipeline as ep5-ep9. Episode dir: `episodes/0010_where-do-your-thoughts-come-from/`. Follow brand/STRATEGY.md, VOICE.md, IMAGE_STYLE.md, FORMATS.md, CHARACTER.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Features **Stan**. Written LONGER (~1,750 words) to land ~7 min — do not trim.
- `02_storyboard.md` — visual anchors, one bold idea per frame.
- `00_idea.md` — context, register, myth-risk, the 4 teaser-short angles.

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed.

## Main video steps (same as ep5-ep9)
1. `generate_audio.py` (Jack config, chunked by beat). LOCK audio before timestamping. **Target runtime ~7 min**; if the read lands under ~6:00 something got dropped — check.
2. Timestamp -> `narration.srt` + segments json. Proof captions (no em dashes; "forty-seven percent"/numbers clean; "by heart" intact).
3. Per-timestamp SCENE descriptions -> `04_scenes.json`, anchored to `02_storyboard.md`. Stan consistent; one bold metaphor per frame.
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate cluttered/broken frames.
5. `assemble.py` (frame-exact timing). Ducked score + voice leveling, mood arc: curious -> unsettling (Libet) -> playful (history) -> calm/liberating. -> `0010_where-do-your-thoughts-come-from.mp4`.
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR. No CTA text on the main video.
7. `upload.md`: title "Where Do Your Thoughts Come From?", **SHORT teaser-style description** (brand/FORMATS.md: opener withholds the answer; tease bullets; comment-bait "what random thought just popped into your head?"; SOURCES + AI-disclosure at bottom), Education category, search-intent tags, thumbnails (below).

## Thumbnails — produce 3 DISTINCT options for A/B (brand/FORMATS.md)
(a) Stan + thought bubble from a "?" cloud, "WHO SENT THAT?"; (b) Stan's head with a mail-slot, thought-letter sliding out, "YOU DIDN'T WRITE IT?"; (c) brain in a trash can beside a heart on a pedestal, "WRONG ORGAN?". One bold idea, big caps, high contrast each.

## Shorts (4 teasers — withhold payoff, drive to the FULL VIDEO)
Each ~15-25s, native 9:16 (`--portrait`), one idea per frame, Jack VO. **End card = Playedd logo + up-arrow + "FOR FULL BREAKDOWN" as the PRIMARY CTA** (the short's job is to funnel to the full video; a themed line is optional bonus, but do NOT replace "FOR FULL BREAKDOWN" with like-bait — that drifted on ep9, keep it primary here). Drip over the week+ after the main video.
1. "Guess your next thought before you think it. You can't. So who's sending them?" Tease.
2. "Don't think of a white bear. ...Can't, right? You can't even stop a thought." Tease.
3. "Your mind wanders ~47% of your life on thoughts you never chose." Tease.
4. "The Egyptians threw the brain in the trash. They thought you think with your heart." Tease.

## Guardrails
- REGISTER: neutral + wonder, gently LIBERATING landing (you're not your thoughts; you choose what to act on). NOT nihilistic, NOT "no free will," NOT woo. Keep concrete.
- LIBET accuracy: debated, simple-movements-only, include Libet's own "veto"/free-won't caveat. Do NOT conclude free will is disproven.
- Minimize em dashes. Critic pass on the final cut (hook in 2s, runtime ~7 min, retention, clutter, Stan consistency, captions) with specific fixes.
- Do NOT touch ep4-ep9. Do NOT publish. Commit + push (conventional). If git complains about a lock: `rm -f .git/index.lock` first. Report cost + runtime.
