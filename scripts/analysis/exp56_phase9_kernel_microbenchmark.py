#!/usr/bin/env python3
"""exp56 Phase 9 -- "iter당 고정비"가 CUDA 커널 레벨에서 진짜 N-무관인지 직접
프로파일링으로 검증. 같은 카메라(n_view=1 view-op)에 대해 gaussian 개수만
10k/30k/60k/90k(실제 exp56 최종 체크포인트 크기)로 바꿔가며 forward+backward를
torch.profiler(CUDA activity)로 커널 단위 분해 -- Phase0/5가 말한 "고정비"가
launch overhead인지, 아니면 우리가 못 잡아낸 N-비례 항인지 확인. 상세 결과/해석은
context/experiments/exp56_mapping_fixedcost_reduction.md Phase 9 참조.

실행 (vigs-slam-5090 conda env, VIGS-SLAM repo 안에서):
  python exp56_phase9_kernel_microbenchmark.py         # 커널별 breakdown (N별)
  python exp56_phase9_kernel_microbenchmark.py full     # N=90770 전체 CUDA 이벤트 나열
  python exp56_phase9_kernel_microbenchmark.py wall     # 순수 wall-clock 교차검증 (ground truth)

주의: torch.profiler의 key_averages()에서 모든 이벤트의 device_time_total을 그냥
합산하면 C++ 확장 wrapper(_RasterizeGaussians[Backward])가 자식 커널 시간을
self_device_time에 중복 합산해 총합이 부풀려짐(N=90770에서 8.39ms vs 실제
wall-clock 3.43ms, 2.4배 과대) -- `wall` 모드의 순수 wall-clock 수치를 ground
truth로 쓸 것.
"""
import sys, os
sys.path.append("/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM/vigs")
import numpy as np
import torch
from plyfile import PlyData
from scipy.spatial.transform import Rotation as R

from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.renderer import render

PLY = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp56_ax8_camcache/3dgs_before_final.ply"
RUN_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp56_ax8_camcache"


def load_gaussians(ply_path, n_subsample=None, seed=0):
    p = PlyData.read(ply_path)
    v = p.elements[0]
    xyz = np.stack([np.asarray(v["x"]), np.asarray(v["y"]), np.asarray(v["z"])], axis=1)
    opacities = np.asarray(v["opacity"])[..., np.newaxis]
    features_dc = np.zeros((xyz.shape[0], 3, 1))
    features_dc[:, 0, 0] = np.asarray(v["f_dc_0"])
    features_dc[:, 1, 0] = np.asarray(v["f_dc_1"])
    features_dc[:, 2, 0] = np.asarray(v["f_dc_2"])
    scale_names = sorted([pr.name for pr in v.properties if pr.name.startswith("scale_")], key=lambda x: int(x.split("_")[-1]))
    scales = np.stack([np.asarray(v[n]) for n in scale_names], axis=1)
    rot_names = sorted([pr.name for pr in v.properties if pr.name.startswith("rot")], key=lambda x: int(x.split("_")[-1]))
    rots = np.stack([np.asarray(v[n]) for n in rot_names], axis=1)

    N = xyz.shape[0]
    if n_subsample is not None and n_subsample < N:
        rng = np.random.default_rng(seed)
        idx = rng.choice(N, size=n_subsample, replace=False)
        xyz, opacities, features_dc, scales, rots = xyz[idx], opacities[idx], features_dc[idx], scales[idx], rots[idx]

    class G:
        pass
    g = G()
    g._xyz = torch.tensor(xyz, dtype=torch.float, device="cuda")
    g._features_dc = torch.tensor(features_dc, dtype=torch.float, device="cuda").transpose(1, 2).contiguous()
    g._features_rest = torch.zeros((g._xyz.shape[0], 0, 3), dtype=torch.float, device="cuda")
    g._opacity = torch.tensor(opacities, dtype=torch.float, device="cuda")
    g._scaling = torch.tensor(scales, dtype=torch.float, device="cuda")
    g._rotation = torch.tensor(rots, dtype=torch.float, device="cuda")
    g.max_sh_degree = 0
    g.active_sh_degree = 0
    g.scaling_activation = torch.exp
    g.opacity_activation = torch.sigmoid
    g.rotation_activation = torch.nn.functional.normalize
    # requires_grad on the leaf tensors actually used by render()
    for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
        t.requires_grad_(True)
    # get_* must be recomputed fresh every call (not cached) -- otherwise the activation
    # op's graph node is shared across loop iterations and the 2nd backward() errors
    # ("backward through the graph a second time").
    type(g).get_xyz = property(lambda self: self._xyz)
    type(g).get_scaling = property(lambda self: self.scaling_activation(self._scaling))
    type(g).get_rotation = property(lambda self: self.rotation_activation(self._rotation))
    type(g).get_opacity = property(lambda self: self.opacity_activation(self._opacity))
    type(g).get_features = property(lambda self: torch.cat((self._features_dc, self._features_rest), dim=1))
    return g


def build_camera():
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    row = traj[len(traj) // 2]
    tx, ty, tz, qx, qy, qz, qw = row[1:8]
    T_c2w = np.eye(4)
    T_c2w[:3, :3] = R.from_quat([qx, qy, qz, qw]).as_matrix()
    T_c2w[:3, 3] = [tx, ty, tz]
    pose = torch.tensor(np.linalg.inv(T_c2w), dtype=torch.float32, device="cuda")
    W, H = 1024, 1024
    fx, fy, cx, cy = float(K[0]), float(K[1]), float(K[2]), float(K[3])
    Kfull = [fx, fy, cx, cy, W, H]
    projection_matrix = getProjectionMatrix2(znear=0.01, zfar=100.0, fx=fx, fy=fy, cx=cx, cy=cy, W=W, H=H).transpose(0, 1).cuda()
    return Camera.init_from_tracking(None, None, None, pose, 0, projection_matrix, Kfull)


def profile_at_n(n, cam, n_warmup=3, n_iters=8):
    g = load_gaussians(PLY, n_subsample=n)
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")

    for _ in range(n_warmup):
        pkg = render(cam, g, bg)
        loss = pkg["render"].sum()
        loss.backward()
        for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
            t.grad = None
    torch.cuda.synchronize()

    from torch.profiler import profile, ProfilerActivity
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        for _ in range(n_iters):
            pkg = render(cam, g, bg)
            loss = pkg["render"].sum()
            loss.backward()
            for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
                t.grad = None
        torch.cuda.synchronize()

    events = prof.key_averages()
    # keep only CUDA kernels (not aten:: aggregate ops), matched by our rasterizer's own kernel names
    kernel_names = ["preprocessCUDA", "renderCUDA", "computeCov2DCUDA", "duplicateWithKeys",
                     "identifyTileRanges", "DeviceRadixSort", "DeviceScan", "InclusiveSum", "SortPairs"]
    rows = []
    total_cuda_us = 0.0
    for ev in events:
        total_cuda_us += ev.device_time_total
    for ev in events:
        if any(k in ev.key for k in kernel_names):
            rows.append((ev.key, ev.device_time_total / n_iters, ev.count / n_iters))
    rows.sort(key=lambda r: -r[1])
    return rows, total_cuda_us / n_iters


if __name__ == "__main__":
    cam = build_camera()
    Ns = [10000, 30000, 60000, 90770]
    all_results = {}
    for n in Ns:
        print(f"\n{'='*70}\nN = {n}\n{'='*70}")
        rows, total_us = profile_at_n(n, cam)
        all_results[n] = (rows, total_us)
        print(f"  total CUDA time/iter: {total_us/1000:.3f} ms")
        for key, us_per_iter, cnt in rows[:12]:
            print(f"  {key:40s} {us_per_iter/1000:8.4f} ms/iter  (calls/iter={cnt:.1f})")

    print(f"\n\n{'='*70}\nSUMMARY: 커널별 시간이 N에 따라 어떻게 변하는가\n{'='*70}")
    # union of kernel keys across all N
    all_keys = set()
    for rows, _ in all_results.values():
        for key, _, _ in rows:
            all_keys.add(key)
    print(f"{'kernel':40s} " + "  ".join(f"N={n:>6d}" for n in Ns))
    for key in sorted(all_keys):
        vals = []
        for n in Ns:
            rows, _ = all_results[n]
            match = [r for r in rows if r[0] == key]
            vals.append(match[0][1] / 1000 if match else 0.0)
        print(f"{key:40s} " + "  ".join(f"{v:8.4f}" for v in vals))
    print(f"{'TOTAL':40s} " + "  ".join(f"{all_results[n][1]/1000:8.4f}" for n in Ns))

def profile_full_breakdown(n, cam, n_warmup=3, n_iters=8):
    """모든 CUDA 이벤트(named kernel 필터 없이) 상위 항목 출력 -- 65% 미계측분 정체 확인."""
    g = load_gaussians(PLY, n_subsample=n)
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    for _ in range(n_warmup):
        pkg = render(cam, g, bg)
        pkg["render"].sum().backward()
        for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
            t.grad = None
    torch.cuda.synchronize()
    from torch.profiler import profile, ProfilerActivity
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        for _ in range(n_iters):
            pkg = render(cam, g, bg)
            pkg["render"].sum().backward()
            for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
                t.grad = None
        torch.cuda.synchronize()
    events = prof.key_averages()
    rows = [(ev.key, ev.device_time_total / n_iters, ev.count / n_iters, ev.self_device_time_total / n_iters) for ev in events if ev.device_time_total > 0]
    rows.sort(key=lambda r: -r[3])
    print(f"\n[FULL breakdown, self_device_time 기준 정렬] N={n}")
    tot_self = sum(r[3] for r in rows)
    print(f"  sum(self_device_time_total)/iter = {tot_self/1000:.4f} ms")
    for key, dev_tot, cnt, self_dev in rows[:25]:
        print(f"  {key[:70]:70s} self={self_dev/1000:8.4f}ms  total={dev_tot/1000:8.4f}ms  n={cnt:.0f}")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "full":
    cam = build_camera()
    profile_full_breakdown(90770, cam)

def wallclock_at_n(n, cam, n_warmup=5, n_iters=20):
    """profiler 없이 순수 wall-clock(cuda synchronize 기준)으로 forward/backward 각각 측정.
    -- profiler self_device_time 합산이 _RasterizeGaussians(Backward) 래퍼와 그 안의
    named 커널을 이중 계산하는 걸 발견해서, 이중계산 없는 ground-truth로 교차검증."""
    import time
    g = load_gaussians(PLY, n_subsample=n)
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    for _ in range(n_warmup):
        pkg = render(cam, g, bg)
        pkg["render"].sum().backward()
        for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
            t.grad = None
    torch.cuda.synchronize()

    fwd_times, bwd_times = [], []
    for _ in range(n_iters):
        torch.cuda.synchronize(); t0 = time.perf_counter()
        pkg = render(cam, g, bg)
        torch.cuda.synchronize(); t1 = time.perf_counter()
        loss = pkg["render"].sum()
        loss.backward()
        torch.cuda.synchronize(); t2 = time.perf_counter()
        for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
            t.grad = None
        fwd_times.append((t1 - t0) * 1000)
        bwd_times.append((t2 - t1) * 1000)
    return np.median(fwd_times), np.median(bwd_times)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "wall":
    cam = build_camera()
    print(f"{'N':>8s} {'fwd(ms)':>10s} {'bwd(ms)':>10s} {'total(ms)':>10s}")
    for n in [10000, 30000, 60000, 90770]:
        fwd, bwd = wallclock_at_n(n, cam)
        print(f"{n:8d} {fwd:10.4f} {bwd:10.4f} {fwd+bwd:10.4f}")
