# Final Phase 3 batch: freeze record

Written 2026-09-28 during the laptop pre-flight, before any job of the final batch was submitted. The SHA-256 values
are of the LF-normalised file contents (CRLF -> LF before hashing), computed by Python on the laptop working tree.
After the deploy script strips `\r`, a plain `sha256sum` on the HPC gives the same values.

## 1. Pre-registration

| SHA-256 (LF) | File |
|---|---|
| `1b6eb915424209250708ed99d8618ff31be70cb641b0e31d718d455c9c59cc63` | `phase3/evidence/PREREG_FINAL.md` |
| `3613542b2d363e10b9e2d6870e3ec584c1eb00c44098e8b6be04254124aa7c51` | `phase3/runner/analyze_phase3.py` (`--final` implements the pre-registration and amendment A1; `main()` still reproduces `evidence/phase3_run/` byte for byte) |

Amendment A1 to PREREG_FINAL.md (2026-09-28 19:43 IST, section 9) was made before any job of the final batch was
submitted, and no result of the final batch existed. It adds the processor-level sensitivity (Address_select signed
off by tb.v) and the exploratory gap/default-advice counts. The hash above is of the amended file.

## 2. Code that runs on the HPC

| SHA-256 (LF) | File |
|---|---|
| `42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff` | `src/interpreter/stitch_interpreter.py` (production, unchanged; equals every Phase 3 `metrics.json`) |
| `29321afc43fcef167876eec38a492383539b1e53c508a510d4716dd0136c7dec` | `src/interpreter/stitch_interpreter_v3.py` (`V3_VERSION = "3.0.1"`, unchanged) |
| `90b1403916c75829b95cc70273545f9b8a75638c227ee21f57a26ca332bfe344` | `src/interpreter/_v3_parsers.py` (unchanged) |
| `886bb444f1cf7585fd4c9587c6b527a8e1beebc72d6926231869c277808cf847` | `phase3/runner/system_prompt.txt` (unchanged) |
| `56d177b2bb076013a0fa29290fcfbf8c0f4c1f256d49e09d94ab3dd1080de2d0` | `phase3/runner/p3_eval.py` (unchanged) |
| `119611fe10f2e23a2dc4f7c0c85ce20f7a176fa1311c26ea56b98b1087b76a36` | `phase3/runner/stitch_runner_p3.py` (was `ce78ca4fc2fccf9efee25ed038f62149b69ecbf26660d8682c1c76667978fc06` in the 990 runs; additive diff below) |
| `7115a8a9fd27a3ab3f0ec89b99f6b825dcd8628e37d4e9eb47662069feab5206` | `phase3/runner/compose.py` (unchanged) |
| `63b92e0ce3e67dfa6ed923b20f6486e43fbaf700c3290633b108a737cd2a314a` | `phase3/hpc/common_env.sh` (one Ollama port per job) |
| `ed8e19bbc69741abed91106007e99d5fd4c215abb508363bbe9e3df60e46e1cd` | `phase3/hpc/phase3_run.slurm` (unchanged) |
| `6f35b75a46424df708529d6775ca6ed66a318862285c426b2a533d8748941bfa` | `phase3/hpc/phase3_gate.slurm` (+ G5 baseline_gate check) |
| `6738b1045e103f9a82d2f7450454f2b1316f51471dcfb0f778f248597e3d043b` | `phase3/hpc/pull_ollama_models_phase3.slurm` (`P3_PULL_MODELS`, `df`, before/after `ollama list`) |
| `839a0b176e78e301ef79572c8f5271cba34ae9b6049000834858ef8c32d0ff57` | `phase3/hpc/phase3_compose.slurm` (honours `P3_OUT`) |
| `ea7f6d77c84099b6f692dcaa5aaf5324b8c1d4f4b30f22b3611853b0699ee40a` | `phase3/hpc/models_phase3.txt` (+ `qwen2.5-coder:32b`) |
| `6e3fe03d42a8937c15814545ac1bafb3ae739acdc2e92dc7bab25167669e5b13` | `phase3/hpc/deploy_phase3.ps1` (one tar without `phase3/results`) |
| `6f9ec807a0adfa5303709711e909fc1f6b18f242c466d4a441c6b6fd8fc085d7` | `phase3/hpc/check_final_batch.sh` (read-only status check, new) |

Runner diff against the 990-run version (additive only):
- `baseline_gate` is added to `CONDITIONS`, and `--conditions` takes `choices=CONDITIONS`.
- For baseline_gate, each RTL gets a v3 interpretation that is logged and never fed back: `per_iter[].would_fire`
  and `would_class`, plus the run-level `would_fire`, `would_class` and `would_fire_final`.
- Every run records a `provenance` block: node, toolchain, v3 version, the interpreter, runner, evaluator and
  system-prompt hashes, the Ollama model digest, and the tb.v / spec.md / input.v / meta.json hashes.
- Feedback construction, stop rules, escalation and prompts are untouched. baseline_gate reuses the existing gate
  branch of `build_feedback`.

Mock check (`preflight_final/step3_mock_output.txt`): mux3, register_4bit and register_1bit, mock modes `fix_on_2`
and `echo`.
- For the 5 existing conditions, the 26 + 78 prompts are byte-identical between the pre-diff and post-diff runners
  (aggregate hashes `4bb67cc3…` and `f9870666…` on both sides).
- Metrics are identical apart from timestamp, wall time, path and the new provenance block.
- baseline_gate prompts carry only the simulation line plus the gate message, with toolfb 0, sf 0 and would_fire
  logged.
- A misspelt condition exits with code 2.
- Local gate-lite: 66 mock runs, G5 PASS, `44 passed, 0 failed`, dry-run 1,386.

## 3. Tasks: specs, loop testbenches, sign-off testbenches

Specs, inputs, goldens and `tb.v` are unchanged. `tb_signoff.v` is new and used only by the offline scoring.

| task | `spec.md` | `tb.v` (loop, unchanged) | `tb_signoff.v` |
|---|---|---|---|
| Address_select | `9ab0cf5fe61b3ae63e6b005003a47a41ca1d075380849cea250fc69fe838a608` | `42a2d7c8b6de9b88458c014afcbc18827e61632a9c681be624684857acab1d6a` | `51a37558fb657d96ce11ef4fbe71efb7d571d79e3f64e55cae3fdfed61b6c979` (spec-complete) |
| MuxPC | `156343dbe04f7dbfac832d5c935a2a786c20cdcf9645cf5d4327d8dd95e57c34` | `3075112ab48dd34c6f12a53e464112b192cfb00b9474fc687ed0f9476f081b7b` | identical to tb.v |
| execute_mux | `358e347e5a51931118b16010007c44f75eaf779d0bd88164de0e7a90b26b5f87` | `4889786d4f9300142b139bd8efc9d4d1ca7af219e9214555273e604781b5bedb` | identical to tb.v |
| mem_wb_mux | `e86e0a29d8076e0b81f834553bf5bb86e00dab62a4a015c76106519289d24d84` | `eb16d973f2dabaf2fa06c1561acbd1588ee9e12486936ba01f2f80ae486fdbe6` | `ac308fb12aa5a43ba3f676f6383997357ad8dad55bcb97cb87909ae3fa8c4fdc` (spec-complete) |
| mux3 | `cf58287aefe8f661943af56af8d32526430d280bc6198dd09727d93062621806` | `c3820a3600ca5c73ff750c52931232175e50e639e8fa0d627a12872ec189eafa` | identical to tb.v |
| ni_flit_pack | `7b76ca9bcd2f8349a089fe4a62a61e849671c548ad2ff6e231b3195650ee55a8` | `1ae91d19cf4e7d821e768baeb6ab066dd2aa9c5004e63e43368a06f1d1b3ae78` | identical to tb.v |
| noc_xbar4 | `cd682e2be7fd9b23660f0ffe0d73d8ce08b5110927925b11c7bd2ce6077a4ca8` | `2107474fa86e4e68327311d36cbf64469cb010039e90571001335b6469d1ecd1` | identical to tb.v |
| register_1bit | `068063b5edb5065fd003d0a961f92046b2c82f6518bb16814d39c0c537c7f1fb` | `a4645b87d1f460d7dd5b0bf4294b63eb3263f91367546622afd379f7ae555890` | identical to tb.v |
| register_32bit | `fa09b37176e93ede62be3690c63766566caf1dadc7bf8be567c0e2d9893cb640` | `73f3f17e7a0130165d80588c19b27e85800696aef45ff0933219024a09215ef7` | identical to tb.v |
| register_4bit | `b983d18616350abeedfea5b4a3deb9773dc6bf1949eab5973056a3ff1bbca3fe` | `ada034ea35207d5d93c912f64585a876781cfe9a0fa1d2ee9ee0ca434124bb1b` | identical to tb.v |
| riscv_alu_flags | `99f7d7011d216e11bbaec518d70b577ada51a0b1ddd343f150ac2748cc86326b` | `a5b768b1bd8f330b5a56134697a7e32bf51ad3f4bee8ba673813c62d0be53720` | identical to tb.v |

Every spec.md and tb.v hash equals the value recorded at the start of this pre-flight. New runs also record them
per run, in `provenance`.

### Equivalence audit that decides each tb_signoff.v

The audit ran Yosys `equiv_make` / `equiv_simple -seq 5` / `equiv_induct` of each clean_pass final candidate against
golden, plus a count of constant-driven output bits, on every clean_pass run of all 11 tasks, baseline included.
Golden is proven equivalent to itself on every task. Sources: `phase3_run/POSTHOC_CHECKS.md` for the six sim-silent
tasks, and `preflight_final/step2_equiv_output.txt` for the five sim-visible tasks plus mem_wb_mux under its sign-off
testbench.

| task | clean runs | equivalent | equivalent on legal inputs (class ii) | testbench gap (class i) | other (class iii) | decision |
|---|---|---|---|---|---|---|
| MuxPC | per POSTHOC_CHECKS | yes | PCsrc = 2'b11 ("does not occur") | 0 | 0 | identical |
| mux3 | per POSTHOC_CHECKS | yes | sel = 2'b11 ("does not occur") | 0 | 0 | identical |
| execute_mux, register_1bit, riscv_alu_flags | per POSTHOC_CHECKS | all | 0 | 0 | 0 | identical |
| mem_wb_mux | 58 | 42 | 0 | 16 (memwrite = 0, FWD = 2'b11 unchecked) | 0 | spec-complete |
| Address_select | 49 | 8 | 0 | 41 (J_addr checked only on non-flushed JAL) | 0 | spec-complete |
| ni_flit_pack | 36 | 36 | 0 | 0 | 0 | identical |
| noc_xbar4 | 47 | 0 | 47 (gnt not one-hot; spec: one-hot or zero) | 0 | 0 | identical |
| register_32bit | 69 | 69 | 0 | 0 | 0 | identical |
| register_4bit | 66 | 66 | 0 | 0 | 0 | identical |

No candidate had extra constant-driven output bits beyond golden. None of the not-proven runs is class (iii).

Acceptance checks of the two spec-complete testbenches:

| check | mem_wb_mux (`step1_output.txt`) | Address_select (`step2_Address_select_output.txt`) |
|---|---|---|
| (a) golden passes | PASS | PASS |
| (b) every class (i) run fails it | 16/16 | 41/41 |
| (c) every other clean run still passes | 42/42 | 8/8 |
| (d) gap-only mutant: passes tb.v, fails sign-off | PASS / FAIL | PASS / FAIL |
| (e) defective input | passes tb.v, fails sign-off (expected under Option A) | fails both (task is sim-visible anyway) |
| candidates passing sign-off but failing tb.v | 0 | 0 |

Address_select note: the spec defines `J_addr = X + PC` unconditionally. The 41 class (i) candidates drive
`J_addr = 0` (in one run, `X`) when the instruction is not a non-flushed JAL. In the MPSoC, MuxPC reads J_addr only
when PCsrc = 2'b01, which is exactly the case tb.v checks. So these candidates violate the leaf specification but
cannot be observed at the processor level. They are scored as failing, as the plan's rule requires (class i =
spec-defined behaviour differs).

## 4. Final candidates on disk (A1)

For all 990 runs, `final_candidate` in `metrics.json` ends in `iter{llm_calls}/dut.v`, and that file exists and is
non-empty. Every `per_iter` candidate file exists as well. Three superseded `error.json` files sit next to successful
`metrics.json` files (llama3.2:3b raw_adv register_4bit rep1, sem_adv_v2 and sem_adv_v3 riscv_alu_flags rep1). New
runs write the same layout: `iter{n}/dut.v`, where n = LLM calls.

## 5. Git state at freeze

Branch `phase3-setup`, HEAD `f10a90b`, nothing committed by this pre-flight.
- Modified by this pre-flight: `phase3/runner/stitch_runner_p3.py` and `phase3/hpc/{common_env.sh,
  deploy_phase3.ps1, models_phase3.txt, phase3_gate.slurm, pull_ollama_models_phase3.slurm}`.
- New from this pre-flight: `phase3/tasks/*/tb_signoff.v`, `phase3/evidence/{FREEZE_FINAL.md, PREREG_FINAL.md,
  signoff_cache.json, preflight_final/}` and `phase3/evidence/phase3_run/{POSTHOC_SIGNOFF.md,
  posthoc_signoff.json}`. `phase3/runner/analyze_phase3.py` and `posthoc_checks.py`, both still untracked, are
  extended.
- Uncommitted from before this pre-flight: `docs/EXT_FINAL_REVIEW.md`, `handoff.md`, `phase3/README.md`,
  `phase3/designs/SANITISATION.md`, `phase3/docs/*`, `phase3/hpc/phase3_compose.slurm`,
  `phase3/runner/audit_existing_runs.py`, the deletions (`STITCH_EXT_FINAL.pdf`,
  `phase3/docs/PAPER_SECTION_compositional_integrity.md`, `plans/research_plan_v4.md`), and the untracked `paper/`,
  `phase3/docs/archive/`, `phase3/evidence/phase3_run/`, `phase3/runner/{phase3_figures.py, templates/}` and
  `plans/archive/`.
- Changed during this session but not by this pre-flight: `.gitignore` (modified) and `phase2/frontier/` (untracked).
