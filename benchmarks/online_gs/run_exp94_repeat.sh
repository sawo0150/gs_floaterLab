#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_exp94_repeat.sh preflight <run_tag>
  run_exp94_repeat.sh run-all   <run_tag>
  run_exp94_repeat.sh run-one   <run_tag> <rpng|utmm|aria> <scene>

The wrapper always writes to a new pair of directories:
  results/experiments/<run_tag>/
  context/experiments/benchmark_custom/<run_tag>/

VIGS_PYTHON may override the default 5090 Python executable.
EOF
}

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 2
fi

action="$1"
run_tag="$2"

if [[ ! "$run_tag" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "run_tag must contain only letters, numbers, '.', '_' or '-'" >&2
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
workspace="$(cd -- "$script_dir/../.." && pwd)"
python_bin="${VIGS_PYTHON:-/home/colin/miniconda3/envs/vigs-slam-5090/bin/python}"
runner="$script_dir/run_exp94_normalized_metric_v2_fixed_eval.py"
run_root="$workspace/results/experiments/$run_tag"
docs_root="$workspace/context/experiments/benchmark_custom/$run_tag"

if [[ ! -x "$python_bin" ]]; then
  echo "Python executable not found: $python_bin" >&2
  exit 1
fi

case "$action" in
  preflight|run-all)
    if [[ $# -ne 2 ]]; then
      usage >&2
      exit 2
    fi
    exec "$python_bin" "$runner" "$action" \
      --root "$run_root" --docs "$docs_root"
    ;;
  run-one)
    if [[ $# -ne 4 ]]; then
      usage >&2
      exit 2
    fi
    dataset="$3"
    scene="$4"
    exec "$python_bin" "$runner" run-one \
      --dataset "$dataset" --scene "$scene" \
      --root "$run_root" --docs "$docs_root"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
