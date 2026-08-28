# Prompt-format effect check -- RTLCoder native vs. shared

All-42-module aggregate (context, not the verdict): native 50/126 vs. shared 40/126 pooled passes.

**Verdict basis**: recoverable-band modules only (n=17), same delta/threshold method as Table 2 (native wins if delta>=+2, shared wins if delta<=-2, tied if |delta|<=1; delta = native_passes - shared_passes, each pass count out of N=3).

- Native wins: **3**
- Shared wins: **2**
- Tied: **12**

**One-line verdict**: Native prompting has a modest edge over the shared harness prompt (3 vs 2 module wins, 12 tied) -- format is not fully neutral.

**Modules where the sign matters most (top 3 |delta|)**:

| Module | native | shared | delta | verdict |
|---|---|---|---|---|
| freq_div | 3/3 | 0/3 | +3 | native wins |
| instr_reg | 0/3 | 3/3 | -3 | shared wins |
| calendar | 0/3 | 2/3 | -2 | shared wins |

