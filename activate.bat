@echo off
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Virtual environment activated!
echo You can now run: python -m video_summary.cli [args...]
cmd /k
