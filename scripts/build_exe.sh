#!/usr/bin/env bash
set -euo pipefail

# Build a standalone Windows (or local) executable using PyInstaller.
# Requires active venv with dependencies installed.

python -m pip install --upgrade pip wheel build pyinstaller
pyinstaller --onefile -n video-summary \
  --collect-all whisper --collect-all torch --collect-all openai \
  --hidden-import=tqdm --hidden-import=rich \
  src/video_summary/cli.py

echo "Built executable at dist/video-summary(.exe)"

