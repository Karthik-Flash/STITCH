# round_robin_req

## Behaviour

Two-level switch allocator for one output port: picks one of 16 input-VC requests. `req_1` to `req_16`
are four groups of four (group 1 = `req_1` to `req_4`, ..., group 4 = `req_13` to `req_16`).

- One grant per request: once request i has been granted, it is masked until `req_i` returns to 0.
  Flag Li (`gi_latched`) becomes 1 on a rising edge of `gi_int` and is held at 0 while `req_i` is 0.
  The masked request is `reqi` = `req_i` AND NOT Li.
- First level: within each group, a round-robin arbiter (rr_arbiter, clock `rd_clk`) grants among the
  four masked requests, giving `gnt1` to `gnt16`.
- `req_bk` = OR of group k's masked requests; `tk` = `all_vc_not_busy` AND `req_bk`. Second level: a
  round-robin arbiter over `t1` to `t4` gives `g_b1` to `g_b4`.
- `gi` = `gnti` AND `g_b`(group of i). `gi_int` = `gi` registered on rising `rd_clk`.
- `nreq_i` = NOT `req_i`. `tailer1` to `tailer16` have no effect.

## Reset

Active-high `reset`: both arbiter levels reset (see rr_arbiter), and `gi_int` becomes 0 at the next
rising `rd_clk` edge. Li has no reset pin; it clears while `req_i` is 0.

## Ports

<!-- BEGIN generated: ports -->
143 ports, in this exact order:

```verilog
input reset, rd_clk, all_vc_not_busy, req_1, req_2, req_3, req_4, req_5, req_6, req_7, req_8, req_9, req_10,
      req_11, req_12, req_13, req_14, req_15, req_16;
output g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15, g16;
input tailer1, tailer2, tailer3, tailer4, tailer5, tailer6, tailer7, tailer8, tailer9, tailer10, tailer11,
      tailer12, tailer13, tailer14, tailer15, tailer16;
output g_b1, g_b2, g_b3, g_b4, gnt1, gnt2, gnt3, gnt4, gnt5, gnt6, gnt7, gnt8, gnt9, gnt10, gnt11, gnt12,
       gnt13, gnt14, gnt15, gnt16, req1, req2, req3, req4, req5, req6, req7, req8, req9, req10, req11, req12,
       req13, req14, req15, req16, g1_latched, g2_latched, g3_latched, g4_latched, g5_latched, g6_latched,
       g7_latched, g8_latched, g9_latched, g10_latched, g11_latched, g12_latched, g13_latched, g14_latched,
       g15_latched, g16_latched, g1_int, g2_int, g3_int, g4_int, g5_int, g6_int, g7_int, g8_int, g9_int,
       g10_int, g11_int, g12_int, g13_int, g14_int, g15_int, g16_int, t1, t2, t3, t4, req_b1, req_b2, req_b3,
       req_b4, nreq_1, nreq_2, nreq_3, nreq_4, nreq_5, nreq_6, nreq_7, nreq_8, nreq_9, nreq_10, nreq_11,
       nreq_12, nreq_13, nreq_14, nreq_15, nreq_16;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `dff_asynch_clr` x 16: (d, clr, clk, q)
- `dff_synch_reset` x 16: (d, reset, clk, q)
- `rr_arbiter` x 5: (req1, req2, req3, req4, reset, gnt1, gnt2, gnt3, gnt4, clk)
<!-- END generated: children -->

Unclear in golden: the Li flags are flip-flops clocked by `gi_int` with asynchronous clear from NOT `req_i` (gated
clocks). Despite the name, `gi_latched` is not an inferred latch. `tailer1` to `tailer16` are unused.
Nothing latch-dependent.
