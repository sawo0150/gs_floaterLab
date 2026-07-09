#!/bin/bash
# Sequential runner: exp22 → exp23 → exp24
# Run AFTER exp21 is done.
set -e

SCRIPTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/scripts/experiments

echo "=========================================="
echo "  Sequential run: exp22 → exp23 → exp24"
echo "  Start: $(date)"
echo "=========================================="

bash "$SCRIPTS/run_exp22_exploss.sh"
echo ">>> exp22 done. Starting exp23... ($(date))"

bash "$SCRIPTS/run_exp23_adaptive_prune.sh"
echo ">>> exp23 done. Starting exp24... ($(date))"

bash "$SCRIPTS/run_exp24_exp_and_prune.sh"
echo ">>> exp24 done."

echo "=========================================="
echo "  All done: $(date)"
echo "=========================================="
