# Formats & The Anti-Demonetization System

The most important strategy file in the repo. Read it before scaling past a few videos.

## What actually got channels killed in 2026
Not AI voice. Not AI images. Not automation. The terminations targeted *sameness*: every upload with the same cold open, same title formula, same thumbnail template, posted several times a day with no identifiable value. YouTube evaluates the channel as a whole and asks "what does this add that we don't already have ten thousand of." If the answer is nothing, it's gone.

So the system is built around deliberate variation plus real substance.

## The five pillars (rotate them)
Never run the same pillar twice in a row. Across any 5 uploads, hit at least 3 different pillars. Each has a different cold open and thumbnail cue, so rotation creates variation for free.

| Pillar | What it is | Cold open style | Thumbnail cue |
|---|---|---|---|
| Follow The Money | How a business or industry actually profits | "You think they make money on X. They don't." | Dollar sign + arrow to the real source |
| The Psychology Trick | The design built to get your wallet | "This was built to make you spend. Here's the trick." | Brain or eye + a price tag |
| The Scam, Explained | How a con actually works, step by step | "It looks legit. It isn't. Here's the mechanism." | Red "SCAM" stamp |
| Who Owns This | Concealed ownership and the illusion of choice | "You think you have a choice. You have one company." | Many logos collapsing into one |
| Hidden Cost | The real economics behind an everyday thing | "There's a reason it's this cheap / this expensive." | Everyday object + a magnifier |

## Episode format standard
The proven shape for this channel, going forward. Not a one-off.

- **Target length:** 6-9 minutes, trending longer over time toward deep-dive territory. Not 12 minutes yet, but heading that way.
- **Script length:** ~1,200-1,600 words.
- **Depth per beat:** researched specifics over vibes. Real numbers, named people, concrete detail. Every claim should be sourceable.
- **Humor is core, not garnish:** written-in jokes, wry asides, comedic buttons. Timing matters as much as the facts. The bar is a beat that both informs and lands a laugh.
- **Cut cadence:** fast, roughly one image every ~2.3 seconds. The assembler applies `SYNC_OFFSET_SEC = 0.25` globally so images land just after the words, not before (see `pipeline/assemble.py`).
- **Beat structure (keep this spine):** cold-open hook -> setup -> the turn -> human layer -> payoff -> "you got played" button.

### Production rule: lock the audio BEFORE TurboScribe
Finalize the narration read first: trim dead air, fix flubs, lock the performance. THEN run TurboScribe for timestamps. Tight source audio is what makes the downstream image sync tight; re-cutting audio after timestamping throws the whole image track out of sync.

### Title formula
A bold, counterintuitive claim with CAPS on the key words, kept consistent for branding. The title promises the "wait, what?" that the video pays off.

### Description template (every episode)
1. **Hook question** — a line or two that restate the counterintuitive promise.
2. **"What you'll learn"** — 3-5 bullets of the concrete payoffs.
3. **Credibility line** — a one-liner signaling real research ("you're being played, here's how").
4. **Comment-bait question** — invite a reply to feed engagement.
5. **SOURCES block** — the real citations (also the demonetization defense).
6. **Hashtags** — a short, relevant set.

## Rule 1 — Add the human layer (the moat)
Every script must contain at least one of: a non-obvious connection, a genuine "here's why this matters" beat, or a correction of a common myth. Mark it `[HUMAN LAYER]` in the script. It costs two sentences and it's the whole ballgame.

## Rule 2 — Vary the surface
- Titles: rotate at least 4 title structures. Not every title is "The TRUTH about X."
- Thumbnails: doodle style stays consistent; composition and color accents vary by pillar.
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
