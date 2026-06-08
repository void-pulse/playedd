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
- ONE bold idea per frame. A single clear visual metaphor, drawn big and centered. No second competing subject, no busy scene, no clutter.

Composition: horizontal 16:9 wide YouTube frame. Clean, centered, readable. Build the frame around the one idea with generous empty space. Do not crop the main object. Avoid glitches, broken anatomy, unreadable text, or messy overlapping clutter.

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
- **Main episode frames: 16:9 (landscape).** Configured in the script.
- **Shorts: native 9:16 (vertical), generated with the `--portrait` flag.** Don't crop landscape frames into vertical; generate vertical natively (ep4's short was reworked this way).
- Filenames: named by timestamp, zero-padded so they sort in order (e.g. `0007_0m07s.png`). This is what makes CapCut assembly trivial, drop them in filename order and they're already synced.

## Color & design direction
Keep the **subtle-color** direction: a bit more colorful and designed than bare black-on-white, while keeping the crude doodle identity. Thumbnails: bold solid background + selective pop color (the ep3 v3 level), not full rainbow; nudge slightly richer each time. In-video frames can carry a little more color and composition. An evolution up, not a restyle. Pair this with THE BAR above: more color, still one idea per frame.

> OPEN DECISION (Logan): these docs assume we KEEP the crude-doodle identity and enforce the one-bold-idea bar. If the wonder lane wants a more iconic, designed look (closer to Zenn), that's a restyle, say so and I'll rewrite this whole file. Also flagging: I read "--portrait" as "shorts stay native vertical," main stays 16:9. Correct me if you meant main frames go portrait.
