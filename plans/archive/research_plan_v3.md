> **SUPERSEDED by research_plan_v4.md. Retained for history.**
>
> Archival note: this document is written as advisory prose addressed to
> the project lead ("your plan", "your handoff doc"). That voice is
> preserved here as part of the historical record. Its technical content
> — the model shortlist in §A/§B and the failure-class taxonomy in §D —
> is carried forward and restated in neutral form in research_plan_v4.md
> §6, which is the version to cite.

# STITCHAdv Research Plan v3 — Extension Layer

**Extends:** `research_plan_v2.md` (v2 is unchanged and still governs Phase 1). This doc adds: RTL-specific model picks, frontier model updates, a corrected Phase-2 module shortlist, a folder restructure, and an optional learned-escalation extension. It does **not** relax v2's Phase 1 gate or its bias-proofing rules — see the note below before reading further.

**Correction logged 2026-08-17:** a request to hand-pick benchmark modules by whether STITCH does well on them was declined and redirected to Rule 1 (select by pre-registered failure class). This note exists so the proposal is not raised again.

---

## A. RTL-specific model additions (Phase 3.1, concrete picks)

Your plan named RTLCoder as the first pick and reasoned about the RTLCoder/deepseek-coder controlled pair. Adding two more, chosen for (a) being runnable locally via Ollama/llama.cpp with existing hardware, (b) covering a genuinely different base architecture or training method so the three aren't redundant:

| Model | Base | Method | Why it earns a slot | Runs via |
|---|---|---|---|---|
| **RTLCoder-DeepSeek-v1.1** | deepseek-coder-6.7b | Instruction-tuned on GPT-3.5-synthesized description/code pairs | Already justified in v2 — controlled pair against your existing `deepseek-coder:6.7b` results | Ollama (GGUF exists) |
| **CodeV-R1-Qwen-7B** | Qwen2.5-Coder-7B | RLVR (reinforcement learning w/ verifiable reward) — the newest-generation RTL training method, distinct from instruction-tuning | You already have `qwen2.5-coder:14b` (non-RTL-tuned) in the suite. This is the controlled pair on the *Qwen* side, and RLVR is a different intervention than RTLCoder's SFT — two fine-tuning methods, not one, doubles the value of the "does fine-tuning make STITCH redundant" question | GGUF: `mradermacher/CodeV-R1-Qwen-7B-i1-GGUF` |
| **CodeV-CL-7B** | CodeLlama-7B | Instruction-tuned, multi-level-summarization data pipeline (distinct from both RTLCoder's and CodeV-R1's data strategy) | Third base architecture (Llama family), keeps the model set from being all-Qwen/all-DeepSeek | GGUF: `tensorblock/CodeV-CL-7B-GGUF` or `mradermacher/CodeV-CL-7B-GGUF` |

All three are Apache/MIT-family licensed open weights, no API cost, and fit your existing local hardware profile (7B-class, same tier as models already benchmarked at 21 min CPU-offload).

**Framing for the paper:** this becomes a 2×3 natural experiment — {SFT, RLVR} × {is escalation still net-positive, does escalation rate drop}. That's a stronger version of your existing §3.1 question, not a new one.

**Sequencing:** per v2 §3.1, this starts only after Phase 1 clears its gate. Setting up the Ollama configs now is fine; running the full sweep isn't.

---

## B. Frontier models — current landscape (Aug 2026)

Your handoff doc's competitive table used `gemini-2.5-flash/pro`. Current generation as of this week:

| Provider | Current relevant models | Notes |
|---|---|---|
| **Anthropic** | `claude-sonnet-5`, `claude-opus-4-8` | Sonnet 5 is the natural mid-tier comparison point; Opus 4.8 if budget allows an upper-bound run. (Fable 5 / Mythos-tier exist but are a different access track — not needed here.) |
| **Google** | `gemini-3.1-pro` (flagship), `gemini-3.6-flash` / `gemini-3.7-flash` (workhorse) | The 2.5 family (used in your paper) is scheduled for shutdown Oct 16, 2026 — migrating to 3.x isn't optional if you want the numbers reproducible past that date. |
| **Moonshot** | `kimi-k3` (2.8T MoE, 1M context) | API live now at platform.kimi.ai, OpenAI-SDK compatible. Open weights published July 27, 2026, so local self-hosting is technically possible but far beyond your local hardware — API only, as your plan already assumed. |

This matches v2 §3.2–3.3 almost exactly; the only real update is Gemini's version number and the concrete Claude model strings.

**The graph you asked for:** plot escalation rate (and separately, tool-invocation count) on the y-axis against model tier on the x-axis, grouped: {sub-8B local} → {RTL-tuned 7B} → {12–14B local} → {frontier API}. This directly operationalizes the hypothesis already in your v2 §3.2 — *"escalation cost scales inversely with model capability"* — and turns a paragraph of prose into the paper's one clean scaling figure. Overlay pass-rate as a secondary line so the same chart shows both "does it still help" and "how much cheaper does it get."

**Kimi K3 caveat (already flagged in v2 §3.3):** always-on thinking mode risks breaking the Stage-2 regex code extraction. Run 2 modules first, inspect raw completions, decide before committing budget — don't skip this step.

---

## C. Optional: learned escalation trigger (extends C1, not a new contribution)

You said you're open to ML training if it makes STITCH better. Your own Phase 6 rules out fine-tuning *the generation model* (correctly — that's RTLCoder's job, not yours, and doing it would blur the paper's differentiator). But there's a narrower, defensible target that doesn't conflict with that scope decision:

**Train a small classifier for the escalation trigger itself**, replacing the fixed `STUCK_THRESHOLD` with a learned one. Inputs: error category, error-message embedding or hand features (error type repeated?, diff size between iterations, token count), iteration number. Output: escalate now / don't. Trained on Phase 1's own N≥3-sample data once it exists (label = "did escalating at this point help in the replay").

This is additive to C1, not a replacement: report both `sem_escalate_fixed(k)` and `sem_escalate_learned` as two rows in the same table. It only makes sense to attempt *after* Phase 1 shows the fixed-threshold version works — if fixed escalation doesn't beat baseline, a learned trigger has nothing to learn from. Flagging it now so it's on the roadmap, not blocking anything.

---

## D. Phase 2 module shortlist — by taxonomy gap, not by outcome

Candidates for the three rows your own v2 table marks "No — real gap," plus the Rule-2 adversarial/control modules the plan requires. None of these have been run yet — I have no idea which ones STITCH will help on, and neither will you until they clear the §2.1 oracle gates and the dev/held-out split.

| Target class | Candidate module | Design intent |
|---|---|---|
| Inferred latch (Yosys-only, no Verilator overlap) | `mode_mux_latch` | Combinational `case` covering 3 of 4 select states; all inputs read (so Verilator's UNUSEDSIGNAL stays silent), but Yosys infers a latch on the missing branch. Tests whether the interpreter's latch directive fires cleanly without piggybacking on an unused-signal warning, unlike `decoder_3to8`. |
| Combinational loop | `priority_chain_comb` | Chained `assign` statements where a later grant signal is accidentally used in computing an earlier one (classic feedback typo). Yosys should flag a combinational loop; Icarus compiles and simulates it "successfully" with X-propagation masked. |
| UNDRIVEN — undeclared vs. unassigned (§5.2 disambiguation) | `partial_output_a` / `partial_output_b` | Two variants: (a) an output port that never appears on any LHS at all (true undriven), (b) an output assigned only inside some branches of an `if`/`case` (partial-assignment, latch-adjacent). Tests whether the interpreter correctly distinguishes these instead of collapsing both into the same `"ambiguous"` fallback your handoff doc flags as still unresolved. |
| Control class (Rule 2 — STITCH must NOT help) | `crc8_checksum` | Compiles, synthesizes, and simulates cleanly; wrong XOR tap order produces incorrect output. No EDA-visible signal exists for any tool to catch — same shape as `alu_ops`/`lfsr_8bit`, new instance so it isn't reused across suites. |
| Second BLKSEQ instance (Rule 2 — adversarial) | `shift_reg_blocking` | Blocking assignments inside a clocked always block causing a race between stages, structurally different from `comb_sensitivity`'s specific mistake so it isn't just a duplicate of your one known-harmful case. |

That's 6 candidates against 3 confirmed gaps + Rule 2's requirement — comfortably inside the 8–14 budget once you add 2–8 more from the thinner-coverage classes (`MULTIDRIVEN`, sequential reset-timing). All six still have to pass all five §2.1 oracle gates and go into the frozen dev/held-out split (Rule 3) before anyone knows whether they help.

If your benchmark drive has modules that fit these same gap classes, treat them as *candidates entering the same oracle-gate and dev/held-out pipeline* — not as a separate "unbiased" set added after the fact to offset a biased one. One pipeline, one set of rules, applied before any run happens.

---

## E. Unified folder structure

```
STITCH_v3/
├── docs/
│   ├── MLCAD_paper.pdf
│   ├── STITCH_PROGRESS_AND_FINDINGS.md      # predecessor, unchanged
│   ├── research_plan_v2.md          # governs Phase 1, unchanged
│   ├── research_plan_v3.md          # this file
│   └── STITCH_JOURNAL_HANDOFF.md
├── interpreter/
│   ├── stitch_interpreter.py                 # the fixed version — canonical
│   └── tests/                                # 16 unit tests
├── runners/
│   ├── autochip_runner.py                    # baseline, unchanged
│   └── escalation_runner.py                  # new Phase 1 runner (§1.1 of v2)
├── models/
│   ├── local_config.yaml                     # 5 existing + RTLCoder/CodeV-R1/CodeV-CL
│   └── frontier_config.yaml                  # claude-sonnet-5, gemini-3.1-pro, kimi-k3
├── benchmark/
│   ├── v20_baseline/                         # frozen, existing 20-module suite — do not edit
│   └── v2_extension/
│       ├── taxonomy.md                       # pre-registered failure classes (§D above)
│       ├── candidates/                       # proposed modules pre-oracle-gate
│       ├── manifest.csv                      # per-module gate pass/fail log
│       ├── dev/                              # frozen after split — tuning happens here only
│       └── heldout/                          # untouched until final evaluation
├── results/
│   ├── phase1_escalation/
│   ├── phase2_extension/
│   ├── phase3_models/
│   └── phase4_comparison/
└── analysis/
    ├── aggregate_results.py
    └── stats.py                              # CI / distribution reporting, N≥3 per cell
```

---

## Immediate next actions (supersedes v2's, which still apply underneath)

1. Stand up this structure from the existing `AutoChipAdvFB/STITCHAdv` tree.
2. Add `local_config.yaml` entries for RTLCoder-DeepSeek-v1.1, CodeV-R1-Qwen-7B, CodeV-CL-7B; pull GGUF weights.
3. Add `frontier_config.yaml` entries for claude-sonnet-5, gemini-3.1-pro, kimi-k3.
4. Everything above is infrastructure — **do not run new-model sweeps yet.** Proceed with v2 Phase 1 (escalation runner, N≥3, 5 local models, existing v20 data) and hit its gate first.
5. In parallel (non-blocking): draft `taxonomy.md` and the 6 candidate modules in §D above, run them through the §2.1 oracle gates, log manifest results.
