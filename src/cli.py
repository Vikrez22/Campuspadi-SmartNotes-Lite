"""
Campuspadi SmartNotes Lite — CLI pipeline
Generates a summary and quiz from a student note using a local LLM via Ollama.
Usage:
    python -m src.cli --note path/to/note.txt
    python -m src.cli --note path/to/note.txt --mode summary
    python -m src.cli --note path/to/note.txt --mode quiz
    python -m src.cli --text "your note text here"
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"
PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "smartnotes.txt"


def load_prompt_template() -> str:
    if not PROMPT_TEMPLATE_PATH.exists():
        print(f"ERROR: Prompt template not found at {PROMPT_TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")


def load_note(note_path: str | None, note_text: str | None) -> str:
    if note_text:
        return note_text.strip()
    if note_path:
        path = Path(note_path)
        if not path.exists():
            print(f"ERROR: Note file not found: {note_path}", file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding="utf-8").strip()
    print("ERROR: Provide --note <path> or --text <string>", file=sys.stderr)
    sys.exit(1)


def build_prompt(template: str, note: str) -> str:
    return template.replace("{note}", note)


def call_ollama(prompt: str, model: str = MODEL) -> tuple[str, float]:
    """
    Calls the Ollama API with the given prompt.
    Returns (response_text, elapsed_seconds).
    Raises SystemExit on network failure — no cloud fallback by design.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        start = time.time()
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        elapsed = time.time() - start
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(
            "ERROR: Cannot reach Ollama at localhost:11434.\n"
            "Make sure Ollama is running: run 'ollama serve' in a separate terminal.",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("ERROR: Ollama request timed out after 120s.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Ollama returned HTTP {response.status_code}: {e}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    return data.get("response", "").strip(), elapsed


def parse_output(raw: str, mode: str) -> dict:
    """
    Parses raw model output into structured summary and/or quiz sections.
    Returns a dict with keys: summary, quiz, raw.
    """
    result = {"summary": None, "quiz": None, "raw": raw}

    summary_marker = "SUMMARY:"
    quiz_marker = "QUIZ:"

    summary_start = raw.upper().find(summary_marker)
    quiz_start = raw.upper().find(quiz_marker)

    if summary_start != -1:
        end = quiz_start if quiz_start != -1 else len(raw)
        result["summary"] = raw[summary_start + len(summary_marker):end].strip()

    if quiz_start != -1:
        result["quiz"] = raw[quiz_start + len(quiz_marker):].strip()

    return result


def print_output(parsed: dict, mode: str, elapsed: float, verbose: bool = False):
    separator = "─" * 60

    if mode in ("summary", "both") and parsed["summary"]:
        print(f"\n{separator}")
        print("SUMMARY")
        print(separator)
        print(parsed["summary"])

    if mode in ("quiz", "both") and parsed["quiz"]:
        print(f"\n{separator}")
        print("QUIZ")
        print(separator)
        print(parsed["quiz"])

    if mode == "both" and not parsed["summary"] and not parsed["quiz"]:
        print("\n[WARNING] Could not parse SUMMARY or QUIZ sections. Raw output:")
        print(parsed["raw"])

    print(f"\n{separator}")
    print(f"Generated in {elapsed:.1f}s using {MODEL}")
    print(separator)

    if verbose:
        print("\n[VERBOSE] Raw model output:")
        print(parsed["raw"])


def main():
    parser = argparse.ArgumentParser(
        description="Campuspadi SmartNotes Lite — offline note summarizer and quiz generator"
    )
    parser.add_argument("--note", type=str, help="Path to a .txt note file")
    parser.add_argument("--text", type=str, help="Note text passed directly as a string")
    parser.add_argument(
        "--mode",
        choices=["summary", "quiz", "both"],
        default="both",
        help="Output mode: summary only, quiz only, or both (default: both)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL,
        help=f"Ollama model to use (default: {MODEL})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output result as JSON instead of formatted text",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print raw model output alongside parsed result",
    )
    args = parser.parse_args()

    template = load_prompt_template()
    note = load_note(args.note, args.text)
    prompt = build_prompt(template, note)

    print(f"Running {args.model} locally via Ollama...", file=sys.stderr)
    raw_output, elapsed = call_ollama(prompt, model=args.model)

    parsed = parse_output(raw_output, args.mode)

    if args.output_json:
        print(json.dumps({**parsed, "elapsed_seconds": round(elapsed, 2), "model": args.model}, indent=2))
    else:
        print_output(parsed, args.mode, elapsed, verbose=args.verbose)


if __name__ == "__main__":
    main()
