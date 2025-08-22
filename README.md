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
# On Windows (Git Bash): source .venv/Scripts/activate
# On Windows (PowerShell): .venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Quick Start Scripts
For convenience, use the provided activation and run scripts:
```bash
# Activate environment (Windows)
./activate.bat

# Or run directly with environment activated
./run.sh path/to/video.mp4 --limit 3p    # Git Bash
run.bat path/to/video.mp4 --limit 3p     # Command Prompt/PowerShell
```

Usage
**Important**: Always activate the virtual environment first!
```bash
# Activate environment
source .venv/Scripts/activate  # Git Bash
# OR: .venv\Scripts\Activate.ps1  # PowerShell
# OR: .venv\Scripts\activate.bat  # Command Prompt

# Then run the tool
python -m video_summary.cli path/to/video.mp4 3 \
  --whisper-model base \
  --openai-model gpt-4o-mini \
  --language auto \
  --out summary.txt
```
- The second positional argument (3) is the number of paragraphs to output.
 - If `--out` is omitted, the summary is written to `<video_stem>.summary.txt`.

New (defaults & limits)
- All optional flags now have sensible defaults: `--whisper-model base`, `--openai-model gpt-4o-mini`, `--language auto`.
- If you omit the positional paragraphs count AND `--limit`, it defaults to 3 paragraphs.
- If you omit `--out`, the summary is written to `<video_stem>.summary.txt` alongside the video.
- Summaries ≤ 1000 characters are also displayed in the terminal for quick viewing.
- Use `--limit` to control output size instead of the positional paragraphs:
  - `--limit 1000` -> summarize to <= 1000 characters.
  - `--limit 2p` -> summarize to exactly (refined to) ~2 paragraphs.
  - If `--limit` is provided with a character count, the paragraphs positional argument is ignored.
  - Paragraph granularity takes precedence if you provide a `Np` form (e.g., `3p`).

Examples
```bash
# Activate environment first
source .venv/Scripts/activate

# Default 3 paragraphs (no positional paragraphs given)
python -m video_summary.cli path/to/video.mp4

# Explicit paragraphs
python -m video_summary.cli path/to/video.mp4 5

# Character limit (<= 1200 chars)
python -m video_summary.cli path/to/video.mp4 --limit 1200

# Two paragraphs via --limit
python -m video_summary.cli path/to/video.mp4 --limit 2p

# Custom models & auto output filename
python -m video_summary.cli path/to/video.mp4 4 --whisper-model small --openai-model gpt-4o-mini
```

Environment
- Set your OpenAI API key before running:
  - PowerShell: `$env:OPENAI_API_KEY = "your_key_here"`
  - Git Bash: `export OPENAI_API_KEY="your_key_here"`
  - Command Prompt: `set OPENAI_API_KEY=your_key_here`

Troubleshooting
- **ModuleNotFoundError**: Make sure to activate the virtual environment first with `source .venv/Scripts/activate`
- **OPENAI_API_KEY not set**: Set your API key in the environment before running
- **ffmpeg not found**: Install ffmpeg and ensure it's in your PATH
- **FP16 warning**: Normal when running on CPU, can be ignored

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

Helper Scripts
The repository includes convenience scripts:
- `activate.bat` - Activates the virtual environment (Windows)
- `run.bat` - Runs the tool with environment activated (Windows Command Prompt)
- `run.sh` - Runs the tool with environment activated (Git Bash)

