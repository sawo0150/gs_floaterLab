"""Render exp08 PLY with Z-colored points: top-down + side view showing floaters."""
import numpy as np
import json
from pathlib import Path
from plyfile import PlyData
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

PLY = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/"
           "exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504/"
           "point_cloud/iteration_30000/point_cloud.ply")
CAM_JSON = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/"
                "exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504/"
                "cameras.json")
OUT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/context/ppt/0706_ppt/imgs/slide03_ply_render.png")

print("Loading PLY...")
ply = PlyData.read(str(PLY))
v = ply['vertex']
x = np.array(v['x'])
y = np.array(v['y'])
z = np.array(v['z'])
print(f"  {len(x):,} pts  Z:[{z.min():.1f},{z.max():.1f}]")

# Load camera positions
with open(CAM_JSON) as f:
    cams = json.load(f)
cam_pos = np.array([c["position"] for c in cams])

# Clip extreme Z outliers for visualization
z_clip = np.clip(z, -4, 5)
# Only show points in reasonable range for the scene visualization
mask_scene = (z > -4) & (z < 5)
xs, ys, zs, zsc = x[mask_scene], y[mask_scene], z[mask_scene], z_clip[mask_scene]

# Floaters = Z > +2m (Pop2)
mask_floater = (z > 2.0) & (z < 5)
xf, yf, zf = x[mask_floater], y[mask_floater], z[mask_floater]

BG = "#0D1B2A"
fig, axes = plt.subplots(1, 2, figsize=(20, 9), facecolor=BG)
fig.patch.set_facecolor(BG)

cmap = plt.cm.RdYlBu_r

# --- LEFT: Side view (X-Z) ---
ax = axes[0]
ax.set_facecolor(BG)
# Downsample for speed
step = max(1, len(xs)//80000)
sc = ax.scatter(xs[::step], zsc[::step], c=zsc[::step], s=0.3, alpha=0.4,
                cmap=cmap, vmin=-4, vmax=5, rasterized=True)
# Highlight floaters
ax.scatter(xf[::3], zf[::3], c='#FF6B35', s=1.5, alpha=0.8, label=f'Pop2 floater (Z>+2m)\n  n={mask_floater.sum():,}', rasterized=True)
# Camera trajectory (projected to XZ)
ax.plot(cam_pos[:,0], cam_pos[:,2], color='#FFD700', linewidth=1.5, alpha=0.9, zorder=5)
ax.scatter(cam_pos[:,0], cam_pos[:,2], c='#FFD700', s=8, zorder=6)
# Pop2 band
ax.axhspan(2.0, 5.0, alpha=0.1, color='#FF6B35', label='Pop2 구간 (Z>+2m)')
ax.axhline(2.0, color='#FF6B35', linestyle='--', linewidth=1.2, alpha=0.8)
ax.set_xlabel("X (m)  — 카메라 이동 방향", color='white', fontsize=11)
ax.set_ylabel("Z (m)  — 높이 (수직)", color='white', fontsize=11)
ax.set_title("Side View (X-Z)\nexp08 30k Gaussian — Z-colored", color='white', fontsize=13, fontweight='bold', pad=10)
ax.tick_params(colors='white')
for spine in ax.spines.values(): spine.set_edgecolor('#334455')
ax.legend(loc='upper right', fontsize=9, facecolor='#1A2B3C', labelcolor='white', framealpha=0.8)
ax.set_xlim(-20, 20)
ax.set_ylim(-4.5, 5.5)
cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label('Z (m)', color='white', fontsize=10)
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')

# --- RIGHT: Top view (X-Y) with Z coloring ---
ax2 = axes[1]
ax2.set_facecolor(BG)
sc2 = ax2.scatter(xs[::step], ys[::step], c=zsc[::step], s=0.3, alpha=0.4,
                  cmap=cmap, vmin=-4, vmax=5, rasterized=True)
ax2.scatter(xf[::3], yf[::3], c='#FF6B35', s=2.0, alpha=0.9, rasterized=True)
ax2.plot(cam_pos[:,0], cam_pos[:,1], color='#FFD700', linewidth=2, alpha=0.9, zorder=5, label='Camera path')
ax2.scatter(cam_pos[:,0], cam_pos[:,1], c='#FFD700', s=10, zorder=6)
ax2.set_xlabel("X (m)  — 카메라 이동 방향", color='white', fontsize=11)
ax2.set_ylabel("Y (m)  — 좌우 방향", color='white', fontsize=11)
ax2.set_title("Top View (X-Y)\n오렌지 = Pop2 floater (Z>+2m)", color='white', fontsize=13, fontweight='bold', pad=10)
ax2.tick_params(colors='white')
for spine in ax2.spines.values(): spine.set_edgecolor('#334455')
ax2.legend(loc='upper right', fontsize=9, facecolor='#1A2B3C', labelcolor='white', framealpha=0.8)
ax2.set_xlim(-20, 20)
ax2.set_ylim(-18, 10)
cbar2 = fig.colorbar(sc2, ax=ax2, fraction=0.03, pad=0.02)
cbar2.set_label('Z (m)', color='white', fontsize=10)
cbar2.ax.yaxis.set_tick_params(color='white')
plt.setp(cbar2.ax.yaxis.get_ticklabels(), color='white')

# Stats annotation
n_floater = mask_floater.sum()
n_total = mask_scene.sum()
pct = 100 * n_floater / len(x)
fig.text(0.5, 0.02,
         f"Total Gaussians: {len(x):,}  |  Pop2 floaters (Z>+2m): {n_floater:,} ({pct:.1f}%)  |  exp08 PSNR@30k = 33.012 dB",
         ha='center', color='#B0BEC5', fontsize=11)

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig(str(OUT), dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print(f"Saved: {OUT}")
