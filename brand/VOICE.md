# Voice — ElevenLabs Setup

## Narration tone (the standard)
The read is curious, smart, and quietly amazed. The driving feeling is wonder, the "wait, what?" of seeing something ordinary turn strange. Humor and wit are still core, not optional, but the cynicism is gone. We're not sneering at how the world cons you; we're handing the viewer a fact that rearranges their day. The best lines still land as buttons, a beat after the setup. Don't mug for the joke or the awe; deliver it flat and let it hit.

- **POV:** "the hidden why." Confident and knowing, never lecturing or preachy. You're letting the viewer in on something fascinating, the thing they walked past ten thousand times and never questioned. Curiosity, not contempt.
- **Writing rule:** minimize em dashes. Overuse is an AI tell. Prefer periods, commas, or a restructured sentence.
- **Honesty as voice:** when a popular version of a fact is overstated or wrong, say so on the record and give the truer, stranger version. The correction IS the wit and the moat (see the sky/blue episode: "you'll hear people say they couldn't see blue. that's not true, and the real answer is better").
- **Lead voice:** currently Drew (NARRATOR_D) as default, but this is now UNDER TEST, not locked (see Voice test below). The tone standard applies regardless of voice; the words carry the wonder and the wit, the voice just has to stay out of the way.

## Emotional register: neutral + wonder (the Zenn rule)
The only feeling we leave is "huh, that's amazing." Zenn's videos are emotionally neutral and pure wonder. They never push the viewer's feelings and never make anyone feel bad. We copy that exactly.

- Spark curiosity and awe. Do NOT play with the viewer's self-esteem in either direction. No insecurity bait, no therapy, no pep talks, no flattery. All of those are still "making them feel something about themselves," which is off-target.
- If a topic brushes something personal (looks, intelligence, money, memory, death), treat it as a fascinating fact about how the world or the brain works, watched from a calm, curious distance. Take the "you" out of the wound and put it into the wonder.
- Never upset the viewer. If a framing could make someone feel judged or insecure, reframe it until it is simply interesting. When in doubt, neutral.
- Titles obey the same rule: a curious question, never one that presupposes a bad feeling. "Why you don't look like your photos" (curious), not "why you hate photos of yourself" (emotional).

## Voice test (DO THIS before locking ep5+)
The reset opens the lead voice back up. Run a real A/B on the same passage (use a meaty paragraph from the sky/blue script) across:
1. **2-3 conversational ElevenLabs voices** from the "to test" list below. Conversational, not news-anchor; the wonder read needs warmth and small pauses.
2. **Logan's own recorded voice.** This matters twice over: it usually sounds more natural than any TTS, and a real human voice sidesteps YouTube's "inauthentic/AI-generated content" monetization flag, which is the single biggest demonetization risk for a faceless channel in 2026.
Keep whichever retains best. If Logan's voice is even close, lean human, the monetization safety alone is worth it.

## The honest take on "ElevenLabs gets you demonetized"
It doesn't. AI voice alone is fine and stays monetizable. What gets flagged is recycling the *exact same* preset over identical templated videos with no added value. The fix isn't avoiding ElevenLabs, it's (a) not using the one voice every AI channel uses, (b) varying delivery, (c) adding real substance. See FORMATS.md.

## Voices to AVOID (overexposed, instant "AI channel" tell)
Aaron, Adam, Rachel, Bella, Antoni, Josh-default. These are the most-used library voices on faceless channels. Using them is sonic camouflage in reverse, it makes you sound like the herd that's getting culled.

## Voices to test (less common, good for narration)
Pull these from the Voice Library, audition with a real paragraph of your script, and keep the 2–3 that fit the channel's slightly-wry, curious tone. Names drift in the library, so verify and copy the voice IDs into the table below.

- **David / British Storyteller** — sophisticated long-form narration, good for "The Scam, Explained" and "Hidden Cost" mood.
- **Bill L. Oxley** — warm documentary read, good default narrator.
- **James** — works well for historical/documentary content.
- **David Castlemore** — mystery/thriller energy, good for the "Scam, Explained" and "Who Owns This" mood.
- **Amelia** — if you want a female narrator for variety; expressive, audiobook-grade.

Run **two narrators** minimum and alternate by pillar. Two distinct voices across the channel is itself part of the variation that keeps you clean, and it lets you A/B which one retains better.

## Settings (paste into pipeline/generate_audio.py config)
Tuned for natural, non-robotic narration:

- **Model:** `eleven_multilingual_v2` for stable long-form narration. Use `eleven_v3` only when you want scripted emotional beats via audio tags (it's more expressive but less predictable on long reads).
- **Stability:** 0.40 (range 35–45%). Lower = more natural variation; below 30% gets unstable.
- **Similarity boost:** 0.80 (range 75–80%). Higher over-enunciates into "news anchor."
- **Style:** 0.15 (range 10–50%). Keep low for narration; raise only for punchy short lines.
- **Speaker boost:** on.

## Make it sound human (script-side, also enforced in prompts/02)
- Write the way you'd say it out loud. Short sentences. Fragments are fine.
- Use punctuation to control pacing: periods for beats, commas for flow.
- Avoid stacks of clauses the voice has to sprint through.
- Generate in scene-sized chunks, not one 1,500-word block, so pacing stays controlled.

## ep5 render config (consistency-tuned)
Voice **Jack (klOYed7ULfdFRLhrPHYE)**. Model `eleven_multilingual_v2`. Stability **0.50**, Style **0.05**, Similarity **0.80**, Speaker Boost **on**. Generate in scene-sized chunks with **request stitching** (pass previous/next text) and a **fixed seed** for the whole episode so tone does not drift chunk to chunk. This is the consistency fix; the voice is secondary to the method.

## Voice ID registry (fill in after you pick)
| Label | Voice name | Voice ID | Used for |
|---|---|---|---|
| NARRATOR_A | Keanan - Natural, Teacher | 2fe8mwpfJcqvj9RGBsC1 | Follow The Money, The Scam Explained |
| NARRATOR_B | Jason Jordan | RCvfNaeRVixdBMcmd2Wl | The Psychology Trick, Who Owns This |
| NARRATOR_C | Tyler Kurk | raMcNf2S8wCmuaBcyI6E | audition (ep 2) |
| NARRATOR_D | Drew | q0IMILNRPxOgtBTS4taI | prior default, now unlocked (under review) |
| NARRATOR_E | Jack | klOYed7ULfdFRLhrPHYE | **ep5 lead voice (testing)** |
