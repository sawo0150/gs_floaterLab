#!/usr/bin/env bash
# Compile the asset-layout draft without regenerating figures or tables.
# Prefer the repository's latexmk workflow; accept a portable Tectonic binary.
set -euo pipefail
TASK_PAPER_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_SOURCE="$TASK_PAPER_ROOT/latex"
TASK_BUILD="$TASK_PAPER_ROOT/build"
TASK_EXPORT="$TASK_PAPER_ROOT/output/pdf"
mkdir -p "$TASK_BUILD" "$TASK_EXPORT"

if command -v latexmk >/dev/null 2>&1; then
  (cd "$TASK_SOURCE" && latexmk -pdf -interaction=nonstopmode -halt-on-error \
    -outdir="$TASK_BUILD" main.tex >"$TASK_BUILD/draft_compile.log" 2>&1)
elif [[ -x "${TECTONIC:-}" ]] || command -v tectonic >/dev/null 2>&1; then
  TASK_TECTONIC="${TECTONIC:-$(command -v tectonic)}"
  (cd "$TASK_SOURCE" && "$TASK_TECTONIC" --keep-logs --keep-intermediates \
    -o "$TASK_BUILD" main.tex >"$TASK_BUILD/draft_compile.log" 2>&1)
else
  echo "Install latexmk or set TECTONIC=/absolute/path/to/tectonic." >&2
  exit 1
fi

cp "$TASK_BUILD/main.pdf" "$TASK_EXPORT/cvpr_draft_layout.pdf"
echo "Built: $TASK_EXPORT/cvpr_draft_layout.pdf"
