# Image Style — The Master Doodle Prompt

Model: **`fal-ai/gpt-image-2`** on fal.ai. GPT Image follows the "intentionally bad" instruction far better than Flux/diffusion models, and renders short handwritten labels correctly. This is the same model family the reference channel used, just accessed through your fal key.

This style block is prepended to every per-scene prompt automatically by `pipeline/generate_images.py` (it reads this file). Edit the style here, once, and every image inherits it.

---

## STYLE_BLOCK (do not delete the markers; the script reads between them)

<!-- STYLE_BLOCK_START -->
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

Composition: horizontal 16:9 wide YouTube frame. Clean, centered, readable. Do not crop important objects. Leave breathing room. Avoid glitches, broken anatomy, unreadable text, or messy overlapping clutter.

The drawing should feel amateur, funny, and intentionally bad, like a noob made it in Paint in thirty seconds. Do NOT make it look good, polished, or professional. That is the entire point.
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
- Aspect ratio: 16:9 (landscape). Configured in the script.
- Filenames: named by timestamp, zero-padded so they sort in order (e.g. `0007_0m07s.png`). This is what makes CapCut assembly trivial, drop them in filename order and they're already synced.
