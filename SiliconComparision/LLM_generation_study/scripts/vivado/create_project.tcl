# Creates a Vivado project of the golden router for the GUI in vivado/project (gitignored).
#   Open Elaborated Design -> Schematic   : the RTL block diagram
#   Run Simulation (sim_1 or sim_mesh)    : tb_router_5port.v / tb_mesh2x2.v, both end with ALL TESTS PASSED
#   Run Synthesis / Run Implementation    : the same out-of-context flow as flow.tcl
# Usage, from the study folder: vivado -mode batch -source scripts/vivado/create_project.tcl
set study [file normalize [file join [file dirname [info script]] .. ..]]
create_project golden_router [file join $study vivado project] -part xc7z020clg484-1 -force

add_files [lsort [glob [file join $study golden rtl *.v]]]
set_property top router_5port [current_fileset]
add_files -fileset constrs_1 [file join $study golden constraints router_5port.xdc]
set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]

add_files -fileset sim_1 [file join $study golden tb tb_router_5port.v]
set_property top tb [get_filesets sim_1]
set_property -name {xsim.simulate.runtime} -value {1ms} -objects [get_filesets sim_1]

create_fileset -simset sim_mesh
add_files -fileset sim_mesh [file join $study golden tb tb_mesh2x2.v]
set_property top tb [get_filesets sim_mesh]
set_property -name {xsim.simulate.runtime} -value {1ms} -objects [get_filesets sim_mesh]

close_project
puts "Project: [file join $study vivado project golden_router.xpr]"
