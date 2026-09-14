#!/usr/bin/env bash
# Isolate view-count ERCB from block and interval-grouping effects.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
results_root="$lab_root/results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time"
family=${1:-utmm}
scene=${2:-fast-straight}
required_opportunities=${MATCHED_REQUIRED_OPPORTUNITIES:-4}
selectors=(
    rr
    view_uniform_k128
    ercb_view_count_b002_k128
    ercb_base
    ercb_relative_floor
    ercb_coverage1
)

failures=0
for selector in "${selectors[@]}"; do
    output="$results_root/$family/$scene/${selector}_unified_pool_workcredit_cycle_r${required_opportunities}_seed0"
    if [ -f "$output/psnr/online_final/final_result.json" ] && \
       [ -f "$output/sensor_eos_audit.json" ]; then
        echo "SKIP complete $family/$scene/$selector workcredit_cycle_r$required_opportunities"
        continue
    fi
    echo "RUN $family/$scene/$selector workcredit_cycle_r$required_opportunities"
    if MATCHED_ADMISSION=work_credit \
       MATCHED_REQUIRED_OPPORTUNITIES="$required_opportunities" \
       bash "$script_dir/run_one.sh" "$family" "$scene" "$selector" "$output"; then
        echo "PASS process $family/$scene/$selector workcredit_cycle_r$required_opportunities"
    else
        status=$?
        failures=$((failures + 1))
        echo "FAIL process $family/$scene/$selector exit=$status (preserved; continuing)"
    fi
    python "$script_dir/collect_metrics.py"
done
python "$script_dir/collect_metrics.py"
echo "SELECTOR_FAMILY_PILOT_DONE failures=$failures total=${#selectors[@]}"
exit "$failures"
