# Workflow — How to Make One Video

Eight steps. Once the pipeline is warm, a video is roughly 20–40 minutes of your time, most of it the CapCut assembly and a quality pass on the script.

## 0. One-time setup (do once)
```bash
cd playedd
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste in FAL_KEY and ELEVENLABS_API_KEY
```
Then audition voices in ElevenLabs (see brand/VOICE.md) and paste the voice IDs into
`pipeline/generate_audio.py` (VOICE_IDS) and the VOICE.md registry.

## 1. Idea
In Claude Code: run `prompts/01_idea_generation.md`. Pick one. Then scaffold:
```bash
python pipeline/new_episode.py "short-topic-slug"
```
Drop the chosen idea into `episodes/<ep>/00_idea.md`.

## 2. Script (humanized)
In Claude Code: run `prompts/02_script_writing.md` with the idea. Save narration to
`episodes/<ep>/01_script.md`. **Read it out loud once.** Fix anything that doesn't sound
like a person. Confirm the `[HUMAN LAYER]` beat is real and the SOURCES are real.

## 3. Audio
```bash
python pipeline/generate_audio.py episodes/<ep>/01_script.md --voice NARRATOR_A
```
Produces `audio/narration.mp3`. (Alternate NARRATOR_A / NARRATOR_B by pillar.)

## 4. Timestamps (TurboScribe)
Upload `narration.mp3` to TurboScribe, export **SRT**, save it as
`episodes/<ep>/02_narration.srt`.
> Pro move once you trust the pipeline: run step 3 with `--with-timestamps` and skip
> TurboScribe entirely, ElevenLabs returns the alignment itself.

## 5. Parse
```bash
python pipeline/parse_timestamps.py episodes/<ep>/02_narration.srt --merge-short 1.5
```
Produces `03_segments.json`. `--merge-short` stops you paying for images that flash by.

## 6. Scene prompts
In Claude Code: run `prompts/03_image_prompt.md`, paste in `03_segments.json`.
Save the JSON it returns as `episodes/<ep>/04_scenes.json`.

## 7. Images
```bash
python pipeline/generate_images.py episodes/<ep>/04_scenes.json --resume
```
Produces `images/0001_0m00s.png ...`, one per timestamp, named so they sort in order.
Re-run with `--resume` to retry failures, or `--only N` to redo one frame.

## 8. Assemble in CapCut
- New 16:9 project. Drop `narration.mp3` on the audio track.
- Select all images, add to timeline **in filename order** (they're pre-sorted).
- Each image's filename tells you its start second. Snap each image's start to the next
  image's timestamp, exactly like the reference video. Add a subtle zoom (Ken Burns) if
  you want motion; optional.
- Add captions (CapCut auto-captions from the audio), an intro card, and a thumbnail.
- Export 1080p.

## 9. Publish (do not skip the compliance bits)
- Upload. **Check "Altered or synthetic content."**
- Description: one synthetic-media disclosure line + the real SOURCES from the script.
- Title + thumbnail per the pillar's variation rules (FORMATS.md). Don't reuse last video's pattern.

## 10. Archive
```bash
make archive EP=episodes/<ep>
```
Zips the finished episode (script, audio, images, json) to `_archive/` outside git, since
media is gitignored. Then commit the text artifacts.
```bash
git add -A && git commit -m "ep <NNNN>: <title>" && git push
```
