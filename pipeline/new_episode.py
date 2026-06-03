#!/usr/bin/env python3
"""
new_episode.py
Scaffold a new episode folder from the template.

Usage:
    python pipeline/new_episode.py "mkultra-mind-control-doodle"
    # creates episodes/0001_mkultra-mind-control-doodle/ from _template
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP_DIR = ROOT / "episodes"
TEMPLATE = EP_DIR / "_template"


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def next_number() -> int:
    nums = []
    for p in EP_DIR.iterdir():
        if p.is_dir() and p.name[:4].isdigit():
            nums.append(int(p.name[:4]))
    return (max(nums) + 1) if nums else 1


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python pipeline/new_episode.py "short-topic-slug"')
    slug = slugify(" ".join(sys.argv[1:]))
    num = next_number()
    name = f"{num:04d}_{slug}"
    dest = EP_DIR / name
    if dest.exists():
        sys.exit(f"Already exists: {dest}")
    shutil.copytree(TEMPLATE, dest)

    idea = dest / "00_idea.md"
    if idea.exists():
        idea.write_text(
            idea.read_text(encoding="utf-8").replace("{{DATE}}", date.today().isoformat())
                                            .replace("{{TITLE}}", slug.replace("-", " ").title()),
            encoding="utf-8",
        )
    print(f"Created {dest}")
    print("Workflow: see docs/WORKFLOW.md")


if __name__ == "__main__":
    main()
