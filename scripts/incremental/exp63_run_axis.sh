#!/usr/bin/env bash
# Wait for the shared GPU to go idle, then run ONE exp63 axis via codex exec and stop.
# Does not chain to the next axis -- each axis's prompt is written by hand only after
# the previous axis's real results have been independently checked (not just its own
# self-report).
set -uo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <AXIS_LETTER>  (e.g. D, B, A, C, E, G)" >&2
  exit 2
fi

AXIS=$1
VIGS_DIR=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM
PROMPT_FILE="$VIGS_DIR/exp63_axes/prompts/${AXIS}_prompt.md"
EVENT_LOG="$VIGS_DIR/exp63_axes/verify/${AXIS}_event_log.jsonl"
REPORT_FILE="$VIGS_DIR/exp63_axes/verify/${AXIS}_report.json"
LOCK_FILE="$VIGS_DIR/exp63_axes/verify/${AXIS}.lock"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "prompt file does not exist: $PROMPT_FILE" >&2
  exit 2
fi

# Two prior "killed" background attempts for this same axis left orphaned
# codex exec / python demo.py processes running for 30+ minutes, silently
# fighting a later Monitor-based attempt for the GPU and clobbering its log
# file (both write to the same path). Refuse to start a second concurrent
# run for the same axis letter.
if [[ -f "$LOCK_FILE" ]]; then
  old_pid=$(cat "$LOCK_FILE" 2>/dev/null)
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "axis $AXIS already has a live runner (pid $old_pid, lock $LOCK_FILE) -- refusing to start a second one" >&2
    exit 3
  fi
  echo "[$(date -Is)] stale lock file found (pid $old_pid not alive) -- removing and continuing" >&2
  rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

echo "[$(date -Is)] waiting for GPU idle before starting axis $AXIS..."
idle_streak=0
while [[ $idle_streak -lt 3 ]]; do
  read -r util mem <<<"$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits | head -1)"
  util=${util//[^0-9]/}
  mem=${mem//[^0-9]/}
  if [[ "$util" -lt 10 && "$mem" -lt 1500 ]]; then
    idle_streak=$((idle_streak + 1))
    echo "[$(date -Is)] idle check $idle_streak/3 passed (util=${util}% mem=${mem}MiB)"
  else
    if [[ $idle_streak -gt 0 ]]; then
      echo "[$(date -Is)] GPU busy again (util=${util}% mem=${mem}MiB), resetting idle streak"
    fi
    idle_streak=0
  fi
  sleep 30
done
echo "[$(date -Is)] GPU confirmed idle, starting axis $AXIS"

rm -f "$REPORT_FILE"
cd "$VIGS_DIR"
# codex exec buffers its own --json output until each long-running command
# finishes, so redirecting straight to a file and blocking on it leaves this
# script's own stdout silent for many minutes at a stretch -- suspected cause
# of two prior "killed" events shortly after the heavy python subprocess
# started. Run it in the background instead and keep emitting a heartbeat to
# our own stdout every 60s so this tracked process never looks idle.
# CODEX_HOME points at a second, separately-authenticated account
# (~/.codex2, distinct auth.json, everything else symlinked back to
# ~/.codex) per user request -- keeps this axis loop off the primary
# account's usage/rate limits.
timeout 10800 env CODEX_HOME=/home/wosas/.codex2 codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  -C "$VIGS_DIR" \
  --skip-git-repo-check \
  "$(cat "$PROMPT_FILE")" \
  --json < /dev/null > "$EVENT_LOG" 2>&1 &
codex_pid=$!
echo "[$(date -Is)] codex exec for axis $AXIS started, pid=$codex_pid"
elapsed=0
while kill -0 "$codex_pid" 2>/dev/null; do
  sleep 60
  elapsed=$((elapsed + 60))
  log_size=$(wc -c < "$EVENT_LOG" 2>/dev/null || echo 0)
  echo "[$(date -Is)] heartbeat: axis $AXIS still running (pid=$codex_pid, elapsed=${elapsed}s, event_log_bytes=$log_size)"
done
wait "$codex_pid"
codex_status=$?
echo "[$(date -Is)] codex exec for axis $AXIS exited with status $codex_status"

if [[ ! -f "$REPORT_FILE" ]]; then
  echo "[$(date -Is)] axis $AXIS: NO REPORT FILE WRITTEN -- treat as failed, do not trust any inline claims" >&2
  exit 1
fi

report_status=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('status','<missing>'))" "$REPORT_FILE" 2>/dev/null)
echo "[$(date -Is)] axis $AXIS report status: $report_status"
echo "[$(date -Is)] axis $AXIS done -- Claude must independently verify before writing the next axis's prompt"
