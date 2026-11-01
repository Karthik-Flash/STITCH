# ni_pair: constraint.sdc for the NI hand-off (pipeline/handoff_study.py).
# The only change versus A1's constraint.sdc: ni_pair has two clock ports (rd_clk, wr_clk) that clock the two
# sides of asynchronous FIFOs, so each gets A1's 10 ns clock and the two clocks are declared asynchronous.
create_clock -name rd_clk -period 10 [get_ports rd_clk]
create_clock -name wr_clk -period 10 [get_ports wr_clk]
set_clock_groups -asynchronous -group [get_clocks rd_clk] -group [get_clocks wr_clk]
