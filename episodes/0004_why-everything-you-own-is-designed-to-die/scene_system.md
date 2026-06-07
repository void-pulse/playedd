# Episode 0004 — Visual System (planned obsolescence / why everything dies)

The per-episode storyboard contract. Feeds `prompts/03` when writing `04_scenes.json`.
Keeps all frames consistent: same cast, same registers, same safety rules.

## Base style
Inherits `brand/IMAGE_STYLE.md` (STYLE_BLOCK auto-prepended by `generate_images.py`).
Crude MS-Paint doodle: thick wobbly black outlines, flat fills, one clear subject per
frame, intentionally bad. Horizontal 16:9. Do NOT restate the base style inside a scene
prompt; describe only the SCENE content, its register's background, and the SAFETY clause.

## Look & feel — BRIGHT, subtle color, light definition (no dark anywhere)
The whole episode is **bright and light**. **NO black or dark backgrounds anywhere** — no dark
cold open, no moody/low-key frames, ever. Trend a bit more colorful and designed than bare
black-on-white, while keeping the crude doodle identity.

**Keep background color SUBTLE and muted — avoid super-bold, super-saturated color fields.**
A key beat can use **either** a soft, muted solid tint **or** a **simple suggested scene with
light definition** (a floor line, a hint of a room / table / counter / window / car interior),
drawn doodle-simple in **subtle, muted colors** — NOT a loud flat field. Vary it: some frames
clean-and-light, some a soft tint, some a simple suggested setting. Lean subtle over loud.

## Visual registers (every scene picks exactly one)
1. **BRIGHT DOODLE** — the default. A clean white / very-light background with **generous flat
   color fills** (more color than sparse black-on-white): colored clothes, props, accents.
   Doodle-on-light. The large majority of frames.
2. **DESIGNED BEAT** — a richer, more composed frame for the punch beats (the **opening hook**,
   the **Phoebus cartel reveal**, the **car-feature subscription payoff**, a few other big
   turns). Give it more than the default: **either** a **soft, muted solid tint** background
   **or** a **simple suggested scene with light definition** (a hint of a boardroom, a counter,
   a car interior — a few simple doodle elements, not a detailed/busy room), in **subtle muted
   colors**, plus ONE selective pop color. Still crude doodle linework, always bright/light.
   **Avoid super-bold saturated color fields** (the earlier loud orange/red/yellow read too
   strong) — keep it soft and a touch designed. Do NOT use heavy solid-black silhouettes. Keep
   DESIGNED BEATS sparing so they stay special.

## HARD RULE — every frame is a specific, meaningful visual
Every frame must be a concrete, meaningful image for ITS narration beat — a visual the viewer
could not get from any other line. **No boring, generic, or filler frames. No placeholders.**
If a beat has no strong visual idea on its own, either (a) design a real, specific one, or
(b) plan to HOLD the previous meaningful image across that beat. Never ship a vague frame.

## Setting (anchor every scene)
This episode's world is **the everyday world of the things you own** — home desk, kitchen,
driveway, garage, and the products themselves. Home/everyday IS on-setting here. The other
recurring place is the **conspiratorial boardroom** for the cartel beats (drawn bright, bold
bg). When abstract, default to the Owner at home with his stuff (BRIGHT DOODLE).

## Recurring cast (draw consistently every time)
- **The Owner ("you") — CANONICAL MODEL, pin to `images/0001_0m00s.png`.** A big plain round
  bald head (a clean circle, no hair, no neck), two simple dot eyes with short eyebrows, and a
  small simple mouth (neutral, or a frown/grimace as the beat needs). A thin single-line stick
  body with thin stick limbs and simple mitt hands (no individual fingers). Proportions: a
  large head on a small stick body (head ≈ a bit taller than the torso). Always the SAME model
  — never restyle, age, hair, or re-proportion him. He is the "you" of the video.
- **The Phone** — a simple rectangular smartphone. Failing: sad sweating face, loading swirl,
  near-empty red battery, stutter/lag lines. Generic, NO brand logo.
- **The Immortal Light Bulb** — a classic round bulb, glowing coil filament, tiny content
  smile; the "lasts forever" hero (Livermore bulb). The yellow through-line, origin to payoff.
- **The Cartel** — a ring of identical old-timey businessmen (suits, bowler/top hats) around a
  round table, conspiring over a light bulb. Drawn as outlined doodle figures (gray suits, not
  solid-black silhouettes) so the frame stays bright. Generic archetypes, no likeness, no name
  labels.
- **The Trick ("the idea") — RECURRING villain, fixed design, pin to `images/0005_0m12s.png`.**
  A small green imp: pointy ears, a wide sly grin with little teeth, mischievous dot eyes, often
  holding a wrench. He IS "the idea that keeps learning" — the personification of planned
  obsolescence. Recurs at: the phone-slowdown decision (pushing the SLOW lever), and the HUMAN
  LAYER "it learned to lock / its cleverest move of all" beats (sabotaging the printer, the
  car). Same green imp every time; do not redesign him.
- **The Printer** — a sly-faced desktop printer flashing a red "INK?" error. Generic, NO logo.
- **The Paywall Car** — a generic car with a padlock on the heated seat + a coin-slot meter.
  NO brand logo. (Lives in the DESIGNED BEAT register.)
- **Bernard London** — a Depression-era man (flat cap, worn coat) with a pamphlet. Generic.
- **The Carmaker** — a designer at an easel redrawing near-identical cars. Generic, NO logo.
- **The Farmer & Tractor** — a farmer locked out of fixing his tractor (padlock/chain on the
  engine). Generic green tractor, NO logo.

## Callback motifs (recur identically)
- **The expiration tag** — a paper toe-tag with a tiny hourglass or skull (NEVER a readable
  date) = the "quiet expiration date."
- **The hands out** — products with little arms, palms up, asking for money/rent.
- **The slow-down lever / dial** — the gremlin pushing a product's speed lever toward a snail
  = a decision made on purpose. (Avoid "a hand reaching INTO a device" phrasing — content
  filter trips on it.)
- **The bulb burns on** — the Immortal Light Bulb recurs; at the payoff an LED version dies
  young, sealed in a fixture it can't be opened from.

## Real people = generic archetypes only (no likeness)
Bernard London, the cartel executives, the attorney general, any CEO, and ANY real person are
drawn ONLY as generic doodle archetypes — never a likeness, never a name label.

## SAFETY (append to every scene)
"No year text, no floating numbers, no brand logos, no flags or insignia; draw only what is
described." Convey era with old-timey dress / cobwebs / a clock, not a year. Convey
"lasts long vs dies fast" with a healthy vs burnt-out bulb, not a number.

## Color
Bright doodle with generous flat fills. Pop colors: **warm bulb-yellow** (the bulb/filament
through-line), **red** (errors, alarms, villainy, the stamp), **money green** (cost/rent).
DESIGNED BEATS get one bold BRIGHT solid background color + one pop color. Everything stays
light and bright — never dark.
