#!/usr/bin/env python3
"""make_figures.py (ppt0720) — exp52/exp53 실시간성 타임라인 시각자료.

데이터 출처: context/experiments/exp52_vigs_slam_eval.md 실측치 (1253 시퀀스, 65.1초 실녹화,
imu_cpp+TensorRT 가속 적용 기준). 두 개의 별도 실측 런에서 나온 숫자를 섞지 않고 각 그림
안에서는 같은 런의 숫자만 쓴다(런간 자연 편차는 각주로 명시).

figure 목록:
  fig_timeline_serial     시나리오A: 순차 실행 누적 구성 (motion_filter+frontend+PGBA+gs_mapping+오버헤드)
  fig_timeline_parallel   시나리오B: gs_parallel 2-레인 타임라인 (실제연산 vs GPU경합지연)
  fig_overlap_efficiency  오버랩 효율 66% 계산 막대
  fig_theoretical_floor   이론적 최선(완벽 병렬 가정) vs 예산선
  fig_components          4패널: frontend/gs_mapping/motion_filter/오버헤드 세부 분해

실행: python make_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as _fm
from matplotlib.patches import Rectangle

for _p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf"]:
    if Path(_p).exists():
        try:
            _fm.fontManager.addfont(_p)
            plt.rcParams["font.family"] = _fm.FontProperties(fname=_p).get_name()
            break
        except Exception:
            pass
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight",
                      "font.size": 11})

HERE = Path(__file__).parent
IMG = HERE / "img"
IMG.mkdir(exist_ok=True)

# ── 팔레트 (아티팩트와 동일 의미 배정: 파랑=tracking, 코랄=mapping, 주황=예산선) ──
BG = "#12151c"
PANEL = "#1a1f2b"
GRID = "#2a3242"
TEXT = "#e8ecf4"
MUTED = "#8b95ab"

C_MOTION = "#7fb0ef"
C_FRONTEND = "#4c86ea"
C_PGBA = "#a9cbf3"
C_OVERHEAD = "#4a5568"

C_BACKWARD = "#ef6a5c"
C_RASTERIZE = "#f0917a"
C_LOSS = "#f4b295"
C_OPT = "#d9506a"
C_MAPETC = "#8a4550"

C_BUDGET = "#ffb454"
C_FLOOR = "#c9d2e3"
C_DELAY = "#3a4256"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL,
    "text.color": TEXT, "axes.edgecolor": GRID,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": MUTED, "grid.color": GRID,
})


def style_ax(ax):
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED)


# ── fig_timeline_serial ──────────────────────────────────────────────
def fig_timeline_serial():
    fig, ax = plt.subplots(figsize=(11, 2.6))
    fig.patch.set_facecolor(BG)
    segs = [
        ("motion_filter", 9.4, C_MOTION),
        ("frontend", 43.2, C_FRONTEND),
        ("PGBA", 10.0, C_PGBA),
        ("gs_mapping", 90.5, C_BACKWARD),
        ("오버헤드", 27.0, C_OVERHEAD),
    ]
    x = 0
    for name, w, c in segs:
        ax.barh(0, w, left=x, height=0.55, color=c, edgecolor=BG, linewidth=1.5)
        if w > 8:
            ax.text(x + w / 2, 0, f"{name}\n{w:.1f}s", ha="center", va="center",
                    fontsize=9.5, color="#0d0f14" if c in (C_MOTION, C_PGBA) else "white", fontweight="bold")
        x += w
    ax.axvline(65.1, color=C_BUDGET, linestyle="--", linewidth=2.2)
    ax.text(65.1, 0.42, "예산 65.1s", color=C_BUDGET, fontsize=10.5, fontweight="bold", ha="left")
    ax.text(180.1, -0.42, "총합 180.10s = 실시간의 2.77배", color=TEXT, fontsize=11,
            fontweight="bold", ha="right")
    ax.set_xlim(0, 195)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([])
    ax.set_xlabel("누적 시간 (초)")
    style_ax(ax)
    ax.set_title("시나리오 A · 순차 실행 (gs_parallel 없음)", fontsize=13, fontweight="bold",
                  color=TEXT, loc="left")
    plt.savefig(IMG / "fig_timeline_serial.png", facecolor=BG)
    plt.close()


# ── fig_timeline_parallel ────────────────────────────────────────────
def fig_timeline_parallel():
    """Tracking 스레드를 frontend/motion_filter/PGBA로 쪼개서, 어느 구성요소가
    실제로 경합의 영향을 받는지 보여준다 (2026-07-20 수정: 이전 버전은 Tracking을
    하나의 뭉친 막대로 그려서 frontend 자체가 느려진 게 안 보였음)."""
    fig, ax = plt.subplots(figsize=(11, 3.3))
    fig.patch.set_facecolor(BG)

    # Tracking 스레드 = frontend + motion_filter + pgba(run+call_gs), 이 순서로 쌓음
    track_segs = [
        ("frontend", 74.28, C_FRONTEND),
        ("motion_filter", 15.56, C_MOTION),
        ("PGBA", 11.23, C_PGBA),
    ]
    y_track = 1
    x = 0
    for name, v, c in track_segs:
        ax.barh(y_track, v, left=x, height=0.55, color=c, edgecolor=BG, linewidth=1.5)
        if v > 8:
            ax.text(x + v / 2, y_track, f"{name}\n{v:.1f}s", ha="center", va="center",
                    fontsize=9, color="white" if c != C_PGBA else "#0d0f14", fontweight="bold")
        x += v
    ax.text(-2, y_track, "Tracking\n스레드", ha="right", va="center", fontsize=10.5,
            color=TEXT, fontweight="bold")
    ax.text(x + 2, y_track, f"합 {x:.1f}s", ha="left", va="center", fontsize=9.5, color=MUTED)

    y_map = 0
    ax.barh(y_map, 86.24, left=0, height=0.55, color=C_BACKWARD, edgecolor=BG, linewidth=1.5)
    ax.text(86.24 / 2, y_map, "gs_mapping (raw)\n86.24s", ha="center", va="center",
            fontsize=9.5, color="white", fontweight="bold")
    ax.text(-2, y_map, "GS Mapping\n스레드", ha="right", va="center", fontsize=10.5,
            color=TEXT, fontweight="bold")

    ax.axvline(65.1, color=C_BUDGET, linestyle="--", linewidth=2.2)
    ax.text(65.1, 1.62, "예산 65.1s", color=C_BUDGET, fontsize=10.5, fontweight="bold", ha="left")
    ax.axvline(133.04, color=TEXT, linestyle=":", linewidth=1.5, alpha=0.6)
    ax.text(133.04, -0.78, "실측 총합(wall-clock) 133.04s — 두 스레드가 함께 끝남",
            color=TEXT, fontsize=9.5, ha="center", va="top")

    ax.set_xlim(-24, 152)
    ax.set_ylim(-1.05, 1.85)
    ax.set_yticks([])
    ax.set_xlabel("초 (Tracking 행은 구성요소별 합, Mapping 행은 raw 연산량 — 둘이 wall-clock상\n"
                  "동시에 겹쳐 돌면서 서로를 지연시켜 133.04s에 함께 수렴; 아래 그림 참조)")
    style_ax(ax)
    ax.set_title("시나리오 B · gs_parallel — Tracking 스레드 내부 구성", fontsize=13,
                  fontweight="bold", color=TEXT, loc="left")
    plt.savefig(IMG / "fig_timeline_parallel.png", facecolor=BG)
    plt.close()


# ── fig_frontend_contention (신규) ───────────────────────────────────
def fig_frontend_contention():
    """직렬 vs 병렬에서 frontend/motion_filter/PGBA 각각이 얼마나 느려졌는지 직접 비교."""
    fig, ax = plt.subplots(figsize=(11, 3.4))
    fig.patch.set_facecolor(BG)

    items = [
        ("frontend", 43.2, 74.28, C_FRONTEND),
        ("motion_filter", 9.4, 15.56, C_MOTION),
        ("PGBA", 10.0, 11.23, C_PGBA),
    ]
    bar_h = 0.32
    for i, (name, serial, parallel, c) in enumerate(items):
        y0 = (len(items) - 1 - i) * 1.1
        ax.barh(y0 + 0.22, serial, height=bar_h, color=GRID, edgecolor=BG, linewidth=1)
        ax.text(serial + 1.5, y0 + 0.22, f"{serial:.1f}s", va="center", fontsize=10, color=MUTED)
        ax.barh(y0 - 0.22, parallel, height=bar_h, color=c, edgecolor=BG, linewidth=1)
        ax.text(parallel + 1.5, y0 - 0.22, f"{parallel:.1f}s", va="center", fontsize=10,
                color=TEXT, fontweight="bold")
        pct = (parallel / serial - 1) * 100
        ax.text(max(serial, parallel) + 16, y0, f"+{pct:.0f}%", va="center", fontsize=12,
                color=c, fontweight="bold")
        ax.text(-2, y0, name, va="center", ha="right", fontsize=11.5, color=TEXT, fontweight="bold")

    # legend proxies
    ax.barh(-1.3, 0, color=GRID, label="직렬 실행")
    ax.barh(-1.3, 0, color=C_FRONTEND, label="gs_parallel")
    ax.legend(loc="lower right", frameon=False, labelcolor=TEXT, fontsize=10)

    ax.set_xlim(-14, 100)
    ax.set_ylim(-0.6, 2.7)
    ax.set_yticks([])
    ax.set_xlabel("초")
    style_ax(ax)
    ax.set_title("직렬 vs gs_parallel — 구성요소별 자체 비용 변화 (경합 영향)", fontsize=13,
                  fontweight="bold", color=TEXT, loc="left")
    plt.savefig(IMG / "fig_frontend_contention.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_overlap_efficiency ───────────────────────────────────────────
def fig_overlap_efficiency():
    fig, ax = plt.subplots(figsize=(11, 3.2))
    fig.patch.set_facecolor(BG)

    tracking, mapping = 103.72, 86.24
    naive_sum = tracking + mapping          # 189.96
    perfect = max(tracking, mapping)         # 103.72
    actual = 133.04
    saved_actual = naive_sum - actual        # 56.92
    saved_max = naive_sum - perfect          # 86.24
    efficiency = saved_actual / saved_max    # 0.660

    bars = [
        ("순차 실행이라면", naive_sum, C_OVERHEAD),
        ("완벽한 병렬(경합 0)이라면", perfect, C_FLOOR),
        ("실측(gs_parallel)", actual, C_FRONTEND),
    ]
    y = list(range(len(bars)))[::-1]
    for (label, val, c), yy in zip(bars, y):
        ax.barh(yy, val, height=0.5, color=c, edgecolor=BG, linewidth=1.2)
        ax.text(val + 3, yy, f"{val:.1f}s", va="center", fontsize=11, color=TEXT, fontweight="bold")
        ax.text(-3, yy, label, va="center", ha="right", fontsize=10.5, color=TEXT)

    ax.axvline(65.1, color=C_BUDGET, linestyle="--", linewidth=2)
    ax.text(65.1, 2.75, "예산 65.1s", color=C_BUDGET, fontsize=10, fontweight="bold", ha="left")

    ax.set_xlim(-70, 205)
    ax.set_ylim(-0.6, 2.6)
    ax.set_yticks([])
    ax.set_xlabel("초")
    style_ax(ax)
    ax.set_title("오버랩 효율 = 실제 절약 / 최대 가능 절약", fontsize=13, fontweight="bold",
                  color=TEXT, loc="left")

    eq = (f"실제 절약 = 189.96 − 133.04 = 56.92s\n"
          f"최대 가능 절약 = 189.96 − 103.72 = 86.24s\n"
          f"오버랩 효율 = 56.92 / 86.24 = 66.0%  (나머지 34% = GPU 경합으로 못 숨긴 시간)")
    ax.text(1.0, -0.30, eq, transform=ax.transAxes, ha="right", va="top", fontsize=11,
            color=TEXT,
            bbox=dict(boxstyle="round,pad=0.5", facecolor=PANEL, edgecolor=GRID))
    plt.savefig(IMG / "fig_overlap_efficiency.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_theoretical_floor ────────────────────────────────────────────
def fig_theoretical_floor():
    fig, ax = plt.subplots(figsize=(11, 2.2))
    fig.patch.set_facecolor(BG)

    ax.barh(0.35, 89.6, height=0.3, color=C_FRONTEND, edgecolor=BG, linewidth=1.2)
    ax.text(89.6 / 2, 0.35, "직렬 체인 89.6s", ha="center", va="center", fontsize=9.5,
            color="white", fontweight="bold")
    ax.barh(-0.05, 90.5, height=0.3, color=C_BACKWARD, edgecolor=BG, linewidth=1.2)
    ax.text(90.5 / 2, -0.05, "gs_mapping 90.5s", ha="center", va="center", fontsize=9.5,
            color="white", fontweight="bold")

    ax.axvline(65.1, color=C_BUDGET, linestyle="--", linewidth=2.2)
    ax.text(65.1, 0.62, "예산 65.1s", color=C_BUDGET, fontsize=10.5, fontweight="bold", ha="left")
    ax.axvline(90.5, color=C_FLOOR, linestyle=":", linewidth=2)
    ax.text(93.5, -0.42, "이론적 최선 = max(89.6, 90.5) = 90.5s > 65.1s", color=C_FLOOR,
            fontsize=10, ha="left", fontweight="bold")

    ax.set_xlim(0, 145)
    ax.set_ylim(-0.35, 0.75)
    ax.set_yticks([])
    ax.set_xlabel("초")
    style_ax(ax)
    ax.set_title("완벽한 병렬화를 가정해도 도달 불가능한 예산", fontsize=13, fontweight="bold",
                  color=TEXT, loc="left")
    plt.savefig(IMG / "fig_theoretical_floor.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_components (4-panel) ─────────────────────────────────────────
def fig_components():
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4))
    fig.patch.set_facecolor(BG)

    panels = [
        ("Frontend Tracking · 43.2s", [
            ("bundle_adjust (BA solve)", 21.1, C_FRONTEND),
            ("update_op_forward (GRU)", 13.6, C_MOTION),
            ("corr_lookup/build/upsample", 6.9, C_PGBA),
            ("미계측", 1.6, C_OVERHEAD),
        ]),
        ("GS Mapping · 90.5s", [
            ("backward", 34.7, C_BACKWARD),
            ("rasterize", 31.4, C_RASTERIZE),
            ("loss_compute", 16.8, C_LOSS),
            ("optimizer/densify", 1.3, C_OPT),
            ("미계측", 6.3, C_MAPETC),
        ]),
        ("motion_filter · 9.4s", [
            ("prior_extractor(Omnidata)", 3.3, C_MOTION),
            ("flow_check", 2.9, C_PGBA),
            ("context_encoder", 0.7, C_FRONTEND),
            ("feature_encoder(fnet)", 0.6, C_BUDGET),
            ("미계측", 1.8, C_OVERHEAD),
        ]),
        ("track() 바깥 오버헤드 · 27.0s", [
            ("model_loading(1회성)", 1.5, C_MOTION),
            ("queue_get_wait(IPC 대기)", 4.4, C_PGBA),
            ("미계측 잔여(추정)", 21.1, C_OVERHEAD),
        ]),
    ]

    for ax, (title, items) in zip(axes.flat, panels):
        total = sum(v for _, v, _ in items)
        n = len(items)
        BAR_Y = -1.3
        x = 0
        for name, v, c in items:
            ax.barh(BAR_Y, v, left=x, height=0.9, color=c, edgecolor=BG, linewidth=1.2)
            x += v
        # legend list occupies data-y from (n-1) down to 0, well above the bar strip
        for i, (name, v, c) in enumerate(items):
            yy = (n - 1) - i
            ax.add_patch(Rectangle((0, yy - 0.16), total * 0.018, 0.32, color=c,
                                    transform=ax.transData, clip_on=False))
            ax.text(total * 0.03, yy, f"{name}: {v:.1f}s", fontsize=9.5, color=MUTED,
                    va="center", ha="left")
        ax.set_xlim(0, total * 1.02)
        ax.set_ylim(BAR_Y - 0.9, n)
        ax.set_yticks([])
        style_ax(ax)
        ax.set_title(title, fontsize=11.5, fontweight="bold", color=TEXT, loc="left", pad=8)

    fig.suptitle("구성요소별 세부 분해 — 순차 실행 런 기준 (1253 시퀀스 누적 시간)", fontsize=14, fontweight="bold",
                  color=TEXT, x=0.02, ha="left", y=1.0)
    fig.text(0.02, -0.01, "※ gs_parallel 하에서는 frontend(43.2→74.28s)·motion_filter(9.4→15.56s)가"
                          " GPU 경합으로 더 커짐 — 뒤 슬라이드 참조", fontsize=9.5, color=MUTED)
    plt.tight_layout(rect=[0, 0.01, 1, 0.95])
    plt.savefig(IMG / "fig_components.png", facecolor=BG, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    fig_timeline_serial()
    fig_timeline_parallel()
    fig_frontend_contention()
    fig_overlap_efficiency()
    fig_theoretical_floor()
    fig_components()
    print("done:", sorted(p.name for p in IMG.glob("*.png")))
