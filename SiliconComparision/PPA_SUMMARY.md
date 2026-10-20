# Silicon PPA Summary

## 1. Comparison

A1 keeps the inferred latches; B replaces them with golden, clocked registers. The supplied CSVs cover the 2x2 and 3x3 meshes, ORFS with SKY130HD and a 10 ns clock, one run per variant/design. Power activity was not matched. The STITCH repair targets sign-off correctness, so this measures the cost of correctness, not an improvement.

## 2. Measurements

Values below are copied from `complete_metrics_table.csv` and `latch_effect_percent_change.csv`; power components and total are in W as recorded. DRC is final detailed-route count; antenna is nets/pins. Empty source fields are `not measured`.

| Variant / design | Final std-cell area (um^2) | Area / total power change (%) | Fmax (MHz) | Setup WNS / TNS (ns) | Dynamic split: internal / switching / dynamic (W) | Leakage (W) | Total power (W) | D_NET cap (pF) | Wire length (um) | Vias | DRC / antenna nets/pins; max-slew/max-cap |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---|
| A1 / 2x2 | 780685 | reference / reference | 106.84 | not measured / not measured | 0.105666 / 0.0326422 / 0.1383082 | 2.58123e-07 | 0.138308 | 440.202708 | not measured | not measured | not measured / not measured; 2.0 / 2.0 |
| B / 2x2 | 808319 | 3.539711919660298 / 9.24892269427656 | 108.0 | not measured / not measured | 0.116 / 0.0351 / 0.1511 | 2.63e-07 | 0.1511 | 439.497569 | not measured | not measured | not measured / not measured; 20.0 / 10.0 |
| A1 / 3x3 | 2235731 | reference / reference | 99.2363 | -0.0769544 / -0.322059 | 0.3 / 0.0922 / 0.3922 | 7.44e-07 | 0.392244 | 1543.319526 | 9122103.0 | 1245396.0 | 0.0 / 2.0/2.0; not measured |
| B / 3x3 | 2312740 | 3.4444662618177233 / 9.388033978849906 | 98.0925 | -0.194461 / -0.718273 | 0.32814 / 0.100927 / 0.429067 | 7.60921e-07 | 0.429068 | 1667.661449 | 9739427.0 | 1342265.0 | 0.0 / 1.0/1.0; 124.0 / 31.0 |

## 3. Derived Deltas

Area per repaired latch bit uses the requested latch-cell counts. Power uses the CSV `total_w` values.

- 2x2 area: 808319 - 780685 = 27634 um^2; 27634 / 2880 = 9.595139 um^2/bit.
- 3x3 area: 2312740 - 2235731 = 77009 um^2; 77009 / 6480 = 11.884105 um^2/bit.
- 2x2 total power: (0.1511 - 0.138308) W = 12.792 mW; 12.792 mW / 2880 = 4.441667 uW/bit.
- 3x3 total power: (0.429068 - 0.392244) W = 36.824 mW; 36.824 mW / 6480 = 5.682716 uW/bit.
- Area delta scaling: 77009 / 27634 = 2.786748x; ideal 9/4 scaling is 2.25x.
- Total-power delta scaling: 36.824 / 12.792 = 2.878674x; ideal 9/4 scaling is 2.25x.

## 4. Why Area and Power Rose

- **HYPOTHESIS: to confirm.** A latch maps to a smaller cell than a resettable flip-flop. Check synthesized cell types and areas in `synth_stat.txt` and the liberty file (`dlxtp` versus `dfxtp`/`dfrtp`). Those files were not supplied: not measured.
- **HYPOTHESIS: to confirm.** The original latch enables were data-driven, not clocked; repair adds clock sinks and clock power. Check clock sink counts and clock-group power for both variants; expect about 2,880 additional sinks on 2x2. Counts and clock-group power: not measured.
- **HYPOTHESIS: to confirm.** Remaining area difference is timing-repair buffering. Check buffer and inverter counts by variant. Counts: not measured.

## 5. Conclusions and Limits

Yosys verification reports latch cells falling from 2,880 / 6,480 in A1 to 0 / 0 in B. Area rises 3.4-3.5%; the derived cost is about 9.6-11.9 um^2 per repaired latch bit. The 3x3 timing and parasitic differences come from one run each and cannot be separated from flow noise; make no causal claim. Leakage and power need a sanity check with identical activity and power-analysis settings. The 2x2 B power values appear rounded in the CSV (0.1511 W total, 0.116 W internal, 0.0351 W switching); request raw power reports. D_NET is reported as supplied; raw ground/coupling SPEF sums are not treated as design metrics.

## 6. Coworker Checks

1. Count untimed endpoints in A1 versus B using OpenSTA `check_setup -verbose` and `report_checks -unconstrained`.
2. Compare clock sink counts and clock power per variant.
3. Compare synthesized cell-type histograms per variant.
4. Run three placement seeds per variant, report the spread, and use identical activity (same VCD or same defaults).
5. Provide missing 2x2 routing, DRC and antenna values.

## 7. Takeaway

Removing the inferred latches cost about 3.5% area and an estimated 9% power on SKY130HD, because the repaired registers are real clocked flip-flops. The benefit is analysability and correctness, not lower PPA. This is not exactly a fair like-for-like comparison because the original registers were not clocked; further activity-matched, multi-seed reports can study the same cost with better controls.