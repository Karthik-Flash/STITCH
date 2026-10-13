#!/usr/bin/env python3
"""Writes paper/V8_CHANGES.md: every change v7 -> v8, and every Phase 3 number in v8 Section 9/10 and in
PHASE3_MPSOC_v2.tex with the file and line it comes from. Each source is located by substrings that must all
occur on ONE line of the source file; the script fails if any is missing, so every listed source is checked.
Repo root:  python paper/make_v8_changes.py"""
import hashlib
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "phase3/evidence/phase3_final/PHASE3_FINAL.md"
N = "phase3/evidence/phase3_final/PAPER_NUMBERS.md"
Z = "phase3/evidence/FREEZE_FINAL.md"
P = "phase3/evidence/PREREG_FINAL.md"
B = "phase3/evidence/phase3_final/backend_check_output.txt"
R = "phase3/evidence/phase3_run/PHASE3_RESULTS.md"
M = "−"  # minus sign used in PHASE3_FINAL.md contrast names

# (where in the paper, numbers as printed in the paper, source file, substrings that must share one source line)
E = [
    # ---- run counts, pre-registration, backend
    ("S9 intro, 9.4, Table 9, S10: first 990 runs", "990", P, ["| original (990) |", "990 |"]),
    ("S9 intro, 9.4: control arm", "198", P, ["| A: control arm |", "198 |"]),
    ("S9 intro, 9.4: 32B arm; 1,386 = 990 + 198 + 198", "198; 1,386", P, ["| C: 32B |", "198 |"]),
    ("S9 intro, 9.4: API runs (396 = 2 x 198)", "396; 198 each", N, ["provenance over 396 runs"]),
    ("9.4: pre-registration hash", "1b6eb915", Z, ["1b6eb915424209250708ed99d8618ff31be70cb641b0e31d718d455c9c59cc63", "PREREG_FINAL.md"]),
    ("9.4: backend check, identical first responses", "41% vs 41%", B, ["(41%)", "112/270"]),
    ("MPSOC 5: backend check, identical prompts", "90/90", B, ["iter1 prompt byte-identical 90"]),
    ("MPSOC 5: backend check, first-call func_pass", "42/90 vs 44/90", B, ["baseline 44/90", "baseline_gate 42/90"]),
    ("9.4: nine other tasks equivalent; no tied-off output", "(no number)", Z, ["No candidate had extra constant-driven output bits"]),
    ("9.4: cell bootstrap over 66 cells, 1.7 x Wilson (unchanged v7 sentence)", "66; 1.7", R, ["66 (model, task) cells", "1.7 times wider"]),
    # ---- Table 9
    ("Table 9 baseline", "22% (17 to 28) [23%]; 63%; 85%; 1.34; 1,425", N, ["| baseline | 168/198", "43/198 (22%, 17", "125/198 (63%", "1,425", "1.34"]),
    ("Table 9 raw_adv", "53% (46 to 59) [59%]; 12%; 65%; 3.27; 4,396", N, ["| raw_adv | 128/198", "104/198 (53%, 46", "24/198 (12%", "4,396"]),
    ("Table 9 v2", "63% (56 to 69) [68%]; 8%; 71%; 2.83; 3,831", N, ["| sem_adv_v2 | 140/198", "124/198 (63%, 56", "16/198 (8%", "3,831"]),
    ("Table 9 v3", "67% (60 to 73) [74%]; 8%; 74%; 2.51; 3,377", N, ["| sem_adv_v3 | 147/198", "132/198 (67%, 60", "15/198 (8%", "3,377"]),
    ("Table 9 esc", "72% (65 to 78) [80%]; 13%; 85%; 2.99; 3,798", N, ["| sem_esc_restart_v3 | 168/198", "142/198 (72%, 65", "26/198 (13%", "3,798"]),
    ("Table 9 gate", "52% (45 to 59) [56%]; 15%; 67%; 3.39; 3,835", N, ["| baseline_gate | 132/198", "103/198 (52%, 45", "29/198 (15%", "3,835"]),
    # ---- (1)
    ("(1) baseline 125/198 signed off defective; all 108 sim-silent", "125/198 (63%); 108", N, ["(1) baseline on the six sim-silent tasks: signed off 108/108"]),
    ("(1) 18/18 sim-silent signed off, qwen2.5-coder:32b", "18/18", N, ["- baseline: signoff_clean 12/33", "(sim-silent 18/18)"]),
    ("(1) 18/18 sim-silent signed off, claude-haiku-4.5", "18/18", N, ["claude-haiku-4-5-20251001 baseline:", "(sim-silent 18/18)"]),
    ("(1) 18/18 sim-silent signed off, gpt-4.1-mini", "18/18", N, ["gpt-4.1-mini-2025-04-14 baseline:", "(sim-silent 18/18)"]),
    ("(1) latch-free 24% -> 88% (Yosys only, oracle-independent); MPSOC also 65% gate", "24%; 88%; 35/144; 127/144; 94/144", N, ["latch-bearing tasks", "baseline 35/144 (24%)", "sem_adv_v3 127/144 (88%)", "baseline_gate 94/144 (65%)"]),
    # ---- (2)
    ("(2) Table 10 contrast 1, all", "+19.7 [+11.1, +29.3]; <0.001; 42/3; as run +23.7", F, [f"sem_esc_restart_v3 {M} baseline_gate | all", "+19.7 [+11.1, +29.3]", "42/3", "+23.7 [+14.1, +33.8]"]),
    ("(2) Table 10 contrast 1, sim-silent", "+23.1 [+11.1, +37.0]; 0.002; 27/2", F, ["+23.1 [+11.1, +37.0]", "0.002", "27/2"]),
    ("(2) Table 10 contrast 1, sim-visible", "+15.6 [+4.4, +27.8]; 0.022; 15/1", F, ["+15.6 [+4.4, +27.8]", "0.022", "15/1"]),
    ("(2) Table 10 contrast 2, all", "+14.6 [+3.0, +26.3]; 0.021; 43/14; as run +17.7", F, ["+14.6 [+3.0, +26.3]", "0.021", "43/14", "+17.7 [+5.1, +30.3]"]),
    ("(2) Table 10 contrast 2, sim-silent", "+23.1 [+6.5, +39.8]; 0.014; 31/6", F, ["+23.1 [+6.5, +39.8]", "0.014", "31/6"]),
    ("(2) Table 10 contrast 2, sim-visible", "+4.4 [-11.1, +20.0]; 0.688; 12/8", F, ["+4.4 [-11.1, +20.0]", "0.688", "12/8"]),
    ("(2) Table 10 contrast 3, all", "-0.5 [-9.1, +8.1]; 1.000; 16/17", F, ["-0.5 [-9.1, +8.1]", "16/17"]),
    ("MPSOC Table 5 contrast 3, sim-silent", "-2.8 [-13.0, +7.4]; 0.738; 6/9", F, ["-2.8 [-13.0, +7.4]", "0.738", "6/9"]),
    ("MPSOC Table 5 contrast 3, sim-visible", "+2.2 [-11.1, +15.6]; 0.882; 10/8", F, ["+2.2 [-11.1, +15.6]", "0.882", "10/8"]),
    ("(2) Table 10 contrast 4, sim-visible", "-1.1 [-4.4, +2.2]; 1.000; 2/3", F, ["-1.1 [-4.4, +2.2]", "2/3"]),
    ("(2) pre-registered reading R1", "R1", F, ["Pre-registered reading (pooled):** R1"]),
    ("(2) processor-level sensitivity, contrast 1", "+24.2 [+14.6, +34.3]", F, ["+24.2 [+14.6, +34.3]"]),
    ("(2) processor-level sensitivity, contrast 2", "+19.7 [+7.6, +32.3]", F, ["+19.7 [+7.6, +32.3]"]),
    ("MPSOC Table 6: sensitivity contrast 3 (both views)", "-3.0 [-12.1, +6.1]", F, ["-3.0 [-12.1, +6.1]", "17/23", "-3.0 [-12.1, +6.1] |"]),
    ("MPSOC Table 6: sensitivity contrast 4 (both views)", "-2.2 [-7.8, +3.3]", F, ["-2.2 [-7.8, +3.3]", "3/5"]),
    ("(2) ladder: alarm 52% plateau from call 3 (50%) to call 6 (52%)", "50%; 52%", F, ["| baseline_gate | 0/198", "99/198 (50%", "103/198 (52%"]),
    ("(2) escalation climbs 56% -> 72%", "56%; 72%", F, ["| sem_esc_restart_v3 | 0/198", "111/198 (56%", "142/198 (72%"]),
    ("(2) sim-silent loop pass at end: alarm 80/108", "80/108", F, ["| baseline_gate | 108 | 80/108"]),
    ("(2) sim-silent loop pass at end: escalation 97/108", "97/108", F, ["| sem_esc_restart_v3 | 108 | 97/108"]),
    ("(2) would_fire: 95 failed, all 95 would fire, 38 on returned RTL; 103 clean", "95; 95; 38; 103", F, ["| all | 198 | 95 | 95 | 38 | 103 |"]),
    ("(2) per model llama3.2:3b +39.4, Holm 0.006", "+39.4; 0.006; 19/33 vs 6/33", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | llama3.2:3b", "+39.4", "0.006", "19/33", "6/33"]),
    ("(2) per model gemma3:4b +33.3, Holm 0.006", "+33.3; 0.006; 17/33 vs 6/33", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | gemma3:4b", "+33.3", "0.006", "17/33"]),
    ("MPSOC: esc - gate deepseek-coder:6.7b", "+12.1", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | deepseek-coder:6.7b", "+12.1"]),
    ("MPSOC: esc - gate qwen2.5-coder:7b", "+18.2", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | qwen2.5-coder:7b", "+18.2"]),
    ("MPSOC: esc - gate llama3.1:8b", "+9.1", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | llama3.1:latest", "+9.1"]),
    ("MPSOC: esc - gate qwen2.5-coder:14b", "+6.1", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | qwen2.5-coder:14b", "+6.1"]),
    ("MPSOC: esc - gate noc_xbar4 = 0 (the only non-positive task)", "+0.0", F, [f"sem_esc_restart_v3 {M} baseline_gate | all | noc_xbar4", "+0.0"]),
    # ---- (3)
    ("(3) v3 - raw: 132 vs 104, +14.1 [+3.5, +24.7], p 0.014, 40/12", "132/198; 104/198; +14.1; 0.014; 40/12", F, [f"sem_adv_v3 {M} raw_adv | all", "+14.1 [+3.5, +24.7]", "0.014", "40/12"]),
    ("(3) v2 - raw: +10.1 [+2.0, +18.7], p 0.030", "+10.1; 0.030", F, [f"sem_adv_v2 {M} raw_adv | all", "+10.1 [+2.0, +18.7]", "0.030"]),
    ("(3) about 23% fewer calls and tokens (also S10)", "-23.3%; -23.2%", N, ["calls -23.3%, tokens -23.2%"]),
    ("(3) tokens per sign-off clean pass", "5,066; 8,370", N, ["tokens per clean pass, sign-off: v3 5,066, raw 8,370"]),
    ("(3) clean after the first call 55 / 41 / 15%; MPSOC also 40% gate, 42% esc", "55%; 41%; 15%; 40%; 42%", N, ["clean after the first call, sign-off", "(55%", "(41%", "(15%", "(40%", "(42%"]),
    ("(3) 3B +24.2", "+24.2 (13/33 vs 5/33)", N, ["llama3.2:3b, sign-off: v3 13/33, raw 5/33, +24.2"]),
    ("(3) qwen2.5-coder:7b +27.3", "+27.3 (30/33 vs 21/33)", N, ["qwen2.5-coder:7b, sign-off: v3 30/33, raw 21/33, +27.3"]),
    ("(3) 14B at 30/33 either", "30/33", N, ["qwen2.5-coder:14b, sign-off: v3 30/33, raw 30/33"]),
    ("MPSOC: per-model v3/raw for gemma3:4b, deepseek, llama3.1", "15/6; 25/24; 19/18", N, ["per model gemma3:4b", "raw_adv 6", "sem_adv_v3 15"]),
    ("MPSOC Table 7: v3 - raw sim-silent / sim-visible", "+20.4; +6.7", F, ["+20.4 [+5.6, +35.2]"]),
    ("MPSOC Table 7: v3 - raw sim-visible", "+6.7 [-7.8, +21.1]; 0.474", F, ["+6.7 [-7.8, +21.1]", "0.474"]),
    ("MPSOC Table 7: v3 - v2", "+4.0 [-4.0, +12.1]; 0.408", F, ["+4.0 [-4.0, +12.1]", "0.408"]),
    ("MPSOC Table 7: esc - v3", "+5.1 [-2.0, +12.6]; 0.255", F, ["+5.1 [-2.0, +12.6]", "0.255"]),
    ("MPSOC Table 7: esc - raw", "+19.2 [+9.6, +28.8]; <0.001", F, ["+19.2 [+9.6, +28.8]"]),
    ("MPSOC Table 8: tokens per sign-off clean (all conditions)", "6,562; 8,370; 6,117; 5,066; 5,295; 7,372", F, ["| baseline | 198 | 168/198", "| 6562 |"]),
    # ---- (4)
    ("(4) tool rounds 47.5% fewer than v3", "47.5%", N, ["escalation tool rounds vs v3: -47.5%"]),
    ("(4) esc - baseline sim-visible +14.4, 56/90 vs 43/90, p 0.048; as run +23.3", "+14.4 [+3.3, +27.8]; 0.048; +23.3", F, [f"sem_esc_restart_v3 {M} baseline | visible", "+14.4 [+3.3, +27.8]", "0.048", "+23.3 [+8.9, +37.8]"]),
    ("(4) llama3.2:3b sim-visible 7 / 1 / 8 of 15", "7/15; 1/15; 8/15", N, ["llama3.2:3b sim-visible, sign-off: baseline 7/15, raw_adv 1/15, sem_esc_restart_v3 8/15"]),
    ("MPSOC: sim-visible deepseek 13/15, qwen7b 12/15 vs baseline 9/15", "13/15; 12/15; 9/15", N, ["per model deepseek-coder:6.7b", "sim-visible of 15: baseline 9, sem_esc_restart_v3 13"]),
    ("MPSOC: escalated vs not (109 -> 100; 89 -> 42)", "109; 100; 89; 42", N, ["never escalated: 109 runs, signoff_clean 100"]),
    # ---- (5)
    ("(5) Table 11 2x2 mesh", "0 / 15 / 13 / 16 / 18 / 11 of 18", N, ["composition six models mesh2x2", "baseline_gate 11/18 (at bound 8)"]),
    ("(5) Table 11 3x3 mesh", "0 / 15 / 13 / 16 / 18 / 11 of 18", N, ["composition six models mesh3x3", "baseline_gate 11/18 (at bound 8)"]),
    ("(5) Table 11 MPSoC top", "0 / 13 / 12 / 16 / 15 / 11 of 18; gate at bound 1", N, ["composition six models mpsoc", "baseline_gate 11/18 (at bound 1)"]),
    ("(5) leaf-clean => bound, 990 runs (unchanged v7 sentence)", "32/32; 32/32; 27/27", R, ["32/32 (mesh2x2)", "27/27 (mpsoc)"]),
    ("MPSOC: 32B composition 3/3 at bound", "3/3", N, ["composition qwen2.5-coder:32b mpsoc", "sem_adv_v3 3/3 (at bound 3)"]),
    # ---- (6)
    ("(6) Table 12 qwen2.5-coder:32b rows", "12(0/12) 28(16/12) 30(18/12) x4; tokens 663..1,850", N, ["- baseline_gate: signoff_clean 28/33 (sim-silent 16/18, sim-visible 12/15)", "1,824"]),
    ("(6) Table 12 qwen2.5-coder:32b tool rows", "30 (18/12); 1,492; 1,655; 1,660; 1,850", N, ["- sem_esc_restart_v3: signoff_clean 30/33 (sim-silent 18/18", "1,850"]),
    ("(6) Table 12 gpt-4.1-mini gate row", "28 (16/12); 1,529", N, ["gpt-4.1-mini-2025-04-14 baseline_gate: signoff_clean 28/33 (sim-silent 16/18", "1,529"]),
    ("(6) Table 12 gpt-4.1-mini v3 row", "30 (18/12); 1,257", N, ["gpt-4.1-mini-2025-04-14 sem_adv_v3: signoff_clean 30/33", "1,257"]),
    ("(6) Table 12 claude-haiku-4.5 gate row", "30 (18/12); 1,099", N, ["claude-haiku-4-5-20251001 baseline_gate: signoff_clean 30/33", "1,099"]),
    ("(6) Table 12 claude-haiku-4.5 esc row", "30 (18/12); 1,101", N, ["claude-haiku-4-5-20251001 sem_esc_restart_v3: signoff_clean 30/33", "1,101"]),
    ("(6) every 32B miss outside baseline is Address_select, plus 2 alarm runs on riscv_alu_flags", "3 each; 2", N, ["32B non-baseline runs that are not signoff_clean", "('riscv_alu_flags', 'baseline_gate'): 2"]),
    ("(6) every API miss outside baseline is Address_select, plus 2 alarm runs (gpt-4.1-mini) on riscv_alu_flags", "3 each; 2", N, ["API non-baseline runs that are not signoff_clean", "'riscv_alu_flags', 'baseline_gate'): 2"]),
    ("MPSOC: 7-model pool esc - gate", "+17.7 [+10.4, +25.6]", F, ["+17.7 [+10.4, +25.6]"]),
    ("MPSOC: 7-model pool v3 - gate", "+13.4 [+3.5, +23.8]", F, ["+13.4 [+3.5, +23.8]"]),
    # ---- (7)
    ("(7) focus tasks 42/72 -> 50/72 under sign-off", "42/72; 50/72", N, ["four focus tasks, sign-off: v2 42/72, v3 50/72"]),
    ("(7) +11.1, CI [-9.7, +31.9] (unchanged v7 numbers; tasks unaffected by the oracle)", "+11.1; -9.7; +31.9", R, ["+11.1 points, cell-level CI [-9.7, +31.9]"]),
    ("(7) 18/18 fired; 3/18 -> 15/18 interpreter-credited (unchanged v7 numbers)", "18/18; 3/18; 15/18", R, ["sf-gated wins v2 3/18", "v3 15/18"]),
    # ---- (8)
    ("(8) mem_wb_mux: 16 loop-clean repairs violate the spec", "16", Z, ["| mem_wb_mux | 58 | 42 | 0 | 16"]),
    ("(8) Address_select: 41 loop-clean repairs set J_addr = 0", "41", Z, ["| Address_select | 49 | 8 | 0 | 41"]),
    ("(8) gap runs with advice: v2 8 of 8", "8; 8", F, ["| Address_select | six models | sem_adv_v2 | gap (loop clean, sign-off fails) | 8/18 | 8 | 8 |"]),
    ("(8) gap runs with advice: v3 12 of 12", "12; 12", F, ["| Address_select | six models | sem_adv_v3 | gap (loop clean, sign-off fails) | 12/18 | 12 | 12 |"]),
    ("(8) gap runs with advice: esc 11 of 11", "11; 11", F, ["| Address_select | six models | sem_esc_restart_v3 | gap (loop clean, sign-off fails) | 11/18 | 11 | 11 |"]),
    ("(8) gap runs without advice: baseline 3", "3; 0", F, ["| Address_select | six models | baseline | gap (loop clean, sign-off fails) | 3/18 | 0 |"]),
    ("(8) gap runs without advice: raw 7", "7; 0", F, ["| Address_select | six models | raw_adv | gap (loop clean, sign-off fails) | 7/18 | 0 |"]),
    ("(8) gap runs without advice: alarm 2", "2; 0", F, ["| Address_select | six models | baseline_gate | gap (loop clean, sign-off fails) | 2/18 | 0 |"]),
    ("MPSOC Table 13: mem_wb_mux gap runs raw 6 (0), v2 3 (3), v3 2 (2), esc 5 (0), gate 6 (0)", "6/3/2/5/6", F, ["| mem_wb_mux | six models | sem_adv_v2 | gap (loop clean, sign-off fails) | 3/18 | 3 | 3 |"]),
    ("MPSOC: mem_wb_mux advice reached all 11 sign-off clean v2 runs", "11/11", F, ["| mem_wb_mux | six models | sem_adv_v2 | signoff_clean | 11/18 | 11 | 11 |"]),
    ("MPSOC Table 12: audit ni_flit_pack / noc_xbar4 / registers", "36; 47; 69; 66", Z, ["| noc_xbar4 | 47 | 0 | 47 (gnt not one-hot"]),
    # ---- PHASE3_MPSOC_v2 tables: strata, per task, would_fire per task, upgrade table
    ("MPSOC 6.1: sim-silent sign-off clean raw 64 / v2 83 / v3 86 / esc 86 / gate 61 (of 108)", "64; 83; 86; 86; 61", F, ["| baseline_gate | 108 | 80/108", "61/108"]),
    ("MPSOC 6.1: sim-visible sign-off clean baseline 43 / raw 40 / v2 41 / v3 46 / esc 56 / gate 42 (of 90)", "43; 40; 41; 46; 56; 42", F, ["| baseline_gate | 90 | 52/90", "42/90"]),
] + [(f"MPSOC Table 9 (per task): {t}", "row", F, [f"| {t} | ", " → ", " /18 |"]) for t in (
    "Address_select", "MuxPC", "execute_mux", "mem_wb_mux", "mux3", "ni_flit_pack", "noc_xbar4", "register_1bit",
    "register_32bit", "register_4bit", "riscv_alu_flags")] + [
    (f"MPSOC Table 4 (would_fire): {t}", "row", F, [f"| {t} | 18 | "]) for t in (
    "Address_select", "MuxPC", "execute_mux", "mem_wb_mux", "mux3", "ni_flit_pack", "noc_xbar4", "register_1bit",
    "register_32bit", "register_4bit", "riscv_alu_flags")] + [
    ("MPSOC Table 10 (upgrade): fired counts v2/v3 (unchanged v7 table; oracle-independent)", "0/18; 18/18", R, ["register_1bit (0/18 runs)", "ni_flit_pack (0/18)"]),
    ("MPSOC 7: keep-best, 23 of 198 (v3) and 11 (esc) lost a simulation pass (990 runs, loop testbench)", "23; 11", "phase3/evidence/phase3_run/phase3_tables.md", ["| sem_adv_v3 | 198 | 23 |"]),
    ("MPSOC 7: keep-best, escalation 11", "11", "phase3/evidence/phase3_run/phase3_tables.md", ["| sem_esc_restart_v3 | 198 | 11 |"]),
    # ---- abstract (applied on the user's instruction, 2026-09-30)
    ("Abstract: 8% signed off defective with the interpreter (v3; v2 also 8%)", "8%", N, ["| sem_adv_v3 | 147/198", "15/198 (8%"]),
    ("Abstract: control-arm CIs", "+3.0 to +26.3; +11.1 to +29.3", F, ["+19.7 [+11.1, +29.3]", "42/3"]),
    ("Abstract: interpretation vs raw", "14.1; +3.5 to +24.7", F, ["+14.1 [+3.5, +24.7]", "40/12"]),
    # ---- 9.6 / S10
    ("9.6, S10: 14.6 over the alarm, 19.7 for escalation; 14.1 over raw; 63%; 72%", "14.6; 19.7; 14.1; 63%; 72%", F, [f"sem_adv_v3 {M} baseline_gate | all", "+14.6 [+3.0, +26.3]"]),
]


def main():
    rows, bad, cache = [], [], {}
    for where, nums, f, subs in E:
        if f not in cache:
            cache[f] = open(os.path.join(REPO, f), encoding="utf-8").read().splitlines()
        hit = next((i for i, l in enumerate(cache[f]) if all(s in l for s in subs)), None)
        if hit is None:
            bad.append((where, f, subs))
            continue
        rows.append(f"| {where} | {nums} | `{f}`:{hit + 1} |")
    if bad:
        for b in bad:
            print("NOT FOUND:", b)
        sys.exit(1)
    h = lambda p: hashlib.sha256(open(os.path.join(REPO, p), "rb").read()).hexdigest()
    v7 = open(os.path.join(REPO, "docs", "archive", "paper", "STITCH_EXT_v7.tex"), "rb").read()  # archived 2026-10-13
    v8 = open(os.path.join(REPO, "paper", "STITCH_EXT_v8.tex"), "rb").read()
    S9 = b"\\section{Is STITCH Useful on Real Hardware? An MPSoC Case Study}"
    p7, p8 = v7[:v7.index(S9)], v8[:v8.index(S9)]

    def strip(b):   # drop the header comment block and the abstract, the two places the user asked to change
        b = b[b.index(b"\\documentclass"):]
        return b[:b.index(b"\\begin{abstract}")] + b[b.index(b"\\end{abstract}"):]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "V8_CHANGES.md")
    MARK = "## Numbers and their sources (generated by paper/make_v8_changes.py)"
    prose = open(path, encoding="utf-8").read().split(MARK)[0].rstrip() + "\n\n"
    open(path, "w", encoding="utf-8", newline="\n").write(
        prose + MARK + "\n\nEach source line below was located by the script and checked to contain the quoted values. "
        f"Prefix (everything before the Section 9 heading): SHA-256 v7 `{hashlib.sha256(p7).hexdigest()}`, "
        f"v8 `{hashlib.sha256(p8).hexdigest()}`; outside the abstract and the header comment the two prefixes are "
        f"{'byte-identical' if strip(p7) == strip(p8) else 'DIFFERENT'}.\n\n"
        "| Where | Number(s) as printed | Source (file:line) |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    print(f"{len(rows)} sources verified; prefix sha256 v7 {hashlib.sha256(p7).hexdigest()} v8 {hashlib.sha256(p8).hexdigest()} "
          f"{'MATCH' if p7 == p8 else 'MISMATCH'}")


if __name__ == "__main__":
    main()
