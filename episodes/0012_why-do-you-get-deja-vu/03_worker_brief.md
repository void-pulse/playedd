# Claude Code Worker Brief — Build ep12 (Why Do You Get Déjà Vu?)

Build ep12 end to end from the locked script, same pipeline as ep5-ep11. Episode dir: `episodes/0012_why-do-you-get-deja-vu/`. Follow brand/STRATEGY.md, VOICE.md, IMAGE_STYLE.md (incl. the ANTI-PATTERNS), FORMATS.md, CHARACTER.md, SCRIPT_PLAYBOOK.md. Conventional commits; audio/images/mp4 gitignored.

## Inputs (in the episode dir)
- `01_script.md` — LOCKED narration (beats tagged). Stan used sparingly. ~1,750 words / ~7 min — do not trim.
- `02_storyboard.md` — visual anchors, one bold idea per frame.
- `00_idea.md` — context, register, myth-risk, 4 teaser-short angles. (If 00_idea.md isn't present, derive idea/thumbnail/short concepts from this brief + the storyboard.)

## Voice
ElevenLabs **Jack** `klOYed7ULfdFRLhrPHYE`, eleven_multilingual_v2, stability 0.50, style 0.05, similarity 0.80, speaker boost on, request stitching + fixed seed.

## Main video steps (same as ep5-ep11)
1. `generate_audio.py` (Jack config, chunked by beat). LOCK audio before timestamping. Target ~7 min; if under ~6:00, something dropped.
2. Timestamp -> narration.srt + segments json. Proof captions (no em dashes; "déjà vu"/"jamais vu" spelled right).
3. Per-timestamp SCENE descriptions -> 04_scenes.json, anchored to 02_storyboard.md. ONE bold idea per frame; obey IMAGE_STYLE anti-patterns (no cross-out-AND-restate; don't over-name Stan; plenty of pure-concept frames).
4. `generate_images.py` (fal-ai/gpt-image-2, STYLE_BLOCK). 16:9, timestamp-named. Regenerate cluttered/broken frames.
5. `assemble.py` (frame-exact timing). Ducked score + voice leveling; mood: eerie-curious -> grounded -> reassuring/wonder. -> `0012_why-do-you-get-deja-vu.mp4`.
6. End card = silent like/subscribe outro, lower-left only, center + top-right CLEAR. No CTA text on main.
7. `upload.md`: title "Why Do You Get Déjà Vu?", SHORT teaser-style description (opener withholds the answer; comment-bait "when's the last time déjà vu hit you?"; SOURCES + AI-disclosure at bottom), Education category, search-intent tags, thumbnails below.

## Thumbnails — 3 DISTINCT for A/B
(a) Stan + faint ghost-double, "BEEN HERE BEFORE?"; (b) brain with "FAMILIAR!" alarm + magnifier, "JUST A GLITCH?"; (c) past-life ghost beside a brain, "NOT A PAST LIFE?". One bold idea, big caps, high contrast.

## Shorts (4 teasers — withhold payoff, drive to FULL VIDEO)
Each ~15-25s, 9:16 (`--portrait`), Jack VO. **End card = logo + arrow "FOR FULL BREAKDOWN" as the PRIMARY CTA** (themed line optional bonus only).
1. "You walk into a new room and KNOW you've been there. You haven't. Why?" Tease.
2. "Say 'door' 30 times, it stops sounding real. That's déjà vu's evil twin." Tease.
3. "For centuries people thought déjà vu meant a past life. The truth is weirder." Tease.
4. "Déjà vu might be the feeling of your brain catching its own mistake." Tease.

## Guardrails
- REGISTER: neutral + wonder, reassuring landing. Do NOT endorse past lives / precognition / simulation (they're the head-fake). NOT alarming.
- The "brain fact-checking" (O'Connor) theory is the LEADING idea, not settled, frame as "most likely / points to."
- Medical caveat stays responsible: ordinary déjà vu is normal/healthy; only frequent/prolonged WITH other symptoms warrants a doctor. Don't imply normal déjà vu = epilepsy.
- Minimize em dashes. Critic pass (hook in 2s + withholds answer, ~7 min, clutter, anti-patterns, captions).
- Do NOT touch ep4-ep11. Do NOT publish. Commit + push (conventional; rm -f .git/index.lock if needed). Report cost + runtime.
