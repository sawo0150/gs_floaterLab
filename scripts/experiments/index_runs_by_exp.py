#!/usr/bin/env python3
"""index_runs_by_exp.py — results/experiments/의 런들을 exp 번호별 폴더뷰(symlink)로 인덱싱.

원본은 results/experiments/ 에 flat으로 그대로 둠(모든 glob 경로 유지) →
results/by_exp/<group>/<run> 에 상대 symlink만 생성해 폴더별 브라우징 제공.
멱등: 매 실행마다 by_exp/를 비우고 재생성. 새 실험 후 다시 돌리면 자동 반영.

group 규칙: 'expNN' 접두(뒤 문자 접미 무시, exp46_ax3→exp46, exp40b→exp40) /
            'scene_*'→scenes / 그 외→misc.

사용: python scripts/experiments/index_runs_by_exp.py
"""
import re
import shutil
from pathlib import Path

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
SRC = LAB / "results/experiments"
DST = LAB / "results/by_exp"


def group_of(name: str) -> str:
    m = re.match(r"(exp\d+)", name)
    if m:
        return m.group(1)
    if name.startswith("scene_"):
        return "scenes"
    if name.startswith("new_scene") or name.startswith("scene_baseline"):
        return "scenes"
    return "misc"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)
    (DST / "README.md").write_text(
        "# results/by_exp — 자동 생성 symlink 인덱스\n\n"
        "원본 런은 `results/experiments/`에 flat으로 있고, 여기는 exp 번호별 폴더뷰(상대 symlink).\n"
        "`python scripts/experiments/index_runs_by_exp.py`로 재생성. 편집 금지(덮어씀).\n")
    counts = {}
    for entry in sorted(SRC.iterdir()):
        if entry.name.startswith(".") or entry.name == "README.md":
            continue
        g = group_of(entry.name)
        gdir = DST / g
        gdir.mkdir(exist_ok=True)
        link = gdir / entry.name
        target = Path("../../experiments") / entry.name   # by_exp/<g>/<name> → experiments/<name>
        link.symlink_to(target)
        counts[g] = counts.get(g, 0) + 1
    total = sum(counts.values())
    print(f"[by_exp] {total}개 런/파일 → {len(counts)}개 그룹")
    for g in sorted(counts, key=lambda k: (-counts[k], k)):
        print(f"  {g:12} {counts[g]}")


if __name__ == "__main__":
    main()
