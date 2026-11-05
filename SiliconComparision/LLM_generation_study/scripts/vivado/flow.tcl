# Out-of-context synthesis and implementation of one design for ZedBoard, with every report the study uses.
# Usage: vivado -mode batch -source flow.tcl -tclargs <rtl dir> <xdc> <top> <out dir>
lassign $argv rtl_dir xdc top out
set part xc7z020clg484-1
file mkdir $out

read_verilog [lsort [glob $rtl_dir/*.v]]
read_xdc $xdc
synth_design -top $top -part $part -mode out_of_context
report_utilization -file $out/utilization_synth.rpt

opt_design
place_design
route_design

report_utilization               -file $out/utilization_routed.rpt
report_utilization -hierarchical -file $out/utilization_hier_routed.rpt
report_timing_summary -max_paths 10 -report_unconstrained -file $out/timing_summary_routed.rpt
check_timing -verbose            -file $out/check_timing.rpt
report_methodology               -file $out/methodology.rpt
report_drc                       -file $out/drc_routed.rpt
report_power                     -file $out/power_routed.rpt
write_checkpoint -force $out/routed.dcp
