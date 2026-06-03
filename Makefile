.PHONY: help setup new audio parse images archive

help:
	@echo "Drawn & Declassified — pipeline commands"
	@echo ""
	@echo "  make setup                 create venv + install deps"
	@echo "  make new SLUG=topic-slug   scaffold a new episode"
	@echo "  make audio EP=episodes/0001_x VOICE=NARRATOR_A"
	@echo "  make parse EP=episodes/0001_x"
	@echo "  make images EP=episodes/0001_x"
	@echo "  make archive EP=episodes/0001_x   zip finished media outside git"
	@echo ""
	@echo "Full per-video flow: docs/WORKFLOW.md"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo "Now: cp .env.example .env and fill in FAL_KEY + ELEVENLABS_API_KEY"

new:
	python pipeline/new_episode.py "$(SLUG)"

audio:
	python pipeline/generate_audio.py $(EP)/01_script.md --voice $(or $(VOICE),NARRATOR_A)

parse:
	python pipeline/parse_timestamps.py $(EP)/02_narration.srt --merge-short 1.5

images:
	python pipeline/generate_images.py $(EP)/04_scenes.json --resume

archive:
	@mkdir -p _archive
	@name=$$(basename $(EP)); \
	zip -r "_archive/$$name.zip" "$(EP)" >/dev/null; \
	echo "Archived to _archive/$$name.zip"
