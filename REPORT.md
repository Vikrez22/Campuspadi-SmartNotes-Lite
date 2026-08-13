# Technical Report — Campuspadi SmartNotes Lite

**Team ID:** 1059796 | **Submitter:** Victor Jonah ([@vikrez2021](https://github.com/vikrez2021))
**Domain:** `corporate_enterprise` | **Model:** Llama-3.2-3B-Instruct-Q4_K_M

---

## 1. Problem Definition

Nigerian university students face a structural access barrier: AI-powered study tools require stable internet and recurring API subscriptions. For a student at ESUT (Enugu State University of Science and Technology) in Enugu, campus internet is unreliable and mobile data is rationed. A student with 200MB left isn't spending it on an AI summarization API.

The bottleneck isn't the technology — it's access economics.

**Campuspadi SmartNotes Lite** is a scoped offline reimplementation of the Smart Notes feature already live in [Campuspadi](https://campuspadi.com) — a study platform with real users at ESUT. The cloud version generates summaries, flashcards, and quizzes via a hosted LLM. This submission proves the same core value — turning a student's own typed note into a summary and quiz — works with zero internet dependency.

---

## 2. Constraints

| Constraint | Detail |
|---|---|
| RAM ceiling | 7 GB hard limit — disqualification above it |
| No discrete GPU | CPU-only inference throughout |
| Zero network at inference | No API calls, no retrieval, no external data at runtime |
| Single document input | One note in, summary + quiz out — no multi-doc aggregation |
| English only | No multilingual support this cycle — no validated demand in current user base |

---

## 3. Design Decisions

**Scope — Summary + Quiz only (not full Smart Notes suite)**
Scoping to two output modes from a single typed note keeps the RAM budget focused on one model, makes accuracy self-validatable against the source note, and keeps the pipeline auditable. AI Tutor, chatbot, and OCR features were explicitly excluded — not from inability, but because adding them would add failure surfaces without improving the scored metrics.

**No RAG**
Retrieval over external corpora requires an embedding model competing for the same 7 GB RAM budget. The core task — grounding output in the student's own note — doesn't require it. A summary that adds outside knowledge is less faithful, not more. Documented as a V2 roadmap item.

**No African language support**
Zero validated demand in Campuspadi's existing user base for Nigerian-language note summarization. Building it to chase the bonus points would mean shipping a feature no current user has asked for. Judges scoring for "real African use case" authenticity can likely distinguish a genuine use-case feature from a points-driven one. Documented as a V2 item pending demand signal.

**Model selection — Llama 3.2 3B Instruct Q4_K_M**
Four models benchmarked against three real student notes (computing systems, biology, Nigerian economy):

| Model | Summary Quality | Quiz Faithfulness | Structure | Verdict |
|---|---|---|---|---|
| Gemma 2 2B | ✅ Good | ❌ Hallucinated on OS question | ✅ Clean | Eliminated |
| Phi-3.5-mini 3.8B | ⚠️ Run-on | ❌ Invented correct answers | ❌ Broken | Eliminated |
| Qwen2.5 3B | ⚠️ Paraphrase only | ✅ Faithful | ❌ No answer markers | Runner-up |
| **Llama 3.2 3B** | ✅ Genuine synthesis | ✅ Faithful across all notes | ✅ Consistent | **Selected** |

Phi-3.5-mini was eliminated immediately — it marked a hallucinated answer as correct (claimed hex "stores larger amounts than binary," contradicting the source note). Gemma added outside knowledge not in the note. Llama 3.2 3B produced the best combination of faithfulness, summary synthesis, and consistent structured output.

**Quantization — Q4_K_M**
K-quant preserves more weight information in attention layers than naive Q4. Established sweet spot for accuracy vs. RAM on this hardware band. ~2.0 GB weights, leaving comfortable headroom under the 7 GB ceiling.

**Runtime — llama.cpp**
CPU-optimised, GGUF-native, OpenBLAS-accelerated, directly compatible with `llama-bench` and `adtc-profiler`. No abstraction layers between model and hardware.

---

## 4. Tools

| Tool | Purpose |
|---|---|
| `llama.cpp` (build 69bf64379) | Inference runtime — CPU + OpenBLAS |
| GGUF Q4_K_M | Model format — memory-mapped loading |
| `llama-bench` | Throughput benchmarking (pp/tg isolation) |
| `adtc-profiler 0.1.0` | Official submission audit — RAM, thermal, TPS |
| `lm-sensors` + `thermald` | Thermal monitoring — prevents -10pt penalty |
| Python + `requests` | Pipeline glue — single dependency |

---

## 5. Prompt Design

Template lives in `src/prompts/smartnotes.txt` — single source of truth, not inline strings.

Key instructions and why:
- **"do not add outside knowledge, do not infer anything not explicitly stated"** — targets hallucination directly
- **"EXACTLY ONE correct answer"** — prevents ambiguous questions when the note attributes a property to multiple components together
- **"Do NOT use All of the above"** — closes the loophole where models combine multiple correct answers into one option
- **"Do NOT ask questions where the note attributes a property to multiple items together"** — prevents the specific edge case where the note names several components jointly (e.g. "CPU contains control unit, ALU, and registers")

---

## 6. Benchmarks

*Measured on Intel Core i5-6300U, 6.8 GB RAM (WSL2, swap=0), Ubuntu 22.04.5 LTS, CPU-only.*
*Raw data: `bench/results/llama-bench-i5.json` and `bench/results/submission.json`.*

| Metric | Value |
|---|---|
| Prompt processing (pp512) | 17.88 t/s |
| **Text generation (tg128)** | **4.62 t/s** |
| Generation TPS (profiler) | 5.86 t/s |
| First token latency | 31,993 ms |
| **Peak RAM (RSS)** | **3,436 MB (3.4 GB)** |
| Steady state RAM | 3,320 MB |
| CPU usage (p99) | 75.1% |
| Thermal throttling | **None — 0pt penalty** |
| params_match | **true** |

**Derived scores:**

| Score | Calculation | Value |
|---|---|---|
| **Seff** | 100 × ((7 − 3.44) ÷ 7) | **50.9 / 100** |
| **Sperf** | 100 × (5.86 ÷ TPSmax) | Relative to field |
| Thermal penalty | None detected | **0** |

Peak RAM at 3.4 GB leaves 3.6 GB headroom — no OOM risk. No thermal throttling detected.

---

## 7. Limitations and Roadmap

**Current scope (intentional, not accidental):**
- English only
- Typed notes only — no OCR from handwritten or scanned notes
- Summary and quiz only — 3 questions fixed
- No external retrieval

**V2 roadmap:**
- African language support (Yoruba, Igbo, Hausa) — pending demand signal from Campuspadi's user base
- OCR pipeline for handwritten notes
- RAG over a local course-specific corpus
- Configurable quiz length
- Integration back into Campuspadi as an offline-capable fallback

