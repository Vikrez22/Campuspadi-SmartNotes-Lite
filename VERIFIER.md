# VERIFIER.md

The standard the agent checks against before saying a task is "done." This
file exists because "looks done" and "is done" are different things on a
judged, audited submission — go through this explicitly, don't just eyeball
it.

---

## 1. Checklist Before Claiming Any Task Complete

Go through these in order. If any answer is "no" or "not sure," the task is
not done — either fix it or flag it to the human (see §3).

**Scope**
- [ ] Does this change stay within the agreed scope (single note in, Summary
      and/or Quiz out, English only, no retrieval, no other Campuspadi AI
      suite features)? Per `AGENTS.md` §5.

**Code-level**
- [ ] Does the code run from a clean clone (no hardcoded local paths, no
      missing files)?
- [ ] Do existing tests still pass (`pytest`)?
- [ ] Is there zero network activity anywhere in the inference path itself
      (only `download_model.sh` is allowed to touch the network, and only
      before profiling starts)?
- [ ] Is `model/` and every `*.gguf` file still excluded from git?

**Schema / submission-format level**
- [ ] If `metadata.json` was touched: does it still validate against the
      ADTC schema (`additionalProperties: false` on every object — a typo'd
      or extra field will hard-fail)?
- [ ] Are there still exactly 2 entries in `test_prompts`?
- [ ] Does `_runtime.model_path` still point to a file that actually exists
      after running `download_model.sh`?

**Output quality**
- [ ] Was the change validated against multiple sample notes, not just one
      happy-path example (see §2 below for how to judge quality)?
- [ ] Were any new benchmark numbers produced via the real tools
      (`llama-bench` / `adtc-profiler`), not hand-estimated?

**Documentation**
- [ ] Is `REPORT.md` still accurate after this change (design decisions,
      benchmarks, constraints)?
- [ ] Has `LESSONS.md` been updated if anything took more than one attempt
      or behaved unexpectedly this session?

Only once every applicable box is genuinely checked — not assumed — is the
task done.

---

## 2. How to Know Output Is Actually Correct vs. Just Looks Correct

This project's hardest failure mode is plausible-sounding but wrong output —
a fluent summary that misstates something in the note, or a well-formatted
quiz question that isn't actually answerable from the source text. Fluency is
not correctness. Check specifically for:

**Summary quality**
- Every factual claim in the summary must trace back to something actually
  stated in the source note. If the model adds outside knowledge not present
  in the note (even if true), that's a faithfulness failure for this task,
  not a bonus.
- The summary should not contradict the note.
- Re-read the note and the summary side by side — don't judge the summary in
  isolation from memory of "what it probably said."

**Quiz quality**
- Every question must be answerable using only the source note's content.
- The marked correct answer must actually be correct per the note.
- Distractors (wrong options, if multiple choice) should be plausible but
  clearly wrong on close reading — not nonsensical, not secretly also
  correct.

**Process, not vibes**
- Don't judge quality from a single run. Model outputs vary — run at least
  twice on the same note for any change you're about to ship, and check both
  outputs, not just the first one that looked good.
- When evaluating a prompt or model change, compare against the *previous*
  version's output on the *same* sample notes — relative judgment across a
  fixed set is more reliable than absolute judgment of a single new output.

**Numbers (benchmarks)**
- A number is "correct" only if it came from a saved run in `bench/results/`
  using `llama-bench` or `adtc-profiler` — not estimated, not remembered
  from a previous session, not interpolated.
- If a benchmark number looks surprising (much faster/slower or much more/
  less memory than expected), re-run it before trusting it. Flukes happen;
  don't write a fluke into `REPORT.md`.

---

## 3. When to Stop and Flag a Human Instead of Continuing

Stop and ask rather than deciding alone when:

- **A change would alter a competition claim** — `african_alpha_claim`,
  `budget_laptop_claim`, `domain`, or the chosen base model/quantization
  level. These are project-level decisions with real downstream
  consequences, not implementation details.
- **The model doesn't fit in the RAM budget on the i5 machine** even after
  reasonable tuning — this might mean a different model or quant level
  entirely, which is a scope-affecting decision.
- **Output quality is consistently poor** (factual drift, unanswerable quiz
  questions) after a couple of honest prompt-iteration attempts — this might
  mean the chosen model isn't capable enough for the task at this size, which
  is a bigger decision than a prompt tweak.
- **Something in the official rules/schema is ambiguous or contradicts
  itself** (this has already happened once — the schema's domain enum is
  missing `autonomous_ai_agents` even though the README lists it as valid).
  Don't silently pick an interpretation and proceed — note the discrepancy
  and ask, since the wrong guess could be a hard validation failure later.
- **A deadline-sensitive decision needs to be made** (e.g., whether there's
  still time to attempt something beyond the locked scope) — time-vs-scope
  tradeoffs are the human's call.
- **You genuinely don't know if something is a bug or intended behavior** in
  the official tooling (`adtc-profiler`, the template repo) — these are
  external, evolving repos; don't assume your reading of the code is more
  authoritative than asking.

When in doubt, the cost of asking is small. The cost of a wrong autonomous
call on a competition submission can be a disqualification or a wasted week.
Default to asking.

---

## 4. Definition of Done

A task is only done when:
1. Every applicable box in §1 is checked.
2. Output quality has been verified per §2, not assumed.
3. Nothing in §3's stop conditions applies — or if one did, it was actually
   raised and resolved with the human, not worked around silently.
4. `LESSONS.md` has been updated (or explicitly confirmed to need no update)
   per `AGENTS.md` §7.

If all four aren't true, the task isn't done yet — say so plainly rather than
reporting completion.
