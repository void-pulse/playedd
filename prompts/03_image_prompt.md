# Prompt 03 — Scene Prompts (one per timestamp)

Use this AFTER you have the timestamped segments (`03_segments.json`, produced by `pipeline/parse_timestamps.py` from your TurboScribe export). Output goes in `04_scenes.json`.

This is the step that replaces the reference video's "Higgsfield skill." Instead of a black-box skill, Claude Code reads each timestamped line and writes a short scene description for it. `generate_images.py` then renders each scene through `fal-ai/gpt-image-2` with the locked style.

---

You are the storyboard artist for **Playedd**. You will be given a JSON array of timestamped narration segments. Read `brand/IMAGE_STYLE.md` so you know the visual language (crude MS-Paint stickman doodles).

For EACH segment, write a single **SCENE** description: a short, concrete description of one simple image that illustrates what the narrator is saying at that exact moment.

Rules for each scene:
- One clear visual idea per image. Simple enough to draw badly on purpose.
- Concrete and literal. "A stickman in a lab coat pouring liquid from one beaker to another, red question mark above his head." Not "the concept of scientific uncertainty."
- Match the emotion and meaning of that line. The image is a visual subtitle.
- Lean into the doodle medium's strength: visual gags, arrows, labels, simple symbols.
- If a short handwritten label would help (a name, a year, a place), specify the exact text, kept short and correctly spelled.
- Do NOT restate the style (white background, stickmen, etc.), that's added automatically. Only describe the SCENE content.
- Keep continuity: if a character or object recurs across nearby segments, describe it consistently.

Output **valid JSON only**, no prose, no markdown fences. Same length as the input array. Schema:

```json
[
  { "index": 1, "timestamp": "0:00", "seconds": 0.0, "scene": "..." },
  { "index": 2, "timestamp": "0:07", "seconds": 7.0, "scene": "..." }
]
```

INPUT SEGMENTS:
[paste contents of 03_segments.json]
