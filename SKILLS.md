# SKILLS.md

How recurring tasks should be done in this project. Read the relevant section
before starting a task that matches it.

---

## 1. How to Add a New Feature (Step by Step)

"Feature" here almost always means: a new prompt variant, a new output mode,
or a refinement to summary/quiz generation quality. Given the scope lock in
`AGENTS.md`, it should rarely mean a whole new capability.

1. **Check it's actually in scope.** Does it serve the Summary or Quiz
   pipeline for a single typed note, fully offline, in English? If not, stop
   and flag it to the human — don't build it speculatively.
2. **Write the prompt/logic change in isolation first.** Test it directly
   against the chosen model via a quick CLI call or notebook-style script
   before wiring it into the main pipeline.
3. **Validate against 3–5 sample notes minimum**, not just one. Use
   `sample_notes/`. Check both typical cases and at least one edge case
   (very short note, very long note, note with unusual formatting).
4. **Run the local profiler smoke test** (`adtc-profiler run --mode
   participant --skip-accuracy`) after any change that could affect model
   loading, memory, or inference path — not just after "real" feature work.
5. **Update `REPORT.md`** if the change affects design decisions, benchmarks,
   or constraints described there. Stale `REPORT.md` is a real risk — it's
   judged directly.
6. **Run the `VERIFIER.md` checklist** before calling it done.

---

## 2. How to Write and Run Tests

There are two different kinds of "correctness" here — keep them separate:

### A. Pipeline / code correctness (does it run without crashing)
- Standard unit tests for any parsing, formatting, or CLI logic in `src/`
  that doesn't require the model itself (e.g., prompt templating, output
  JSON/markdown formatting, file I/O).
- Run with `pytest` from repo root. Add new tests under a `tests/` directory
  mirroring `src/`.

### B. Output quality correctness (is the summary/quiz actually good)
This cannot be a simple assert — it requires human or rubric-based judgment.
- For every prompt/model change, run it against the **same fixed set of
  sample notes** in `sample_notes/` so outputs are comparable across runs.
- Self-judge against a simple rubric (see `VERIFIER.md` §2 for the actual
  rubric) — does the summary contain a claim not supported by the source
  note? Are quiz questions answerable from the note alone? Don't just
  eyeball "does this sound fluent."
- Save outputs to `bench/results/quality/` with a timestamp or commit hash
  so regressions are traceable.

### C. Performance benchmarking (not the same as "tests" — see SKILLS §3)

---

## 3. How to Benchmark (Speed / Memory / Thermal)

This is distinct from quality testing — use the actual competition tooling,
not custom timing code, for any number that will appear in `REPORT.md`.

1. **`llama-bench`** for raw throughput (tokens/sec) and prompt-processing
   speed. Isolate `pp` (prompt processing) vs `tg` (text generation) — the
   competition cares about generation speed (`Sperf`).
2. **`adtc-profiler run --mode participant`** for the full picture: memory
   (peak + steady-state RSS), thermal, and throughput together, in the exact
   schema the audit will use. This is the closest thing to a dry run of
   actual judging.
3. **Always run on the i5 / 8GB machine for numbers that go in `REPORT.md`.**
   The i7/16GB machine is for fast iteration only — its numbers are not
   representative and should not be reported as the submission's benchmarks.
4. **Watch for HDD effects on the i5 machine.** Model *load* time will look
   worse than on the actual (SSD-based) audit hardware — that's expected and
   not a real problem. But if you observe RSS climbing toward the 7 GB
   ceiling and performance degrading sharply (not just slow load), that's a
   genuine swap/memory-pressure signal worth treating seriously, since the
   audit machine will hit the same ceiling even on SSD.
5. **Check `vm.swappiness` and consider `--mlock`** (per the org's own
   recommended reading) on the i5 box specifically, to keep the model pinned
   in RAM and get trustworthy steady-state numbers rather than swap-skewed
   ones.
6. **Record every benchmark run's raw JSON output** in `bench/results/`,
   named with a date and the model/quant combination tested
   (e.g. `2026-06-25_qwen2.5-3b-q4km.json`). Never overwrite previous runs —
   comparison across attempts is part of how design decisions get justified
   in `REPORT.md`.

---

## 4. How to Handle Errors and Edge Cases

- **Model fails to load / OOM on the i5 box:** This is not a "just reduce
  context length and move on" situation — it's signal that the current
  quant/model choice may not survive the audit's 7 GB ceiling. Log it in
  `LESSONS.md` immediately, and flag to the human before quietly downsizing
  the model — that's a project-level decision, not a code-level one.
- **Note text is very short (a few lines) or very long (multi-page):**
  Both are realistic real-world inputs (a quick lecture note vs. a full
  chapter). Test both. Don't assume the happy-path note length seen in early
  examples is representative.
- **Model produces a quiz question not answerable from the note:**
  This is an accuracy failure, not a formatting one. Don't try to patch it
  with stricter formatting instructions alone — it likely needs prompt
  redesign (e.g., explicit "only ask questions answerable from the text
  above" instruction) and re-validation across the sample set.
- **`download_model.sh` fails or is non-idempotent:** This blocks the entire
  profiler pipeline and is a Gate 1 submission blocker. Treat as high
  priority. Test by running it twice in a row and confirming the second run
  exits cleanly without re-downloading.
- **`adtc-profiler` schema validation fails:** Read the exact validation
  error — the schema is strict (`additionalProperties: false` throughout),
  so a typo'd or extra field in `metadata.json` will fail loudly. Don't
  guess at a fix; check the field against the schema requirements named in
  `README.md`'s field reference table.

---

## 5. Project-Specific Patterns to Always Follow

- **Single source document, single user, no aggregation, no retrieval.**
  Every pipeline change should be checkable against this constraint: does
  it still take exactly one note as input and produce summary/quiz grounded
  only in that note's text? If a change requires anything else as input,
  it's out of scope.
- **Prompts should ask for structured, parseable output** (e.g., clearly
  delimited quiz questions) — judges and the hidden-prompt audit will run
  this against notes we haven't seen, so brittle output parsing is a real
  risk, not a cosmetic one.
- **Two test prompts in `metadata.json` must be genuinely representative**,
  not cherry-picked best cases — organizers add two hidden prompts in the
  same domain, so an overfit pair will be caught.
- **Every design decision that trades off accuracy vs. speed vs. memory
  should be written down in `REPORT.md` as it's made**, not reconstructed
  from memory later. Treat `REPORT.md` as a living document, not a
  end-of-project writing exercise.
