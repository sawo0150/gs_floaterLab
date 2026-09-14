#!/usr/bin/env bash
# Resume-safe serial queue for scenes not already covered by exp81/82.
set -uo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
queue_log="$script_dir/queue.log"

tasks=(
    "utmm ego-drive"
    "utmm square-2"
    "rpng table_01"
    "rpng table_02"
    "rpng table_06"
    "rpng table_07"
    "rpng table_04"
    "rpng table_05"
    "rpng table_03"
    "rpng table_08"
)

failures=0
for task in "${tasks[@]}"; do
    read -r family scene <<< "$task"
    output_dir="$lab_root/results/benchmarks/benchmark_vanila/synchronous_unbounded/$family/$scene/origin22ffe24_pure_online_seed0"
    result_file="$output_dir/psnr/after_opt/final_result.json"
    if [ -f "$result_file" ]; then
        printf '%s SKIP completed %s/%s\n' "$(date --iso-8601=seconds)" "$family" "$scene" | tee -a "$queue_log"
        continue
    fi
    if [ -d "$output_dir" ] && [ -n "$(find "$output_dir" -mindepth 1 -print -quit)" ]; then
        printf '%s FAIL incomplete output requires audit %s/%s %s\n' "$(date --iso-8601=seconds)" "$family" "$scene" "$output_dir" | tee -a "$queue_log"
        failures=$((failures + 1))
        continue
    fi

    printf '%s START %s/%s\n' "$(date --iso-8601=seconds)" "$family" "$scene" | tee -a "$queue_log"
    if "$script_dir/run_one.sh" "$family" "$scene" "$output_dir"; then
        printf '%s DONE %s/%s\n' "$(date --iso-8601=seconds)" "$family" "$scene" | tee -a "$queue_log"
    else
        status=$?
        printf '%s FAIL exit=%s %s/%s\n' "$(date --iso-8601=seconds)" "$status" "$family" "$scene" | tee -a "$queue_log"
        failures=$((failures + 1))
    fi
done

"$script_dir/collect_metrics.py"
exit "$failures"
