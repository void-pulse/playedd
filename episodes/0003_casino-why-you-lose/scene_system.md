# Episode 0003 — Visual System (casino / why you lose)

The per-episode storyboard contract. Feeds `prompts/03` when writing `04_scenes.json`.
Keeps 245 frames consistent: same cast, same motifs, same safety rules.

## Base style
Inherits `brand/IMAGE_STYLE.md` (the STYLE_BLOCK is auto-prepended by
`pipeline/generate_images.py`). Crude MS-Paint doodle: thick wobbly black
outlines, flat fills, one clear subject per frame, mostly empty white space,
intentionally bad. Do NOT restate the base style inside a scene prompt; describe
only the SCENE content (plus the SAFETY clause below).

## Recurring cast (draw consistently every time)
- **The Player** — a small, hunched, round-headed everyman with worried dot
  eyes, usually seated at a slot machine. The "you" of the video.
- **The Slot Machine** — the villain. A tall boxy machine with a sly grinning
  face: three reel windows for a mouth, a lever like a cocked eyebrow, light
  bulbs around the frame. Looms larger than the Player.
- **The Host** — a smarmy suited figure with a too-wide grin and slicked hair,
  who appears holding a steak on a plate. Friendly on the surface, predatory.
- **Friedman** — a doodle professor with round glasses and a small mustache,
  holding a blueprint.
- **Roger Thomas** — a doodle designer holding something luxe (a chandelier, a
  gold frame, a champagne glass); the "playground" architect.

## Callback motifs (must recur identically)
- **(a) The maze** — Friedman's no-exit casino floor plan (tangled corridors of
  slot boxes, a red dashed line that dead-ends) in THE BUILDING. The SAME maze
  pattern is reused as the feed inside a phone screen in the BUTTON.
- **(b) The celebration** — the Slot Machine's win party (flashing bulbs, music
  notes, confetti, beaming face) is drawn IDENTICALLY for a real win and for the
  "loss disguised as a win." Only the Player's shrinking coin pile differs.
- **(c) The green zero** — a single flat-green roulette slot, drawn slightly
  oversized as a glowing sliver, recurs as a motif for the house's hidden edge.

## Real people = generic archetypes only (no likeness)
Friedman, Roger Thomas, Natasha Dow Schull, Steve Wynn, the Waterloo
researchers, and ANY real person named in the narration are drawn ONLY as
generic doodle archetypes (a professor with round glasses, a luxe designer with
a champagne glass, an anthropologist with a notebook, a researcher in a lab
coat). Never a likeness of the actual person, and never a name label in the
image. The narration says the name; the picture just shows the archetype.

## Color
Doodle-on-white by default. Selective pop color only: casino red (signage,
arrows, alarm), coin gold-green (money), roulette green (the zero sliver),
surveillance red (tracking/eyes). Use a split or flat color background only on
contrast/emphasis beats; most frames stay clean white.

## SAFETY (mandatory in every scene prompt)
- **No bare year labels and no floating numbers.** Any time reference is
  described plainly in the scene ("an old-timey scene", "decades ago"), never as
  a year, and never as a floating number/percentage. Use words, not digits.
- **No ambiguous flags, symbols, or insignia.** No national/political/military
  marks of any kind.
- **No weapons, guns, or depictions of violence.** Render "target/pinpoint/aim"
  metaphors as surveillance (cameras, a watching eye, a reticle) with NO weapon
  present.
- **Describe exactly what is drawn** — concrete objects and actions only, no
  abstractions for the model to invent.
- Each scene prompt ends with the clause:
  `No year text, no floating numbers, no flags or insignia; draw only what is described.`
