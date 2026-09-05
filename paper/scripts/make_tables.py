#!/usr/bin/env python3
"""results/tables/*.csv -> latex/tab/*.tex

표 숫자를 손으로 적지 않기 위한 스크립트.
CSV 한 개가 tex 표 한 개가 된다. CSV 첫 줄이 헤더.

사용법:
    python3 paper/scripts/make_tables.py                # 전부 변환
    python3 paper/scripts/make_tables.py main_results   # 하나만

CSV 규약:
  - 헤더 셀에 '_' 가 있으면 공백으로 바꿔 출력한다 (수식 헤더 '$\\rho_H$' 는 예외).
  - '$' 나 '\\' 가 든 셀은 이미 LaTeX로 보고 이스케이프하지 않는다.
  - 숫자로 파싱되는 셀은 오른쪽 정렬(r), 아니면 왼쪽 정렬(l).
  - 셀 값이 '**...**' 이면 \\textbf{...} 로 굵게.
  - 파일명 앞에 'caption:' 으로 시작하는 주석 줄(#)이 있으면 캡션으로 쓴다.
"""
import csv, sys, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
SRC = os.path.join(PAPER, "results", "tables")
DST = os.path.join(PAPER, "latex", "tab")


def esc(s):
    """셀을 LaTeX로. 이미 LaTeX인 셀($ 또는 \\ 포함)은 그대로 통과시킨다."""
    s = str(s).strip()
    m = re.fullmatch(r"\*\*(.*)\*\*", s)
    bold = m is not None
    if bold:
        s = m.group(1)
    if "$" not in s and "\\" not in s:      # 순수 텍스트일 때만 이스케이프
        for a, b in [("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")]:
            s = s.replace(a, b)
    s = s.replace("±", r"$\pm$").replace("−", "-")
    return rf"\textbf{{{s}}}" if bold else s


def head_label(h):
    """헤더의 '_'는 공백으로 바꾸되, 수식/LaTeX 헤더는 건드리지 않는다."""
    h = str(h)
    return h if ("$" in h or "\\" in h) else h.replace("_", " ")


def is_num(s):
    try:
        float(str(s).replace("−", "-").replace("*", "").strip())
        return True
    except ValueError:
        return False


def convert(path):
    name = os.path.splitext(os.path.basename(path))[0]
    caption, rows = f"TODO caption for {name}", []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                if line[1:].strip().lower().startswith("caption:"):
                    caption = line.split(":", 1)[1].strip()
                continue
            rows.append(next(csv.reader([line])))
    rows = [r for r in rows if r and any(c.strip() for c in r)]
    if not rows:
        print(f"  건너뜀 (빈 파일): {path}")
        return
    head, body = rows[0], rows[1:]
    align = "".join("r" if body and is_num(body[0][i]) else "l" for i in range(len(head)))

    out = [
        f"% 자동 생성: paper/scripts/make_tables.py <- results/tables/{name}.csv",
        "% 이 파일을 직접 수정하지 마세요. CSV를 고치고 스크립트를 다시 돌리세요.",
        r"\begin{table}[t]", r"  \centering", r"  \small",
        rf"  \begin{{tabular}}{{{align}}}", r"    \toprule",
        "    " + " & ".join(esc(head_label(h)) for h in head) + r" \\",
        r"    \midrule",
    ]
    out += ["    " + " & ".join(esc(c) for c in r) + r" \\" for r in body]
    out += [
        r"    \bottomrule", r"  \end{tabular}",
        rf"  \caption{{{caption}}}", rf"  \label{{tab:{name}}}",
        r"\end{table}",
    ]
    os.makedirs(DST, exist_ok=True)
    dst = os.path.join(DST, name + ".tex")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"  {path} -> {dst}  ({len(body)} rows)")


if __name__ == "__main__":
    os.makedirs(SRC, exist_ok=True)
    want = sys.argv[1:]
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".csv"))
    if want:
        files = [f for f in files if os.path.splitext(f)[0] in want]
    if not files:
        print(f"변환할 CSV가 없습니다: {SRC}")
        sys.exit(0)
    print(f"{len(files)}개 변환:")
    for f in files:
        convert(os.path.join(SRC, f))
