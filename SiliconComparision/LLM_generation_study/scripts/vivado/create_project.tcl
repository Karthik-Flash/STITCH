# Creates a Vivado project of the golden router for the GUI in vivado/project (gitignored).
#   Open Elaborated Design -> Schematic   : the RTL block diagram
#   Run Simulation (sim_1 or sim_mesh)    : tb_router_5port.v / tb_mesh2x2.v, both end with ALL TESTS PASSED
#   Run Synthesis / Run Implementation    : the same out-of-context flow as flow.tcl
# Usage, from the study folder: vivado -mode batch -source scripts/vivado/create_project.tcl
# Any other router (scripts/vivado/vivado_routers.py --projects does this for every LLM router that compiles):
#   vivado -mode batch -source scripts/vivado/create_project.tcl -tclargs <rtl dir> <project dir> <project name>
set study [file normalize [file join [file dirname [info script]] .. ..]]
if {[llength $argv] == 3} {
    lassign $argv rtl_dir proj_dir proj_name
} else {
    set rtl_dir [file join $study golden rtl]
    set proj_dir [file join $study vivado project]
    set proj_name golden_router
}
create_project $proj_name $proj_dir -part xc7z020clg484-1 -force

add_files [lsort [glob [file join $rtl_dir *.v]]]
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
puts "Project: [file join $proj_dir $proj_name.xpr]"
