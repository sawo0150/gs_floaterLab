#!/usr/bin/env bash
# exp62 — overnight autonomous milestone runner for the live OKVIS2‖3dgs-custom pipeline.
# Runs M1..M5 in order via `codex exec`, stopping immediately (no retry) the first time a
# milestone's self-verification report is missing or status != "pass". See
# context/experiments/exp62_live_okvis2_mapping_pipeline_plan.md for the full design.
set -uo pipefail

LB=/home/wosas/Desktop/26-1_RPM/gsProjects/okvis2_bench_5070ti/live_bridge
MS="$LB/milestones"
LOG="$LB/logs/orchestrator.log"
mkdir -p "$LB/logs" "$LB/verify"

# Per-milestone wall-clock cap. Generous on purpose (C++ build + multi-scene runs + a real
# GPU training pass all cost real time) but bounded so one stuck milestone can't eat the
# whole night.
MILESTONE_TIMEOUT_S=$((3 * 3600))

log() { echo "[$(date -Is)] $*" | tee -a "$LOG"; }

log "=== orchestrator start ==="

for m in M1 M2 M3 M4 M5; do
  prompt_file="$MS/${m}_prompt.md"
  report_file="$LB/verify/${m}_report.json"
  event_log="$LB/logs/${m}.jsonl"

  if [ ! -f "$prompt_file" ]; then
    log "FATAL: missing prompt file $prompt_file"
    exit 1
  fi

  log "--- $m: starting (timeout ${MILESTONE_TIMEOUT_S}s) ---"
  rm -f "$report_file"

  timeout --signal=TERM "$MILESTONE_TIMEOUT_S" \
    codex exec --dangerously-bypass-approvals-and-sandbox \
      -C "$LB" --skip-git-repo-check \
      "$(cat "$prompt_file")" \
      --json \
    < /dev/null > "$event_log" 2>&1
  codex_rc=$?

  if [ "$codex_rc" -eq 124 ] || [ "$codex_rc" -eq 137 ]; then
    log "$m: TIMED OUT after ${MILESTONE_TIMEOUT_S}s (codex exit=$codex_rc). Stopping loop."
    log "$m: see $event_log for what it was doing when it timed out."
    exit 2
  fi

  if [ "$codex_rc" -ne 0 ]; then
    log "$m: codex exec exited non-zero ($codex_rc). Continuing to check report anyway"
    log "$m: (codex sometimes exits non-zero on its own tool errors but still wrote a report)."
  fi

  if [ ! -f "$report_file" ]; then
    log "$m: FAILED — no $report_file written. Stopping loop."
    log "$m: last 40 lines of $event_log:"
    tail -40 "$event_log" | tee -a "$LOG"
    exit 3
  fi

  status=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('status','<missing>'))" "$report_file" 2>&1)

  if [ "$status" != "pass" ]; then
    log "$m: FAILED — report status='$status' (expected 'pass'). Stopping loop."
    log "$m: report contents:"
    cat "$report_file" | tee -a "$LOG"
    exit 4
  fi

  log "$m: PASSED. Report:"
  cat "$report_file" | tee -a "$LOG"

  # Safety-net commit in case the milestone prompt's own commit step was skipped.
  git -C "$LB" add -A
  if ! git -C "$LB" diff --cached --quiet; then
    git -C "$LB" commit -q -m "orchestrator: safety-net commit after $m passed" || true
    log "$m: orchestrator safety-net commit made (milestone may already have committed separately)."
  fi

  log "--- $m: done ---"
done

log "=== ALL MILESTONES PASSED ==="
