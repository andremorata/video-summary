@echo off
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Checking if OPENAI_API_KEY is set...
if "%OPENAI_API_KEY%"=="" (
    echo [WARNING] OPENAI_API_KEY is not set!
    echo Please set it with: set OPENAI_API_KEY=your_key_here
    echo Or in PowerShell: $env:OPENAI_API_KEY = "your_key_here"
    echo.
    pause
    exit /b 1
)

echo Running video-summary...
echo Note: Summaries ≤1000 chars will also display in terminal
python -m video_summary.cli %*
