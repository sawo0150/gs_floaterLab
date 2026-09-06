#!/usr/bin/env bash
# tex.sh — paper/latex 를 로컬에서 빌드한다.
#
#   ./paper/scripts/tex.sh            한 번 빌드하고 끝
#   ./paper/scripts/tex.sh open       빌드 후 PDF 뷰어로 열기
#   ./paper/scripts/tex.sh watch      파일이 바뀔 때마다 자동 재빌드 (Ctrl-C 로 종료)
#   ./paper/scripts/tex.sh clean      build/ 지우기
#
# 산출물: paper/build/main.pdf  (build/ 는 git에 안 올라간다)
# 참고: Overleaf 와의 관계와 동기화 규칙은 paper/latex/SYNC.md
set -uo pipefail

export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$PATH"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/latex"
OUT="$ROOT/build"
CMD="${1:-build}"

command -v latexmk >/dev/null || {
  echo "latexmk 없음. TinyTeX 설치: curl -sSL https://yihui.org/tinytex/install-bin-unix.sh | sh" >&2
  exit 1; }

mkdir -p "$OUT"

case "$CMD" in
  clean) rm -rf "$OUT"; echo "지움: $OUT"; exit 0 ;;
esac

build() {
  ( cd "$SRC" && latexmk -pdf -interaction=nonstopmode -file-line-error \
      -outdir="$OUT" main.tex >"$OUT/latexmk.log" 2>&1 )
  local rc=$?
  local pdf="$OUT/main.pdf"
  if [[ -f "$pdf" ]]; then
    local pages; pages=$(pdfinfo "$pdf" 2>/dev/null | awk '/^Pages/{print $2}')
    echo "✓ main.pdf  ${pages:-?}쪽  ($(date +%H:%M:%S))"
  else
    echo "✗ PDF 안 나옴"
  fi
  # 에러와 미해결 참조만 보여준다
  grep -E '^[^ ]+\.tex:[0-9]+:|^! ' "$OUT/latexmk.log" | head -12
  local undef; undef=$(grep -c 'Citation .* undefined\|Reference .* undefined' "$OUT/main.log" 2>/dev/null || true)
  [[ "${undef:-0}" -gt 0 ]] && echo "  ⚠ 미해결 인용·참조 $undef건"
  # 분량 경고
  if [[ -n "${pages:-}" && "$pages" -gt 8 ]]; then
    echo "  ⚠ 본문 8쪽 초과 ($pages쪽) — CVPR 제한 확인"
  fi
  return $rc
}

case "$CMD" in
  build) build ;;
  open)  build; command -v evince >/dev/null && (evince "$OUT/main.pdf" >/dev/null 2>&1 &) || xdg-open "$OUT/main.pdf" ;;
  watch)
    echo "감시 중: $SRC  (Ctrl-C 로 종료)"
    build
    if command -v inotifywait >/dev/null; then
      while inotifywait -qq -r -e modify,create,move "$SRC" --exclude '\.(aux|log|out|bbl|blg|fls|fdb_latexmk)$'; do
        sleep 0.3; build
      done
    else
      echo "  (inotifywait 없음 → 2초 폴링)"
      local_prev=""
      while true; do
        cur=$(find "$SRC" -name '*.tex' -o -name '*.bib' -o -name '*.sty' | xargs stat -c %Y 2>/dev/null | sort | md5sum)
        [[ "$cur" != "$local_prev" ]] && { local_prev="$cur"; build; }
        sleep 2
      done
    fi ;;
  *) echo "사용법: tex.sh [build|open|watch|clean]" >&2; exit 1 ;;
esac
