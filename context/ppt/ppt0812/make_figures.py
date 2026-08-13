#!/usr/bin/env python3
"""make_figures.py (ppt0812) — exp63 예산 경쟁 구조 분석 + 다음 4방향 계획 시각자료.

ppt0720(다크 테마, GPU 타임라인)과 동일 팔레트를 그대로 재사용.

figure 목록:
  fig_thread_arch       tracking 스레드 vs gs_worker 스레드, 공유 GPU 경쟁 구조
  fig_a2_scene_flip     A2 파라미터가 305는 살리고 12F는 죽인 실측 대조
  fig_polish_collapse   12F에서 background_polish step 수 6586->772 붕괴
  fig_instrumentation   기존 계측 커버리지(있음/없음) 지도
  fig_tradeoff_concept  keyframe 밀도 다이얼의 "이득 vs 손해" 개념도(305 vs 12F)
  fig_next_steps        계측 정비 4단계 로드맵

실행: python make_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as _fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

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
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight", "font.size": 11})

HERE = Path(__file__).parent
IMG = HERE / "img"
IMG.mkdir(exist_ok=True)

BG = "#12151c"
PANEL = "#1a1f2b"
GRID = "#2a3242"
TEXT = "#e8ecf4"
MUTED = "#8b95ab"
BUDGET = "#ffb454"
BLUE = "#4c86ea"
CORAL = "#ef6a5c"
GREEN = "#5fd68a"
PURPLE = "#b48cf0"


def _ax(figsize=(10, 5.6)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(TEXT)
    return fig, ax


# ── fig_thread_arch ──────────────────────────────────────────────
def fig_thread_arch():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    def box(x, y, w, h, text, color, fontsize=12.5, sub=None):
        r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.4, edgecolor=color, facecolor=PANEL)
        ax.add_patch(r)
        ax.text(x + w / 2, y + h / 2 + (0.16 if sub else 0), text, ha="center", va="center",
                 color=TEXT, fontsize=fontsize, fontweight="bold")
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.22, sub, ha="center", va="center",
                     color=MUTED, fontsize=9.5)

    # Tracking thread lane
    ax.text(0.15, 5.75, "TRACKING 스레드 (메인, 동기)", color=BLUE, fontsize=13, fontweight="bold")
    box(0.2, 4.8, 2.0, 0.75, "motion_filter", BLUE)
    box(2.5, 4.8, 2.35, 0.75, "frontend BA", BLUE, sub="for itr in range(iters1): 시간체크 없음")
    box(5.15, 4.8, 2.1, 0.75, "PGBA", BLUE, sub="loop closure")
    for x0, x1 in [(2.2, 2.5), (4.85, 5.15)]:
        ax.add_patch(FancyArrowPatch((x0, 5.175), (x1, 5.175), color=MUTED,
                                       arrowstyle="-|>", mutation_scale=14))

    # gs_worker thread lane
    ax.text(0.15, 3.55, "GS_WORKER 스레드 (별도, 큐 기반)", color=CORAL, fontsize=13, fontweight="bold")
    box(0.2, 2.6, 2.7, 0.75, "map()", CORAL, sub="키프레임 도착시 디스패치")
    box(3.2, 2.6, 3.4, 0.75, "background_polish_step", CORAL, sub="_gs_queue 비었을 때만 (idle-gated)")
    ax.add_patch(FancyArrowPatch((7.3, 4.15), (3.2, 3.35), color=MUTED, arrowstyle="-|>",
                                   mutation_scale=13, connectionstyle="arc3,rad=-0.25", linestyle=":"))
    ax.text(7.45, 3.9, "큐 비어있는지 확인", color=MUTED, fontsize=9, style="italic")

    # shared GPU
    box(2.0, 0.9, 5.5, 1.0, "공유 RTX GPU\nself.video.get_lock()으로 직렬화", BUDGET, fontsize=12.5)
    for x in [1.3, 4.75]:
        ax.add_patch(FancyArrowPatch((x, 2.55), (x, 1.9), color=BUDGET,
                                       arrowstyle="-|>", mutation_scale=13, linestyle="--", alpha=0.85))
    ax.add_patch(FancyArrowPatch((6.2, 4.75), (5.3, 3.75), color=BUDGET, arrowstyle="-|>",
                                   mutation_scale=13, linestyle="--", alpha=0.6,
                                   connectionstyle="arc3,rad=0.2"))

    ax.text(8.7, 4.0, "tracking이 바빠질수록\n→ polish 기회 감소", color=CORAL, fontsize=10.5,
             ha="left", va="center")
    ax.text(8.7, 5.2, "tracking엔\n시간예산 캡 없음", color=BLUE, fontsize=10.5, ha="left", va="center")

    fig.savefig(IMG / "fig_thread_arch.png", facecolor=BG)
    plt.close(fig)


# ── fig_a2_scene_flip ────────────────────────────────────────────
def fig_a2_scene_flip():
    fig, ax = _ax((10, 5.8))
    scenes = ["aria301_305", "aria301_12F"]
    before = [22.8154, 27.993]
    after = [29.8154, 23.153]
    x = range(len(scenes))
    w = 0.32
    b_vals = [v if v is not None else 0 for v in before]
    a_vals = after
    bars_b = ax.bar([i - w / 2 for i in x], b_vals, width=w, color=MUTED, alpha=0.55,
                      label="A2 이전(구 설정)")
    bars_a = ax.bar([i + w / 2 for i in x], a_vals, width=w,
                      color=[GREEN, CORAL], label="A2 적용 후")
    for i, (bv, av) in enumerate(zip(before, after)):
        if bv is not None:
            ax.text(i - w / 2, bv + 0.4, f"{bv:.2f}", ha="center", color=MUTED, fontsize=10)
            delta = av - bv
            sign = "+" if delta >= 0 else ""
            ax.text(i, max(bv, av) + 1.3, f"{sign}{delta:.2f}dB", ha="center",
                     color=(GREEN if delta >= 0 else CORAL), fontsize=12, fontweight="bold")
        ax.text(i + w / 2, av + 0.4, f"{av:.2f}", ha="center", color=TEXT, fontsize=10)
    ax.set_xticks(list(x))
    ax.set_xticklabels(scenes, color=TEXT, fontsize=12)
    ax.set_ylabel("Fixed held-out PSNR (dB)")
    ax.set_ylim(0, 34)
    ax.set_title("같은 A2 파라미터(thresh 2.6·iters1=2) — 305는 +7.0dB, 12F는 -4.8dB (미검증 상태로 방치됐다가 발견)",
                  fontsize=12.5)
    ax.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, loc="upper left")
    ax.grid(axis="y", color=GRID, alpha=0.4)
    fig.savefig(IMG / "fig_a2_scene_flip.png", facecolor=BG)
    plt.close(fig)


# ── fig_polish_collapse ──────────────────────────────────────────
def fig_polish_collapse():
    fig, ax = _ax((9.5, 5.6))
    labels = ["축A\n(thresh3.6/iters1=1)", "A2\n(thresh2.6/iters1=2)"]
    steps = [6586, 772]
    colors = [GREEN, CORAL]
    bars = ax.bar(labels, steps, width=0.45, color=colors)
    for b, v in zip(bars, steps):
        ax.text(b.get_x() + b.get_width() / 2, v + 120, f"{v:,} step", ha="center",
                 color=TEXT, fontsize=13, fontweight="bold")
    ax.annotate("", xy=(1, 900), xytext=(0, 6400),
                 arrowprops=dict(arrowstyle="-|>", color=BUDGET, lw=2,
                                  connectionstyle="arc3,rad=0.15"))
    ax.text(0.5, 4200, "-88%", color=BUDGET, fontsize=18, fontweight="bold", ha="center")
    ax.set_ylabel("background_polish 실행 step 수 (aria301_12F)")
    ax.set_title("12F: keyframe이 촘촘해질수록 polish가 돌 idle 시간이 사라진다", fontsize=12.5)
    ax.grid(axis="y", color=GRID, alpha=0.4)
    fig.savefig(IMG / "fig_polish_collapse.png", facecolor=BG)
    plt.close(fig)


# ── fig_instrumentation ──────────────────────────────────────────
def fig_instrumentation():
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    have = [
        ("motion_filter", "vigs.py:699"),
        ("frontend (BA)", "vigs.py:702"),
        ("pgba_run / pgba_call_gs", "vigs.py:720,732"),
        ("map() 섹션별 (iters/n_view/n_gauss 포함)", "gs_backend.py:3908"),
    ]
    missing = [
        ("background_polish_step 전체", "gs_backend.py:1216-2121 — 계측 0건"),
    ]

    ax.text(0.2, 5.65, "VIGS_TIMING_LOG로 이미 커버됨 (이번 세션 내내 미사용)", color=GREEN,
             fontsize=13.5, fontweight="bold")
    y = 5.0
    for name, loc in have:
        r = FancyBboxPatch((0.2, y - 0.32), 9.4, 0.55, boxstyle="round,pad=0.02,rounding_size=0.06",
                            linewidth=1.2, edgecolor=GREEN, facecolor=PANEL)
        ax.add_patch(r)
        ax.text(0.45, y - 0.045, name, color=TEXT, fontsize=12, va="center")
        ax.text(9.35, y - 0.045, loc, color=MUTED, fontsize=9.5, va="center", ha="right")
        y -= 0.72

    ax.text(0.2, y - 0.15, "빠져있음 — 새로 계측 필요", color=CORAL, fontsize=13.5, fontweight="bold")
    y -= 0.75
    for name, loc in missing:
        r = FancyBboxPatch((0.2, y - 0.32), 9.4, 0.55, boxstyle="round,pad=0.02,rounding_size=0.06",
                            linewidth=1.4, edgecolor=CORAL, facecolor=PANEL)
        ax.add_patch(r)
        ax.text(0.45, y - 0.045, name, color=TEXT, fontsize=12, va="center")
        ax.text(9.35, y - 0.045, loc, color=MUTED, fontsize=9.5, va="center", ha="right")
        y -= 0.72

    fig.savefig(IMG / "fig_instrumentation.png", facecolor=BG)
    plt.close(fig)


# ── fig_tradeoff_concept ─────────────────────────────────────────
def fig_tradeoff_concept():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.0))
    fig.patch.set_facecolor(BG)
    titles = ["aria301_305 (원래 커버리지 부족)", "aria301_12F (원래 커버리지 충분)"]
    gains = [7.0, 0.0]
    losses = [-0.3, -4.8]
    for ax, title, gain, loss in zip(axes, titles, gains, losses):
        ax.set_facecolor(BG)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.tick_params(colors=MUTED)
        bars = ax.bar(["커버리지\n개선 이득", "polish 굶주림\n손해"], [gain, loss],
                       color=[GREEN, CORAL], width=0.5)
        net = gain + loss
        ax.axhline(0, color=GRID, lw=1)
        for b, v in zip(bars, [gain, loss]):
            ax.text(b.get_x() + b.get_width() / 2, v + (0.3 if v >= 0 else -0.5), f"{v:+.1f}dB",
                     ha="center", color=TEXT, fontsize=12, fontweight="bold")
        ax.set_title(f"{title}\n순효과 {net:+.1f}dB", color=TEXT, fontsize=11.5)
        ax.set_ylim(-6, 8)
        ax.grid(axis="y", color=GRID, alpha=0.3)
    fig.suptitle("같은 다이얼(keyframe 밀도↑)의 순효과 = 장면이 원래 얼마나 커버돼 있었는지에 따라 반대",
                  color=TEXT, fontsize=12.5, y=1.02)
    fig.savefig(IMG / "fig_tradeoff_concept.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_next_steps ───────────────────────────────────────────────
def fig_next_steps():
    fig, ax = plt.subplots(figsize=(11, 4.6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3)
    ax.axis("off")
    steps = [
        ("1", "기존 로그 켜기", "VIGS_TIMING_LOG 추가\n코드 변경 0", BLUE),
        ("2", "polish 계측 추가", "_Sect 패턴 이식\ngs_backend.py 한 곳", CORAL),
        ("3", "타임라인 재구성", "언제 GPU를 누가\n썼는지 스크립트 병합", PURPLE),
        ("4", "파라미터 스윕", "시간=a+b×iters1\n같은 함수형 확정", BUDGET),
    ]
    w = 2.5
    for i, (num, title, sub, color) in enumerate(steps):
        x = 0.2 + i * 2.65
        r = FancyBboxPatch((x, 0.9), w, 1.5, boxstyle="round,pad=0.03,rounding_size=0.1",
                            linewidth=1.6, edgecolor=color, facecolor=PANEL)
        ax.add_patch(r)
        circ = Circle((x + 0.35, 2.05), 0.22, facecolor=color, edgecolor="none")
        ax.add_patch(circ)
        ax.text(x + 0.35, 2.05, num, color=BG, fontsize=13, fontweight="bold", ha="center", va="center")
        ax.text(x + w / 2, 1.6, title, color=TEXT, fontsize=12.5, fontweight="bold", ha="center")
        ax.text(x + w / 2, 1.12, sub, color=MUTED, fontsize=9, ha="center", va="center",
                 linespacing=1.5)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + w, 1.65), (x + w + 0.15, 1.65), color=MUTED,
                                           arrowstyle="-|>", mutation_scale=15))
    fig.savefig(IMG / "fig_next_steps.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_frontend_scaling (실측 결과) ──────────────────────────────
def fig_frontend_scaling():
    fig, ax = _ax((9.5, 5.6))
    labels = ["12F pre-A2\n(thresh3.6/iters1=1)", "12F A2\n(thresh2.6/iters1=2)",
              "305 A2\n(thresh2.6/iters1=2)"]
    totals = [41.49, 88.92, 45.43]
    pcts = [63.6, 73.4, 64.0]
    colors = [GREEN, CORAL, GREEN]
    bars = ax.bar(labels, totals, width=0.5, color=colors)
    for b, v, p in zip(bars, totals, pcts):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}s\n({p:.0f}%)",
                 ha="center", color=TEXT, fontsize=12.5, fontweight="bold")
    ax.set_ylabel("frontend(트래킹 BA) 누적 wall time (s)")
    ax.set_title("실측: 같은 A2 설정이라도 12F가 305보다 frontend 비용이 2배 — 씬 자체가 keyframe을 더 뽑는다",
                  fontsize=12)
    ax.set_ylim(0, 105)
    ax.grid(axis="y", color=GRID, alpha=0.4)
    fig.savefig(IMG / "fig_frontend_scaling.png", facecolor=BG)
    plt.close(fig)


# ── fig_polish_opportunity (실측 결과) ────────────────────────────
def fig_polish_opportunity():
    fig, ax = _ax((9.5, 5.6))
    labels = ["12F pre-A2", "12F A2", "305 A2"]
    calls = [5683, 822, 9866]
    per_call = [4.66, 6.37, 3.86]
    colors = [GREEN, CORAL, GREEN]
    bars = ax.bar(labels, calls, width=0.5, color=colors)
    for b, v, pc in zip(bars, calls, per_call):
        ax.text(b.get_x() + b.get_width() / 2, v + 250, f"{v:,}회\n({pc:.2f}ms/call)",
                 ha="center", color=TEXT, fontsize=12.5, fontweight="bold")
    ax.set_ylabel("background_polish_step 실행 횟수")
    ax.set_title("실측: call당 비용은 3.9~6.4ms로 거의 고정 — 차이는 전부 \"기회 횟수\"에서 옴 (13배 차이)",
                  fontsize=12)
    ax.set_ylim(0, 12000)
    ax.grid(axis="y", color=GRID, alpha=0.4)
    fig.savefig(IMG / "fig_polish_opportunity.png", facecolor=BG)
    plt.close(fig)


# ── fig_map_breakdown (실측 결과) ─────────────────────────────────
def fig_map_breakdown():
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.0))
    fig.patch.set_facecolor(BG)
    sections = ["loss_compute", "backward", "rasterize", "optimizer_step", "densify_prune"]
    colors5 = [CORAL, BLUE, GREEN, BUDGET, PURPLE]
    data = {
        "12F A2": [37.87, 30.28, 5.40, 1.55, 0.15],
        "305 A2": [18.57, 18.68, 3.12, 0.82, 0.12],
    }
    for ax, (title, vals) in zip(axes, data.items()):
        ax.set_facecolor(BG)
        total = sum(vals)
        pcts = [v / total * 100 for v in vals]
        wedges, _ = ax.pie(vals, colors=colors5, startangle=90,
                             wedgeprops=dict(edgecolor=BG, linewidth=2))
        ax.set_title(f"{title}\nmap() 내부 {total:.1f}s", color=TEXT, fontsize=12.5)
        for w, sec, pct in zip(wedges, sections, pcts):
            if pct < 3:
                continue
            ang = (w.theta1 + w.theta2) / 2
            import numpy as _np
            x, y = _np.cos(_np.radians(ang)) * 0.7, _np.sin(_np.radians(ang)) * 0.7
            ax.text(x, y, f"{sec}\n{pct:.0f}%", ha="center", va="center", color=BG,
                     fontsize=9, fontweight="bold")
    fig.suptitle("map() 콜 내부 구성 — 두 씬 모두 loss_compute+backward가 ~90%, rasterize는 ~7%뿐",
                  color=TEXT, fontsize=12.5, y=1.03)
    fig.savefig(IMG / "fig_map_breakdown.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_scale_sweep (실측 결과, 신규) ─────────────────────────────
def fig_scale_sweep():
    fig, ax1 = plt.subplots(figsize=(10, 5.8))
    fig.patch.set_facecolor(BG)
    ax1.set_facecolor(BG)
    for spine in ax1.spines.values():
        spine.set_color(GRID)
    ax1.tick_params(colors=MUTED)

    scales = [1.5, 2.0, 3.0]
    polish = [806, 5681, 10000]
    psnr = [23.84, 28.10, 25.97]

    x = range(len(scales))
    bars = ax1.bar(x, polish, width=0.45, color=BLUE, alpha=0.85, label="polish 실행 횟수")
    ax1.set_ylabel("background_polish 실행 횟수", color=BLUE)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([f"scale={s}" for s in scales], color=TEXT, fontsize=12)
    for b, v in zip(bars, polish):
        cap_note = " (캡)" if v == 10000 else ""
        ax1.text(b.get_x() + b.get_width() / 2, v + 200, f"{v:,}{cap_note}",
                  ha="center", color=BLUE, fontsize=11, fontweight="bold")

    ax2 = ax1.twinx()
    ax2.plot(x, psnr, color=BUDGET, marker="o", markersize=10, linewidth=2.5, label="PSNR")
    ax2.set_ylabel("Fixed held-out PSNR (dB)", color=BUDGET)
    ax2.tick_params(colors=MUTED)
    for spine in ax2.spines.values():
        spine.set_visible(False)
    ax2.set_ylim(20, 32)
    for xi, v in zip(x, psnr):
        ax2.text(xi, v + 0.7, f"{v:.2f}dB", ha="center", color=BUDGET, fontsize=12, fontweight="bold")

    ax1.set_title("실측: scale 1.5→2.0에서 회귀 대부분 회복, 그러나 3.0에서 다시 하락(역-U자형)",
                   color=TEXT, fontsize=12.5)
    fig.savefig(IMG / "fig_scale_sweep.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_gap_quantization (실측 결과, 신규) ────────────────────────
def fig_gap_quantization():
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    ax.text(0.2, 5.1, "keyframe 디스패치 사이 gap 구조 (실측, scale=1.5)", color=TEXT,
             fontsize=14, fontweight="bold")

    # timeline
    y0 = 3.6
    segs = [
        (0.2, 1.3, CORAL, "map()\n처리중"),
        (1.3, 1.9, PANEL, ""),
        (1.9, 3.0, CORAL, "map()\n처리중"),
        (3.0, 3.2, PANEL, ""),
        (3.2, 4.4, CORAL, "map()\n처리중"),
        (4.4, 7.6, PANEL, ""),
        (7.6, 7.9, CORAL, ""),
        (7.9, 10.3, PANEL, ""),
    ]
    for x0, x1, color, label in segs:
        r = FancyBboxPatch((x0, y0), x1 - x0, 0.9, boxstyle="round,pad=0.01,rounding_size=0.03",
                            linewidth=1.2, edgecolor=(color if color != PANEL else GRID),
                            facecolor=(color if color != PANEL else PANEL))
        ax.add_patch(r)
        if label:
            ax.text((x0 + x1) / 2, y0 + 0.45, label, ha="center", va="center", color=BG,
                     fontsize=8.5, fontweight="bold")

    # mark polish ticks in the two longest gaps
    for x0, x1, n in [(4.4, 7.6, 6), (7.9, 10.3, 4)]:
        step = (x1 - x0) / (n + 1)
        for k in range(1, n + 1):
            xt = x0 + step * k
            ax.plot([xt, xt], [y0 + 0.05, y0 + 0.85], color=GREEN, linewidth=2, alpha=0.85)
    # short gap: no room
    ax.text((1.3 + 1.9) / 2, y0 - 0.35, "너무 짧음\n(0개)", ha="center", va="top", color=CORAL,
             fontsize=8.5)
    ax.text((3.0 + 3.2) / 2, y0 - 0.35, "0개", ha="center", va="top", color=CORAL, fontsize=8.5)
    ax.text((4.4 + 7.6) / 2, y0 - 0.35, "6개 낌", ha="center", va="top", color=GREEN, fontsize=9,
             fontweight="bold")
    ax.text((7.9 + 10.3) / 2, y0 - 0.35, "4개 낌", ha="center", va="top", color=GREEN, fontsize=9,
             fontweight="bold")
    ax.plot([0.2, 0.2], [y0 - 0.1, y0 + 1.0], color=MUTED, linewidth=1, linestyle=":")

    ax.text(0.2, 2.0,
             "총 polish 횟수 = Σ floor(gap 길이 / step비용 4~6ms)\n"
             "→ 정수 나눗셈의 합이라 본질적으로 \"계단식(양자화)\"",
             color=TEXT, fontsize=12.5, va="top", linespacing=1.6)

    ax.text(0.2, 0.9,
             "실측: gap의 43~57%는 step 1개(4~6ms)도 못 낄 만큼 짧음(zero-polish gap).\n"
             "총량은 소수의 긴 gap(최대 526→1582→2478ms, scale 1.5→2.0→3.0)이 지배.",
             color=MUTED, fontsize=11, va="top", linespacing=1.5)

    fig.savefig(IMG / "fig_gap_quantization.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_thread_arch()
    fig_a2_scene_flip()
    fig_polish_collapse()
    fig_instrumentation()
    fig_tradeoff_concept()
    fig_next_steps()
    fig_frontend_scaling()
    fig_polish_opportunity()
    fig_map_breakdown()
    fig_scale_sweep()
    fig_gap_quantization()
    print("done ->", IMG)
