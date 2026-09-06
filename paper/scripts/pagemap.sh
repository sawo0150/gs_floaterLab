#!/usr/bin/env bash
# pagemap.sh — build/main.pdf 에서 절이 몇 쪽을 먹는지 재고 계획과 비교한다.
#   ./paper/scripts/pagemap.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import subprocess,re,sys
root=sys.argv[1]; pdf=f"{root}/build/main.pdf"
n=int(re.search(r'Pages:\s+(\d+)',subprocess.run(['pdfinfo',pdf],capture_output=True,text=True).stdout).group(1))
pat=re.compile(r'^\s*(\d+)\.\s+([A-Z][A-Za-z \-]{3,45})\s*$')
starts={}
for p in range(1,n+1):
    t=subprocess.run(['pdftotext','-f',str(p),'-l',str(p),pdf,'-'],capture_output=True,text=True).stdout
    for l in t.split('\n'):
        m=pat.match(l)
        if m:
            k=f"{m.group(1)} {m.group(2).strip()}"
            starts.setdefault(k,p)
# 참고문헌 시작 = 본문 끝
refs=None
for p in range(1,n+1):
    t=subprocess.run(['pdftotext','-f',str(p),'-l',str(p),pdf,'-'],capture_output=True,text=True).stdout
    if re.search(r'^\s*References\s*$',t,re.M): refs=p; break
plan={'1 Introduction':1.0,'2 Related Work':1.15,'3 Method':2.4,
      '4 Experiments':2.2,'5 Limitations':0.2,'6 Conclusion':0.2}
ks=list(starts.items())
print(f"총 {n}쪽" + (f" · References 시작 p{refs} (그 쪽에 본문이 같이 있을 수 있음)" if refs else ""))
print(f"{'절':32s} {'시작쪽':>6s} {'실제':>6s} {'계획':>6s}  차이")
body=[(k,v) for k,v in ks if k in plan]
for i,(k,v) in enumerate(body):
    nxt = body[i+1][1] if i+1<len(body) else (refs or n+1)
    got = nxt - v if nxt>v else 0.5
    want= plan[k]
    d = got-want
    flag = "  ⚠" if abs(d)>=0.6 else ""
    print(f"{k:32s} {v:6d} {got:6.1f} {want:6.2f}  {d:+.1f}{flag}")
if refs:
    if refs>9:   print(f"\n⚠ 본문이 8쪽을 넘는다 (References가 p{refs}). CVPR 본문 제한 8쪽.")
    elif refs==9:print(f"\n⚠ References가 p9다. 본문 마지막 쪽을 References와 나눠 쓰고 있어 아슬아슬하다.")
    else:        print(f"\n✓ 본문 8쪽 안에 들어간다 (References p{refs}).")
print("\n주: 절이 한 쪽을 나눠 쓰면 '실제'가 과대 계산된다. 추세를 보는 용도.")
PY
