#!/usr/bin/env python3
"""
generate_sfx.py
Generate the channel's reusable SFX kit via the ElevenLabs Sound Effects API.

Auto-length is OFF: each effect uses a fixed duration_seconds so the kit is
predictable. casino_ambience loops. Files land in assets/sfx/<name>.mp3 (repo
root, reused across episodes). Atomic writes (temp -> rename): a mid-run quota
failure can never truncate a completed effect.

Usage:
    python pipeline/generate_sfx.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
SFX_DIR = ROOT / "assets" / "sfx"

# name -> (prompt, duration_seconds, loop)
SFX = [
    ("slot_jackpot.mp3", "retro slot machine jackpot win, celebratory bells and cascading coins", 3.0, False),
    ("coin_drop.mp3", "single coin dropping on a felt table", 1.0, False),
    ("casino_ambience.mp3", "casino floor ambience, distant slot chimes and low crowd murmur", 10.0, True),
    ("record_scratch.mp3", "sharp comedic record scratch, abrupt stop", 1.0, False),
    ("bass_thud.mp3", "deep ominous bass thud, single impact", 2.0, False),
    ("whoosh.mp3", "soft UI whoosh transition", 1.0, False),
    ("card_riffle.mp3", "playing card shuffle riffle", 2.0, False),
    ("cha_ching.mp3", "cash register cha-ching", 1.0, False),
    # --- added for ep3 ---
    ("door_slam.mp3", "heavy door slamming shut, single hard thud", 1.5, False),
    ("roulette_spin.mp3", "roulette wheel spinning, ball rattling then settling into a slot", 4.0, False),
    ("slot_reel_spin.mp3", "slot machine reels spinning and clicking to a stop", 2.0, False),
    ("near_miss.mp3", "slot machine almost-win, hopeful rising tone that deflates", 2.0, False),
    ("card_beep.mp3", "plastic card swipe with a short electronic beep", 1.0, False),
    ("service_bell.mp3", "small front-desk service bell ding", 1.0, False),
    ("grand_chime.mp3", "bright magical shimmer chime, luxurious reveal", 2.0, False),
    ("perfume_spray.mp3", "perfume atomizer spritz, short spray", 1.0, False),
    ("machine_zone_drone.mp3", "low muffled hypnotic drone, the world going quiet and hollow", 6.0, True),
    ("phone_notify.mp3", "smartphone notification pop with a short scroll swipe", 1.0, False),
    # --- ep3 palette expansion: one-shots ---
    ("clock_tick.mp3", "a steady mechanical clock ticking, a few crisp ticks", 2.0, False),
    ("applause.mp3", "a short burst of enthusiastic crowd applause and cheering", 3.0, False),
    ("slot_lever.mp3", "a slot machine lever pulled down with a mechanical clunk", 1.0, False),
    ("slot_button.mp3", "a single plastic arcade button press, soft click", 0.6, False),
    ("data_blips.mp3", "rapid soft digital data blips and computer processing beeps", 2.0, False),
    ("camera_servo.mp3", "a surveillance camera motor whirring and zooming, small servo", 1.5, False),
    ("footsteps_approach.mp3", "footsteps on carpet approaching and getting closer", 2.0, False),
    ("chip_clink.mp3", "casino poker chips stacked and clinking together", 1.5, False),
    ("glass_clink.mp3", "cocktail glasses clinking with a soft drink pour", 1.5, False),
    ("atm_beep.mp3", "an ATM beeping and dispensing cash, button presses", 2.0, False),
    ("scroll_swipe.mp3", "repeated thumb swipes scrolling a phone screen, soft whooshes", 1.5, False),
    ("crowd_cheer.mp3", "a distant crowd cheering at a big casino win", 3.0, False),
    # --- ep3 palette expansion: ambient beds (looped in the build) ---
    ("casino_floor_walla.mp3", "ambient busy casino floor, distant chatter, faint slot jingles, occasional coins, low room tone", 21.0, True),
    ("slot_machine_chorus.mp3", "a wall of distant slot machines beeping, chiming and jingling continuously, no voices", 21.0, True),
    ("casino_lounge.mp3", "calm upscale casino lounge ambience, soft murmur, gentle distant shimmer, classy and spacious", 21.0, True),
    ("tension_bed.mp3", "a low ominous ambient drone, hollow and unsettling, subtle", 21.0, True),
    # --- ep1 popcorn short ---
    ("stamp_slam.mp3", "a single heavy deep pound, a heavy mallet or fist slamming down hard onto a wooden desk with a low booming thud and powerful weighty impact", 1.3, False),
    ("popcorn_pop.mp3", "popcorn kernels popping in a popper, a quick lively burst of pops", 2.0, False),
    ("cash_register.mp3", "an old cash register cha-ching with a bright bell and drawer", 1.5, False),
    ("empty_thud.mp3", "a low hollow falling thud, something heavy collapsing in an empty room", 2.0, False),
    ("regal_ding.mp3", "a short bright regal chime fanfare, a tiny triumphant royal flourish", 1.5, False),
    # --- ep2 diamond short ---
    ("ring_sparkle.mp3", "a glassy magical sparkle shimmer twinkle, a bright diamond glint", 1.5, False),
    ("bubble_pop.mp3", "a soft bubble pop deflating, a gentle little pop and fizzle", 1.0, False),
    ("eerie_whoosh.mp3", "a low mysterious whoosh, a hollow unsettling tone sweeping in", 2.0, False),
    # --- ep4 cinematic palette (upgraded: richer prompts, natural tails) ---
    ("icy_freeze.mp3", "frost rapidly spreading across glass, a delicate icy crackle with a cold shimmering tone descending, cinematic", 2.5, False),
    ("cartel_murmur.mp3", "low conspiratorial mumbling voices of men gathered in a closed room, indistinct hushed murmur, no clear words", 6.0, True),
    ("factory_hum.mp3", "an old early-1900s factory of machines, steady mechanical hum and distant clatter", 6.0, True),
    ("slow_winddown.mp3", "an electronic device slowing down, a sad descending power-down whir", 2.5, False),
    ("error_buzzer.mp3", "a device politely refusing input, a soft warm descending two-tone error, gentle and not harsh", 2.0, False),
    ("padlock_click.mp3", "a small set of keys jingling, then a lock smoothly turning and clicking shut, a clean satisfying latch, light and crisp, not a heavy slam or clunk", 2.2, False),
    ("coin_meter.mp3", "a coin dropping into an old metal parking meter, a clink then a mechanical ratchet turn that settles", 2.5, False),
    ("horse_whinny.mp3", "a single proud horse whinny and snort, warm and natural, one short call", 2.0, False),
    ("crowd_angry.mp3", "a frustrated crowd grumbling and muttering with irritation, a rising wave of annoyed voices", 3.0, False),
    ("gavel_bang.mp3", "a wooden judge's gavel banging twice, firm and authoritative", 1.5, False),
    ("light_hum.mp3", "a warm wondrous reveal shimmer, soft glassy bells blooming and gently fading out, magical and bright", 3.0, False),
    ("scissors_snip.mp3", "a crisp sharp metal scissor snip cutting a wire, a clean snick with a tiny glassy tink", 1.8, False),
    ("typewriter_ding.mp3", "an old typewriter clack with a bright carriage-return ding", 2.0, False),
    ("dark_swell.mp3", "a smooth cinematic rising swell, low warm strings growing with a quiet sense of menace, something evolving, subtle and not scary, no melody", 3.0, False),
    ("digital_lag.mp3", "a smartphone gently slowing to a crawl, a soft warm descending whir winding down, smooth and subtle, not harsh, no glitch, no stutter", 2.5, False),
    # --- ep4 cinematic stings (new) ---
    ("cartel_reveal.mp3", "a dark conspiratorial reveal sting, a low ominous orchestral swell with a soft cinematic boom, a secret being uncovered, tasteful not jumpy", 3.0, False),
    ("realization_chime.mp3", "a single clear bright realization chime, a clean glassy bell with a soft shimmering tail, an aha moment", 2.5, False),
]


def credit_count(client):
    try:
        sub = client.user.subscription.get()
        return getattr(sub, "character_count", None)
    except Exception:
        return None


def main():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Add it to .env")

    SFX_DIR.mkdir(parents=True, exist_ok=True)

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=api_key)

    start_credits = credit_count(client)
    done = skipped = 0
    for name, prompt, duration, loop in SFX:
        out_path = SFX_DIR / name
        if out_path.exists() and out_path.stat().st_size > 0:   # skip-existing (no re-bill)
            skipped += 1
            print(f"[--] {name}: skip (exists)")
            continue
        print(f"[{done + 1:02d}] {name}: {duration:.0f}s loop={loop} ...")
        audio = client.text_to_sound_effects.convert(
            text=prompt,
            duration_seconds=duration,   # explicit -> auto-length OFF
            loop=loop,
            prompt_influence=0.3,
        )
        tmp = out_path.with_suffix(".mp3.tmp")
        try:
            with open(tmp, "wb") as f:
                for chunk in audio:      # request happens here; may raise (e.g. quota)
                    if chunk:
                        f.write(chunk)
            os.replace(tmp, out_path)
        except BaseException:
            tmp.unlink(missing_ok=True)  # never leave a partial effect
            raise
        done += 1

    end_credits = credit_count(client)
    used = (end_credits - start_credits) if (start_credits is not None and end_credits is not None) else None
    print(f"\nDone. generated={done} skipped={skipped} total={len(SFX)} -> {SFX_DIR}")
    if used is not None:
        print(f"Credits used (character_count delta): {used}")
    else:
        print("Credits used: unavailable (subscription endpoint did not report a count)")


if __name__ == "__main__":
    main()
