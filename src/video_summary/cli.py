#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console

console = Console()


def fail(msg: str, code: int = 1) -> None:
    console.print(f"[red]Error:[/red] {msg}")
    sys.exit(code)


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        fail(
            "ffmpeg not found on PATH. Please install ffmpeg and ensure 'ffmpeg' is available in your PATH.\n"
            "Windows: winget install Gyan.FFmpeg or choco install ffmpeg\n"
            "macOS: brew install ffmpeg\n"
            "Linux: use your distro's package manager"
        )


def ensure_whisper() -> None:
    try:
        import whisper  # noqa: F401
        import torch  # noqa: F401
    except Exception as e:  # pragma: no cover
        fail(
            "Python packages for local Whisper not available. Install with:\n"
            "  pip install openai-whisper torch\n"
            f"Details: {type(e).__name__}: {e}"
        )


def extract_audio_to_wav(video_path: Path) -> Path:
    tmp_wav = Path(tempfile.mkstemp(suffix=".wav")[1])
    # 16kHz mono PCM WAV for Whisper
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ar", "16000", "-ac", "1", str(tmp_wav)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        fail(f"ffmpeg failed to extract audio: {e}")
    return tmp_wav


def transcribe_with_whisper(audio_path: Path, whisper_model: str = "base", language: Optional[str] = None) -> str:
    import whisper
    model = whisper.load_model(whisper_model)
    result = model.transcribe(str(audio_path), language=None if language in (None, "auto") else language)
    return result.get("text", "").strip()


def _trim_to_char_limit(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    # try not to cut off mid-word
    trimmed = s[:limit].rstrip()
    last_space = trimmed.rfind(" ")
    if last_space > limit * 0.6:  # only backtrack if it keeps majority
        trimmed = trimmed[:last_space]
    return trimmed.rstrip(". ") + "..."


def summarize_text(text: str, model: str, paragraphs: Optional[int] = None, char_limit: Optional[int] = None) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        fail(
            "OPENAI_API_KEY not set in environment. Set it and re-run.\n"
            "Example (bash): export OPENAI_API_KEY=your_key_here\n"
            "Example (PowerShell): $env:OPENAI_API_KEY = \"your_key_here\""
        )

    try:
        from openai import OpenAI
    except Exception as e:  # pragma: no cover
        fail(f"openai package is not installed: {e}")

    client = OpenAI()

    if paragraphs is None and char_limit is None:
        fail("Internal error: either paragraphs or char_limit must be provided")

    if paragraphs is not None:
        instruction = (
            "You are an expert summarizer. Return exactly {n} paragraphs, separated by a single blank line, "
            "no headings, no title, no bullet points."
        ).format(n=paragraphs)
    else:
        instruction = (
            "You are an expert summarizer. Produce a concise summary no longer than {c} characters. "
            "Avoid pre/postamble, no headings or bullet points. If truncation would harm clarity, prioritize clarity "
            "while staying under the limit."
        ).format(c=char_limit)

    # Simple chunking to avoid overly long prompts
    MAX_CHARS = 8000
    chunks = [text] if len(text) <= MAX_CHARS else [text[i:i+MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]

    def summarize_chunk(t: str) -> str:
        if paragraphs is not None:
            user_prompt = f"Summarize this transcript chunk into at most {paragraphs} paragraphs (will refine later):\n\n{t}"
        else:
            user_prompt = f"Summarize this transcript chunk within {char_limit} characters (will refine later):\n\n{t}"
        resp = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content.strip()

    if len(chunks) == 1:
        summary = summarize_chunk(chunks[0])
        if char_limit is not None:
            summary = _trim_to_char_limit(summary, char_limit)
        return summary

    # Summarize each chunk first
    partials = [summarize_chunk(c) for c in chunks]
    # Then summarize the partial summaries down to exactly N paragraphs
    combined = "\n\n".join(partials)
    if paragraphs is not None:
        refine_prompt = f"Combine and refine into exactly {paragraphs} paragraphs:\n\n{combined}"
    else:
        refine_prompt = f"Combine and refine into a summary within {char_limit} characters (shorter is fine if clear):\n\n{combined}"
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": refine_prompt},
        ],
    )
    final = resp.choices[0].message.content.strip()
    if char_limit is not None:
        final = _trim_to_char_limit(final, char_limit)
    return final


def parse_limit(limit_value: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse the --limit value.

    Returns (paragraphs, char_limit).
    Examples:
        1000  -> (None, 1000)
        2p    -> (2, None)
        002p  -> (2, None)
    """
    lv = limit_value.strip().lower()
    if not lv:
        fail("--limit value cannot be empty")
    if lv.endswith("p"):
        num = lv[:-1]
        if not num.isdigit():
            fail("Invalid paragraph limit format. Use e.g. --limit 3p")
        p = int(num)
        if p <= 0:
            fail("Paragraph limit must be positive")
        return p, None
    # character limit
    if not lv.isdigit():
        fail("Invalid character limit format. Use integer number of characters or Np for paragraphs")
    chars = int(lv)
    if chars <= 0:
        fail("Character limit must be positive")
    return None, chars


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="video-summary",
        description="Transcribe a video with local Whisper and summarize it with OpenAI."
    )
    parser.add_argument("video", help="Path to input video file (e.g., .mp4)")
    parser.add_argument("paragraphs", type=int, nargs="?", help="Number of paragraphs in the summary output (ignored if --limit provided)")
    parser.add_argument("--whisper-model", default="base", help="Whisper model size: tiny, base, small, medium, large")
    parser.add_argument("--language", default="auto", help="Force language code or 'auto' to detect")
    parser.add_argument("--openai-model", default="gpt-4o-mini", help="OpenAI model for summarization")
    parser.add_argument("--out", help="Optional path to write the summary instead of printing")
    parser.add_argument("--limit", help="Summary limit: <N> characters (e.g. 800) or <N>p paragraphs (e.g. 3p). If omitted, uses positional paragraphs or defaults to 3 paragraphs.")

    args = parser.parse_args(argv)

    # Basic validations
    video_path = Path(args.video)
    if not video_path.exists():
        fail(f"Video not found: {video_path}")
    paragraphs_arg: Optional[int] = args.paragraphs

    limit_paragraphs: Optional[int] = None
    char_limit: Optional[int] = None
    if args.limit:
        limit_paragraphs, char_limit = parse_limit(args.limit)

    if limit_paragraphs is not None:
        effective_paragraphs = limit_paragraphs
    else:
        # If char limit used, paragraphs ignored
        if char_limit is not None:
            effective_paragraphs = None
        else:
            # Default paragraphs if neither provided
            if paragraphs_arg is None:
                effective_paragraphs = 3
            else:
                if paragraphs_arg <= 0:
                    fail("paragraphs must be a positive integer")
                effective_paragraphs = paragraphs_arg

    console.rule("[bold]Validating environment")
    ensure_ffmpeg()
    ensure_whisper()

    console.rule("[bold]Transcription")
    tmp_wav = extract_audio_to_wav(video_path)
    try:
        transcript = transcribe_with_whisper(tmp_wav, whisper_model=args.whisper_model, language=args.language)
    finally:
        try:
            tmp_wav.unlink(missing_ok=True)
        except Exception:
            pass

    console.rule("[bold]Summarization")
    summary = summarize_text(
        transcript,
        model=args.openai_model,
        paragraphs=effective_paragraphs,
        char_limit=char_limit,
    )

    if args.out:
        out_path = Path(args.out)
    else:
        # Default output file next to video: <stem>.summary.txt
        out_path = video_path.parent / f"{video_path.stem}.summary.txt"
    out_path.write_text(summary, encoding="utf-8")
    console.print(f"[green]Summary written to {out_path}")
    
    # Also display in terminal if short enough
    if len(summary) <= 1000:
        console.rule("[bold]Summary")
        console.print(summary)
        console.rule()


if __name__ == "__main__":
    main()

