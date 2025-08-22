# video-summary

CLI tool to transcribe local videos with Whisper (offline) and summarize with OpenAI.

Features
- Uses local Whisper (openai-whisper + PyTorch) for transcription.
- Requires system ffmpeg (validated at runtime).
- Summarizes with OpenAI (reads OPENAI_API_KEY from environment).
- Can be packaged into a standalone Windows exe with PyInstaller.

Prerequisites
- Windows 64-bit recommended (others possible for source run).
- ffmpeg available in PATH (e.g., `ffmpeg -version` should work).
- Python 3.13 for development and building.
- For transcription: Python packages `openai-whisper` and `torch`.
- For summary: `openai` package and `OPENAI_API_KEY` in your environment.

Install (dev)
```bash
python -m venv .venv
. .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Usage
```bash
video-summary path/to/video.mp4 3 \
  --whisper-model base \
  --openai-model gpt-4o-mini \
  --language auto \
  --out summary.txt
```
- The second positional argument (3) is the number of paragraphs to output.
- If `--out` is omitted, the summary is printed to stdout.

Environment
- Set your OpenAI API key before running:
  - PowerShell: `$env:OPENAI_API_KEY = "..."`
  - bash: `export OPENAI_API_KEY=...`

Build a standalone Windows exe
```bash
python -m pip install --upgrade pip wheel build pyinstaller
pyinstaller --onefile -n video-summary \
  --collect-all whisper --collect-all torch --collect-all openai \
  --hidden-import=tqdm --hidden-import=rich \
  src/video_summary/cli.py
# Run the exe
./dist/video-summary.exe --help
```
Note: First-time Whisper model download happens at runtime and is cached (e.g., under `%LOCALAPPDATA%/whisper` or `~/.cache/whisper`). The exe still requires ffmpeg available in PATH.

Repository
- Public: https://github.com/andremorata/video-summary
- License: Apache-2.0

