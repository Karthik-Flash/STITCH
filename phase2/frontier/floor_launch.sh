#!/bin/bash
# Set 4b launcher for one provider: floor_launch.sh provider:model:projected_usd:cap_usd
export SET4_TAG=floor_full SET4_LEDGERS=ledgers_4b SET4_GLOBAL_CAP=14 SET4_STATUS_SUFFIX="${1%%:*}"
export SET4_EXTRA="--modules LIFObuffer,accu,adder_16bit,adder_32bit,adder_bcd,adder_pipe_64bit,alu,barrel_shifter,counter_12,div_16bit,float_multi,freq_divbyfrac,fsm,multi_pipe_4bit,multi_pipe_8bit,parallel2serial,pulse_detect,serial2parallel,traffic_light"
exec python3 "$(dirname "$0")/full_run.py" "$1"
