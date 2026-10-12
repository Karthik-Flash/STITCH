"""Spend per provider for Set 4 (ledgers/) and Set 4b (ledgers_4b/), USD and INR (96/USD + 18% GST)."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SET4 = os.path.join(HERE, "..", "results", "set4_api")
R = 96 * 1.18
grand = 0.0
per_provider = {}
P3A_LEDGERS = os.path.join(HERE, "..", "results", "p3_api", "ledgers")
for d, name in ((os.path.join(SET4, "ledgers"), "Set 4"), (os.path.join(SET4, "ledgers_4b"), "Set 4b"),
                (P3A_LEDGERS, "Final"), (os.path.join(SET4, "ledgers_4c"), "Set 4c")):
    tot = 0.0
    for f in sorted(glob.glob(os.path.join(d, "*_ledger.jsonl"))):
        recs = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        usd = sum(x["cost_usd"] for x in recs)
        tot += usd
        prov = os.path.basename(f).split('_')[0]
        per_provider[prov] = per_provider.get(prov, 0.0) + usd
        tags = {}
        for x in recs:
            tags[x.get("tag")] = tags.get(x.get("tag"), 0) + x["cost_usd"]
        print(f"{name:7s} {os.path.basename(f).split('_')[0]:10s} ${usd:.4f} INR {usd * R:7.1f} calls {len(recs)} "
              f"non-ok {sum(1 for x in recs if x['status'] != 'ok')} "
              f"reasoning>0 {sum(1 for x in recs if x.get('reasoning_tokens', 0) > 0)} "
              + " ".join(f"{k}=${v:.4f}" for k, v in tags.items()))
    print(f"{name:7s} TOTAL      ${tot:.4f} INR {tot * R:7.1f}")
    grand += tot
for prov, usd in sorted(per_provider.items()):
    print(f"ALL     {prov:10s} ${usd:.4f} INR {usd * R:7.1f}")
print(f"GRAND   TOTAL      ${grand:.4f} INR {grand * R:7.1f}")
