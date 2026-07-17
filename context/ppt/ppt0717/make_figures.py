#!/usr/bin/env python3
"""make_figures.py (ppt0717) — 슬라이드 4/5용 시각자료를 실제 렌더/실측 데이터로 생성.

전제: render_cache/*.png 는 3dgs-custom/render_view_subset.py로 실제 학습 체크포인트에서
직접 렌더링한 이미지(같은 카메라 pose, baseline vs 개선판 짝) — 합성/모사 아님.
  - 305_baseline_00796.png / 305_hybrid_00796.png       (exp46 축1: scene_301_305_baseline vs exp46_ax1_305hyb)
  - 12F_baseline_00658.png / 12F_hybcarve_00658.png      (exp46 축2b: scene_301_12F_baseline vs exp46_ax2b_12Fhybcarve)
  - 12F_hybcarve_00658.png / 12F_S2cheapcarve_00658.png  (exp47 축S2: 기준 66분 vs cheapcarve 26.8분 — 무손실 검증용)

figure 목록:
  fig_init_recipe   init(hybrid) 생성 파이프라인 — 어떤 anchor로 무엇을 걸러냈는지 (신규)
  fig_305_compare   305 baseline vs hybrid init 렌더 비교 + PSNR/먼지 수치
  fig_12F_compare   12F baseline vs hybrid+carve 렌더 비교 + PSNR/먼지 수치
  fig_dust_bars     free-space 먼지 개수 before/after (305, 12F 두 패널, log scale)
  fig_speed_pareto  exp47 속도 트랙 시간-PSNR 산점도, S2 강조
  fig_12F_lossless  12F ctrl(66분) vs S2 cheapcarve(26.8분) 렌더 비교 — 무손실 시각 증거

실행: python make_figures.py
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager as _fm
from PIL import Image

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
plt.rcParams.update({"figure.dpi": 130, "savefig.bbox": "tight",
                     "axes.titlesize": 13, "axes.titleweight": "bold",
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.25})

HERE = Path(__file__).parent
IMG = HERE / "img"
IMG.mkdir(exist_ok=True)
CACHE = HERE / "render_cache"

ACCENT = "#0f4c81"
RED = "#c0392b"
GRAY = "#95a5a6"
GREEN = "#27ae60"


def save(fig, name):
    fig.savefig(IMG / f"{name}.png")
    plt.close(fig)
    print(f"  saved {name}.png")


def _flow(ax, boxes, arrows, xlim, ylim):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off"); ax.grid(False)
    for (x, y, w, h, txt, color) in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                    fc=color, ec=ACCENT, lw=1.3))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=9.5)
    for a in arrows:
        x1, y1, x2, y2 = a[:4]
        col = a[4] if len(a) > 4 else "#555"
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.6, color=col))


# ── 0. init 파이프라인 — 실제 anchor 상세 (scripts/anchors/build_hybrid_init_scene.py 그대로) ──
def fig_init_recipe():
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    boxes = [
        (0.2, 3.6, 2.4, 1.3, "RoMA 삼각측량\n인접 keyframe쌍 dense\ncorrespondence\n→ reproj<2px만 채택\n(기하 검증)", "#dbe7f3"),
        (0.2, 1.9, 2.4, 1.3, "Sobel-PPM depth-lift\n텍스처 가중 샘플 4k/frame\n+ SLAM-Huber 보정 depth\n(콘텐츠-적응)", "#dbe7f3"),
        (0.2, 0.2, 2.4, 1.3, "원본 SLAM 점\n(희소, 항상 신뢰)", "#dbe7f3"),
        (3.1, 2.1, 2.0, 1.6, "병합\n4cm voxel dedupe\nRoMA 우선권", "#f6e2c0"),
        (5.6, 2.1, 2.6, 1.6, "재필터 (핵심 anchor)\ndepth-anchor field\n(exp43, depth-pro 보정\n조밀 표면 anchor)\nw = ρ·d5 > 0.5 제거", "#f9d0d0"),
        (8.7, 2.1, 2.2, 1.6, "최종 hybrid init\nSLAM + RoMA + PPM\n(305: 89.4만 / 12F: 59.7만)", "#cfe3cf"),
    ]
    arrows = [
        (2.6, 4.25, 3.1, 3.1), (2.6, 2.55, 3.1, 2.95), (2.6, 0.85, 3.1, 2.6),
        (5.1, 2.9, 5.6, 2.9), (8.2, 2.9, 8.7, 2.9),
    ]
    _flow(ax, boxes, arrows, (0, 11.2), (0, 5.4))
    ax.set_title("Init(hybrid) 생성 파이프라인 — 재필터 단계의 anchor가 핵심", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig_init_recipe")


# ── 1. 305 렌더 비교 ────────────────────────────────────────
def fig_305_compare():
    im_a = Image.open(CACHE / "305_baseline_00796.png")
    im_b = Image.open(CACHE / "305_hybrid_00796.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    for ax, im, title, sub in zip(
        axes, [im_a, im_b],
        ["baseline (ORB init only)", "hybrid init (RoMA+PPM, exp46 축1)"],
        ["PSNR 34.508 · free-space 먼지 461", "PSNR 35.84 (+1.33dB) · free-space 먼지 4 (−99%)"]):
        ax.imshow(im); ax.axis("off")
        ax.set_title(title, fontsize=12)
        ax.text(0.5, -0.04, sub, transform=ax.transAxes, ha="center", va="top",
                fontsize=11, color=GREEN if "hybrid" in title else GRAY, fontweight="bold")
    fig.suptitle("301_305 — 같은 카메라 시점, 초기화(init)만 교체", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "fig_305_compare")


# ── 2. 12F 렌더 비교 ────────────────────────────────────────
def fig_12F_compare():
    im_a = Image.open(CACHE / "12F_baseline_00658.png")
    im_b = Image.open(CACHE / "12F_hybcarve_00658.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    for ax, im, title, sub in zip(
        axes, [im_a, im_b],
        ["baseline (ORB init only)", "hybrid init + carve (exp46 축2b)"],
        ["PSNR 32.034 · free-space 먼지 1,289", "PSNR 35.07 (+3.03dB) · free-space 먼지 243 (−81%, 청소 후 유지)"]):
        ax.imshow(im); ax.axis("off")
        ax.set_title(title, fontsize=12)
        ax.text(0.5, -0.04, sub, transform=ax.transAxes, ha="center", va="top",
                fontsize=11, color=GREEN if "carve" in title else GRAY, fontweight="bold")
    fig.suptitle("301_12F (fog 로비) — 같은 카메라 시점, 초기화만 교체", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "fig_12F_compare")


# ── 3. free-space 먼지 개수 before/after 막대 ──────────────
def fig_dust_bars():
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    data = [("301_305", [461, 4], ["baseline", "hybrid init\n(exp46 축1)"]),
            ("301_12F", [1289, 243], ["baseline", "hybrid+carve\n(exp46 축2b)"])]
    for ax, (title, vals, labels) in zip(axes, data):
        cols = [GRAY, GREEN]
        b = ax.bar(labels, vals, color=cols, width=0.55)
        for r, v in zip(b, vals):
            ax.text(r.get_x() + r.get_width() / 2, v * 1.05, f"{v:,}", ha="center",
                    fontweight="bold", fontsize=11)
        pct = 100 * (1 - vals[1] / vals[0])
        ax.set_yscale("log")
        ax.set_ylim(1, max(vals) * 3)
        ax.set_title(f"{title}  (−{pct:.0f}%)")
        ax.set_ylabel("free-space 먼지 개수 (log)")
    fig.suptitle("초기화(init) 개선만으로 진짜 부유물(free-space) 먼지 급감", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig_dust_bars")


# ── 4. exp47 속도 트랙 Pareto ───────────────────────────────
def fig_speed_pareto():
    # (label, time_min, psnr, highlight, xytext offset)
    rows = [
        ("기준 (hybrid+carve)", 66.0, 35.07, False, (8, 8)),
        ("S2 cheapcarve", 26.8, 35.116, True, (8, 10)),
        ("S3 15k iter", 39.9, 32.801, False, (8, -14)),
        ("S4 kf300", 53.8, 34.397, False, (10, -14)),
        ("S5 budget235k", 63.2, 34.400, False, (8, -14)),
        ("S6 r/2", 56.1, 35.553, False, (8, 6)),
        ("S1S4 kf300+cuda", 53.8, 34.470, False, (10, 10)),
        ("TARGET (기각)", 12.6, 32.943, None, (8, 8)),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for label, t, p, hi, (dx, dy) in rows:
        if hi is True:
            c, ms, z = GREEN, 220, 5
        elif hi is None:
            c, ms, z = RED, 160, 4
        else:
            c, ms, z = ACCENT, 140, 3
        ax.scatter(t, p, s=ms, color=c, zorder=z, edgecolor="white", linewidth=1.2)
        ax.annotate(label, (t, p), textcoords="offset points", xytext=(dx, dy), fontsize=9,
                    fontweight="bold" if hi else "normal")
    ax.axhline(33.5, color=RED, linestyle="--", linewidth=1, alpha=0.6)
    ax.text(68, 33.6, "품질 하한 33.5dB", color=RED, fontsize=9, va="bottom", ha="right")
    ax.set_xlabel("학습 시간 (분)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("12F 속도-품질 Pareto — S2가 화질 무손실로 60% 단축")
    ax.set_ylim(32.4, 36.1)
    ax.set_xlim(70, 8)
    fig.tight_layout()
    save(fig, "fig_speed_pareto")


# ── 5. 12F 무손실 속도 개선 렌더 비교 ───────────────────────
def fig_12F_lossless():
    im_a = Image.open(CACHE / "12F_hybcarve_00658.png")
    im_b = Image.open(CACHE / "12F_S2cheapcarve_00658.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    for ax, im, title, sub in zip(
        axes, [im_a, im_b],
        ["기준 레시피 — 66분", "S2 cheapcarve — 26.8분 (−60%)"],
        ["PSNR 35.07", "PSNR 35.116 (오차범위 내 동일)"]):
        ax.imshow(im); ax.axis("off")
        ax.set_title(title, fontsize=12)
        ax.text(0.5, -0.04, sub, transform=ax.transAxes, ha="center", va="top",
                fontsize=11, color=GREEN, fontweight="bold")
    fig.suptitle("같은 카메라 시점 — 육안 차이 없음, 시간만 60% 단축", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "fig_12F_lossless")


def main():
    fig_init_recipe()
    fig_305_compare()
    fig_12F_compare()
    fig_dust_bars()
    fig_speed_pareto()
    fig_12F_lossless()
    print(f"완료 — {IMG}")


if __name__ == "__main__":
    main()
