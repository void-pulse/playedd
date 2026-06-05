# Voice — ElevenLabs Setup

## Narration tone (the standard)
The read is dry, smart, and a little irreverent. Humor and wit are core, not optional. The best lines land as buttons, a beat after the setup. Don't mug for the joke; deliver it flat and let it hit.

- **POV:** "you're being played, here's how." Confident and knowing, never lecturing or preachy. You're letting the viewer in on something, not teaching a class.
- **Writing rule:** minimize em dashes. Overuse is an AI tell. Prefer periods, commas, or a restructured sentence.
- **Lead voice:** LOCKED to Drew (NARRATOR_D). This tone standard applies regardless; the words carry the wit, the voice just has to stay out of the way.

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

## Voice ID registry (fill in after you pick)
| Label | Voice name | Voice ID | Used for |
|---|---|---|---|
| NARRATOR_A | Keanan - Natural, Teacher | 2fe8mwpfJcqvj9RGBsC1 | Follow The Money, The Scam Explained |
| NARRATOR_B | Jason Jordan | RCvfNaeRVixdBMcmd2Wl | The Psychology Trick, Who Owns This |
| NARRATOR_C | Tyler Kurk | raMcNf2S8wCmuaBcyI6E | audition (ep 2) |
| NARRATOR_D | Drew | q0IMILNRPxOgtBTS4taI | **LOCKED channel lead voice** |
