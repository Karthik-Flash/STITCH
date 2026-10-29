# final_op_data

## Behaviour

Combinational output-flit formatter.
- `data_out[31]` = `data_in[31]`.
- `data_out[30]` = `data_in[30]` OR NOT `gnt_or`; `data_out[29]` = `data_in[29]` OR NOT `gnt_or`.
- `data_out[28:27]` = `vc_id`.
- `data_out[26:0]` = `data_in[26:0]` when `gnt_or` is 1, else 0.
So with no grant the output is an idle flit (type 11) carrying `vc_id`, with bit 31 passed through.

## Reset

None. The module is combinational.

## Ports

<!-- BEGIN generated: ports -->
4 ports, in this exact order:

```verilog
input [31:0] data_in;
input [1:0] vc_id;
input gnt_or;
output [31:0] data_out;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: none.
