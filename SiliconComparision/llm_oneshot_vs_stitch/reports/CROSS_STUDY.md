# Cross-study summary (pipeline/cross_study.py)

One model (qwen2.5-coder:32b), one run per arm, same options in every study (T=0.1, no seed, num_ctx 32768, budget 6 calls). N=1 per study: counts, no rates. NEW = generated in this study; REUSED = the 2x2 result of the same module (golden and prompt match, reports/REUSE.md). Per-arm values are oneshot / simloop / stitch and count NEW modules only.

| | 2x2 (top top_2x2_router) | mesh3x3 (top top_3x3_router) | ni (top ni_pair) |
|---|---|---|---|
| modules NEW / REUSED | 34 / 0 | 1 / 33 | 4 / 5 |
| so_clean (of the NEW modules) | 9 / 14 / 14 | 0 / 0 / 0 | 0 / 0 / 0 |
| so_clean NEW modules without children | 9 / 14 / 14 (of 16) | 0 / 0 / 0 (of 0) | 0 / 0 / 0 (of 2) |
| so_clean NEW modules with children | 0 / 0 / 0 (of 18) | 0 / 0 / 0 (of 1) | 0 / 0 / 0 (of 2) |
| so_clean under STITCH only | 0 | 0 | 0 |
| attributable structural gains of STITCH (different prompt) | falling_edge_pulse_generator, top_2x2_router | none | none |
| regressions vs retry: attributable / sampling | none / ip_link, irs | top_3x3_router / none | none / new1 |
| dominant failure classes (primary label, final files) | ports (9 / 6 / 7), syntax (11 / 4 / 4) | function (1 / 1 / 0), ports (0 / 0 / 1) | function (2 / 2 / 2), ports (2 / 1 / 2) |
| audit classes of failing finals (all arms) | LLM_BUG 63, TB_ARTIFACT 2 | LLM_BUG 3 | LLM_BUG 12 |
| pure design composes | n / n / n | n / n / n | n / n / n |
| hybrid_signoff composes | n / n / n | n / n / n | y / y / y |
| LLM modules in hybrid_signoff, NEW / REUSED | 9 / 0 ; 14 / 0 ; 14 / 0 | 0 / 9 ; 0 / 14 ; 0 / 14 | 0 / 2 ; 0 / 2 ; 0 / 2 |
| hybrid_signoff drop-in failures (all formally equivalent to golden) | dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh | dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh | none |
| hybrid_signoff with those swapped back composes | y / y / y | y / y / y | - / - / - |
| golden-RTL findings | 1 | 2 | 4 |

so_clean NEW counts: 2x2 of 34, mesh3x3 of 1, ni of 4. composes = the whole design passes its top testbench (2x2, 3x3: cycle-exact mesh tb; ni: ni_pair property checks).

## Golden-RTL findings

- 2x2: blocking-assignment flops in the golden race in the cycle-exact mesh tb (reports/ASSEMBLY.md)
- mesh3x3: nine mesh-edge data outputs wired to implicit 1-bit nets in mesh_router3x3.v (reports/HANDWRITTEN.md); the 2x2 golden blocking-assignment race carries over to the cycle-exact 3x3 mesh tb (reports/ASSEMBLY.md)
- ni: new1 and nidepack connect router_fifo positionally with its last outputs shifted (full_int <- full_ext, empty <- full_int) (README, reports/FAILURE_AUDIT.md); rp1's j is initialised at declaration and never reset: one packet per power-up, undefined in silicon (specs/rp1.md); depack holds wr_en after a word, so the FIFO rewrites the word until it fills (specs/depack.md); golden halves joined directly in ni_pair misread each other on the same clock edge (reports/NI_PAIR_TRACE.md)

## Conclusions across studies

1. Retrying repairs 2x2 modules but none of the NEW 3x3 and NI modules. In 2x2, so_clean rises from 9 (one-shot) to 14 / 14 (simloop / stitch); in mesh3x3 and NI it stays at 0 / 0 / 0 of 1 and 0 / 0 / 0 of 4. This contradicts the 2x2 reading that retrying repairs failures in general: here it repaired none of the 5 NEW modules.
2. The 2x2 split between leaf and hierarchical modules holds only in part. No NEW module with children is so_clean in any arm of any study (2x2 0 / 0 / 0 (of 18), mesh3x3 0 / 0 / 0 (of 1), NI 0 / 0 / 0 (of 2)). The 2x2 "leaf modules, yes" does not carry over to NI: its two leaf modules, the state machines rp1 and depack, are so_clean in no arm (0 / 0 / 0 (of 2)).
3. STITCH does not produce a so_clean module that the simulation-only retry misses, in any study (STITCH only: 2x2 0, mesh3x3 0, ni 0). Its attributable effects are single flags: 2x2 gains on falling_edge_pulse_generator, top_2x2_router; mesh3x3 one regression after a STITCH prompt (top_3x3_router); NI none (the new1 regression is sampling).
4. The failures are the LLM's: every failing final file of mesh3x3 and NI is LLM_BUG, as in 2x2 apart from its two asynch_comparator TB_ARTIFACT cases. No study has a SPEC_AMBIGUITY case and NI has no GOLDEN_DEFECT case (audit classes: 2x2 LLM_BUG 63, TB_ARTIFACT 2; mesh3x3 LLM_BUG 3; ni LLM_BUG 12). The one NI file that could have failed only through the golden's port shift (new1, simloop) still mismatches the shift-corrected golden.
5. No pure design composes in any study. In 2x2 and 3x3 the hybrid_signoff meshes fail the cycle-exact mesh tb only through the same modules (dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh in 2x2; dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh in 3x3), each formally equivalent to its golden; with them swapped back the meshes compose. The NI hybrid_signoff design composes, but it keeps no NEW module (LLM modules NEW / REUSED: 0 / 2): it measures REUSED 2x2 modules only.
