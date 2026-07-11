# Campuspadi SmartNotes Lite

**ADTC 2026 Submission — Corporate/Enterprise Track**

> Offline AI that turns a student's typed study note into a one page summary and quiz — no internet, no cloud, no data plan required. Built from [Campuspadi](https://campuspadi.com), a live edtech platform serving Nigerian university students.

---

## The Problem

Nigerian university students face a real access barrier: the AI-powered study tools that could help them most — summarization, quiz generation, concept breakdown — require stable internet and API subscriptions they often can't afford or access. A student in a lecture hall with 200MB of data left shouldn't have to choose between using it for study tools or saving it for something else.

## The Solution

Campuspadi SmartNotes Lite runs a quantized 3B language model entirely on-device — no cloud calls at inference time — to generate:

- **Summaries** — 3–5 sentence condensations of the student's own note
- **Quizzes** — 3 multiple-choice questions grounded exclusively in the note's content

This is a scoped, offline reimplementation of the Smart Notes feature already live in Campuspadi, validated against real student notes.

---

## Hardware Target

Designed for the ADTC Standard Laptop profile:

| Component | Spec |
|---|---|
| CPU | Intel Core i5 / AMD Ryzen 5 (x86-64) |
| RAM | 8 GB DDR4 (7 GB usable budget) |
| GPU | Integrated only — no discrete GPU |
| OS | Ubuntu 22.04 LTS |

---

## Model

- **Base model:** Llama 3.2 3B Instruct
- **Format:** GGUF Q4_K_M
- **Runtime:** llama.cpp
- **Size:** ~2.0 GB

Selected after benchmarking Gemma 2 2B, Phi-3.5-mini, Qwen2.5-3B, and Llama 3.2 3B against real student notes on the summarization + quiz generation task. Llama 3.2 3B produced the best combination of faithfulness, summary quality, and structured output consistency.

---

## Quick Start

```bash
# 1. Download the model (idempotent — safe to re-run)
bash download_model.sh

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the pipeline
python src/cli.py --note sample_notes/computing_systems.txt

# Summary only
python src/cli.py --note sample_notes/photosynthesis.txt --mode summary

# Quiz only
python src/cli.py --note sample_notes/nigerian_economy.txt --mode quiz

# Pass note text directly
python src/cli.py --text "Your note text here"

# JSON output (for programmatic use)
python src/cli.py --note sample_notes/computing_systems.txt --json
```

---

## Repository Structure

```
.
├── src/
│   ├── cli.py              # Core pipeline — note in, summary + quiz out
│   └── prompts/
│       └── smartnotes.txt  # Prompt template (single source of truth)
├── sample_notes/           # Anonymized student notes for testing
├── bench/
│   └── results/            # Raw benchmark output from llama-bench + adtc-profiler
├── model/                  # .gguf file lives here (not committed to git)
├── REPORT.md               # Technical writeup
├── metadata.json           # ADTC submission schema
├── download_model.sh       # Idempotent model downloader
├── requirements.txt        # Python dependencies (requests only)
```

---

## Design Decisions

**Why no RAG?**
Retrieval over external corpora adds a second engineering surface (embedding model, corpus curation, retrieval quality) that competes for the same 7 GB RAM budget as the LLM itself. The core value — grounding the output in the student's own note — doesn't require retrieval. We deliberately scoped this out and documented it rather than building a half-working retrieval layer.

**Why Q4_K_M?**
The K-quant suffix preserves more weight information in attention layers than naive Q4, giving meaningfully better output quality at the same file size. Q4_K_M is the established practical sweet spot for accuracy vs. RAM on this hardware band.

**Why llama.cpp?**
CPU-only inference with OpenBLAS acceleration, no CUDA dependency, native GGUF support, and direct integration with the ADTC profiler toolchain. No abstraction layers between the model and the hardware.

---

## Benchmarks

*Full benchmark results from the ADTC Standard Laptop profile will be added before Gate 1 submission. Raw data in `bench/results/`.*

---

## About Campuspadi

[Campuspadi](https://campuspadi.com) is a live study platform built for Nigerian university students, offering Smart Notes, AI Tutor, Study Groups, and CGPA tools. SmartNotes Lite is an offline proof-of-concept of its core note intelligence feature, built to demonstrate that the access-economics barrier — not the technology — is the real bottleneck.

---

**ADTC 2026 | Corporate/Enterprise Track**
