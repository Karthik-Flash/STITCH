"""
hpc_checkpoint.py — interim read on whatever HPC data has landed so far.

Structure of the pulled tree: STITCHAdv/runs/hpc_pull/<tag:a100|h100>/<safe_model>/<condition>/<module>/metrics.json
This is a checkpoint on jobs that may still be running/queued/timed-out —
not a final closure pass. Every count is reported against /20 so partial
coverage from an in-progress or timed-out job is visible, not hidden.
"""

import json
from collections import defaultdict
from pathlib import Path

HPC_PULL = Path(r"D:\BITS Files\Year 3\3-2\LLM_Verilog Project\AgenticAI\AutoChipAdvFB\STITCHAdv\runs\hpc_pull")
MANIFEST = ["alu_8bit","alu_accumulator_top","bcd_to_7seg","comparator_8bit","counter_4bit",
            "dff_sync_reset","fsm_seq_detector","full_adder","gray_counter_4bit","half_adder",
            "lfsr_8bit","param_register_file","pipeline_mult_4x4","priority_enc_8","pwm_generator",
            "ripple_carry_adder","simple_cpu_alu","spi_master_8bit","sync_fifo_8","uart_tx"]

files = list(HPC_PULL.rglob("metrics.json"))
print(f"Total metrics.json under hpc_pull: {len(files)}")

data = defaultdict(dict)  # (tag, model) -> {condition: {module: metrics}}
for f in files:
    try:
        m = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  WARNING unparsable {f}: {e}")
        continue
    rel = f.relative_to(HPC_PULL)
    tag = rel.parts[0]
    data[(tag, m["model"])].setdefault(m["condition"], {})[m["module"]] = m

print("\n=== Coverage + pass rate per (hardware, model, condition) ===")
for (tag, model) in sorted(data.keys()):
    print(f"\n{tag.upper()} | {model}")
    for cond in ["baseline", "raw_adv", "sem_adv"]:
        mods = data[(tag, model)].get(cond, {})
        n = len(mods)
        p = sum(1 for m in mods.values() if m["pass"])
        missing = sorted(set(MANIFEST) - set(mods.keys()))
        status = "COMPLETE" if n == 20 else f"PARTIAL, missing: {missing}"
        print(f"  {cond:<10} {p}/{n if n else 0} of 20 passed  [{status}]" if n else f"  {cond:<10} 0/20  [NOT STARTED]")

print("\n=== A100 vs H100 head-to-head, ONLY where both sides have data for the same module (apples-to-apples) ===")
for model in sorted({m for (t, m) in data.keys()}):
    a100 = data.get(("a100", model), {})
    h100 = data.get(("h100", model), {})
    if not a100 or not h100:
        print(f"\n{model}: only one hardware class has data so far, skipping head-to-head")
        continue
    print(f"\n{model}")
    for cond in ["baseline", "raw_adv", "sem_adv"]:
        a_mods, h_mods = a100.get(cond, {}), h100.get(cond, {})
        shared = sorted(set(a_mods) & set(h_mods))
        if not shared:
            continue
        a_pass = sum(1 for mo in shared if a_mods[mo]["pass"])
        h_pass = sum(1 for mo in shared if h_mods[mo]["pass"])
        print(f"  {cond:<10} on {len(shared)} shared modules: A100 {a_pass}/{len(shared)}  vs  H100 {h_pass}/{len(shared)}")
