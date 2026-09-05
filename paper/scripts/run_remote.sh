#!/usr/bin/env bash
# run_remote.sh — 원격 GPU에 논문 실험을 디스패치하고 run_id / manifest 뼈대를 만든다.
#
#   ./paper/scripts/run_remote.sh <Pnn> <machine> <arm> <scene> <seed>
#
# 예)
#   ./paper/scripts/run_remote.sh P01 fastmri-desktop token-noprepurchase aria1253 0
#   ./paper/scripts/run_remote.sh P03 chaehyun ercb-k128-b002 aria1253rot 1
#
# machine: chaehyun (5090) | fastmri-desktop (5070Ti)
#
# ⚠ 실제 실행 커맨드는 P01 구현 후 아래 RUN_CMD 를 채운다. 지금은 manifest만 만든다.
set -euo pipefail

P="${1:?사용법: run_remote.sh <Pnn> <machine> <arm> <scene> <seed>}"
MACHINE="${2:?machine: chaehyun | fastmri-desktop}"
ARM="${3:?arm}"
SCENE="${4:?scene}"
SEED="${5:?seed}"

case "$MACHINE" in
  chaehyun)        GPU="RTX 5090";    TAG="5090"   ;;
  fastmri-desktop|fastmri-5070ti) GPU="RTX 5070 Ti"; TAG="5070ti" ;;
  *) echo "알 수 없는 machine: $MACHINE" >&2; exit 1 ;;
esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER="$(dirname "$HERE")"
PROTO="$(basename "$(readlink "$PAPER/experiments/protocol/CURRENT.md")" .md)"

RUN_ID="${P}_$(date +%Y%m%d)_${TAG}_${ARM}_seed${SEED}"
OUT="$PAPER/results/runs/$RUN_ID"
mkdir -p "$OUT"

# 원격 코드 커밋 확인 (재현성)
CODE_SHA="$(ssh "$MACHINE" 'cd ~/VIGS-SLAM* 2>/dev/null && git rev-parse --short HEAD' 2>/dev/null || echo UNKNOWN)"

cat > "$OUT/manifest.json" <<JSON
{
  "run_id": "$RUN_ID",
  "protocol_version": "$PROTO",
  "experiment": "$P",
  "arm": "$ARM",
  "scene": "$SCENE",
  "machine": "$MACHINE",
  "gpu": "$GPU",
  "seed": $SEED,
  "code_commit": "$CODE_SHA",
  "config": "TODO",
  "strict_contract": {"S1": null, "S2": null, "S3": null, "S4": null, "S5": null, "S6": null},
  "wall_time_s": null,
  "started_at": "$(date -Is)",
  "notes": ""
}
JSON
echo "manifest: $OUT/manifest.json"

# GPU 점유 확인 — 타 프로세스가 있으면 종료하지 말고 대기 (AGENTS.md 규칙)
echo "--- $MACHINE nvidia-smi ---"
ssh "$MACHINE" 'nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv' || true

# TODO: P01 구현 후 실제 실행 커맨드를 여기에.
# RUN_CMD="cd ~/VIGS-SLAM-... && conda run -n vings python demo.py --scene $SCENE --seed $SEED --arm $ARM"
# ssh "$MACHINE" "$RUN_CMD" 2>&1 | tee "$OUT/stdout.log"
echo
echo "⚠ RUN_CMD 미설정 — manifest만 생성했습니다. P01 구현 후 스크립트를 채우세요."
