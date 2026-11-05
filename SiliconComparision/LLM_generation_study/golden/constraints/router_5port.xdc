# router_5port on ZedBoard (xc7z020clg484-1), out-of-context: the router has 340 I/O, the package 200 user I/O,
# so no pins are placed. 100 MHz = the ZedBoard PL clock (GCLK, pin Y9).
create_clock -period 10.000 -name clk [get_ports clk]
# Every input and output is timed against clk (setup 2 ns, hold 0.5 ns), so unconstrained endpoints can only
# come from the design itself.
set_input_delay  -clock clk -max 2.000 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay  -clock clk -min 0.500 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock clk -max 2.000 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock clk -min 0.500 [get_ports -filter {DIRECTION == OUT}]
