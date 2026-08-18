# `interpreter/` — the semantic interpreter

`stitch_interpreter.py` is the single source of truth for warning
classification and directive generation. Both the runner and any future
escalation runner import from it; nothing reimplements this logic locally.
(That rule exists because a duplicated latch check in the runner was the direct
cause of one of the five defects recorded in
`../illustrations/retired/session_2026-08-18_findings.md`.)

- **Warning classes and their verification status:** `WARNING_TAXONOMY.md`
- **Tests:** `tests/test_interpreter.py` — 39 tests. Run with
  `python -m unittest discover -s interpreter/tests -p "test_interpreter.py"`

---

## Monitoring

### The UNUSEDSIGNAL parameterisation fallback

The `UNUSEDSIGNAL` directive tells the model to gate its logic on the unused
port and to zero the output on the else-branch. To do that it must name the
module's actual output port(s) and width(s), which it extracts from the module
header. Earlier versions hard-coded `out = 8'b0`, which was correct only for
modules whose single output happens to be named `out` and 8 bits wide.

Extraction **falls back** to the generic hard-coded template when the output
port cannot be resolved with confidence:

- parameterised or macro-defined width (e.g. `output reg [WIDTH-1:0] q`),
- unparseable or non-standard module header,
- no source file available to the interpreter,
- any declared output whose width is not a literal integer range.

The fallback is deliberate — a half-correct assignment naming the wrong signal
is worse than a generic one. But it is **silent to the model**: the directive
still looks authoritative, it is just less precise.

### Why this must be checked

The paper makes claims about **directive precision**. A run in which the
fallback fired on most of its `UNUSEDSIGNAL` warnings does not support those
claims, and nothing in the results files would reveal it. Fallback-heavy runs
distort the precision story while still producing plausible-looking output.

### Threshold and procedure

**After every large run — any run exceeding roughly 50 module-iterations —
inspect the fallback log.**

> **If the fallback fires on more than ~10% of `UNUSEDSIGNAL` warnings in a
> run, extend the extraction logic rather than leaving it to fall back
> silently.**

Below ~10%, record the figure and move on. Above it, the parameteriser is not
covering the module population actually in use, and the precision claim needs
either a code fix or an explicit caveat in the write-up.

### PREREQUISITE — logging is not yet wired up

**As of the pre-Phase-1 freeze this check cannot be performed.** The
interpreter logs the fallback via a module-level logger at `INFO`:

```python
_LOG = logging.getLogger(__name__)   # "stitch_interpreter"
_LOG.info("UNUSEDSIGNAL directive for %r fell back to the generic "
          "hard-coded template - %s.", sig, why)
```

but **the runner never calls `logging.basicConfig()` or attaches a handler**.
Verified directly: the logger has no handlers and an effective level of
`WARNING`, so these `INFO` records are discarded before reaching any stream.
The fallback fires correctly; nothing is written anywhere.

Before the monitoring procedure can run, the runner (or the Phase 1 escalation
runner) must configure logging so interpreter records are captured to a file —
for example, at startup:

```python
logging.basicConfig(
    level=logging.INFO,
    filename="interpreter.log",
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
```

This is tracked as open question #6 in
`../docs/research_plan_v4.md` §7. **No code change was made for it
during the doc freeze.**

### The check itself

Once logging writes to a file, count fallbacks against total `UNUSEDSIGNAL`
firings for the run:

```bash
# 1. Fallback occurrences (numerator)
grep -c "fell back to the generic" interpreter.log

# 2. Total UNUSEDSIGNAL directives issued (denominator) — from the run's own
#    per-module metrics, which record every code that fired
grep -ro '"UNUSEDSIGNAL"' results/<run>/ --include=metrics.json | wc -l

# 3. Which modules fell back, and why (parameterised width vs no source)
grep "fell back to the generic" interpreter.log | sed 's/.*template - //' | sort | uniq -c
```

Divide (1) by (2). If the ratio exceeds ~0.10, extend `_output_ports()` /
`_parse_width()` in `stitch_interpreter.py` to cover the declaration forms that
are failing, and re-run.

If logging has not yet been wired up, the equivalent one-shot check is to
re-run the interpreter over the run's saved `.v` files with logging enabled,
rather than to assume the fallback rate was low.
