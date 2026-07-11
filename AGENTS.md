# AGENTS.md

Read this file at the start of every session, before touching any code.

---

## 1. Project Overview

**Project name: Campuspadi SmartNotes Lite**

**What this is:** An ADTC 2026 (Africa Deep Tech Challenge — "Laptop LLM Challenge")
submission. We are building a fully offline, on-device pipeline that takes a
student's typed study note and generates a **summary** and a **quiz**, running
entirely on a quantized small language model via `llama.cpp` — no cloud calls,
no internet dependency at inference time.

Use "Campuspadi SmartNotes Lite" consistently as the project name — in
`REPORT.md`, commit messages, the pitch deck, and the 2-minute demo video.
Don't substitute generic placeholders or invent alternate names mid-project.

**Why it exists:** This is a scoped-down, offline reimplementation of one
feature from Campuspadi (campuspadi.com), an existing live edtech platform —
specifically the "Smart Notes" feature's Summary and Quiz tabs. The cloud
version already works (calls a hosted LLM with internet). This project proves
the same core value — turning a student's own note into a summary and a quiz —
can run on a $400 laptop with no data plan, no electricity-hungry server, and
no recurring API cost. That access-economics story (not feature completeness)
is the actual thing being judged.

**What this is NOT:**
- Not a port of the whole Campuspadi AI suite. AI Tutor, Study Group, and AI
  Padi (chatbot) are explicitly out of scope. Do not build them, even if it
  seems like "just a bit more work."
- Not a RAG system. We deliberately do not retrieve from external corpora or
  the open web. The model only ever sees the note text the user provides, plus
  the system prompt and structured output instructions. If you find yourself
  adding retrieval, stop — that wasn't the agreed scope. Flag it.
- Not multilingual. English only for this submission cycle. There was no
  validated user demand for Yoruba/Igbo/Hausa support in Campuspadi's existing
  user base, so we are not claiming the African Use Case Bonus this cycle.
  `african_alpha_claim` in `metadata.json` must stay `false` unless a human
  explicitly says otherwise.

**Domain (per ADTC schema):** `corporate_enterprise` — knowledge-work
productivity (summarization, structured extraction). This is the correct
enum value; do not change it to `coding_assistants` or anything else without
explicit instruction.

---

## 2. Folder Structure

This repo follows the **official ADTC 2026 submission template** exactly.
Do not restructure it — the profiler tool and the audit pipeline expect this
exact layout.

```
.
├── AGENTS.md            ← this file
├── SKILLS.md             ← how-to guide for recurring tasks
├── LESSONS.md            ← running log of mistakes and fixes
├── VERIFIER.md           ← definition of done, checked before any "done" claim
├── README.md             ← official ADTC template README (do not remove rules)
├── REPORT.md             ← the actual judged technical writeup — keep current
├── metadata.json         ← REQUIRED. Schema-validated. See §6 below.
├── download_model.sh     ← downloads the .gguf weight file. Must be idempotent.
├── .gitignore            ← must exclude *.gguf and model/ contents
├── model/                ← .gguf file lands here at runtime. NEVER COMMIT.
├── src/                  ← pipeline code (prompt templates, CLI, inference glue)
├── bench/                ← benchmarking scripts and recorded results
│   └── results/          ← raw JSON output from llama-bench / adtc-profiler runs
└── sample_notes/         ← anonymized/synthetic example notes for self-testing
```

If `src/`, `bench/`, or `sample_notes/` don't exist yet, create them as needed
— but never touch the required top-level files' names or locations.

---

## 3. Tech Stack and Key Dependencies

- **Inference runtime:** `llama.cpp` exclusively. The ADTC rules state
  `model.runtime` must literally be `"llama.cpp"` — no Ollama-only setups,
  no Transformers/PyTorch inference path for the actual submission (Ollama is
  fine for early exploration but the submitted pipeline must run llama.cpp
  directly, since that's what `adtc-profiler` and `llama-bench` invoke).
- **Model format:** GGUF, quantized to **Q4_K_M** (the agreed sweet spot for
  this hardware band — do not silently change quant level; if a different
  quant looks better in testing, flag it for a human decision, don't just
  swap it).
- **Candidate base models (shortlist, not yet finalized):** Qwen2.5-3B-Instruct,
  Phi-3.5-mini (3.8B), Gemma 2 2B, Llama 3.2 3B-Instruct. Whichever is chosen,
  record the decision and reasoning in `REPORT.md` and `LESSONS.md` if
  switching mid-project.
- **Profiling tools:** `adtc-profiler` (official, installed via
  `pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"`)
  and `llama-bench` (ships with llama.cpp). These are the actual scoring
  instruments — do not write custom benchmarking logic that replaces them for
  final numbers. Custom scripts are fine for quick iteration only.
- **Python:** >= 3.11, managed via `uv` (matches the profiler repo's own
  tooling).
- **Target eval environment:** Ubuntu 22.04 LTS, 8 GB RAM (7 GB usable
  budget), no discrete GPU, x86-64 (Intel i5 10th–12th gen / AMD Ryzen 5
  3000–5000 class).

---

## 4. Coding Conventions and Style Rules

- **Prefer boring and explicit over clever.** This is a judged, audited
  submission — reviewers and an LLM-based audit system read `REPORT.md` and
  may read the code. Clear > terse.
- **All prompts live in one place** (`src/prompts/` or equivalent) as plain
  text/template files, not scattered inline strings. Judges and future-you
  need to be able to find and read the exact prompts used.
- **No hardcoded absolute paths.** Everything must run from a fresh clone on
  someone else's machine.
- **No network calls anywhere in the inference path.** Downloading the model
  via `download_model.sh` is the only permitted network activity, and it must
  complete *before* profiling starts. Any HTTP call inside the actual
  summarize/quiz pipeline is a disqualifying bug — treat it as a P0.
- **Every benchmark number that ends up in `REPORT.md` must be reproducible**
  from a script in `bench/`, with the raw output saved in `bench/results/`.
  Never hand-type a number into `REPORT.md` without a saved artifact backing
  it.
- **Commit messages describe what changed and why**, not just "update files."

---

## 5. What the Agent Should NEVER Do

- **Never commit a `.gguf` file or anything in `model/` to git.** Check
  `.gitignore` covers this before every commit involving that directory.
- **Never add retrieval/RAG, multilingual support, or any of the other
  Campuspadi AI suite features** (AI Tutor, Study Group, AI Padi chatbot)
  without an explicit, current instruction from the human. Past conversation
  history may mention these as ideas that were deliberately rejected — don't
  resurrect them on your own initiative.
- **Never set `african_alpha_claim: true` or `budget_laptop_claim: false`**
  in `metadata.json` without explicit human sign-off — these are competition
  claims with real consequences if false.
- **Never invent or estimate benchmark numbers.** If `bench/` doesn't have a
  fresh run backing a number, the number doesn't go in `REPORT.md`. Say "not
  yet benchmarked" instead.
- **Never change `model.runtime` away from `llama.cpp`** or restructure the
  required top-level files away from the official template layout.
- **Never assume the dev machine's benchmark numbers are the submission
  numbers.** The i7/16GB dev machine is for iteration speed only. Real
  validation happens on the i5/8GB machine and ultimately via
  `adtc-profiler run --mode participant` before submission.
- **Never mark a task "done" without going through `VERIFIER.md` first.**

---

## 6. How to Run the Project Locally

```bash
# 1. Download the model weights (idempotent — safe to re-run)
bash download_model.sh

# 2. Quick smoke test of the inference pipeline (adjust path to actual entrypoint)
python -m src.cli --note sample_notes/example_01.txt --mode summary

# 3. Run the official local self-check before any submission-readiness claim
adtc-profiler run \
  --submission . \
  --mode participant \
  --output bench/results/submission.json \
  --skip-accuracy

cat bench/results/submission.json
```

`metadata.json` must always be fully filled in (no placeholder values) for
the profiler to run at all — it errors out if `model_path` doesn't resolve
to an existing file under `model/`.

---

## 7. Standing Instruction — End of Every Task

After completing any task:

1. **Check if anything unexpected happened** — an error that took more than
   one attempt to fix, a tool behaving differently than documented, a
   judgment call that wasn't obvious from existing docs, a number that didn't
   match expectations.
2. **If yes, update `LESSONS.md`** using its template, before considering the
   task finished. This is not optional polish — it is part of the task.
3. **If no, say so explicitly** ("no unexpected issues this session") rather
   than silently skipping the check.

This is the project's main defense against repeating the same mistake across
sessions. Treat it as seriously as the actual code change.
