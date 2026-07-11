# Technical Report — Campuspadi SmartNotes Lite

**Team ID:** 1059796
**Submitter:** Victor Jonah ([@vikrez2021](https://github.com/vikrez2021))
**Domain:** `corporate_enterprise`
**Model:** Llama-3.2-3B-Instruct-Q4_K_M
**Deadline:** August 25, 2026

---

## 1. Problem Definition and Context

### The Access-Economics Problem

Nigerian university students face a structural barrier to AI-powered study tools: the tools that would help them most require stable internet connectivity and recurring API subscriptions. For a student at ESUT (Enugu State University of Science and Technology) in Enugu, a university campus does not guarantee reliable internet. Mobile data is rationed carefully — a student running on 200MB of remaining data is not going to spend it on an AI summarization API.

The bottleneck is not the technology. Open-weight language models capable of genuine summarization and quiz generation have existed for years. The bottleneck is access economics: cloud-hosted LLMs require API fees, stable fibre, and sustained electricity. These are not minor frictions for a university student in Enugu — they are blockers.

### The Target User

A Nigerian university student — specifically ESUT students, the existing user base of Campuspadi — who:
- Takes typed or handwritten lecture notes
- Wants a summary of a dense note to aid revision
- Wants quiz questions generated from their own notes to test their understanding
- Has a laptop but unreliable or expensive internet access

This is not a hypothetical persona. Campuspadi (campuspadi.com) is a live study platform with real users at ESUT. The Smart Notes feature — which already does summarization, flashcard generation, and quiz generation via a cloud-hosted LLM — is a real, used feature. Campuspadi SmartNotes Lite is a proof-of-concept that the same core value can be delivered without any cloud dependency.

### Why Offline Matters for This Specific Use Case

Unlike a general chatbot — where offline removes convenience but the user can work around it — a study session has a specific timing constraint: the student is at their desk with their notes, about to revise or prepare for an exam. If the tool requires internet at that moment and internet is unavailable, the tool has zero value at exactly the moment it was needed. The offline constraint is load-bearing for this use case, not a preference.

---

## 2. Identified Constraints

### Hardware Constraints
- **Target:** ADTC Standard Laptop — Intel Core i5 10th–12th gen or AMD Ryzen 5 3000–5000, 8 GB DDR4, integrated graphics only (Intel UHD / Iris Xe or AMD Radeon integrated), 256 GB SSD, Ubuntu 22.04 LTS
- **Hard RAM ceiling:** 7 GB usable — exceeding this results in disqualification (Stotal = 0)
- **No discrete GPU:** All inference is CPU-only. No CUDA, no ROCm, no Metal. This eliminates GPU-optimised runtimes and makes quantization and thread tuning the primary performance levers.

### Connectivity Constraints
- **Zero network calls at inference time.** The entire pipeline — prompt construction, model inference, output parsing — runs without touching the network. The only permitted network activity is the one-time model download via `download_model.sh`, which is explicitly separated from the inference path.

### Compute Constraints
- **CPU-only inference** means tokens-per-second is lower than GPU-based systems. This makes model size and quantization level the primary knobs for Sperf (30% of total score).
- **Context window management:** longer notes consume more KV cache RAM. The pipeline is designed for single-document, bounded-length notes — not multi-document retrieval — which keeps context length predictable.

### Data Constraints
- **No external retrieval.** The model only ever sees the note the student provides, plus the system prompt. There is no retrieval-augmented generation over an external corpus. This was a deliberate scope decision (see §3).

---

## 3. Design Alternatives and Final Decisions

### Decision 1: Scope — What to Build

**Alternatives considered:**
- **AI Tutor (full offline tutor):** Requires sustained multi-turn reasoning across a broad curriculum. Needs a larger model to not feel broken. Hard to self-validate quality (you'd need domain experts to judge correctness). High RAM and quality risk.
- **AI Padi (offline chatbot):** General-purpose chat is the most commoditized category in this contest — 880 participants, many will attempt a general chatbot. Accuracy is hardest to evaluate objectively. Needs a larger model for general coherence.
- **Full Smart Notes suite (summary + flashcards + quiz + OCR from handwriting):** OCR from handwritten notes adds a second, independent engineering surface (handwriting recognition model) competing for the same RAM budget as the LLM. Doubles the failure surface for Gate 2 audit.
- **SmartNotes Lite — Summary + Quiz from typed notes (chosen):** Single-document, single-user, bounded input. Accuracy is self-checkable (judge against the source note). RAM budget stays focused on one model. The offline constraint is structurally necessary (not decorative) for this use case. Engineering depth can go into what's actually scored — quantization, memory management, prompt faithfulness — rather than feature breadth.

**Decision:** Build SmartNotes Lite. Scope down to Summary + Quiz from typed notes. No RAG, no OCR, no other Campuspadi features.

### Decision 2: No RAG

**What was considered:** Retrieval-augmented generation over a local corpus of reference materials (textbooks, Wikipedia dumps) to enrich summaries beyond what the raw note contains.

**Why rejected:**
1. Adds a second model (embedding model for retrieval) competing for RAM budget alongside the LLM
2. Corpus curation is a separate, time-consuming engineering problem
3. The core task — faithful summarization and quiz generation from a student's own note — does not require external retrieval. A summary that adds outside knowledge to a note is actually less faithful, not more
4. Retrieval quality is hard to validate without ground-truth relevance judgments

**Decision:** No RAG. The model only sees the note text provided by the user.

### Decision 3: No African Language Support

**What was considered:** Adding Yoruba, Igbo, or Hausa support to claim the African Use Case Bonus (+10 points per DevPost rules).

**Why rejected:**
1. Zero validated user demand in Campuspadi's existing ESUT user base for note summarization in Nigerian languages — students currently study in English
2. Adding a language with no demand is a feature built for points, not for users — which contradicts the "real African use case" emphasis in ADTC's own judging criteria
3. A mediocre Yoruba output in front of judges actively scoring for authentic African use case depth would cost more in Sacc than the bonus is worth
4. Aya (Cohere's multilingual model) — the org's own recommended model for this bonus — has no benchmarked track record on the specific summarization/quiz extraction task

**Decision:** English only for this submission cycle. African language support documented as a V2 roadmap item, pending demand signal from the user base.

### Decision 4: Model Selection

**Candidates benchmarked** (all Q4_K_M via Ollama, tested against three real student notes — computing systems, photosynthesis, Nigerian economy):

| Model | Summary Quality | Quiz Faithfulness | Structure | Verdict |
|---|---|---|---|---|
| Gemma 2 2B | ✅ Good synthesis | ❌ Hallucinated on Q3 (OS note) | ✅ Clean | Eliminated |
| Phi-3.5-mini 3.8B | ⚠️ Run-on sentence | ❌ Invented correct answers | ❌ Broken output | Eliminated |
| Qwen2.5 3B | ⚠️ Paraphrase only | ✅ No hallucinations | ❌ No answer markers | Runner-up |
| **Llama 3.2 3B** | ✅ Genuine synthesis | ✅ Faithful across all notes | ✅ Consistent | **Selected** |

**Key findings:**
- Phi-3.5-mini was eliminated immediately — it invented a "correct" answer that directly contradicted the source note (claimed hexadecimal "stores larger amounts than binary," which the note does not say). A model that is confidently wrong about the source material fails the core task regardless of speed or size.
- Gemma 2 2B hallucinated on the OS question — added outside knowledge not present in the note. Same failure mode, less severe.
- Qwen2.5 3B produced no hallucinations but its summaries were essentially paraphrases (sentence-by-sentence rewrites) rather than genuine synthesis. Also failed to mark correct answers consistently.
- Llama 3.2 3B produced genuine summaries, grounded quiz questions, and consistent structured output across all three test notes. One edge case (ambiguous question when the note attributes a property to multiple components together) was resolved via prompt refinement.

**Decision:** Llama 3.2 3B Instruct, Q4_K_M.

### Decision 5: Quantization Level

**Alternatives:**
- **Q2_K:** Smallest RAM footprint, but perceptible quality degradation on structured extraction tasks — quiz questions become less coherent
- **Q4_K_M:** The K-quant suffix preserves more weight information in attention and feed-forward layers than naive Q4. Established practical sweet spot for accuracy vs. RAM on this hardware band. ~2.0 GB weights
- **Q5_K_M:** Marginally better quality, ~2.4 GB — not worth the RAM cost given Q4_K_M already performs well on this task
- **Q8_0:** ~3.2 GB — comfortable in RAM but slower, and accuracy gain over Q4_K_M on this specific task is marginal

**Decision:** Q4_K_M.

### Decision 6: Runtime

**Alternatives:**
- **Ollama:** Good for development and exploration, but abstracts away the llama.cpp invocation. The ADTC profiler invokes llama.cpp directly — Ollama-only setups would not match the audit pipeline.
- **Transformers/PyTorch:** No GGUF support natively, requires GPU for reasonable speed, not appropriate for CPU-only target hardware.
- **llama.cpp (chosen):** Native GGUF support, CPU-optimised with OpenBLAS acceleration for matrix operations, direct integration with `llama-bench` and `adtc-profiler`, no abstraction layers between model and hardware.

**Decision:** llama.cpp with OpenBLAS (`-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS`).

---

## 4. Tools Used and Why

| Tool | Purpose | Why chosen |
|---|---|---|
| `llama.cpp` | Inference runtime | CPU-only, GGUF-native, OpenBLAS-accelerated, matches ADTC audit pipeline |
| GGUF Q4_K_M | Model format | Memory-mapped loading, 4-bit K-quant preserves attention layer quality |
| `llama-bench` | Throughput benchmarking | Native llama.cpp tool, isolates pp vs tg speeds, maps directly to Sperf scoring |
| `adtc-profiler` | Full submission audit | Official ADTC tool — RAM, thermal, throughput in one run, produces submission.json |
| `lm-sensors` + `thermald` | Thermal monitoring | Prevents -10 point thermal penalty (>85°C or throttling detected) |
| Python + `requests` | Pipeline glue | Lightweight, single dependency, calls Ollama API for development; llama.cpp directly for submission |
| Ollama | Development inference | Fast iteration during model selection and prompt engineering on Windows dev machine |

---

## 5. Performance Benchmarks

### Development Machine (i7, 16GB, Windows/WSL2)
*Used for pipeline development and model selection only — not representative of submission performance.*

| Metric | Value |
|---|---|
| Machine | Intel Core i7, 16 GB RAM, Windows 11 / WSL2 |
| Model | Llama 3.2 3B Instruct Q4_K_M via Ollama |
| Generation time (computing systems note) | ~67 seconds |
| Thermal throttling | Not observed |

> Note: 67s on WSL2/Windows is expected to be significantly slower than native Ubuntu with llama.cpp + OpenBLAS due to WSL2 overhead and the absence of OpenBLAS optimisation in Ollama's Windows build.

### Reference Hardware Benchmarks (ADTC Standard Laptop)
*To be completed before Gate 1 submission using `llama-bench` and `adtc-profiler run --mode participant` on Ubuntu 22.04, Intel Core i5, 8 GB RAM, integrated graphics.*

| Metric | Value |
|---|---|
| Machine | Intel Core i5, 8 GB DDR4, integrated graphics, Ubuntu 22.04 |
| Peak RAM (RSS) | TBD |
| Generation speed (TPS) | TBD |
| Time to first token | TBD |
| Thermal throttling | TBD |
| `adtc-profiler` Sperf score | TBD |
| `adtc-profiler` Seff score | TBD |

*Raw benchmark output will be committed to `bench/results/` before submission.*

---

## 6. Prompt Design

The prompt template lives in `src/prompts/smartnotes.txt` as the single source of truth. Key design decisions:

- **Explicit faithfulness instruction:** "do not add outside knowledge, do not infer anything not explicitly stated" — targets hallucination directly, not just output format
- **Exactly one correct answer rule:** "Each question must have EXACTLY ONE correct answer" — fixes the failure mode where models produce questions with multiple defensible answers when the note attributes a property to a group of components
- **No "All of the above":** Explicitly prohibited after Qwen2.5 3B used this to combine multiple correct answers into one option
- **Grounded distractors:** "Wrong options must be plausible but clearly incorrect based on the note alone" — prevents both nonsensical distractors and secretly-also-correct ones
- **Collective-property guard:** "Do NOT ask questions where the note attributes a property to multiple items together" — prevents the CPU components edge case (control unit + ALU + registers all cited together for execution)

---

## 7. Limitations and Future Work

**Current limitations:**
- English only — no African language support in this submission cycle
- Typed notes only — no OCR from handwritten or scanned notes
- Summary and quiz only — AI Tutor and chatbot features are out of scope
- No retrieval — the model is grounded only in the provided note, not external reference material
- 3 quiz questions fixed — future versions should allow configurable quiz length

**V2 roadmap (post-ADTC):**
- African language support (Yoruba, Igbo, Hausa) pending validated demand signal from Campuspadi's user base
- OCR pipeline for handwritten notes using a lightweight vision model
- RAG over a local corpus of course-specific reference materials
- Integration back into the full Campuspadi platform as an offline-capable fallback when connectivity is unavailable

---

*This report will be updated with final benchmark numbers from the ADTC Standard Laptop profile before Gate 1 submission on August 25, 2026.*