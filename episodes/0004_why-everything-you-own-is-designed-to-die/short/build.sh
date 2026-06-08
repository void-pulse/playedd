#!/usr/bin/env bash
# Reproducible ep4 short build (locked vignette format). Run from repo root after generating
# the short narration (generate_audio on 01_short_script.md) and the 7 images (generate_images
# on 04_short_scenes.json). White bg, narration ends before the brand line, silent stamp slam.
set -euo pipefail
EP=episodes/0004_why-everything-you-own-is-designed-to-die/short
.venv/bin/python pipeline/build_short.py "$EP/audio/narration.mp3" \
  --images "$EP"/images/0001_*.png "$EP"/images/0002_*.png "$EP"/images/0003_*.png \
           "$EP"/images/0004_*.png "$EP"/images/0005_*.png "$EP"/images/0006_*.png "$EP"/images/0007_*.png \
  --bg "#FFFFFF" --cta-sec 0 --tail 2.5 \
  --stamp-sfx assets/sfx/stamp_slam.mp3 \
  --sfx-cues "$EP/sfx_cues.json" \
  --cuts 0.0 4.5 7.5 10.5 12.2 14.2 17.0 \
  --out "$EP/short_paywall.mp4"
