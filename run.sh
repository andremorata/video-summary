#!/bin/bash
echo "Activating virtual environment..."
source .venv/Scripts/activate

echo ""
echo "Checking if OPENAI_API_KEY is set..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "[WARNING] OPENAI_API_KEY is not set!"
    echo "Please set it with: export OPENAI_API_KEY=your_key_here"
    echo ""
    exit 1
fi

echo "Running video-summary..."
echo "Note: Summaries ≤1000 chars will also display in terminal"
python -m video_summary.cli "$@"
