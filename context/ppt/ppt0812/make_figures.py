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
    fig, ax = plt.subplots(figsize=(13.2, 8.6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 8.6)
    ax.axis("off")

    def box(x, y, w, h, text, color, fontsize=12.5, sub=None):
        r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.4, edgecolor=color, facecolor=PANEL)
        ax.add_patch(r)
        ax.text(x + w / 2, y + h / 2 + (0.16 if sub else 0), text, ha="center", va="center",
                 color=TEXT, fontsize=fontsize, fontweight="bold")
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.22, sub, ha="center", va="center",
                     color=MUTED, fontsize=8.8)

    # ── 실제로는 스레드가 3개다 (이전 버전 그림엔 loop-closure 스레드가 통째로 빠져있었음) ──
    # Row A: tracking thread (동기, 메인)
    ax.text(0.15, 8.3, "TRACKING 스레드 (메인, 동기)", color=BLUE, fontsize=13, fontweight="bold")
    box(0.2, 7.25, 2.0, 0.75, "motion_filter", BLUE)
    box(2.5, 7.25, 2.35, 0.75, "frontend BA", BLUE, sub="for itr in range(iters1): 시간체크 없음")
    box(5.15, 7.25, 2.1, 0.75, "PGBA", BLUE, sub="매 프레임 큐 확인(~1ms) 뿐")
    for x0, x1 in [(2.2, 2.5), (4.85, 5.15)]:
        ax.add_patch(FancyArrowPatch((x0, 7.625), (x1, 7.625), color=MUTED,
                                       arrowstyle="-|>", mutation_scale=14))
    ax.text(9.7, 8.15, "실선 화살표 = 순차 실행\n(A 끝나야 B 시작)", color=MUTED, fontsize=9.5,
             ha="left", va="top", style="italic")
    ax.text(9.7, 7.35, "tracking엔 시간예산 캡\n없음(iters1 루프에 타임체크 X)", color=BLUE,
             fontsize=9.5, ha="left", va="top")

    # Row B: loop-closure 검출 스레드 (제3의 스레드 — 이전 버전 그림에서 통째로 누락됐던 부분)
    ax.text(0.15, 6.75, "LOOP CLOSURE 검출 스레드 (별도, 0.1s 폴링)", color=GREEN, fontsize=12,
             fontweight="bold")
    box(0.2, 5.55, 4.4, 0.75, "pgobuf.spin()", GREEN,
        sub="keyframe≥60부터 후보 탐색 · 24쌍 모이면(or 타임아웃) 큐잉")
    ax.add_patch(FancyArrowPatch((4.5, 6.15), (5.5, 7.25), color=GREEN, arrowstyle="-|>",
                                   mutation_scale=14, connectionstyle="arc3,rad=-0.25"))
    ax.text(5.75, 6.55, "후보가 큐에 있을 때만\n다음 프레임에서 소비", color=GREEN, fontsize=9.5,
             ha="left", va="center")
    ax.text(0.35, 5.15,
             "(이전 버전 그림엔 이 스레드 자체가 없어서, PGBA가 매 프레임 실제 BA를\n"
             "도는 것처럼 보였음 — 실제 무거운 계산은 이 스레드가 후보를 큐잉할 때만)",
             color=MUTED, fontsize=9, ha="left", va="top", style="italic", linespacing=1.4)

    # Row C: gs_worker thread lane
    ax.text(0.15, 4.15, "GS_WORKER 스레드 (별도, 큐 기반)", color=CORAL, fontsize=13, fontweight="bold")
    box(0.2, 3.05, 2.7, 0.75, "map()", CORAL, sub="키프레임 도착시 디스패치")
    box(3.2, 3.05, 3.4, 0.75, "background_polish_step", CORAL,
        sub="자기 큐 빌 때만(idle-gated)·PGBA 무관")
    ax.text(9.7, 3.4, "tracking이 바빠질수록\n→ polish 기회 감소", color=CORAL, fontsize=10.5,
             ha="left", va="center")

    # ── GPU 락 상호배제 (방향 화살표 아님 — PGBA <-> background_polish_step 만 해당) ──
    lock_x, lock_y, lock_w, lock_h = 9.6, 4.75, 3.0, 0.95
    r = FancyBboxPatch((lock_x, lock_y), lock_w, lock_h, boxstyle="round,pad=0.02,rounding_size=0.1",
                        linewidth=1.6, edgecolor=BUDGET, facecolor=PANEL, linestyle="--")
    ax.add_patch(r)
    ax.text(lock_x + lock_w / 2, lock_y + lock_h / 2 + 0.18, "LOCK  self.video.get_lock()",
             ha="center", va="center", color=BUDGET, fontsize=11.5, fontweight="bold")
    ax.text(lock_x + lock_w / 2, lock_y + lock_h / 2 - 0.22, "둘 중 하나만 동시 보유 → 직렬화",
             ha="center", va="center", color=MUTED, fontsize=9)
    # 연결선(화살촉 없이 점선+원형 마커) — "먼저 온 쪽이 이긴다"는 상호배제 관계이지 호출 순서가 아님
    for (px, py) in [(7.25, 7.25), (6.6, 3.8)]:
        ax.plot([px, lock_x], [py, lock_y + lock_h / 2], color=BUDGET, linestyle=":",
                 linewidth=1.6, alpha=0.85, zorder=1)
        ax.add_patch(Circle((px, py), 0.045, color=BUDGET, zorder=2))
    ax.add_patch(Circle((lock_x, lock_y + lock_h / 2), 0.05, color=BUDGET, zorder=2))
    ax.text(lock_x + lock_w / 2, lock_y - 0.18,
             "exp60에서 background_polish_step에만 추가된 락 —\nmap()은 이 락을 쓰지 않음(_gaussian_lock만 사용)",
             ha="center", va="top", color=MUTED, fontsize=8.6, linespacing=1.35)

    # shared GPU (물리 자원 — map()도 여기엔 연결되지만 위 lock과는 별개 개념)
    box(2.0, 0.9, 5.5, 1.0, "공유 RTX GPU (물리 자원)", BUDGET, fontsize=12.5)
    for x in [1.55, 4.9]:
        ax.add_patch(FancyArrowPatch((x, 3.0), (x, 1.95), color=BUDGET,
                                       arrowstyle="-|>", mutation_scale=13, linestyle="--", alpha=0.85))

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


# ── fig_frame_cycle (신규, 실측 기반) ─────────────────────────────
def fig_frame_cycle():
    fig, ax = plt.subplots(figsize=(13.5, 9.4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 9.4)
    ax.axis("off")

    ax.text(0.2, 9.1, "프레임 1개 처리 주기 — 코드 레벨 이벤트 (unit=10ms, scale=2.0 실측 기준)",
             color=TEXT, fontsize=14, fontweight="bold")

    # ── Row A: TRACKING 스레드, to-scale (busy 53.3ms / idle 46.7ms / period 100ms) ──
    ax.text(0.2, 8.55, "TRACKING 스레드", color=BLUE, fontsize=12.5, fontweight="bold")
    y0 = 7.7
    x0 = 0.6
    busy_w, idle_w = 5.33, 4.67
    ax.broken_barh([(x0, busy_w)], (y0, 0.75), facecolors=BLUE, edgecolors=BLUE)
    ax.broken_barh([(x0 + busy_w, idle_w)], (y0, 0.75), facecolors=PANEL,
                     edgecolors=MUTED, hatch="///", linewidth=1.2)
    ax.text(x0 + busy_w / 2, y0 + 0.375, "motion_filter+frontend BA+PGBA체크\n(~53ms 실측)",
             ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
    ax.text(x0 + busy_w + idle_w / 2, y0 + 0.375, "다음 frame 예정시각까지 대기\n(~47ms, pacing wait)",
             ha="center", va="center", color=MUTED, fontsize=9.5)

    for x, label, color in [
        (x0, "track(t) 시작\n_tracking_active.set()", BLUE),
        (x0 + busy_w, "_track_impl 끝\n_tracking_active.clear()\n_tracking_idle_since=now", GREEN),
        (x0 + busy_w + idle_w, "다음 frame 예정시각\n(=50ms×replay_time_scale)", MUTED),
    ]:
        ax.plot([x, x], [y0 - 0.05, y0 + 0.85], color=color, linewidth=1.2, linestyle=":")
        ax.text(x, y0 - 0.15, label, ha="center", va="top", color=color, fontsize=8.6, linespacing=1.3)

    # ── Row B: GS_WORKER 폴링 (idle 구간에만 존재) ──
    ax.text(0.2, 6.05, "GS_WORKER 스레드 (poll, 0.2~2ms 주기)", color=CORAL, fontsize=12.5,
             fontweight="bold")
    y1 = 5.15
    poll_x = x0 + busy_w
    step_w = 0.49  # ~4.9ms
    n_steps = int(idle_w // step_w)
    for i in range(n_steps):
        xs = poll_x + i * step_w
        ax.broken_barh([(xs, step_w * 0.86)], (y1, 0.6), facecolors=CORAL, edgecolors=CORAL, alpha=0.9)
    ax.text(poll_x + idle_w / 2, y1 - 0.35,
             f"idle 47ms 안에 background_polish_step(~4.9ms) {n_steps}회 낌",
             ha="center", va="top", color=CORAL, fontsize=9.5)
    ax.text(11.7, y1 + 0.85,
             "매 poll마다 4개 조건 AND 확인:\n① self._background_polish\n"
             "② idle_long_enough (tracking 지금 idle?)\n③ under_budget (max_steps 안 넘음?)\n"
             "④ map_mature_enough (frame≥polish 시작점?)\n→ 전부 True일 때만 1회 실행 후 즉시 재확인",
             color=MUTED, fontsize=9, ha="left", va="top", linespacing=1.5)

    # ── Row C: scale별 busy/idle 비율 비교 (상대폭, 실측) ──
    ax.text(0.2, 3.85, "scale이 커지면 idle 구간(=폴리시 슬롯)이 늘어난다 (실측, 상대폭 75:100:150ms)",
             color=TEXT, fontsize=12, fontweight="bold")
    rows = [
        ("scale=1.5", 75, 52.8, 22.2, 4.5, "23.84dB · polish 806회"),
        ("scale=2.0", 100, 53.3, 46.7, 6.0, "28.10dB · polish 5,681회"),
        ("scale=3.0", 150, 49.1, 100.9, 9.0, "25.97dB · polish 10,000회(캡)"),
    ]
    ry = 3.1
    for label, total_ms, busy_ms, idle_ms, w, tail in rows:
        bw = w * busy_ms / total_ms
        iw = w * idle_ms / total_ms
        ax.broken_barh([(0.6, bw)], (ry, 0.5), facecolors=BLUE, edgecolors=BLUE)
        ax.broken_barh([(0.6 + bw, iw)], (ry, 0.5), facecolors=PANEL, edgecolors=MUTED,
                         hatch="///", linewidth=1.0)
        ax.text(0.6 + bw + iw + 0.25, ry + 0.25,
                 f"{label}: busy {busy_ms:.0f}ms / idle {idle_ms:.0f}ms  —  {tail}",
                 ha="left", va="center", color=TEXT, fontsize=10)
        ry -= 0.75

    ax.text(0.2, 0.7,
             "실제 총 횟수는 위 \"프레임당 슬롯\" 추정보다 훨씬 적다 — ① map() 실행 중엔 이 poll 루프 자체가 "
             "안 돎(같은 스레드) ② background_polish_start_frame 이전(전체 프레임의 53.7%)엔 애초에 "
             "비활성(map_mature_enough=False) — 다음 그림(매크로 타임라인)에서 설명",
             color=MUTED, fontsize=10, va="top", linespacing=1.4)

    fig.savefig(IMG / "fig_frame_cycle.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_macro_timeline (신규, 실측 기반) ──────────────────────────
def fig_macro_timeline():
    fig, ax = plt.subplots(figsize=(18.2, 8.4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 18.2)
    ax.set_ylim(0, 8.4)
    ax.axis("off")

    ax.text(0.2, 8.1, "매크로 타임라인 — map()이 주기적으로 폴리시 기회를 통째로 삼킨다 (스케마틱, 실측 비율 반영)",
             color=TEXT, fontsize=13.5, fontweight="bold")

    # TRACKING 스레드: 끊임없이 프레임 틱 (map()과 무관하게 계속 돔)
    ax.text(0.2, 7.4, "TRACKING 스레드 — map()과 무관하게 계속 프레임 처리", color=BLUE, fontsize=11.5,
             fontweight="bold")
    ty = 6.75
    x = 0.5
    tick_w = 0.42
    kf_positions = []
    for i in range(38):
        is_kf = (i % 7 == 6)
        ax.broken_barh([(x, tick_w * 0.62)], (ty, 0.5), facecolors=BLUE, edgecolors=BLUE)
        ax.broken_barh([(x + tick_w * 0.62, tick_w * 0.38)], (ty, 0.5), facecolors=PANEL,
                         edgecolors=MUTED, linewidth=0.6)
        if is_kf:
            kf_positions.append(x + tick_w / 2)
            ax.plot(x + tick_w / 2, ty + 0.75, marker="v", color=GREEN, markersize=9)
        x += tick_w
    ax.text(x + 0.3, ty + 0.25, "... (평균 6.6프레임마다 keyframe 1개)", color=MUTED, fontsize=9.5,
             va="center")

    # GS_WORKER 스레드: idle-poll 티크 구간 + map() 블록 번갈아
    ax.text(0.2, 5.65, "GS_WORKER 스레드 — idle-poll 틱 구간 ↔ map() 블록이 번갈아 나온다", color=CORAL,
             fontsize=11.5, fontweight="bold")
    ax.text(0.2, 5.2,
             "map() 실행 중엔 같은 스레드의 poll 루프가 통째로 정지 — idle-poll 구간 폭은 직전 gap의 "
             "실제 idle 시간에 따라 매번 달라짐(실측)",
             color=MUTED, fontsize=9.3, va="top")
    gy = 4.0
    gx = 0.5
    segs = [("poll", 1.7), ("map", 3.3), ("poll", 1.1), ("map", 3.3), ("poll", 2.2), ("map", 3.3),
            ("poll", 1.4)]
    map_starts = []
    for kind, w in segs:
        if kind == "poll":
            n_ticks = max(1, int(w / 0.42))
            for i in range(n_ticks):
                ax.broken_barh([(gx + i * 0.42, 0.32)], (gy, 0.55), facecolors=CORAL, alpha=0.85,
                                 edgecolors=CORAL)
        else:
            map_starts.append(gx)
            r = FancyBboxPatch((gx, gy - 0.05), w, 0.65, boxstyle="round,pad=0.01,rounding_size=0.05",
                                 linewidth=1.6, edgecolor=BUDGET, facecolor=PANEL)
            ax.add_patch(r)
            ax.text(gx + w / 2, gy + 0.275, "map()\n(~270~305ms)", ha="center", va="center",
                     color=BUDGET, fontsize=9, fontweight="bold")
        gx += w
    # keyframe -> map() 트리거 연결선 (대표 1개만)
    if kf_positions and map_starts:
        kfx = kf_positions[2]
        mstart = map_starts[1]
        ax.add_patch(FancyArrowPatch((kfx, ty), (mstart + 0.1, gy + 0.65), color=GREEN,
                                       arrowstyle="-|>", mutation_scale=13,
                                       connectionstyle="arc3,rad=0.15", linestyle="--"))
        ax.text((kfx + mstart) / 2 + 0.3, (ty + gy) / 2 + 0.3,
                 "motion_filter가 이 프레임을\nkeyframe으로 선택\n→ _gs_queue.put()",
                 color=GREEN, fontsize=9, ha="left", va="center", linespacing=1.3)

    # 하단: map() 총 점유 비율 (실측) + GPU 오버랩 실측
    py = 2.2
    stats = [
        ("scale=1.5", "map() 점유 57.5%\n(89.65s / 155.99s)"),
        ("scale=2.0", "map() 점유 49.5%\n(102.15s / 206.44s)"),
        ("scale=3.0", "map() 점유 30.9%\n(94.85s / 306.55s)"),
    ]
    sx = 0.6
    for label, txt in stats:
        card = FancyBboxPatch((sx, py), 3.5, 1.05, boxstyle="round,pad=0.02,rounding_size=0.08",
                                linewidth=1.3, edgecolor=BUDGET, facecolor=PANEL)
        ax.add_patch(card)
        ax.text(sx + 1.75, py + 0.75, label, ha="center", color=TEXT, fontsize=10.5, fontweight="bold")
        ax.text(sx + 1.75, py + 0.32, txt, ha="center", va="center", color=MUTED, fontsize=9.3,
                 linespacing=1.3)
        sx += 3.85

    ax.text(0.2, 1.35,
             "scale을 키우면 (1) 프레임당 idle 시간이 늘고 (2) map() 총 점유 비율도 같이 줄어든다 — "
             "두 효과가 겹쳐 idle-poll 구간이 넓어지는 게 polish 급증(806→5,681)의 실제 원인.",
             color=TEXT, fontsize=10.5, va="top", linespacing=1.35)
    ax.text(0.2, 0.75,
             "GPU 실행 자체는 이 CPU 스레드 경계와 정확히 안 맞는다 — 실측: 세 스레드 총 busy 시간 합이 "
             "실제 벽시계 구간의 81~135%(scale별) → 부분적으로 겹쳐 실행됨(완전 직렬 아님, 공유 legacy "
             "default stream이라도).",
             color=MUTED, fontsize=9.5, va="top", linespacing=1.35)

    fig.savefig(IMG / "fig_macro_timeline.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_freeze_spectrum (신규, 실측 기반) ─────────────────────────
def fig_freeze_spectrum():
    fig, ax1 = plt.subplots(figsize=(10.5, 6.2))
    fig.patch.set_facecolor(BG)
    ax1.set_facecolor(BG)
    for spine in ax1.spines.values():
        spine.set_color(GRID)
    ax1.tick_params(colors=MUTED)

    labels = ["즉시 freeze\n(frame 700)", "never freeze\n(끝까지 안 함)", "A2 채택 지점\n(61% 지점)"]
    vals_305 = [19.35, 24.896, 29.815]
    colors = [CORAL, BUDGET, GREEN]
    x = range(3)
    bars = ax1.bar(x, vals_305, width=0.5, color=colors, alpha=0.9)
    for b, v in zip(bars, vals_305):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.9, f"{v:.2f}dB", ha="center",
                  color=TEXT, fontsize=13, fontweight="bold")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, color=TEXT, fontsize=11.5)
    ax1.set_ylabel("aria301_305 Fixed held-out PSNR (dB)")
    ax1.set_ylim(0, 40)
    ax1.axhline(29.815, color=GREEN, linestyle=":", linewidth=1, alpha=0.6)
    ax1.set_title("freeze 시점 스펙트럼 3지점(305) — 두 극단 모두 A2 채택 지점보다 나쁘다",
                   fontsize=12.5, color=TEXT)

    # OOM 배지 (12F, never-freeze 지점 전용)
    oom_x = 1
    ax1.annotate("12F는 이 지점에서\nCUDA OOM (14.11GiB)",
                  xy=(oom_x + 0.22, vals_305[oom_x] + 0.5), xytext=(oom_x + 0.62, 20.5),
                  color=CORAL, fontsize=10.5, ha="center",
                  arrowprops=dict(arrowstyle="-|>", color=CORAL, lw=1.6))
    ax1.text(0, 24.5, "12F는 완주\n(24.996dB)", ha="center", color=MUTED, fontsize=9.5)
    ax1.text(2, 34.7, "12F는 완주,\nOOM 없음(7.97GiB)", ha="center", color=MUTED, fontsize=9.5)

    fig.savefig(IMG / "fig_freeze_spectrum.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── fig_freeze_mechanism (신규) ────────────────────────────────────
def fig_freeze_mechanism():
    fig, ax = plt.subplots(figsize=(13, 6.6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.6)
    ax.axis("off")

    ax.text(0.2, 6.3, "\"freeze\"가 실제로 하는 일 — map()의 유일한 학습-비용 상한선",
             color=TEXT, fontsize=14, fontweight="bold")

    def box(x, y, w, h, text, color, sub=None, fontsize=11.5):
        r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                             linewidth=1.5, edgecolor=color, facecolor=PANEL)
        ax.add_patch(r)
        ax.text(x + w / 2, y + h / 2 + (0.18 if sub else 0), text, ha="center", va="center",
                 color=TEXT, fontsize=fontsize, fontweight="bold", linespacing=1.3)
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.28, sub, ha="center", va="center",
                     color=MUTED, fontsize=9.5, linespacing=1.3)

    # Row: freeze 없음 (위)
    ax.text(0.2, 5.55, "freeze 없음 (축 C)", color=CORAL, fontsize=12, fontweight="bold")
    box(0.3, 4.35, 3.6, 1.0, "map()이 매 keyframe마다\nrasterizer forward+backward",
        CORAL, sub="시퀀스 끝까지(2201프레임) 계속")
    ax.add_patch(FancyArrowPatch((3.9, 4.85), (5.4, 4.85), color=CORAL, arrowstyle="-|>", mutation_scale=15))
    box(5.5, 4.35, 3.4, 1.0, "가우시안 수 계속 증가\n+ 순간 최대메모리 계속 증가", CORAL)
    ax.add_patch(FancyArrowPatch((9.0, 4.85), (10.5, 4.85), color=CORAL, arrowstyle="-|>", mutation_scale=15))
    box(10.6, 4.35, 2.15, 1.0, "reserved 하이워터마크\n15.46GiB 초과", CORAL, fontsize=10.5)
    ax.text(12.68, 4.85, "→ OOM", color=CORAL, fontsize=13, fontweight="bold", ha="left", va="center")

    # Row: freeze 있음 (아래, A2)
    ax.text(0.2, 3.35, "freeze 있음 — A2 채택 지점 (61%)", color=GREEN, fontsize=12, fontweight="bold")
    box(0.3, 2.15, 3.6, 1.0, "map()이 61% 지점에서\n완전히 멈춤", GREEN,
        sub="같은 가우시안 수(~127k)에서도")
    ax.add_patch(FancyArrowPatch((3.9, 2.65), (5.4, 2.65), color=GREEN, arrowstyle="-|>", mutation_scale=15))
    box(5.5, 2.15, 3.4, 1.0, "메모리 성장 정지\n(rasterizer 호출 자체가 없음)", GREEN)
    ax.add_patch(FancyArrowPatch((9.0, 2.65), (10.5, 2.65), color=GREEN, arrowstyle="-|>", mutation_scale=15))
    box(10.6, 2.15, 2.15, 1.0, "7.97GiB에서\n안정", GREEN, fontsize=10.5)
    ax.text(12.68, 2.65, "→ 완주", color=GREEN, fontsize=13, fontweight="bold", ha="left", va="center")

    ax.text(0.2, 1.35,
             "핵심: 원인은 \"가우시안 개수 자체\"가 아니라 \"freeze 없이 이 무거운 호출이 시퀀스 끝까지\n"
             "반복된다\"는 것 — 같은 가우시안 수(~127k)에서도 freeze 유무에 따라 7.97GiB ↔ 15.46GiB+ 로 갈렸다(12F 실측).",
             color=TEXT, fontsize=11, va="top", linespacing=1.4)
    ax.text(0.2, 0.55,
             "부가 효과: freeze 이후엔 map()이 GPU를 안 쓰니 background_polish가 그 시간을 넘겨받는다 —\n"
             "즉 freeze 시점은 \"메모리 안전판\"이자 \"구조생성↔정제 예산 분배선\" 둘 다다.",
             color=MUTED, fontsize=10, va="top", linespacing=1.4)

    fig.savefig(IMG / "fig_freeze_mechanism.png", facecolor=BG, bbox_inches="tight")
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
    fig_frame_cycle()
    fig_macro_timeline()
    fig_freeze_spectrum()
    fig_freeze_mechanism()
    print("done ->", IMG)
