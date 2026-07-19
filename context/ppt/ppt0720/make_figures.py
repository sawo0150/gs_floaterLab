#!/usr/bin/env python3
"""make_figures.py (ppt0720) — exp52/exp53 실시간성 타임라인 시각자료.

2026-07-20 전면 갱신: "온라인 루프 총합"에 리더 프로세스의 인위적 20초 슬립이
섞여있던 타이밍 버그(reader.join()이 TRACK_LOOP_DONE_EPOCH보다 먼저 실행됨)를
발견·수정한 뒤 재검증한 수치로 전부 교체. 구 수치(180.10s/133.04s 등)는 폐기.

데이터 출처: exp52_timingfix_serial / exp52_timingfix_parallel 재검증 런
(context/experiments/exp52_vigs_slam_eval.md "⚠ 중대 정정" 절).

figure 목록:
  fig_timeline_serial     시나리오A: 순차 실행 누적 구성
  fig_timeline_parallel   시나리오B: gs_parallel 2-레인 타임라인
  fig_frontend_contention 직렬 vs 병렬 구성요소별 자체 비용 변화(경합 영향)
  fig_overlap_efficiency  오버랩 효율 88.3% 계산 막대
  fig_theoretical_floor   이론적 최선(완벽 병렬 가정) vs 예산선
  fig_components          4패널: frontend/gs_mapping/motion_filter/오버헤드 세부 분해
  fig_gsmapping_granular  GS Mapping 루프 세부 단계(process_track_data + map() 내부)

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

# ── 팔레트 (파랑=tracking, 코랄=mapping, 주황=예산선) ──
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

# 새로 추가하는 process_track_data 세부 항목용 컬러(초록/청록 계열, mapping 계열과 구분)
C_PTD1 = "#5fbf9e"
C_PTD2 = "#8fd6bc"
C_PTD3 = "#3f9e80"

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


# ═══ 정정된 실측치 (2026-07-20 재검증) ═══════════════════════════════
BUDGET_S = 65.1

# 순차 실행 (exp52_timingfix_serial, 총합 150.56s)
S_MOTION = 8.775
S_FRONTEND = 40.315
S_PGBA = 9.482
S_MAPPING = 85.768
S_OVERHEAD = 6.001  # queue_get_wait 4.348 + model_loading 1.510 + pbar/savetraj 0.143
S_TOTAL = 150.56

# gs_parallel (exp52_timingfix_parallel, 총합 98.94s)
P_FRONTEND = 63.457
P_MOTION = 13.493
P_PGBA = 10.638
P_MAPPING_ENQUEUE = 0.558
P_TRACK_TOTAL = 89.990
P_MAPPING_RAW = 76.223  # rasterize+loss_compute+backward+optimizer_step+densify_prune
P_OVERHEAD = 6.970
P_TOTAL = 98.94


# ── fig_timeline_serial ──────────────────────────────────────────────
def fig_timeline_serial():
    fig, ax = plt.subplots(figsize=(11, 2.6))
    fig.patch.set_facecolor(BG)
    segs = [
        ("motion_filter", S_MOTION, C_MOTION),
        ("frontend", S_FRONTEND, C_FRONTEND),
        ("PGBA", S_PGBA, C_PGBA),
        ("gs_mapping", S_MAPPING, C_BACKWARD),
        ("오버헤드", S_OVERHEAD, C_OVERHEAD),
    ]
    x = 0
    for name, w, c in segs:
        ax.barh(0, w, left=x, height=0.55, color=c, edgecolor=BG, linewidth=1.5)
        if w > 7:
            ax.text(x + w / 2, 0, f"{name}\n{w:.1f}s", ha="center", va="center",
                    fontsize=9.5, color="#0d0f14" if c in (C_MOTION, C_PGBA) else "white", fontweight="bold")
        x += w
    ax.axvline(BUDGET_S, color=C_BUDGET, linestyle="--", linewidth=2.2)
    ax.text(BUDGET_S, 0.42, f"예산 {BUDGET_S}s", color=C_BUDGET, fontsize=10.5, fontweight="bold", ha="left")
    ax.text(S_TOTAL, -0.42, f"총합 {S_TOTAL:.2f}s = 실시간의 {S_TOTAL/BUDGET_S:.2f}배", color=TEXT,
            fontsize=11, fontweight="bold", ha="right")
    ax.set_xlim(0, 165)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([])
    ax.set_xlabel("누적 시간 (초)")
    style_ax(ax)
    ax.set_title("시나리오 A · 순차 실행 (gs_parallel 없음) — 정정판", fontsize=13, fontweight="bold",
                  color=TEXT, loc="left")
    plt.savefig(IMG / "fig_timeline_serial.png", facecolor=BG)
    plt.close()


# ── fig_timeline_parallel ────────────────────────────────────────────
def fig_timeline_parallel():
    fig, ax = plt.subplots(figsize=(11, 3.3))
    fig.patch.set_facecolor(BG)

    track_segs = [
        ("frontend", P_FRONTEND, C_FRONTEND),
        ("motion_filter", P_MOTION, C_MOTION),
        ("PGBA", P_PGBA, C_PGBA),
    ]
    y_track = 1
    x = 0
    for name, v, c in track_segs:
        ax.barh(y_track, v, left=x, height=0.55, color=c, edgecolor=BG, linewidth=1.5)
        if v > 7:
            ax.text(x + v / 2, y_track, f"{name}\n{v:.1f}s", ha="center", va="center",
                    fontsize=9, color="white" if c != C_PGBA else "#0d0f14", fontweight="bold")
        x += v
    ax.text(-2, y_track, "Tracking\n스레드", ha="right", va="center", fontsize=10.5,
            color=TEXT, fontweight="bold")
    ax.text(x + 2, y_track, f"합 {x:.1f}s", ha="left", va="center", fontsize=9.5, color=MUTED)

    y_map = 0
    ax.barh(y_map, P_MAPPING_RAW, left=0, height=0.55, color=C_BACKWARD, edgecolor=BG, linewidth=1.5)
    ax.text(P_MAPPING_RAW / 2, y_map, f"gs_mapping (raw)\n{P_MAPPING_RAW:.1f}s", ha="center", va="center",
            fontsize=9.5, color="white", fontweight="bold")
    ax.text(-2, y_map, "GS Mapping\n스레드", ha="right", va="center", fontsize=10.5,
            color=TEXT, fontweight="bold")

    ax.axvline(BUDGET_S, color=C_BUDGET, linestyle="--", linewidth=2.2)
    ax.text(BUDGET_S, 1.62, f"예산 {BUDGET_S}s", color=C_BUDGET, fontsize=10.5, fontweight="bold", ha="left")
    ax.axvline(P_TOTAL, color=TEXT, linestyle=":", linewidth=1.5, alpha=0.6)
    ax.text(P_TOTAL, -0.78, f"실측 총합(wall-clock) {P_TOTAL:.2f}s — 두 스레드가 함께 끝남",
            color=TEXT, fontsize=9.5, ha="center", va="top")

    ax.set_xlim(-24, 118)
    ax.set_ylim(-1.05, 1.85)
    ax.set_yticks([])
    ax.set_xlabel("초 (Tracking 행은 구성요소별 합, Mapping 행은 raw 연산량 — 둘이 wall-clock상\n"
                  "동시에 겹쳐 돌면서 서로를 지연시켜 함께 수렴)")
    style_ax(ax)
    ax.set_title("시나리오 B · gs_parallel — Tracking 스레드 내부 구성 — 정정판", fontsize=13,
                  fontweight="bold", color=TEXT, loc="left")
    plt.savefig(IMG / "fig_timeline_parallel.png", facecolor=BG)
    plt.close()


# ── fig_frontend_contention ───────────────────────────────────────────
def fig_frontend_contention():
    fig, ax = plt.subplots(figsize=(11, 3.4))
    fig.patch.set_facecolor(BG)

    items = [
        ("frontend", S_FRONTEND, P_FRONTEND, C_FRONTEND),
        ("motion_filter", S_MOTION, P_MOTION, C_MOTION),
        ("PGBA", S_PGBA, P_PGBA, C_PGBA),
    ]
    bar_h = 0.32
    for i, (name, serial, parallel, c) in enumerate(items):
        y0 = (len(items) - 1 - i) * 1.1
        ax.barh(y0 + 0.22, serial, height=bar_h, color=GRID, edgecolor=BG, linewidth=1)
        ax.text(serial + 1.2, y0 + 0.22, f"{serial:.1f}s", va="center", fontsize=10, color=MUTED)
        ax.barh(y0 - 0.22, parallel, height=bar_h, color=c, edgecolor=BG, linewidth=1)
        ax.text(parallel + 1.2, y0 - 0.22, f"{parallel:.1f}s", va="center", fontsize=10,
                color=TEXT, fontweight="bold")
        pct = (parallel / serial - 1) * 100
        ax.text(max(serial, parallel) + 13, y0, f"+{pct:.0f}%", va="center", fontsize=12,
                color=c, fontweight="bold")
        ax.text(-2, y0, name, va="center", ha="right", fontsize=11.5, color=TEXT, fontweight="bold")

    ax.barh(-1.3, 0, color=GRID, label="직렬 실행")
    ax.barh(-1.3, 0, color=C_FRONTEND, label="gs_parallel")
    ax.legend(loc="lower right", frameon=False, labelcolor=TEXT, fontsize=10)

    ax.set_xlim(-14, 85)
    ax.set_ylim(-0.6, 2.7)
    ax.set_yticks([])
    ax.set_xlabel("초")
    style_ax(ax)
    ax.set_title("직렬 vs gs_parallel — 구성요소별 자체 비용 변화 (경합 영향) — 정정판", fontsize=13,
                  fontweight="bold", color=TEXT, loc="left")
    plt.savefig(IMG / "fig_frontend_contention.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_overlap_efficiency ───────────────────────────────────────────
def fig_overlap_efficiency():
    fig, ax = plt.subplots(figsize=(11, 3.2))
    fig.patch.set_facecolor(BG)

    tracking, mapping = P_TRACK_TOTAL, P_MAPPING_RAW
    naive_sum = tracking + mapping
    perfect = max(tracking, mapping)
    actual = P_TOTAL
    saved_actual = naive_sum - actual
    saved_max = naive_sum - perfect
    efficiency = saved_actual / saved_max

    bars = [
        ("순차 실행이라면", naive_sum, C_OVERHEAD),
        ("완벽한 병렬(경합 0)이라면", perfect, C_FLOOR),
        ("실측(gs_parallel)", actual, C_FRONTEND),
    ]
    y = list(range(len(bars)))[::-1]
    for (label, val, c), yy in zip(bars, y):
        ax.barh(yy, val, height=0.5, color=c, edgecolor=BG, linewidth=1.2)
        ax.text(val + 2, yy, f"{val:.1f}s", va="center", fontsize=11, color=TEXT, fontweight="bold")
        ax.text(-3, yy, label, va="center", ha="right", fontsize=10.5, color=TEXT)

    ax.axvline(BUDGET_S, color=C_BUDGET, linestyle="--", linewidth=2)
    ax.text(BUDGET_S, 2.75, f"예산 {BUDGET_S}s", color=C_BUDGET, fontsize=10, fontweight="bold", ha="left")

    ax.set_xlim(-55, 180)
    ax.set_ylim(-0.6, 2.6)
    ax.set_yticks([])
    ax.set_xlabel("초")
    style_ax(ax)
    ax.set_title("오버랩 효율 = 실제 절약 / 최대 가능 절약 — 정정판", fontsize=13, fontweight="bold",
                  color=TEXT, loc="left")

    eq = (f"실제 절약 = {naive_sum:.2f} − {actual:.2f} = {saved_actual:.2f}s\n"
          f"최대 가능 절약 = {naive_sum:.2f} − {perfect:.2f} = {saved_max:.2f}s\n"
          f"오버랩 효율 = {saved_actual:.2f} / {saved_max:.2f} = {efficiency*100:.1f}%"
          f"  (나머지 {100-efficiency*100:.1f}% = GPU 경합으로 못 숨긴 시간)")
    ax.text(1.0, -0.30, eq, transform=ax.transAxes, ha="right", va="top", fontsize=11,
            color=TEXT,
            bbox=dict(boxstyle="round,pad=0.5", facecolor=PANEL, edgecolor=GRID))
    plt.savefig(IMG / "fig_overlap_efficiency.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_theoretical_floor ────────────────────────────────────────────
def fig_theoretical_floor():
    fig, ax = plt.subplots(figsize=(11, 2.2))
    fig.patch.set_facecolor(BG)

    track_uncontended = S_MOTION + S_FRONTEND + S_PGBA  # 58.572
    map_uncontended = S_MAPPING                          # 85.768
    floor = max(track_uncontended, map_uncontended)

    ax.barh(0.35, track_uncontended, height=0.3, color=C_FRONTEND, edgecolor=BG, linewidth=1.2)
    ax.text(track_uncontended / 2, 0.35, f"직렬 체인 {track_uncontended:.1f}s", ha="center", va="center",
            fontsize=9.5, color="white", fontweight="bold")
    ax.barh(-0.05, map_uncontended, height=0.3, color=C_BACKWARD, edgecolor=BG, linewidth=1.2)
    ax.text(map_uncontended / 2, -0.05, f"gs_mapping {map_uncontended:.1f}s", ha="center", va="center",
            fontsize=9.5, color="white", fontweight="bold")

    ax.axvline(BUDGET_S, color=C_BUDGET, linestyle="--", linewidth=2.2)
    ax.text(BUDGET_S, 0.62, f"예산 {BUDGET_S}s", color=C_BUDGET, fontsize=10.5, fontweight="bold", ha="left")
    ax.axvline(floor, color=C_FLOOR, linestyle=":", linewidth=2)
    ax.text(floor + 3, -0.42,
            f"이론적 최선 = max({track_uncontended:.1f}, {map_uncontended:.1f}) = {floor:.1f}s"
            f" > {BUDGET_S}s ({floor/BUDGET_S:.2f}배)",
            color=C_FLOOR, fontsize=10, ha="left", fontweight="bold")

    ax.set_xlim(0, 130)
    ax.set_ylim(-0.35, 0.75)
    ax.set_yticks([])
    ax.set_xlabel("초")
    style_ax(ax)
    ax.set_title("완벽한 병렬화를 가정해도 도달 불가능한 예산 — 정정판", fontsize=13, fontweight="bold",
                  color=TEXT, loc="left")
    plt.savefig(IMG / "fig_theoretical_floor.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_components (4-panel) ─────────────────────────────────────────
def fig_components():
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4))
    fig.patch.set_facecolor(BG)

    panels = [
        (f"Frontend Tracking · {S_FRONTEND:.1f}s", [
            ("bundle_adjust (BA solve)", 19.65, C_FRONTEND),
            ("update_op_forward (GRU)", 12.94, C_MOTION),
            ("corr_lookup/build/upsample", 6.42, C_PGBA),
            ("(미계측 잔여)", S_FRONTEND - 19.65 - 12.94 - 6.42, C_OVERHEAD),
        ]),
        (f"GS Mapping · {S_MAPPING:.1f}s (순차 실행)", [
            ("backward", 34.7, C_BACKWARD),
            ("rasterize", 31.4, C_RASTERIZE),
            ("loss_compute", 16.8, C_LOSS),
            ("optimizer/densify", 1.3, C_OPT),
            ("(process_track_data 부가작업)", S_MAPPING - 34.7 - 31.4 - 16.8 - 1.3, C_MAPETC),
        ]),
        (f"motion_filter · {S_MOTION:.1f}s", [
            ("prior_extractor(Omnidata)", 3.18, C_MOTION),
            ("flow_check", 2.73, C_PGBA),
            ("context_encoder", 0.70, C_FRONTEND),
            ("feature_encoder(fnet)", 0.60, C_BUDGET),
            ("(미계측 잔여)", S_MOTION - 3.18 - 2.73 - 0.70 - 0.60, C_OVERHEAD),
        ]),
        (f"track() 바깥 오버헤드 · {S_OVERHEAD:.1f}s (해소됨)", [
            ("model_loading(1회성)", 1.510, C_MOTION),
            ("queue_get_wait(IPC 대기)", 4.348, C_PGBA),
            ("pbar+save_trajectory", 0.143, C_OVERHEAD),
        ]),
    ]

    for ax, (title, items) in zip(axes.flat, panels):
        total = sum(v for _, v, _ in items)
        n = len(items)
        BAR_Y = -1.3
        x = 0
        for name, v, c in items:
            ax.barh(BAR_Y, max(v, 0), left=x, height=0.9, color=c, edgecolor=BG, linewidth=1.2)
            x += v
        for i, (name, v, c) in enumerate(items):
            yy = (n - 1) - i
            ax.add_patch(Rectangle((0, yy - 0.16), total * 0.018, 0.32, color=c,
                                    transform=ax.transData, clip_on=False))
            ax.text(total * 0.03, yy, f"{name}: {v:.2f}s", fontsize=9.5, color=MUTED,
                    va="center", ha="left")
        ax.set_xlim(0, total * 1.02)
        ax.set_ylim(BAR_Y - 0.9, n)
        ax.set_yticks([])
        style_ax(ax)
        ax.set_title(title, fontsize=11.5, fontweight="bold", color=TEXT, loc="left", pad=8)

    fig.suptitle("구성요소별 세부 분해 — 순차 실행 런 기준, 정정판 (1253 시퀀스 누적 시간)",
                  fontsize=14, fontweight="bold", color=TEXT, x=0.02, ha="left", y=1.0)
    fig.text(0.02, -0.01,
              f"※ gs_parallel 하에서는 frontend({S_FRONTEND:.1f}→{P_FRONTEND:.1f}s)·"
              f"motion_filter({S_MOTION:.1f}→{P_MOTION:.1f}s)가 GPU 경합으로 더 커짐 — 뒤 슬라이드 참조",
              fontsize=9.5, color=MUTED)
    plt.tight_layout(rect=[0, 0.01, 1, 0.95])
    plt.savefig(IMG / "fig_components.png", facecolor=BG, bbox_inches="tight")
    plt.close()


# ── fig_gsmapping_granular (신규, exp53 요청) ─────────────────────────
def fig_gsmapping_granular(data):
    """GS Mapping 루프를 process_track_data() 부가작업 + map() 내부로 최대한 잘게 쪼갠 그림.
    data: dict {key: seconds} — 실측 후 채워짐."""
    fig, ax = plt.subplots(figsize=(11, 4.2))
    fig.patch.set_facecolor(BG)

    order = [
        ("pose_scale_update", C_PTD1),
        ("w2c_compute", C_PTD2),
        ("camera_init", C_PTD1),
        ("render_for_mask", C_PTD2),
        ("add_next_kf", C_PTD3),
        ("add_next_kf_init", C_PTD3),
        ("rasterize", C_RASTERIZE),
        ("loss_compute", C_LOSS),
        ("backward", C_BACKWARD),
        ("densify_prune", C_OPT),
        ("optimizer_step", C_MAPETC),
        ("map() 내부 미계측(isotropic loss·viewpoint 샘플링 추정)", C_OVERHEAD),
    ]
    items = [(k, data.get(k, 0.0), c) for k, c in order if data.get(k, 0.0) > 0]
    items.sort(key=lambda t: -t[1])
    total = sum(v for _, v, _ in items)

    y = list(range(len(items)))[::-1]
    for (name, v, c), yy in zip(items, y):
        ax.barh(yy, v, height=0.62, color=c, edgecolor=BG, linewidth=1)
        ax.text(v + total * 0.01, yy, f"{name}: {v:.2f}s ({v/total*100:.1f}%)", va="center",
                fontsize=10.5, color=TEXT)

    ax.set_xlim(0, total * 1.55)
    ax.set_ylim(-0.7, len(items) - 0.3)
    ax.set_yticks([])
    ax.set_xlabel("초 (1253 시퀀스 누적)")
    style_ax(ax)
    ax.set_title(f"GS Mapping 루프 최대 세분화 — {total:.1f}s ({len(items)}단계)", fontsize=13,
                  fontweight="bold", color=TEXT, loc="left")
    plt.savefig(IMG / "fig_gsmapping_granular.png", facecolor=BG, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    fig_timeline_serial()
    fig_timeline_parallel()
    fig_frontend_contention()
    fig_overlap_efficiency()
    fig_theoretical_floor()
    fig_components()
    print("done (granular figure built separately once data is ready):",
          sorted(p.name for p in IMG.glob("*.png")))
