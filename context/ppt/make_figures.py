#!/usr/bin/env python3
"""make_figures.py — PPT용 시각자료를 실제 데이터로 렌더해 img/ 에 저장.

figure 목록(→ 매핑은 build_ppt.py IMG_MAP):
  fig_landscape       loss landscape 두 분지 (개념)
  fig_raycoverage     ray 커버리지 높이별 불균등 (carve field transit)
  fig_auc_plateau     plateau vs raw vs carve AUC 막대
  fig_grad_asym       plateau/RGB gradient 비대칭 막대
  fig_label_highlight 표면 vs 라벨 floater (rot, top view)
  fig_region          사면체 확장 영역 voxel (rot, top view)
  fig_rho_section     빈공간 증거 rho 수평 단면 히트맵
  fig_waterfall       exp38–40 7런 region_n 막대
  fig_pareto          먼지 vs test PSNR Pareto
  fig_scenes          세 장면 대표 이미지 + 텍스처/대비
  fig_sobel_ppm       이미지 + Sobel PPM 히트맵
  fig_anchors         SLAM(희소) vs depth(조밀) 앵커 top view
  fig_huber           depth Huber 보정 산점도
  fig_crossscene_auc  교차 장면 AUC 막대(+0.95 문턱)
  fig_slamfree_ladder SLAM-프리 vr AUC 사다리
  (fig_ab_render      기존 exp30r/exp40b 렌더 복사)

실행: python make_figures.py
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from matplotlib import font_manager as _fm
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

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
IMG = Path(__file__).parent / "img"
IMG.mkdir(exist_ok=True)
sys.path.insert(0, str(LAB / "scripts/analysis"))

ACCENT = "#0f4c81"
RED = "#c0392b"
GRAY = "#95a5a6"
GREEN = "#27ae60"


def save(fig, name):
    fig.savefig(IMG / f"{name}.png", facecolor="white")
    plt.close(fig)
    print("  saved", name)


def read_ply(path):
    from plyfile import PlyData
    v = PlyData.read(str(path))["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    op = 1 / (1 + np.exp(-np.asarray(v["opacity"], np.float64)))
    return v, xyz, op


# ── 1. loss landscape 개념도 ────────────────────────────────
def fig_landscape():
    x = np.linspace(-3, 3, 500)
    # 두 우물: floater 분지(얕고 가까움) + 표면 분지(깊고 멈)
    y = 0.6*(x+1.3)**2 * np.exp(-0.5*(x+1.3)**2) + 1.0*(x-1.4)**2*np.exp(-0.4*(x-1.4)**2)
    y = -np.exp(-2*(x+1.2)**2)*0.55 - np.exp(-1.5*(x-1.5)**2)*1.0 + 0.15*x**2*0.1 + 1.1
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.plot(x, y, color=ACCENT, lw=2.5)
    ax.scatter([-1.2], [np.interp(-1.2, x, y)], s=120, color=RED, zorder=5)
    ax.annotate("floater basin\n(가까운 숏컷)", (-1.2, np.interp(-1.2,x,y)),
                textcoords="offset points", xytext=(-8, 26), ha="center", color=RED, fontsize=9)
    ax.scatter([1.5], [np.interp(1.5, x, y)], s=120, color=GREEN, zorder=5)
    ax.annotate("correct geometry\n(깊지만 먼 정답)", (1.5, np.interp(1.5,x,y)),
                textcoords="offset points", xytext=(6, 20), ha="center", color=GREEN, fontsize=9)
    ax.annotate("", xy=(0.9, np.interp(0.9,x,y)+0.05), xytext=(-0.6, np.interp(-0.6,x,y)+0.05),
                arrowprops=dict(arrowstyle="->", color="#888", lw=1.5))
    ax.text(0.15, np.interp(0.15,x,y)+0.16, "init / smoothing\n으로 이 분지로", ha="center", fontsize=8, color="#555")
    ax.set_xlabel("gaussian 배치 (개념 축)"); ax.set_ylabel("photometric loss")
    ax.set_yticks([]); ax.set_title("Floater = photometric loss의 분지(basin)")
    save(fig, "fig_landscape")


# ── 2. ray coverage 높이별 불균등 ───────────────────────────
def fig_raycoverage():
    z = np.load(LAB/"results/experiments/exp32_lineage_diag/carve_fields.npz")
    tr = z["transit"]; lo = z["lo"]; dims = z["dims"]
    vox = 0.10
    per_z = tr.sum(axis=(0,1))
    hgt = lo[2] + (np.arange(len(per_z))+0.5)*vox
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    ax.barh(hgt, per_z, height=vox*0.9, color=ACCENT, alpha=0.85)
    ax.set_xlabel("ray 통과 증거량 (transit 합)"); ax.set_ylabel("높이 Z (m)")
    ax.set_title("ray 커버리지가 높이별로 극단적 불균등")
    save(fig, "fig_raycoverage")


# ── 3. AUC plateau vs raw vs carve ──────────────────────────
def fig_auc_plateau():
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    names = ["Plateau\n(정규화 D)", "Raw 거리", "Carve score"]
    vals = [0.511, 0.93, 0.974]
    cols = [GRAY, "#e67e22", GREEN]
    b = ax.bar(names, vals, color=cols)
    ax.axhline(0.5, ls="--", color="#aaa", lw=1); ax.text(2.4, 0.52, "무작위", color="#aaa", fontsize=8)
    for r, v in zip(b, vals): ax.text(r.get_x()+r.get_width()/2, v+0.01, f"{v:.3f}", ha="center", fontweight="bold")
    ax.set_ylim(0.45, 1.02); ax.set_ylabel("floater 판별 AUC")
    ax.set_title("신호는 있었다 — 손실이 버렸을 뿐")
    save(fig, "fig_auc_plateau")


# ── 4. gradient 비대칭 ──────────────────────────────────────
def fig_grad_asym():
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    names = ["Plateau\ngrad", "표면\n(기준 1.0)", "RGB\ngrad"]
    vals = [0.58, 1.0, 2.23]
    cols = [GRAY, "#bbb", RED]
    b = ax.bar(names, vals, color=cols)
    for r, v in zip(b, vals): ax.text(r.get_x()+r.get_width()/2, v+0.03, f"{v:.2f}×", ha="center", fontweight="bold")
    ax.set_ylabel("표면 대비 gradient 비율")
    ax.set_title("floater는 RGB gradient의 비호를 받는다")
    save(fig, "fig_grad_asym")


# ── 5. 라벨 floater 하이라이트 (rot) ────────────────────────
def _rot_labels():
    from design_floater_loss_candidates import match_deleted
    base = LAB/"results/experiments/scene_301_1253_rot_baseline_20260712_100443/point_cloud/iteration_30000"
    v, xyz, op = read_ply(base/"point_cloud.ply")
    # match_deleted(v_orig, v_clean) 시그니처: design 버전은 (v_orig, cleaned_path)
    from plyfile import PlyData
    vc = PlyData.read(str(base/"point_cloud_cleaned_labelingpruningplus.ply"))["vertex"]
    fo = np.stack([np.asarray(v[k]) for k in ("f_dc_0","f_dc_1","f_dc_2")],1).astype(np.float32)
    fc = np.stack([np.asarray(vc[k]) for k in ("f_dc_0","f_dc_1","f_dc_2")],1).astype(np.float32)
    from scipy.spatial import cKDTree
    d,_ = cKDTree(fc).query(fo, workers=-1)
    deleted = d > 1e-5
    return xyz, op, deleted

def fig_label_highlight():
    xyz, op, deleted = _rot_labels()
    surf = (~deleted) & (op > 0.3)
    rng = np.random.default_rng(0)
    si = rng.choice(np.where(surf)[0], min(25000, surf.sum()), replace=False)
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.scatter(xyz[si,0], xyz[si,1], s=1, c=GRAY, alpha=0.35, label=f"표면 gaussian ({surf.sum():,})")
    ax.scatter(xyz[deleted,0], xyz[deleted,1], s=3, c=RED, alpha=0.7, label=f"사용자 라벨 floater ({deleted.sum():,})")
    ax.set_aspect("equal"); ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
    ax.legend(loc="upper right", fontsize=8, markerscale=3)
    ax.set_title("사용자가 직접 지운 floater (top view)")
    save(fig, "fig_label_highlight")


# ── 6. 사면체 확장 영역 ─────────────────────────────────────
def fig_region():
    z = np.load(LAB/"data/scenes/301_1253_rot/floater_region/region_mask.npz")
    mask = z["mask"]; lo = z["lo"]; vox = float(z["voxel"])
    ii = np.argwhere(mask)
    c = lo + (ii + 0.5) * vox
    xyz, op, deleted = _rot_labels()
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.scatter(c[:,0], c[:,1], s=6, c="#8e44ad", alpha=0.25, label=f"삭제 영역 voxel ({len(c):,})")
    ax.scatter(xyz[deleted,0], xyz[deleted,1], s=3, c=RED, alpha=0.7, label=f"라벨 floater ({deleted.sum():,})")
    ax.set_aspect("equal"); ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
    ax.legend(loc="upper right", fontsize=8, markerscale=2)
    ax.set_title("점 라벨 → 사면체 채움으로 3D 영역 확장")
    save(fig, "fig_region")


# ── 7. rho 수평 단면 ────────────────────────────────────────
def fig_rho_section():
    z = np.load(LAB/"results/experiments/exp32_lineage_diag/carve_fields.npz")
    from scipy.ndimage import uniform_filter
    tr = uniform_filter(z["transit"],3); te = uniform_filter(z["terminal"],3)
    rho = tr/(tr+3*te+1e-6)
    # 가장 증거 많은 z-layer
    zbest = int(np.argmax(z["transit"].sum(axis=(0,1))))
    sl = rho[:,:,zbest]
    fig, ax = plt.subplots(figsize=(5.0, 3.6))
    im = ax.imshow(sl.T, origin="lower", cmap="RdYlGn", vmin=0, vmax=1, aspect="equal")
    ax.set_title("빈 공간 증거 ρ — 수평 단면 (초록=빈공간)")
    ax.set_xlabel("X voxel"); ax.set_ylabel("Y voxel")
    fig.colorbar(im, ax=ax, fraction=0.04, label="ρ (빈 공간 증거비)")
    save(fig, "fig_rho_section")


# ── 8. exp38–40 7런 region_n ───────────────────────────────
def fig_waterfall():
    runs = ["exp30r\nbaseline","38a\nfull soft","38b\nsoft off","38c\nsoftlite","40a\nforce","40b\n챔피언"]
    reg = [3749, 559, 1744, 946, 1309, 498]
    cols = [GRAY,"#e67e22","#e67e22","#e67e22","#e67e22",GREEN]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    b = ax.bar(runs, reg, color=cols)
    for r,v in zip(b,reg): ax.text(r.get_x()+r.get_width()/2, v+40, f"{v:,}", ha="center", fontsize=8, fontweight="bold")
    ax.set_ylabel("region 먼지 개수 (낮을수록 좋음)")
    ax.set_title("성분 분해: soft가 주역, force가 무비용 추가")
    save(fig, "fig_waterfall")


# ── 9. Pareto ───────────────────────────────────────────────
def fig_pareto():
    dust = [3700, 1795, 1136, 460]
    psnr = [31.549, 31.459, 31.336, 31.106]
    lab = ["baseline","prune+gate","+force","softlite+force\n(챔피언)"]
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.plot(dust, psnr, "-o", color=ACCENT, lw=2, ms=8)
    for d,p,l in zip(dust,psnr,lab):
        ax.annotate(l, (d,p), textcoords="offset points", xytext=(8,-4), fontsize=8)
    ax.invert_xaxis()
    ax.set_xlabel("region 먼지 (←적을수록 깨끗)"); ax.set_ylabel("held-out test PSNR")
    ax.set_title("먼지↔PSNR Pareto: 운영점은 연속 조절")
    save(fig, "fig_pareto")


# ── 10. 세 장면 대표 이미지 ─────────────────────────────────
def fig_scenes():
    import cv2
    specs = [("1253", "data/03_rgb_3dgs_full/images", "텍스처 18.8 / 대비 39"),
             ("305",  "data/scenes/301_305/03_rgb_3dgs/images", "텍스처 13.7 / 대비 39"),
             ("12F",  "data/scenes/301_12F/03_rgb_3dgs/images", "텍스처 11.5 / 대비 25.6 (fog)")]
    fig, axs = plt.subplots(1, 3, figsize=(9.5, 3.2))
    for ax,(nm,d,cap) in zip(axs, specs):
        files = sorted((LAB/d).glob("*.jpg"))
        im = cv2.cvtColor(cv2.imread(str(files[len(files)//2])), cv2.COLOR_BGR2RGB)
        ax.imshow(im); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{nm}\n{cap}", fontsize=10)
    fig.suptitle("세 장면 이미지 특성 — 12F만 대비(fog)가 반토막", fontsize=12, fontweight="bold", y=1.06)
    save(fig, "fig_scenes")


# ── 11. Sobel PPM ───────────────────────────────────────────
def fig_sobel_ppm():
    import cv2
    files = sorted((LAB/"data/scenes/301_305/03_rgb_3dgs/images").glob("*.jpg"))
    im = cv2.cvtColor(cv2.imread(str(files[len(files)//2])), cv2.COLOR_BGR2RGB)
    g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(np.float32)
    sob = np.hypot(cv2.Sobel(g,cv2.CV_32F,1,0), cv2.Sobel(g,cv2.CV_32F,0,1))
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.1))
    axs[0].imshow(im); axs[0].set_title("입력 이미지"); axs[0].axis("off")
    axs[1].imshow(sob, cmap="magma"); axs[1].set_title("Sobel PPM (점 배치 확률맵)"); axs[1].axis("off")
    fig.suptitle("PPM: 텍스처 강한 곳에 점을 촘촘히", fontsize=11, fontweight="bold", y=1.04)
    save(fig, "fig_sobel_ppm")


# ── 12. SLAM vs depth 앵커 ──────────────────────────────────
def _load_pts(p):
    out=[]
    for l in open(p):
        t=l.split()
        if len(t)>=7 and not l.startswith("#"): out.append([float(t[1]),float(t[2]),float(t[3])])
    return np.array(out, np.float32)

def fig_anchors():
    slam = _load_pts(LAB/"data/scenes/301_305/03_rgb_3dgs/sparse/0/points3D.txt")
    dep = np.load(LAB/"data/scenes/301_305/depth_anchors.npz")["anchors"]
    rng = np.random.default_rng(0)
    di = rng.choice(len(dep), 40000, replace=False)
    fig, axs = plt.subplots(1, 2, figsize=(8.4, 3.6), sharex=True, sharey=True)
    axs[0].scatter(slam[:,0], slam[:,2], s=4, c=RED, alpha=0.6)
    axs[0].set_title(f"SLAM 앵커 — 희소 {len(slam):,}점\n(표면 못 덮음)")
    axs[1].scatter(dep[di,0], dep[di,2], s=1, c=ACCENT, alpha=0.3)
    axs[1].set_title(f"depth 앵커 — 조밀 {len(dep):,}점\n(표면 커버)")
    for ax in axs: ax.set_aspect("equal"); ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
    fig.suptitle("305: SLAM은 표면을 못 덮고, depth가 구원", fontsize=12, fontweight="bold")
    save(fig, "fig_anchors")


# ── 13. Huber 보정 산점도 ───────────────────────────────────
def fig_huber():
    from design_floater_loss_candidates import FX, FY, CX, CY, IMG_W, IMG_H
    from build_scene_carve_and_pseudolabel import load_cams
    from sklearn.linear_model import HuberRegressor
    base = LAB/"data/scenes/301_305/03_rgb_3dgs/sparse/0"
    Rs, ts = load_cams(base/"images.txt")
    slam = _load_pts(base/"points3D.txt")
    names = [l.split()[9] for l in open(base/"images.txt") if len(l.split())>=10 and not l.startswith("#")]
    n2c = {Path(n).stem:i for i,n in enumerate(names)}
    # depth 있는 프레임 하나
    df = sorted((LAB/"results/diagnostic/depth_maps_301_305/depth_pro").glob("*.npy"))
    for f in df:
        ci = n2c.get(f.stem)
        if ci is None: continue
        depth = np.load(f).astype(np.float32); R,t = Rs[ci], ts[ci]
        pc = slam@R.T+t; z=pc[:,2]; ok=(z>0.3)&(z<12)
        u=pc[:,0]/np.clip(z,1e-6,None)*FX+CX; v=pc[:,1]/np.clip(z,1e-6,None)*FY+CY
        ok&=(u>=1)&(u<IMG_W-1)&(v>=1)&(v<IMG_H-1)
        if ok.sum()<40: continue
        zm=depth[v[ok].astype(int),u[ok].astype(int)]; g=(zm>0.1)&(zm<20)
        if g.sum()<40: continue
        D=zm[g]; Z=z[ok][g]
        reg=HuberRegressor(epsilon=1.35,max_iter=500).fit(D[:,None],Z)
        xs=np.linspace(D.min(),D.max(),50)
        fig, ax = plt.subplots(figsize=(4.8,3.4))
        ax.scatter(D, Z, s=10, alpha=0.5, color=ACCENT, label="SLAM 점")
        ax.plot(xs, reg.coef_[0]*xs+reg.intercept_, color=RED, lw=2,
                label=f"Huber: z≈{reg.coef_[0]:.2f}·D+{reg.intercept_:.2f}")
        ax.set_xlabel("depth-pro 값 D (m)"); ax.set_ylabel("SLAM 깊이 z (m)")
        ax.legend(fontsize=8); ax.set_title("단안 depth를 SLAM으로 미터 보정")
        save(fig, "fig_huber"); return


# ── 14. 교차 장면 AUC ───────────────────────────────────────
def fig_crossscene_auc():
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    names=["1253_rot\n(같은 방)","305\n(다른 방)","12F\n(fog)"]
    vals=[0.9813, 0.7993, 0.858]; cols=[GREEN, RED, "#e67e22"]
    b=ax.bar(names, vals, color=cols)
    ax.axhline(0.95, ls="--", color="#333", lw=1); ax.text(1.6, 0.955, "사전등록 기준 0.95", fontsize=8)
    for r,v in zip(b,vals): ax.text(r.get_x()+r.get_width()/2, v+0.008, f"{v:.3f}", ha="center", fontweight="bold")
    ax.set_ylim(0.6, 1.02); ax.set_ylabel("champion score AUC")
    ax.set_title("교차 장면: 같은 방 성공, 다른 방 실패")
    save(fig, "fig_crossscene_auc")


# ── 15. SLAM-프리 사다리 ────────────────────────────────────
def fig_slamfree_ladder():
    fig, ax = plt.subplots(figsize=(5.2, 3.1))
    names=["vr raw\n(SLAM 불필요)","vr + pose 자가보정\n(SLAM 불필요)","vr + SLAM 보정\n(상한)"]
    vals=[0.855, 0.893, 0.908]; cols=["#e67e22","#f39c12",ACCENT]
    b=ax.bar(names, vals, color=cols)
    for r,v in zip(b,vals): ax.text(r.get_x()+r.get_width()/2, v+0.002, f"{v:.3f}", ha="center", fontweight="bold")
    ax.set_ylim(0.83, 0.92); ax.set_ylabel("12F floater 탐지 AUC")
    ax.set_title("지도 포인트 0개로도 상한의 98%")
    save(fig, "fig_slamfree_ladder")


# ── 16. 렌더 A/B 복사 ───────────────────────────────────────
def fig_ab_render():
    src = LAB/"results/experiments/exp38_40_visual/view0500_top-exp30r_bottom-exp40b.jpg"
    if src.exists():
        shutil.copy(src, IMG/"fig_ab_render.png")
        print("  copied fig_ab_render (exp30r vs exp40b)")


def main():
    for fn in [fig_landscape, fig_raycoverage, fig_auc_plateau, fig_grad_asym,
               fig_label_highlight, fig_region, fig_rho_section, fig_waterfall,
               fig_pareto, fig_scenes, fig_sobel_ppm, fig_anchors, fig_huber,
               fig_crossscene_auc, fig_slamfree_ladder, fig_ab_render]:
        try:
            fn()
        except Exception as e:
            print(f"  [FAIL] {fn.__name__}: {e}")


if __name__ == "__main__":
    main()
