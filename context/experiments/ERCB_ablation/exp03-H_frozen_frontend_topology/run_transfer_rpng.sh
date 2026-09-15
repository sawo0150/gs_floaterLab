#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
root="$lab_root/results/ERCB_ablation/exp03-H_frozen_frontend_topology/rpng/table_07/q3"
frontend_trace_dir="$root/frontend_trace_v3_s0"
topology_trace_dir="$root/topology_trace_v3_s0"

capture="$root/trace_capture_v3_rr_s0"
if [ ! -f "$capture/psnr/online_final/final_result.json" ]; then
    "$script_dir/run_one_rpng.sh" record off rr_role_stratified "$capture"
fi

packet_count=$(find "$frontend_trace_dir" -maxdepth 1 -name 'packet_*.pt' | wc -l)
if [ "$packet_count" -le 0 ]; then
    echo "incomplete frontend reference trace: packets=$packet_count" >&2
    exit 2
fi

topology_capture="$root/topology_capture_v3_rr_s0"
if [ ! -f "$topology_capture/psnr/online_final/final_result.json" ]; then
    "$script_dir/run_one_rpng.sh" replay record rr_role_stratified "$topology_capture"
fi

topology_count=$(find "$topology_trace_dir" -maxdepth 1 -name 'topology_*.pt' | wc -l)
if [ "$topology_count" -le 0 ]; then
    echo "incomplete topology reference trace: events=$topology_count" >&2
    exit 2
fi

for selector in rr_role_stratified ercb_relative_floor_role_stratified; do
    short=rr
    if [[ "$selector" == ercb_* ]]; then short=ercb_dense; fi
    output="$root/${short}_replay_v3_s0"
    if [ -f "$output/psnr/online_final/final_result.json" ]; then
        echo "SKIP_COMPLETE selector=$selector"
        continue
    fi
    "$script_dir/run_one_rpng.sh" replay replay "$selector" "$output"
done
