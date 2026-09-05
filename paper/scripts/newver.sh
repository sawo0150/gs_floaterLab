#!/usr/bin/env bash
# newver.sh — 버전 문서 폴더에 새 버전을 만든다.
#
#   ./paper/scripts/newver.sh <문서폴더> <슬러그> ["트리거"]
#
# 예)
#   ./paper/scripts/newver.sh paper/plan/claims after-P03 "P03 재검증 결과 반영"
#   ./paper/scripts/newver.sh paper/sections/03_method/3-1_gpu_token_admission/plan supervisor-review
#
# 하는 일:
#   1) CURRENT.md 가 가리키는 최신 vNN 을 찾아 v(NN+1)_<오늘>_<슬러그>.md 로 복사
#   2) CURRENT.md 심링크를 새 파일로 재지정
#   3) 상위 README.md 의 버전 이력 표에 행을 추가 (변경 내용은 TODO 로 남김)
#
# ⚠ 버전을 올리는 기준은 paper/README.md "버전 관리 규약" 참조.
#    오탈자·문장 다듬기는 bump 하지 말고 현재 파일을 직접 고칠 것.
set -euo pipefail

DIR="${1:?사용법: newver.sh <문서폴더> <슬러그> [\"트리거\"]}"
SLUG="${2:?슬러그가 필요합니다 (예: after-P03, supervisor-review)}"
TRIGGER="${3:-TODO}"
DATE="$(date +%F)"

[[ -d "$DIR" ]] || { echo "폴더 없음: $DIR" >&2; exit 1; }
cd "$DIR"

# 1) 최신 버전 찾기
LAST="$(ls -1 v[0-9][0-9]_*.md 2>/dev/null | sort | tail -1 || true)"
[[ -n "$LAST" ]] || { echo "버전 파일(vNN_*.md)이 없습니다: $DIR" >&2; exit 1; }
N=$((10#${LAST:1:2} + 1))
NEW="$(printf 'v%02d_%s_%s.md' "$N" "$DATE" "$SLUG")"
[[ -e "$NEW" ]] && { echo "이미 존재: $NEW" >&2; exit 1; }

SRC="$(readlink CURRENT.md 2>/dev/null || echo "$LAST")"
cp "$SRC" "$NEW"
ln -sfn "$NEW" CURRENT.md
echo "생성: $DIR/$NEW  (원본: $SRC)"

# 2) README 버전 이력 표에 행 추가
add_row() {  # $1=README경로 $2=행
  local f="$1" row="$2"
  # 표의 마지막 행 뒤에 삽입
  awk -v row="$row" '
    /^\|/ { last=NR }
    { lines[NR]=$0 }
    END {
      for (i=1;i<=NR;i++) { print lines[i]; if (i==last) print row }
    }' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  echo "이력 추가: $f"
}

if [[ -f README.md ]] && grep -q '^| 버전 |' README.md; then
  add_row README.md "| [v$(printf '%02d' $N)]($NEW) | $DATE | $TRIGGER | **TODO: 무엇이 바뀌었나** | **TODO: 폐기된 주장** |"
elif [[ -f ../README.md ]] && grep -q '^| 종류 |' ../README.md; then
  KIND="$(basename "$PWD")"   # plan 또는 draft
  add_row ../README.md "| $KIND | [v$(printf '%02d' $N)]($KIND/$NEW) | $DATE | $TRIGGER | **TODO: 무엇이 바뀌었나** |"
else
  echo "경고: 버전 이력 표를 못 찾음. README.md 를 직접 갱신하세요." >&2
fi

echo
echo "다음: $DIR/$NEW 를 편집하고, README 의 TODO 두 칸을 채우세요."
