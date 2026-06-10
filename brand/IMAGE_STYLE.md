# Image Style — The Master Doodle Prompt

Model: **`fal-ai/gpt-image-2`** on fal.ai. GPT Image follows the "intentionally bad" instruction far better than Flux/diffusion models, and renders short handwritten labels correctly. This is the same model family the reference channel used, just accessed through your fal key.

This style block is prepended to every per-scene prompt automatically by `pipeline/generate_images.py` (it reads this file). Edit the style here, once, and every image inherits it.

## THE BAR: one bold idea per frame (the biggest upgrade)
This is the single most important image rule going forward. Each frame carries **ONE bold visual metaphor**, drawn big, iconic, high-contrast, and meaningful. Not a literal illustration of the sentence. Not a cluttered scene with five things happening.

- One idea per frame. If you can't name the single image in four words, it's too busy.
- Iconic over literal. "The sky with the word BLUE crossed out" beats "a person standing in a field under a sky next to a house."
- High contrast. The one idea should pop the instant it's on screen, readable at a glance on a phone.
- Meaningful. The metaphor should carry the point of the line, so the picture does work the narration doesn't have to.
- Empty space is a feature. Most frames stay clean and mostly empty around the one idea.

When the scene description (written per timestamp) is vague, force it to one metaphor before generating. A weak frame is almost always two ideas fighting; cut to one.

## Anti-patterns (avoid these) — Logan notes 2026-06-10
- **No redundant cross-out-AND-restate.** Don't X out a word and ALSO write its negation. The red X already means "not." Pick ONE: cross out the wrong word (e.g. "PROBLEM" with a red X), OR state the corrected idea in caps — never both saying the same thing. "PROBLEM" X'd out *plus* "NOT A PROBLEM" underneath is pure redundancy. Best of all: show the idea itself (a calm Stan sleeping peacefully at 3am) instead of a label negating a label.
- **Don't over-name or over-describe Stan.** Stan is the established recurring stickman (CHARACTER.md) and the STYLE_BLOCK already defines the look, so in scene descriptions just say "Stan" (or "the stickman") — you do NOT need the full "round-headed dot-eyed stickman" descriptor on every single frame, and not every frame needs him at all. Vary it; let plenty of frames be pure concept/object with no character. Naming/redrawing him every frame is overkill.

---

## STYLE_BLOCK (do not delete the markers; the script reads between them)

<!-- STYLE_BLOCK_START -->
The image style must look like a SIMPLE, CRUDE, hand-drawn cartoon — a quick doodle colored in flat, like a coloring-book page. It is amateur and simple on purpose. It is NEVER polished, NEVER 3D, NEVER rendered, NEVER glossy, NEVER realistic.

Use a simple stickman / childish cartoon style, colored in flat:
- COLOR THE WHOLE SCENE with flat fills. Give the moment a simple colored setting that fits it (a flat blue sky, a flat green ground or hill, a flat-colored room or floor, a flat night sky). Do NOT leave the subject floating on empty white — but keep the setting SIMPLE: one or two flat color areas plus a simple horizon or ground line, drawn crudely. No detailed scenery, no texture, no depth, no perspective.
- Objects are FULLY colored with flat color fills and thick black outlines (not line-art with a single red accent anymore).
- Thick, uneven, wobbly hand-drawn black outlines on everything.
- Stick-figure humans: round heads, line bodies, dot eyes, very basic expressions. A simple recurring stickman everyman can appear in the scene living the idea.
- FLAT COLORS ONLY. This is the most important rule: no shading, no gradients, no highlights, no soft lighting, no 3D, no realistic rendering. Keep every shape flat and simple like a crude hand-drawn cartoon. If it starts to look smooth, glossy, dimensional, or like a real illustration, it is WRONG.
- No Disney, no anime, no Pixar, no polished vector art, no professional illustration, no 3D render.
- Simple flat backgrounds and settings only: a flat color, a simple ground or horizon line, and a few crude shapes (sun, clouds, hills, walls, floor). Never detailed or textured.
- Flat color palette: green, brown, gray, red, yellow, orange, blue, and simple flats as needed.
- Use red arrows or red question marks to point things out when helpful.
- Handwritten text only when it helps; short, correctly spelled, easy to read, in big bold black caps.
- Build everything from basic shapes: circles, rectangles, arrows, boxes, signs, screens, stickmen, question marks.
- ONE bold idea per frame: a single clear subject or moment, drawn big in a simple colored setting. Color and a simple background are good, but NO second competing subject and NO busy clutter.

Composition: horizontal 16:9 wide YouTube frame. Place the one idea clearly with a simple colored setting around it. Do not crop the main subject. Avoid glitches, broken anatomy, unreadable text, or messy clutter.

The drawing should feel hand-made, simple, and a little crude — colored in flat like a coloring book. Keep it SIMPLE and FLAT. Do NOT make it look polished, smooth, dimensional, 3D, or professional. That is the entire point.
<!-- STYLE_BLOCK_END -->

---

## How a final per-image prompt is assembled
`generate_images.py` builds each prompt as:

```
[STYLE_BLOCK]

SCENE: <the scene description for this timestamp, written by Claude Code from the script>
```

So the style is constant and only the SCENE line changes per timestamp. Consistency for free.

## Output spec
- **Main episode frames: 16:9 (landscape).** Configured in the script.
- **Shorts: native 9:16 (vertical), generated with the `--portrait` flag.** Don't crop landscape frames into vertical; generate vertical natively (ep4's short was reworked this way).
- Filenames: named by timestamp, zero-padded so they sort in order (e.g. `0007_0m07s.png`). This is what makes CapCut assembly trivial, drop them in filename order and they're already synced.

## Color & design direction (UPDATED — colored/scene look, LOCKED IN)
We moved from "white background + one pop of color" to a **fully-colored, simple-scene** look (Zenn-inspired, but kept crude and flat). Every frame is colored in like a coloring book; the subject sits in a simple flat colored setting; still ONE bold idea per frame; still crude stickmen. The hard guardrail: **NO 3D, NO shading, NO gradients, NO polish** — if it looks smooth/dimensional/rendered, it's wrong. Thumbnails: bold and colorful, big caps + black outline (ep5 / casino level). Adopted after the ep5/casino tests; first used on the NEXT video (ep5 already shipped on the old style — don't re-render it).

> TO REVERT to the old crude white-background style: paste the block from **"## Previous style block (archived for revert)"** at the bottom of this file back between the STYLE_BLOCK markers above (or `git show <pre-restyle-commit>:brand/IMAGE_STYLE.md`).

Output format unchanged: main frames 16:9, shorts native 9:16 (`--portrait`).

---

## Previous style block (archived for revert)
The crude, mostly-white-background "MS Paint" style we used through ep5. To go back, paste the text below back between the `STYLE_BLOCK_START` / `STYLE_BLOCK_END` markers above.

```
The image style must look like an extremely simple beginner drawing made in MS Paint, drawn quickly by hand by someone who is not good at drawing.

Use a simple stickman / childish drawing style:
- Clean white or off-white background by default; when a scene calls for it, a flat solid-color background or a simple split two-tone background is allowed (keep it flat, no gradients)
- Thick, uneven black outlines
- Wobbly, hand-drawn lines
- Stick-figure humans: round heads, line bodies, dot or small-circle eyes
- Very basic facial expressions
- Flat colors only, no shading, no gradients; flat color fills may be used a bit more liberally to make a frame pop, but most frames still read clean and mostly empty
- No 3D, no cinematic lighting, no realistic rendering
- No Disney, no anime, no polished vector art, no professional illustration
- No detailed backgrounds, no textures; keep backgrounds simple and flat (empty, or one solid / split color)
- Flat accent colors: green, brown, gray, red, yellow, orange, blue
- Use red arrows or red question marks to point things out when helpful
- Handwritten text only when it helps explain the idea; if text appears it must be short, correctly spelled, and easy to read
- Build everything from basic shapes: squares, circles, rectangles, arrows, boxes, simple tables, signs, screens, stickmen, question marks
- ONE bold idea per frame. A single clear visual metaphor, drawn big and centered. No second competing subject, no busy scene, no clutter.

Composition: horizontal 16:9 wide YouTube frame. Clean, centered, readable. Build the frame around the one idea with generous empty space. Do not crop the main object. Avoid glitches, broken anatomy, unreadable text, or messy overlapping clutter.

The drawing should feel amateur, funny, and intentionally bad, like a noob made it in Paint in thirty seconds. Do NOT make it look good, polished, or professional. That is the entire point.
```
