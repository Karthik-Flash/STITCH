"""Locate the source line of every number that is new or changed in STITCH_EXT_v9.tex (relative to v8), for
V9_CHANGES.md. Prints a markdown table: claim | v9 value | source file:line | the source line (trimmed).
  python -B paper/v9_number_sources.py > paper/v9_number_sources.md
A row whose pattern is not found prints NOT FOUND, so a stale source shows up immediately."""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", newline="\n")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P3F = "phase3/evidence/phase3_final/"
EV = "phase2/frontier/evidence/"
ROWS = [
    # (claim, value in v9, source file, regex)
    ("Set 1 restart - baseline (abstract, S5, 8.1, 8.5)", "0.0 [-4.6, +4.6], p=1.000", "phase3/evidence/phase3_run/POSTHOC_CHECKS.md", r"sem_escalate_restart - baseline: 54/151"),
    ("Set 1 sem_escalate - baseline (S5, 8.1, 8.5)", "-4.7 [-10.7, 0.0], p=0.148", "phase3/evidence/phase3_run/POSTHOC_CHECKS.md", r"sem_escalate - baseline: 47/150"),
    ("Set 1 sem_adv - baseline (S5, 8.1)", "-4.6 [-10.5, +0.7], p=0.199", "phase3/evidence/phase3_run/POSTHOC_CHECKS.md", r"sem_adv - baseline: 47/153"),
    ("Set 3 sem_adv - baseline (8.2)", "-0.7 [-7.8, +6.5]", "phase3/evidence/phase3_run/POSTHOC_CHECKS.md", r"sem_adv - baseline: 85/153"),
    ("Set 3 sem_escalate - baseline (8.2)", "+2.6 [-1.3, +7.2], p=0.404", "phase3/evidence/phase3_run/POSTHOC_CHECKS.md", r"sem_escalate - baseline: 90/153"),
    ("Set 3 restart - baseline (8.2)", "+2.0 [-2.6, +7.2], p=0.596", "phase3/evidence/phase3_run/POSTHOC_CHECKS.md", r"sem_escalate_restart - baseline: 88/151"),
    ("Set 4 pooled pass rates (8.3, abstract)", "99.3 / 98.7 / 98.0 / 98.0%", EV + "set4_analysis_stdout.txt", r"^  baseline +152/153"),
    ("Set 4 tool-call cut (abstract, 8.3, 8.5, 11)", "88.6% (2.29 -> 0.26)", EV + "set4_analysis_stdout.txt", r"tool calls/run sem_adv 2.29 -> sem_escalate 0.26"),
    ("Set 4 GPT-4.1 mini contrasts (8.3)", "-2.0, -3.9, -3.9, p=1.000", EV + "set4_analysis_stdout.txt", r"sem_escalate - baseline: cell mean -3.9"),
    ("Set 4 INR per pass range (8.3)", "0.11 to 0.51", "paper/numbers_set4.tex", r"SetFourInrPass(Min|Max)"),
    ("Set 4 parity (8.3, S6)", "140/140, 51/51", "paper/numbers_set4.tex", r"SetFourParity"),
    ("Set 4 OpenAI fingerprints (8.3, S6)", "256 and 7 calls", EV + "set4_analysis_stdout.txt", r"OpenAI system fingerprints"),
    ("Set 4b coverage (8.3, S6)", "GPT 228, Gemini 228, Haiku 143 (85 errored)", EV + "set4b_analysis_stdout.txt", r"Claude Haiku 4.5 +valid"),
    ("Set 4b floor modules leaving the floor (8.3)", "16 of 19; 4 ceiling for all", "paper/numbers_set4.tex", r"SetFourBLeaveFloor|SetFourBCeilingAll"),
    ("Set 4b interpreter fires on failures (8.3)", "55% (103/188)", "paper/numbers_set4.tex", r"SetFourBToolFailsSF"),
    ("Set 4b directive-before-pass in 0/3 cells (8.3)", "3", EV + "set4b_analysis_stdout.txt", r"^  sem_adv .*passes_sf_before_pass_where_baseline_0of3"),
    ("Set 4b smallest Q3 p (8.3)", "0.062 of 12", EV + "set4b_analysis_stdout.txt", r"gemini-2.5-flash\|sem_escalate_restart"),
    ("Set 4b Q4 strict (8.3)", "freq_divbyfrac only, 36 runs", EV + "set4b_analysis_stdout.txt", r"Q4 strict"),
    ("API runs total (1)", "1,211 (612 + 599)", "paper/numbers_set4.tex", r"SetFourAllValid"),
    ("freq_divbyfrac reference counter (8.4, S7)", "14 half steps; 2 periods per wrap; H3 L4", EV + "freq_divbyfrac_refcheck_stdout.txt", r"counter_period_half_steps"),
    ("freq_divbyfrac reference shift test (8.4, S7)", "20/20 at 0, 14/19 at +-1", EV + "freq_divbyfrac_trace_stdout.txt", r"^reference"),
    ("freq_divbyfrac first mismatch, Set 4b (8.4, S7)", "check 3 in 32 of 34", EV + "freq_divbyfrac_trace_stdout.txt", r"first mismatching check"),
    ("Latch-free clean synthesis (abstract, Result 1)", "35/144 (24%) -> 127/144 (88%); raw 104; alarm 94", P3F + "PAPER_NUMBERS.md", r"latch-bearing tasks"),
    ("Alarm runs whose returned RTL v3 names (Result 2)", "38 of 95", P3F + "PAPER_NUMBERS.md", r"baseline_gate runs not signoff_clean: 95/198"),
    ("Escalation minus alarm (abstract, Result 2)", "+19.7 [+11.1, +29.3]", P3F + "PHASE3_FINAL.md", r"^\| sem_esc_restart_v3 − baseline_gate \| all \| 198"),
    ("v3 minus raw (abstract, Result 3)", "+14.1 [+3.5, +24.7]", P3F + "PHASE3_FINAL.md", r"^\| sem_adv_v3 − raw_adv \| all"),
    ("Calls and tokens, v3 vs raw (abstract, Result 3)", "-23.3% calls, -23.2% tokens", P3F + "PAPER_NUMBERS.md", r"v3 vs raw cost"),
    ("Gemini ladder column (Table 9, S8)", "0+15 516; 18+15 1,160; 18+12 1,291; 18+15 1,478; 18+14 1,479; 18+15 1,225", EV + "p3_ladder_signoff_stdout.txt", r"^\| baseline_gate \|"),
    ("Published GPT/Haiku ladder rows reproduced (S8)", "YES", EV + "p3_ladder_signoff_stdout.txt", r"reproduced"),
    ("Gemini Address_select misses (Result 6, S8)", "raw_adv 3, v3 1", EV + "p3_ladder_signoff_stdout.txt", r"non-baseline runs not signoff_clean"),
    ("Phase 3 pre-registration hash (Availability)", "1b6eb915...cc63", "phase3/evidence/FREEZE_FINAL.md", r"1b6eb915"),
    ("API Phase 3 rows pre-registration hash (Availability)", "680F24F5...C130", "phase2/frontier/p3_api/P3_API_REPORT.md", r"680F24F5"),
    ("API study pre-registration hash (Availability, S6)", "CC23711D...653B", "phase2/frontier/SET4_REPORT.md", r"CC23711D"),
]


def main():
    print("| Claim (v9 location) | v9 value | Source file:line | Source line |")
    print("|---|---|---|---|")
    for claim, val, path, pat in ROWS:
        full = os.path.join(REPO, path)
        hit = None
        if os.path.exists(full):
            for i, line in enumerate(open(full, encoding="utf-8-sig", errors="replace"), 1):
                if re.search(pat, line):
                    hit = (i, line.strip())
                    break
        loc = f"`{path}:{hit[0]}`" if hit else f"`{path}` NOT FOUND"
        src = hit[1][:110].replace("|", "\\|") if hit else ""
        print(f"| {claim} | {val} | {loc} | {src} |")


if __name__ == "__main__":
    main()
