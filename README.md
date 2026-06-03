# Playedd

A content pipeline for a faceless YouTube channel: crude hand-drawn explainers about how the world is quietly getting you, scams, hidden business models, pricing and psychology tricks, and who really profits. Built to ship fast **and** survive YouTube's inauthentic-content enforcement, which is the part most "copy this faceless channel" tutorials ignore and the reason channels got mass-terminated in early 2026.

The defense is baked in: genuinely researched, point-of-view content (not templated slop), rotating formats, real sources, and synthetic-content disclosure. See `brand/FORMATS.md`. Tagline: "you're being played. here's how."

## The stack
| Step | Tool |
|---|---|
| Ideas + scripts + scene prompts | Claude Code (prompts in `prompts/`) |
| Voiceover | ElevenLabs (`pipeline/generate_audio.py`) |
| Timestamps | TurboScribe (or ElevenLabs alignment) → `pipeline/parse_timestamps.py` |
| Images (one per timestamp) | fal.ai `gpt-image-2` (`pipeline/generate_images.py`) |
| Assembly | CapCut |

One image per timestamp, named by timestamp, so CapCut assembly is drag-drop-in-order. Same technique as the reference channel, but the image engine is fal's GPT Image 2 (better at the intentionally-crude style and at rendering labels) instead of Higgsfield.

## Quickstart
```bash
# 1. install fal + deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. keys
cp .env.example .env     # paste FAL_KEY and ELEVENLABS_API_KEY

# 3. pick voices (brand/VOICE.md), paste IDs into pipeline/generate_audio.py

# 4. open this folder in Claude Code and paste claude/KICKOFF.md
```
Then follow `docs/WORKFLOW.md` to make a video.

## Installing fal (the image engine)
fal.ai is API-only, there's nothing to "install" beyond the client library, which `requirements.txt` already pulls in (`fal-client`). The only setup is the key:
1. Go to https://fal.ai/dashboard/keys and create an API key.
2. Put it in `.env` as `FAL_KEY=...` (you've already funded the account with auto top-up, so you're done).
3. The scripts read `FAL_KEY` from the environment automatically.

That's the whole install. No CLI, no Discord, no browser automation. (If you ever want the optional `fal` CLI for poking at models, `pip install fal`, but the pipeline doesn't need it.)

## Repo map
```
brand/      what the channel is, formats, voice, image style  (read these)
prompts/    the three Claude prompts: idea -> script -> scene prompts
pipeline/   the python engine (audio, timestamps, images, new episode)
episodes/   one folder per video (media is gitignored)
claude/     CLAUDE.md context + KICKOFF.md paste prompt
docs/        WORKFLOW.md, the per-video SOP
```

## Cost per video (rough)
- Images: ~100 × $0.04 = ~$4 (gpt-image-2 medium). Use `flux/schnell` to cut it lower while testing.
- Audio: ElevenLabs character quota; a 10-min script is ~1,400 words.
- So a video is a few dollars of API plus your time. The constraint is quality and variety, not cost.

## The one thing to internalize
The pipeline is the easy part. The channel lives or dies on (1) genuinely good, sourced, surprising scripts and (2) not looking like a content farm. Don't let the automation tempt you into daily identical uploads. That's the exact pattern that gets channels deleted. Ship 3 good, varied videos a week before you even think about daily.
