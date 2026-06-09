# Claude Code Worker Brief — Build ep7 (Why Do You Procrastinate?)

Build ep7 end to end from the locked script, same pipeline as ep5/ep6. Episode dir: `episodes/0007_why-do-you-procrastinate/`. Follow brand/STRATEGY.md, VOICE.md, IMAGE_STYLE.md, FORMATS.md, CHARACTER.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Features **Stan**.
- `02_storyboard.md` — visual anchors, one bold idea per frame, Stan consistent.
- `00_idea.md` — context, register, myth-risk, the 4 teaser-short angles.

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed.

## Main video steps (same as ep5/ep6)
1. `generate_audio.py` (Jack config, chunked by beat). LOCK audio before timestamping.
2. Timestamp -> `narration.srt` + segments json. Proof captions (spelling, segmentation, no em dashes).
3. Per-timestamp SCENE descriptions -> `04_scenes.json`, anchored to `02_storyboard.md`. Stan visually consistent every frame (brand/CHARACTER.md). One bold metaphor per frame.
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate cluttered/broken/off-model-Stan frames.
5. `assemble.py` (frame-exact timing; the ep5 drift fix). Upbeat ducked score + voice leveling. -> `0007_why-do-you-procrastinate.mp4`.
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR. No CTA text on the main video.
7. `upload.md`: title "Why Do You Procrastinate?", description per FORMATS template (hook, what-you'll-learn that teases without spoiling, honest-sourcing line, comment-bait "what are you procrastinating on right now?", SOURCES from 01_script.md, hashtags), Education category, search-intent tags, synthetic-content disclosure, thumbnail "NOT LAZY?" (Stan avoiding the deadline).

## Shorts (4 teasers — withhold the payoff, drive to the full video, end on Playedd logo + up-arrow + "FOR FULL BREAKDOWN")
Each ~15-25s, native 9:16 (`--portrait`), one idea per frame, Stan featured, Jack VO. Drip over the week+ after the main video.
1. **The differentiator:** Stan busy-avoiding; "if you feel guilty doing everything BUT the task, you're not lazy, you're procrastinating, and it's the opposite of lazy." Tease.
2. **It's emotional:** "you're not avoiding the work, you're avoiding the FEELING the work gives you." Tease.
3. **Akrasia / the Greeks:** "the ancient Greeks were obsessed with why you do this. they had a word for it." Tease.
4. **The backwards fix:** "the #1 science-backed fix for procrastination is the opposite of what everyone tells you." (do NOT reveal it's self-forgiveness)

## Guardrails
- REGISTER: neutral + wonder, reassuring via mechanism. NEVER shame. Core beat: guilt makes it worse; payoff = self-forgiveness + shrinking the task, not discipline.
- DIFFERENTIATE from ep6 (Lazy): lazy = energy conservation, content doing nothing; procrastination = emotional avoidance, wants to do it, feels terrible. Do NOT reuse the sloth/monk/factory history; this one is akrasia + the Latin word (pro + cras = "to tomorrow").
- ACCURACY: Sirois & Pychyl 2013 (mood-repair); akrasia (Socrates/Aristotle); etymology pro+cras; Wohl/Pychyl/Bennett 2010 (self-forgiveness, 119 students). Say procrastinators are "often" perfectionists, not always. Don't oversell self-forgiveness as a guaranteed cure ("closest thing to a cure").
- Minimize em dashes. Critic pass on the final cut (hook in 2s, retention, clutter, Stan consistency, captions) with specific fixes.
- Do NOT touch ep4 / ep5 / ep6. Do NOT publish. Commit + push (conventional). If git complains about a lock: `rm -f .git/index.lock` first.
