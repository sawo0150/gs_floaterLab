#!/usr/bin/env python3
"""make_figures.py (ppt0727) — VIGS-SLAM 실시간화 여정 exp52->exp56 발표용 그림 생성.

데이터 출처(전부 실측, context/experiments/exp53~56*.md 인용):
  - exp53_frontend_realtime_plan.md  (축A/B/C/D)
  - exp54_gsmapping_speed_ablation_plan.md (축1~7)
  - exp55_online_quality_carve.md (Phase1~3 + 부록)
  - exp56_mapping_fixedcost_reduction.md (Phase0/1/4/5-7/8/8b)

다크 테마 통일(ppt0720/make_figures.py와 동일 팔레트).
실행: python make_figures.py
출력: img/*.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path

HERE = Path(__file__).parent
IMG = HERE / "img"
IMG.mkdir(exist_ok=True)

# ── 한글 폰트 ──────────────────────────────────────────────────────
for cand in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]:
    try:
        fm.fontManager.addfont(cand)
    except Exception:
        pass
for fam in ["Noto Sans CJK KR", "Noto Sans CJK JP", "DejaVu Sans"]:
    if any(fam in f.name for f in fm.fontManager.ttflist) or fam == "DejaVu Sans":
        plt.rcParams["font.family"] = fam
        break

# ── 팔레트 (ppt0720과 동일) ────────────────────────────────────────
BG = "#12151c"
PANEL = "#1a1f2b"
GRID = "#2a3242"
TEXT = "#e8ecf4"
MUTED = "#8b95ab"
BUDGET = "#ffb454"
BLUE = "#4c86ea"
CORAL = "#ef6a5c"
GREEN = "#4cc98a"
PURPLE = "#a479e0"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "grid.color": GRID,
    "font.size": 12,
})


def style_ax(ax, hide_y=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED)
    if hide_y:
        ax.spines["left"].set_visible(False)
        ax.set_yticks([])


def savefig(fig, name):
    fig.savefig(IMG / name, facecolor=BG, bbox_inches="tight", dpi=170)
    plt.close(fig)
    print(f"  [saved] {name}")


# ════════════════════════════════════════════════════════════════
# 슬라이드 3 — TL;DR: 실시간 배수 추이
# ════════════════════════════════════════════════════════════════
def fig_tldr_ratio():
    stages = ["07/20\n(exp52 정정)", "exp53+54", "exp56 최종"]
    vals = [1.52, 0.94, 0.70]
    colors = [CORAL, BUDGET, GREEN]
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    bars = ax.bar(stages, vals, color=colors, width=0.52, zorder=3)
    ax.axhline(1.0, color=TEXT, linestyle="--", linewidth=1.4, zorder=2)
    ax.text(2.35, 1.03, "실시간 기준선(1.0×)", fontsize=11, color=TEXT, ha="right")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.04, f"{v:.2f}×",
                 ha="center", fontsize=17, fontweight="bold", color=TEXT)
    ax.set_ylim(0, 1.75)
    ax.set_ylabel("실시간 배수 (소요/예산, 낮을수록 좋음)")
    style_ax(ax)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_title("1.52× (비실시간) → 0.94× (최초 돌파) → 0.70× (여유 확대)", fontsize=13, pad=12, color=MUTED)
    savefig(fig, "fig_tldr_ratio.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 4 — exp53: 프론트엔드 경량화 축A~D
# ════════════════════════════════════════════════════════════════
def fig_exp53_axes():
    labels = ["축A\ncorrelation iters\n4/2→1/0", "축B\nmotion_filter.thresh\n2.4→3.6", "축C\nfrontend_window/radius\n25/2→15/1", "축D\ncorrelation 해상도\n(재학습 필요)"]
    vals = [-20.7, -15.4, -1.7, 0]
    colors = [BLUE, BUDGET, GREEN, GRID]
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    bars = ax.bar(labels, vals, color=colors, width=0.55, zorder=3)
    for i, (b, v) in enumerate(zip(bars, vals)):
        if i < 3:
            ax.text(b.get_x() + b.get_width() / 2, v - 1.3, f"{v:.1f}%",
                     ha="center", fontsize=15, fontweight="bold", color=TEXT)
        else:
            ax.text(b.get_x() + b.get_width() / 2, 0.6, "구현 불가\n(기각)",
                     ha="center", fontsize=12, color=MUTED, fontweight="bold")
    ax.set_ylabel("온라인 루프 총합 변화 (%)")
    ax.set_ylim(-25, 4)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.axhline(0, color=GRID, linewidth=1)
    ax.set_title("축B(keyframe 밀도 억제)가 최대 단일 레버 — 축D는 정직하게 기각", fontsize=12.5, pad=12, color=MUTED)
    savefig(fig, "fig_exp53_axes.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 5 — exp54: 매핑 경량화 7축
# ════════════════════════════════════════════════════════════════
def fig_exp54_axes():
    rows = [
        ("축1  pcd_downsample 64→128", -3.3, GREEN, "채택"),
        ("축2  init 밀도 2배↓", +1.2, CORAL, "기각(축6과 상쇄)"),
        ("축3  map() iters 10→5", 0.0, CORAL, "기각(ROI 나쁨)"),
        ("축4  render_downsample=2", -4.2, PURPLE, "보류(-0.8dB, 코드만 보존)"),
        ("축5  max_viewpoints 축소", 0.0, CORAL, "기각"),
        ("축6+2  densify 억제+init 성김", +0.2, CORAL, "기각(개수↓해도 시간 그대로)"),
        ("축7  PPM 적응 샘플링", 0.0, GREEN, "채택(+0.16dB 공짜)"),
    ]
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = [r[2] for r in rows]
    tags = [r[3] for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5.4))
    y = np.arange(len(rows))[::-1]
    bars = ax.barh(y, vals, color=colors, height=0.55, zorder=3)
    ax.axvline(0, color=GRID, linewidth=1)
    for yi, v, tag in zip(y, vals, tags):
        xpos = v + (0.35 if v >= 0 else -0.35)
        ha = "left" if v >= 0 else "right"
        vlabel = f"{v:+.1f}%" if v != 0 else "±0%"
        ax.text(xpos, yi, f"{vlabel}  —  {tag}", va="center", ha=ha, fontsize=11.5, color=TEXT)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlim(-5, 8)
    ax.set_xlabel("온라인 루프 총합 변화 (%, 음수=단축)")
    style_ax(ax)
    ax.grid(axis="x", alpha=0.25, zorder=0)
    savefig(fig, "fig_exp54_axes.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 6 — 실시간 최초 돌파 (exp53+54)
# ════════════════════════════════════════════════════════════════
def fig_breakthrough():
    stages = ["07/20 (exp52 정정)", "exp53+exp54 통합"]
    vals = [1.52, 0.94]
    colors = [CORAL, GREEN]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    bars = ax.bar(stages, vals, color=colors, width=0.45, zorder=3)
    ax.axhline(1.0, color=TEXT, linestyle="--", linewidth=1.4, zorder=2)
    ax.text(1.62, 1.03, "실시간 기준선(1.0×)", fontsize=11, color=TEXT, ha="right")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.04, f"{v:.2f}×",
                 ha="center", fontsize=18, fontweight="bold", color=TEXT)
    ax.set_ylim(0, 1.75)
    ax.set_ylabel("실시간 배수")
    style_ax(ax)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_title("61.34s — 이 프로젝트 최초로 1.0배 미만 달성", fontsize=13, pad=12, color=MUTED)
    savefig(fig, "fig_breakthrough.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 7 — exp55 Phase1/2: 내용-적응 gaussian 예산
# ════════════════════════════════════════════════════════════════
def fig_exp55_adaptive():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))

    # 좌: 상관관계 개념도 (r=0.538) — 실측 산점도 원자료가 없어 요약 지표로 표현
    ax = axes[0]
    rng = np.random.default_rng(7)
    n = 113
    x = rng.normal(0.5, 0.18, n).clip(0.05, 1.0)
    noise = rng.normal(0, 0.28, n)
    y = 0.538 * (x - x.mean()) / x.std() + noise
    y = (y - y.min()) / (y.max() - y.min())
    ax.scatter(x, y, s=26, color=BLUE, alpha=0.65, zorder=3, edgecolors="none")
    z = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, np.poly1d(z)(xs), color=BUDGET, linewidth=2.2, zorder=4)
    ax.text(0.05, 0.95, "Pearson r = 0.538\n(n=113 keyframe)", transform=ax.transAxes,
            fontsize=13, color=TEXT, fontweight="bold", va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=PANEL, edgecolor=BUDGET, linewidth=1.2))
    ax.set_xlabel("keyframe Sobel gradient 평균 (디테일 정도)")
    ax.set_ylabel("고밀도 예산에서 얻는 이득 (정규화)")
    ax.set_title("Phase1 — 디테일과 밀도 이득의 상관관계 (개념도, r만 실측치)", fontsize=12, color=MUTED)
    style_ax(ax)
    ax.grid(alpha=0.2, zorder=0)

    # 우: 적응 전/후 평균 gaussian 수
    ax = axes[1]
    labels = ["baseline\n(균일 예산)", "Phase2 채택\n(내용-적응 예산)"]
    vals = [94219, 60439]
    colors = [CORAL, GREEN]
    bars = ax.bar(labels, vals, color=colors, width=0.5, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2000, f"{v:,}", ha="center",
                 fontsize=13, fontweight="bold", color=TEXT)
    ax.text(0.5, 0.5, "−35.9%", transform=ax.transAxes, fontsize=26, fontweight="bold",
            color=GREEN, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=PANEL, edgecolor=GREEN, linewidth=1.5))
    ax.set_ylabel("평균 gaussian 수 (학습 중)")
    ax.set_ylim(0, 110000)
    ax.set_title("Phase2 — PSNR·궤적 손실 없이 gaussian 절감", fontsize=12.5, color=MUTED)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)

    fig.tight_layout()
    savefig(fig, "fig_exp55_adaptive.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 8 — exp55 Phase3: carve loss 온라인 이식
# ════════════════════════════════════════════════════════════════
def fig_exp55_carve():
    metrics = ["가시 floater\n비율", "가시 floater\n수", "평균 score\n(전체)", "평균 score\n(가시만)"]
    before = [18.76, 14199 / 100, 21.75, 20.06]  # normalized scaled where needed for visual only; use pct panel
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))

    ax = axes[0]
    labels = ["carve off\n(baseline)", "carve on\n(carve_lambda=0.05)"]
    vals = [18.76, 17.35]
    colors = [CORAL, GREEN]
    bars = ax.bar(labels, vals, color=colors, width=0.48, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.2f}%", ha="center",
                 fontsize=15, fontweight="bold", color=TEXT)
    ax.annotate("", xy=(1, 17.35), xytext=(0, 18.76),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.6, connectionstyle="arc3,rad=-0.25"))
    ax.text(0.5, 19.6, "상대 −7.5%", fontsize=12.5, color=GREEN, ha="center", fontweight="bold")
    ax.set_ylabel("가시 floater 비율 (%)")
    ax.set_ylim(15, 21)
    ax.set_title("가시 floater 비율", fontsize=12.5, color=MUTED)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)

    ax = axes[1]
    rows = [("가시 floater 수", 14199, 13066, "−8.0%"),
            ("평균 score(전체)", 0.2175, 0.2086, "−4.1%"),
            ("평균 score(가시만)", 0.2006, 0.1906, "−5.0%")]
    y = np.arange(len(rows))[::-1]
    for i, (name, b, a, pct) in enumerate(rows):
        yi = y[i]
        ax.barh(yi + 0.18, 100, height=0.3, color=GRID, zorder=2)
        rel = a / b * 100
        ax.barh(yi + 0.18, rel, height=0.3, color=GREEN, zorder=3)
        ax.text(103, yi + 0.18, f"{pct}", va="center", fontsize=12, color=GREEN, fontweight="bold")
        ax.text(-3, yi + 0.18, name, va="center", ha="right", fontsize=11.5, color=TEXT)
    ax.set_xlim(0, 130)
    ax.set_ylim(-0.3, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("네 지표 전부 일관 개선 (carve on 기준 baseline=100)", fontsize=12.5, color=MUTED)

    fig.tight_layout()
    savefig(fig, "fig_exp55_carve.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 9 — exp55 부록: 직렬 vs 병렬
# ════════════════════════════════════════════════════════════════
def fig_exp55_appendix():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))

    ax = axes[0]
    cats = ["직렬(경합 없음)\n순수 비용", "병렬(gs_parallel)\n실측"]
    tracking = [27.9, 53.19]
    mapping = [80.1, 91.21 - 53.19 if False else 0]  # placeholder unused
    # 직렬: tracking 27.9 + mapping 80.1 (순수). 병렬 실측: tracking 53.19(경합 포함), mapping은 스킵되어 총합과 별개이므로 총합만 표시
    x = np.arange(2)
    track_vals = [27.9, 53.19]
    map_vals = [80.1, 0]  # 병렬은 map이 총합에 안 겹쳐 보이므로 생략, 텍스트로 설명
    b1 = ax.bar(x, track_vals, color=BLUE, width=0.45, zorder=3, label="tracking(순수/실측)")
    b2 = ax.bar(x, map_vals, bottom=track_vals, color=CORAL, width=0.45, zorder=3, label="mapping(순수, 직렬만)")
    ax.text(0, 27.9 + 80.1 + 3, "108.0s", ha="center", fontsize=13, fontweight="bold", color=TEXT)
    ax.text(1, 53.19 + 3, "53.19s\n(GPU 경합으로 +23s 부풀림)", ha="center", fontsize=10.5, color=CORAL, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=11.5)
    ax.set_ylabel("시간 (s)")
    ax.legend(loc="upper left", fontsize=10, framealpha=0)
    ax.set_ylim(0, 130)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.set_title("직렬 순수 비용: mapping이 74%로 압도적", fontsize=12, color=MUTED)

    ax = axes[1]
    labels = ["직렬 실행", "병렬(gs_parallel)"]
    calls = [110, 22]
    colors = [BLUE, BUDGET]
    bars = ax.bar(labels, calls, color=colors, width=0.45, zorder=3)
    for b, v in zip(bars, calls):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v}회", ha="center", fontsize=15, fontweight="bold", color=TEXT)
    ax.annotate("약 80%\n스킵", xy=(1, 22), xytext=(0.5, 70),
                fontsize=12.5, color=CORAL, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=CORAL, lw=1.6))
    ax.set_ylabel("map() 성사 횟수")
    ax.set_ylim(0, 125)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.set_title("_gs_queue 드롭 정책 — 병렬 모드의 숨은 비용", fontsize=12, color=MUTED)

    fig.tight_layout()
    savefig(fig, "fig_exp55_appendix.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 10 — exp56 문제 제기: gaussian↓인데 시간은 그대로
# ════════════════════════════════════════════════════════════════
def fig_exp56_problem():
    labels = ["평균 gaussian 수", "순수 mapping 시간"]
    vals = [-35.9, -12.2]
    colors = [BLUE, CORAL]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(labels, vals, color=colors, width=0.42, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v - 2.2, f"{v:.1f}%", ha="center",
                 fontsize=18, fontweight="bold", color=TEXT)
    ax.axhline(0, color=GRID, linewidth=1)
    ax.set_ylim(-42, 4)
    ax.set_ylabel("변화율 (%)")
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.set_title("gaussian을 35.9% 줄여도 시간은 12.2%만 줄었다 — 왜?", fontsize=13, pad=12, color=MUTED)
    savefig(fig, "fig_exp56_problem.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 11 — Phase0: map() 시간 구성
# ════════════════════════════════════════════════════════════════
def fig_exp56_phase0():
    labels = ["rasterize\n(N+픽셀 혼합)", "backward\n(N+픽셀 혼합)", "loss_compute\n(순수 픽셀, N무관)"]
    vals = [40, 34, 24]
    colors = [BLUE, PURPLE, BUDGET]
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    wedges, texts, autotexts = ax.pie(
        vals + [2], colors=colors + [GRID], startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor=BG, linewidth=2),
        autopct=lambda p: f"{p:.0f}%" if p > 3 else "", pctdistance=0.79,
    )
    for at in autotexts:
        at.set_color(TEXT)
        at.set_fontsize(15)
        at.set_fontweight("bold")
    ax.text(0, 0, "직렬 순수\nmap()\n68.16s", ha="center", va="center", fontsize=13.5, color=TEXT, fontweight="bold")
    ax.legend(wedges[:3], labels, loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=11.5,
              frameon=False, labelcolor=TEXT, ncol=1)
    ax.set_title("전부 iters × n_view에 곱으로 걸림 — 고정비가 지배적", fontsize=12.5, color=MUTED, pad=10)
    savefig(fig, "fig_exp56_phase0.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 12 — Phase1: iters 스윕
# ════════════════════════════════════════════════════════════════
def fig_exp56_phase1():
    iters = ["10\n(baseline)", "7\n(채택)", "5"]
    time_s = [59.80, 50.17, 49.44]
    psnr_mean = [22.61, 22.82, 22.80]
    calls = [22, 26, 32]

    fig, ax1 = plt.subplots(figsize=(9.5, 5.4))
    x = np.arange(3)
    colors = [MUTED, GREEN, BLUE]
    bars = ax1.bar(x, time_s, color=colors, width=0.42, zorder=3)
    for b, v in zip(bars, time_s):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.9, f"{v:.2f}s", ha="center", fontsize=13, fontweight="bold", color=TEXT)
    ax1.set_xticks(x)
    ax1.set_xticklabels(iters, fontsize=12.5)
    ax1.set_xlabel("map() iters")
    ax1.set_ylabel("온라인 루프 총합 (s)")
    ax1.set_ylim(0, 68)
    style_ax(ax1)
    ax1.grid(axis="y", alpha=0.2, zorder=0)

    ax2 = ax1.twinx()
    ax2.plot(x, psnr_mean, color=BUDGET, marker="o", markersize=9, linewidth=2.4, zorder=4, label="PSNR mean")
    for xi, v in zip(x, psnr_mean):
        ax2.text(xi, v + 0.09, f"{v:.2f}dB", ha="center", fontsize=11, color=BUDGET, fontweight="bold")
    ax2.set_ylabel("PSNR mean (dB)", color=BUDGET)
    ax2.set_ylim(22.4, 23.3)
    ax2.tick_params(colors=BUDGET)
    for s in ax2.spines.values():
        s.set_visible(False)

    for xi, c in zip(x, calls):
        ax1.text(xi, 2, f"map() {c}회", ha="center", fontsize=10.5, color=TEXT if xi == 1 else MUTED)

    ax1.set_title("iters=7 — 시간·PSNR·처리 keyframe 수 전부 동시 개선", fontsize=13, color=MUTED, pad=12)
    fig.tight_layout()
    savefig(fig, "fig_exp56_phase1.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 13 — Phase4: 초기화 호출이 49% 차지
# ════════════════════════════════════════════════════════════════
def fig_exp56_phase4():
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    vals = [49.3, 50.7]
    colors = [CORAL, GRID]
    wedges, _ = ax.pie(
        vals, colors=colors, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.44, edgecolor=BG, linewidth=2),
    )
    ax.text(0, 0.12, "49.3%", ha="center", va="center", fontsize=34, color=CORAL, fontweight="bold")
    ax.text(0, -0.14, "초기화 2~3회", ha="center", va="center", fontsize=13, color=TEXT)
    ax.text(0, -0.30, "(전체 26회 중)", ha="center", va="center", fontsize=11, color=MUTED)
    ax.legend(wedges, ["초기화/재초기화 2~3회\n(iters=90~131)", "일반 keyframe 21회\n(iters=7)"],
              loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=11.5, frameon=False, labelcolor=TEXT)
    ax.set_title("map() 호출 26회 중 단 2~3회가 mapping 시간의 절반", fontsize=12.5, color=MUTED, pad=10)
    savefig(fig, "fig_exp56_phase4.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 14 — Phase6(실패) vs Phase7(성공)
# ════════════════════════════════════════════════════════════════
def fig_exp56_phase67():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))

    ax = axes[0]
    labels = ["baseline\n(ws=10,iters=7)", "축1\n(ws=15,iters=5)", "축2\n(ws=19,iters=4)"]
    vals = [22.73, 21.64, 19.27]
    colors = [MUTED, CORAL, "#c0392b"]
    bars = ax.bar(labels, vals, color=colors, width=0.5, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.15, f"{v:.2f}", ha="center", fontsize=13, fontweight="bold", color=TEXT)
    ax.annotate("", xy=(2, 19.6), xytext=(0, 22.5),
                arrowprops=dict(arrowstyle="->", color=CORAL, lw=2.2, connectionstyle="arc3,rad=0.15"))
    ax.set_ylabel("PSNR mean (dB)")
    ax.set_ylim(17, 24.5)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.set_title("Phase6 — 프론티어(window) 확대: 실패", fontsize=12.5, color=CORAL, fontweight="bold")

    ax = axes[1]
    labels = ["baseline\n(n_global=2)", "n_global=6\n(채택)", "n_global=10"]
    vals = [22.73, 22.97, 22.9]
    colors = [MUTED, GREEN, "#3aa66f"]
    bars = ax.bar(labels, vals, color=colors, width=0.5, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}", ha="center", fontsize=13, fontweight="bold", color=TEXT)
    ax.annotate("", xy=(1, 22.9), xytext=(0, 22.8),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=2.2, connectionstyle="arc3,rad=-0.15"))
    ax.set_ylabel("PSNR mean (dB)")
    ax.set_ylim(22.0, 23.4)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.set_title("Phase7 — 과거-keyframe 곁눈질 확대: 성공", fontsize=12.5, color=GREEN, fontweight="bold")

    fig.tight_layout()
    savefig(fig, "fig_exp56_phase67.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 15 — Phase8: 무위험 3관왕
# ════════════════════════════════════════════════════════════════
def fig_exp56_phase8():
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.axis("off")
    cards = [
        ("시간", "−3.0%", "47.20s → 45.79s", BLUE),
        ("PSNR", "+0.52 / +0.45dB", "mean / kf", GREEN),
        ("coverage", "+38%", "map() 26회 → 36회", BUDGET),
    ]
    for i, (label, big, small, color) in enumerate(cards):
        x0 = i / 3
        rect = plt.Rectangle((x0 + 0.02, 0.08), 0.29, 0.84, transform=ax.transAxes,
                              facecolor=PANEL, edgecolor=color, linewidth=1.8, zorder=2)
        ax.add_patch(rect)
        ax.text(x0 + 0.165, 0.72, "✓", transform=ax.transAxes, fontsize=30, color=color,
                ha="center", fontweight="bold")
        ax.text(x0 + 0.165, 0.50, big, transform=ax.transAxes, fontsize=19, color=TEXT,
                ha="center", fontweight="bold")
        ax.text(x0 + 0.165, 0.34, label, transform=ax.transAxes, fontsize=13, color=color,
                ha="center", fontweight="bold")
        ax.text(x0 + 0.165, 0.20, small, transform=ax.transAxes, fontsize=10.5, color=MUTED, ha="center")
    ax.text(0.5, -0.08, "그래디언트 수학은 전혀 안 건드림 — camera_utils.py 행렬 캐싱만 추가",
            transform=ax.transAxes, fontsize=12, color=MUTED, ha="center")
    savefig(fig, "fig_exp56_phase8.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 16 — Phase8b: batch CUDA 5단계 타임라인
# ════════════════════════════════════════════════════════════════
def fig_exp56_phase8b():
    stages = [
        ("1. 구현", "host-loop batch\nCUDA C++ 신규", BLUE),
        ("2. 검증", "forward 완전일치\nbackward 수치검증 통과", BLUE),
        ("3. 실전 버그", "PSNR 6.65dB 붕괴\n(depth shape 불일치)", CORAL),
        ("4. 수정", "out_depth[b,0]\n→ out_depth[b]", BUDGET),
        ("5. 최종 판정", "PSNR 정상화\n시간 개선 없음(<1%)", MUTED),
    ]
    fig, ax = plt.subplots(figsize=(13, 3.4))
    ax.axis("off")
    n = len(stages)
    xs = np.linspace(0.06, 0.94, n)
    ax.plot(xs, [0.5] * n, color=GRID, linewidth=2.5, zorder=1, transform=ax.transAxes)
    for x, (title, desc, color) in zip(xs, stages):
        ax.scatter([x], [0.5], s=280, color=color, zorder=3, transform=ax.transAxes, edgecolors=BG, linewidths=2)
        ax.text(x, 0.78, title, transform=ax.transAxes, ha="center", fontsize=13, color=TEXT, fontweight="bold")
        ax.text(x, 0.20, desc, transform=ax.transAxes, ha="center", fontsize=10.5, color=MUTED, linespacing=1.4)
    savefig(fig, "fig_exp56_phase8b.png")


# ════════════════════════════════════════════════════════════════
# 슬라이드 17 — 전체 타임라인 (라인차트)
# ════════════════════════════════════════════════════════════════
def fig_overall_timeline():
    stages = ["07/20\n(exp52 정정)", "exp53+54", "exp55", "exp56 최종"]
    ratio = [1.52, 0.94, 0.92, 0.70]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    x = np.arange(len(stages))
    ax.plot(x, ratio, color=BLUE, marker="o", markersize=11, linewidth=2.6, zorder=4)
    for xi, v in zip(x, ratio):
        ax.text(xi, v + 0.06, f"{v:.2f}×", ha="center", fontsize=14, fontweight="bold", color=TEXT)
    ax.axhline(1.0, color=BUDGET, linestyle="--", linewidth=1.6, zorder=2)
    ax.text(3.35, 1.03, "실시간 기준선", fontsize=11, color=BUDGET, ha="right")
    ax.fill_between(x, ratio, 1.0, where=np.array(ratio) < 1.0, color=GREEN, alpha=0.12, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=12)
    ax.set_ylabel("실시간 배수")
    ax.set_ylim(0.5, 1.7)
    style_ax(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    ax.set_title("실시간을 달성한 뒤에도 계속 여유를 확대", fontsize=13, color=MUTED, pad=12)
    savefig(fig, "fig_overall_timeline.png")


if __name__ == "__main__":
    print("generating figures ->", IMG)
    fig_tldr_ratio()
    fig_exp53_axes()
    fig_exp54_axes()
    fig_breakthrough()
    fig_exp55_adaptive()
    fig_exp55_carve()
    fig_exp55_appendix()
    fig_exp56_problem()
    fig_exp56_phase0()
    fig_exp56_phase1()
    fig_exp56_phase4()
    fig_exp56_phase67()
    fig_exp56_phase8()
    fig_exp56_phase8b()
    fig_overall_timeline()
    print("done.")
