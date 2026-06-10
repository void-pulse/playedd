# Claude Code Worker Brief — Build ep11 (Why Are You Tired All the Time?)

Build ep11 end to end from the locked script, same pipeline as ep5–ep10. Episode dir: `episodes/0011_why-are-you-tired-all-the-time/`. Follow brand/STRATEGY.md, VOICE.md, IMAGE_STYLE.md, FORMATS.md, CHARACTER.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Features **Stan**. ~1,671 words to land ~7 min — do not trim.
- `02_storyboard.md` — visual anchors, one bold idea per frame.
- `00_idea.md` — context, register, myth-risk, the 4 teaser-short angles.

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed (50505).

## Main video steps (same as ep5–ep10)
1. `generate_audio.py` (Jack config, chunked by beat). LOCK audio before timestamping. **Target runtime ~7 min**; if the read lands under ~6:00 something got dropped — check.
2. Timestamp -> `narration.srt` + segments json. Proof captions (no em dashes; "twenty thousand"/"two out of three"/numbers clean; "first sleep"/"second sleep" intact; "social jetlag" spelled right).
3. Per-timestamp SCENE descriptions -> `04_scenes.json`, anchored to `02_storyboard.md`. Stan consistent; one bold metaphor per frame.
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate cluttered/broken frames (`--resume` to skip existing).
5. `assemble.py` (frame-exact timing). Ducked score + voice leveling, mood arc: curious/relatable -> two-clocks intrigue -> bright (light) -> the click of the reframe (social jetlag) -> warm/cozy (history) -> calm reassuring lift (button). -> `0011_why-are-you-tired-all-the-time.mp4`.
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR. No CTA text on the main video.
7. `upload.md`: title "Why Are You Tired All the Time?", **SHORT teaser-style description** (brand/FORMATS.md: opener withholds the answer; tease bullets; comment-bait "what time does YOUR afternoon crash hit — 3pm on the dot?"; SOURCES + AI-disclosure at bottom), Education category, search-intent tags, thumbnails (below).

## Thumbnails — produce 3 DISTINCT options for A/B (brand/FORMATS.md)
(a) Stan face-down asleep on a desk under a clock at 3:00, big caps "8 HOURS?!"; (b) Stan in bed at night, eyes wide, phone glow on his face, clock at 12:00, caps "WIDE AWAKE?"; (c) Stan drawn as a wind-up clock, an alarm clock yanking him by a string, caps "WRONG TIME ZONE?". One bold idea, big caps, high contrast each.

## Shorts (4 teasers — withhold payoff, drive to the FULL VIDEO)
Each ~15–25s, native 9:16 (`--portrait`), one idea per frame, Jack VO. **End card = Playedd logo + up-arrow + "FOR FULL BREAKDOWN" as the PRIMARY CTA** (the short's only job is to funnel to the full video; keep "FOR FULL BREAKDOWN" primary, no like-bait swap). Drip over the week+ after the main.
1. "You slept a full eight hours. So why are you a zombie by 3pm and wide awake at midnight? It's not the sleep." Tease.
2. "That 3pm crash isn't your lunch. It's a clock in your head, dimming the lights on purpose." Tease (don't name a fix).
3. "Every weekend you give yourself jet lag without leaving your house. Scientists even have a name for it." Tease (social jetlag, don't fully explain).
4. "Waking up at 3am used to be totally normal. People had a 'first sleep' and a 'second sleep.'" Tease (history).

## Guardrails
- REGISTER: neutral + wonder, **reassuring "you're not broken, you're out of sync"** landing. NOT health advice (reveal mechanism, never prescribe), NOT shaming, NOT doom. One light, responsible medical caveat only (weeks-long fatigue → doctor: thyroid/iron/apnea).
- ACCURACY: social jetlag "more than two out of three people" (don't say everyone); segmented sleep is DEBATED (script already hedges, keep it); afternoon dip "mostly your clock, not the sandwich"; caffeine "blocks the signal," doesn't erase tiredness; light "suppresses melatonin and delays" the clock.
- Minimize em dashes (script is already at zero). Critic pass on the final cut (hook in 2s + withholds, runtime ~7 min, retention, clutter, Stan consistency, captions) with specific fixes.
- Keep color words out of rendered label text; describe explicit dot-eyed faces (no "blank face").
- Do NOT touch ep4–ep10. Do NOT publish immediately — schedule per the Tue/Sat cadence. If git complains about a lock: `rm -f .git/index.lock` first. Report cost + runtime.
