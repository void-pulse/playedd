# Formats & The Anti-Demonetization System

The most important strategy file in the repo. Read it before scaling past a few videos.

## What actually got channels killed in 2026
Not AI voice. Not AI images. Not automation. The terminations targeted *sameness*: every upload with the same cold open, same title formula, same thumbnail template, posted several times a day with no identifiable value. YouTube evaluates the channel as a whole and asks "what does this add that we don't already have ten thousand of." If the answer is nothing, it's gone.

So the system is built around deliberate variation plus real substance.

## The veins (rotate them)
The reset broadened the channel from five manipulation pillars to four wonder veins. Never run the same vein twice in a row. Across any 5 uploads, hit at least 3 different veins. Each has a different cold open and thumbnail cue, so rotation creates variation for free.

| Vein | What it is | Cold open style | Thumbnail cue |
|---|---|---|---|
| Deep Time | "Normal" is shockingly recent or invented | "For almost all of history, nobody ever did/said this." | One everyday thing + a strikethrough or a clock |
| Your Own Mind | A glitch or rule inside your own perception/memory | "Your brain is doing something right now you never noticed." | A head/eye + one bold question mark |
| Hidden Scale | You against the very large or very far | "This feels close. It isn't, and that changes everything." | Tiny figure dwarfed by one huge shape |
| Engineered Defaults (the money vein) | Why an everyday designed thing is the way it is, and who profits | "There's a reason it's exactly like this. It's not for you." | The object + an arrow to the real reason |

The old manipulation pillars (Follow The Money, The Psychology Trick, The Scam Explained, Who Owns This, Hidden Cost) all live inside **Engineered Defaults** now. They're sub-types of the money vein, not the channel's identity. Use them when a topic is genuinely about profit and design; reach for the other three veins for the wonder topics that carry reach.

## Episode format standard
The proven shape for this channel, going forward. Not a one-off.

- **Target length:** 6-9 minutes, trending longer over time toward deep-dive territory. Not 12 minutes yet, but heading that way.
- **Script length:** ~1,200-1,600 words.
- **Depth per beat:** researched specifics over vibes. Real numbers, named people, concrete detail. Every claim should be sourceable.
- **Humor is core, not garnish:** written-in jokes, wry asides, comedic buttons. Timing matters as much as the facts. The bar is a beat that both informs and lands a laugh.
- **Cut cadence:** fast, roughly one image every ~2.3 seconds. The assembler applies `SYNC_OFFSET_SEC = 0.25` globally so images land just after the words, not before (see `pipeline/assemble.py`).
- **Beat structure (keep this spine):** cold-open hook -> setup -> the turn -> human layer -> payoff -> wonder button (see brand/STORY.md). The button lands the idea, then cuts to the silent logo. No spoken sign-off.

### Hook-first rule (non-negotiable)
The first 2 seconds decide the video. Open inside the mystery, on the single most arresting line you have. No "in this video," no throat-clearing, no slow build. Every line after that must earn the next one: if a sentence doesn't open a loop or pay one off, cut it. Write the cold open last, after you know your strongest fact, and lead with it.

### End stamp / outro card
The main video ends on a silent **like-and-subscribe outro card** in the Playedd doodle style, held ~5-10s after narration. Logan adds the actual subscribe button and channel logo himself via YouTube's end screen, so the card MUST LEAVE THE CENTER AND TOP-RIGHT CLEAR: center is reserved for the subscribe/logo end-screen element, top-right for YouTube's recommended-video card. Put the doodle like/subscribe prompts in the left and lower-left area only. The old "YOU'RE BEING PLAYED" CTA is retired. Shorts: a brief like/subscribe doodle is fine (no end-screen reservation needed).

### Production rule: lock the audio BEFORE TurboScribe
Finalize the narration read first: trim dead air, fix flubs, lock the performance. THEN run TurboScribe for timestamps. Tight source audio is what makes the downstream image sync tight; re-cutting audio after timestamping throws the whole image track out of sync.

### Title formula
A bold, counterintuitive claim with CAPS on the key words, kept consistent for branding. The title promises the "wait, what?" that the video pays off.

### Description template (every episode)
1. **Hook question** — a line or two that restate the counterintuitive promise.
2. **"What you'll learn"** — 3-5 bullets of the concrete payoffs.
3. **Credibility line** — a one-liner signaling real research and honest sourcing (e.g. "every claim sourced below, including the parts the internet usually gets wrong").
4. **Comment-bait question** — invite a reply to feed engagement.
5. **SOURCES block** — the real citations (also the demonetization defense).
6. **Hashtags** — a short, relevant set.

## Rule 1 — Add the human layer (the moat)
Every script must contain at least one of: a non-obvious connection, a genuine "here's why this matters" beat, or a correction of a common myth. Mark it `[HUMAN LAYER]` in the script. It costs two sentences and it's the whole ballgame.

## Rule 2 — Vary the surface
- Titles: rotate at least 4 title structures. Not every title is "The TRUTH about X."
- Thumbnails: one bold idea per thumbnail (see IMAGE_STYLE.md); style stays consistent; composition and color accents vary by vein.
- Cold opens: never reuse the exact opening pattern back to back.
- Length: target 6-9 min (see Episode format standard below). Vary within that band; don't template the exact runtime.

## Rule 3 — Disclose, always
Check "Altered or synthetic content" in YouTube Studio on every upload, and add a synthetic-media note plus the real sources to every description. Free insurance.

## Rule 4 — Audit monthly
Pull your last 10 videos. Cover the channel name. If they feel like one voice but look varied, you're healthy. If they look like a content farm, fix it before YouTube does.

## Cadence ramp
Low-volume, high-production is the model (see CHANNEL.md). Depth beats frequency in this niche.
- Aim for ~1 strong, longer-form episode per week rather than 3 thin ones.
- Add volume only once the pipeline runs without babysitting and extra uploads don't cost depth, the human layer, or the humor. One great video outperforms three forgettable ones here.

## Cut rhythm / pacing
Cuts are dynamically tuned to the narration, not a fixed rate and not one image per caption. Speed up on fast, energetic, or list lines; hold longer on slow, heavy, or emphatic ones. Every image earns its place: enough coverage, no filler. Map the cut pacing to the voice's energy and meaning at the storyboard stage, fewer and longer shots where the voice lingers, quick cuts only where it's rattling.
