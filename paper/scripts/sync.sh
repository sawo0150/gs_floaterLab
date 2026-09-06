#!/usr/bin/env bash
# sync.sh — 로컬 paper/latex 와 Overleaf 사이의 "아직 안 올린 것"을 관리한다.
#
# 동기화는 사람이 직접 복사·붙여넣기로 한다 (paper/latex/SYNC.md 합의).
# 이 스크립트는 **무엇을 붙여넣어야 하는지만** 알려준다. 자동 전송은 하지 않는다.
#
#   ./paper/scripts/sync.sh status          안 올린 파일 목록
#   ./paper/scripts/sync.sh diff <파일>      마지막 동기화 이후 무엇이 바뀌었나
#   ./paper/scripts/sync.sh mark <파일>...   해당 파일을 Overleaf에 붙여넣었다고 기록
#   ./paper/scripts/sync.sh mark-all        전부 붙여넣었다고 기록
#   ./paper/scripts/sync.sh init <커밋>      기준 상태를 그 커밋의 latex/ 로 초기화
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/latex"
STATE="$SRC/.sync-state"
SNAP="$ROOT/.sync-snapshot"          # 마지막 동기화 시점의 사본 (diff 용, git 제외)
CMD="${1:-status}"

files() { ( cd "$SRC" && find . -type f \
    ! -name '.sync-state' ! -name 'SYNC.md' ! -path './.git*' \
    ! -name '*.aux' ! -name '*.log' ! -name '*.out' ! -name '*.bbl' ! -name '*.blg' \
    ! -name '*.fls' ! -name '*.fdb_latexmk' ! -name '*.synctex.gz' ! -name '*.pdf' \
    | sed 's|^\./||' | sort ); }

hash_of() { sha256sum "$SRC/$1" 2>/dev/null | cut -c1-16; }
recorded() { [[ -f "$STATE" ]] && awk -v f="$1" '$2==f{print $1}' "$STATE" | head -1; }

save_snapshot() { mkdir -p "$(dirname "$SNAP/$1")"; cp -f "$SRC/$1" "$SNAP/$1" 2>/dev/null || true; }

case "$CMD" in
  init)
    ref="${2:?사용법: sync.sh init <커밋>}"
    : > "$STATE"; rm -rf "$SNAP"
    while read -r f; do
      if git -C "$ROOT/.." show "$ref:paper/latex/$f" > /tmp/_s 2>/dev/null; then
        printf '%s  %s\n' "$(sha256sum /tmp/_s | cut -c1-16)" "$f" >> "$STATE"
        mkdir -p "$(dirname "$SNAP/$f")"; cp /tmp/_s "$SNAP/$f"
      fi
    done < <(files)
    echo "기준 상태를 $ref 로 초기화했습니다 ($(wc -l < "$STATE")개 파일)."
    exec "$0" status ;;

  mark-all)
    : > "$STATE"
    while read -r f; do printf '%s  %s\n' "$(hash_of "$f")" "$f" >> "$STATE"; save_snapshot "$f"; done < <(files)
    echo "전부 동기화됨으로 기록했습니다." ;;

  mark)
    shift; [[ $# -gt 0 ]] || { echo "파일을 지정하세요" >&2; exit 1; }
    tmp=$(mktemp)
    for f in "$@"; do
      f="${f#latex/}"; f="${f#paper/latex/}"
      [[ -f "$SRC/$f" ]] || { echo "없는 파일: $f" >&2; continue; }
      grep -v "  $f\$" "$STATE" 2>/dev/null > "$tmp" || true
      printf '%s  %s\n' "$(hash_of "$f")" "$f" >> "$tmp"
      mv "$tmp" "$STATE"; tmp=$(mktemp)
      save_snapshot "$f"; echo "  기록: $f"
    done; rm -f "$tmp" ;;

  diff)
    f="${2:?사용법: sync.sh diff <파일>}"; f="${f#latex/}"; f="${f#paper/latex/}"
    if [[ -f "$SNAP/$f" ]]; then diff -u --color=auto "$SNAP/$f" "$SRC/$f" || true
    else echo "동기화 기록이 없는 새 파일입니다: $f"; fi ;;

  status)
    pend=(); new=(); gone=()
    while read -r f; do
      r=$(recorded "$f")
      if   [[ -z "$r" ]];              then new+=("$f")
      elif [[ "$r" != "$(hash_of "$f")" ]]; then pend+=("$f"); fi
    done < <(files)
    if [[ -f "$STATE" ]]; then
      while read -r _ f; do [[ -f "$SRC/$f" ]] || gone+=("$f"); done < "$STATE"
    fi
    total=$(( ${#pend[@]} + ${#new[@]} + ${#gone[@]} ))
    if [[ $total -eq 0 ]]; then echo "✓ Overleaf 와 같습니다. 올릴 것 없음."; exit 0; fi
    echo "Overleaf 에 아직 안 올린 것 — $total 건"
    echo "  (Overleaf 에서 해당 파일을 열고 로컬 내용으로 통째로 덮어쓰세요)"
    echo
    for f in "${new[@]:-}";  do [[ -n "$f" ]] && echo "  [새 파일] $f"; done
    for f in "${pend[@]:-}"; do [[ -n "$f" ]] && echo "  [수정됨]  $f    ← ./paper/scripts/sync.sh diff $f"; done
    for f in "${gone[@]:-}"; do [[ -n "$f" ]] && echo "  [삭제됨]  $f    (Overleaf 에서도 지울지 판단)"; done
    echo
    echo "붙여넣은 뒤:  ./paper/scripts/sync.sh mark <파일>   또는   mark-all" ;;

  *) echo "사용법: sync.sh [status|diff <파일>|mark <파일>...|mark-all|init <커밋>]" >&2; exit 1 ;;
esac
