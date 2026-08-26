#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#
# train.py
# -----------------------------------------------------------------------------
# REVIEW (이 파일 한눈에 보기)
# -----------------------------------------------------------------------------
# 이 스크립트는 3D Gaussian Splatting의 "학습 루프"를 담당합니다.
#
# 큰 흐름:
#   1) Scene / GaussianModel 생성 및 optimizer 세팅
#   2) 매 iteration마다 랜덤 카메라(viewpoint) 하나 뽑아서 render
#   3) render 결과 vs GT 이미지로 loss 계산 (L1 + DSSIM, + optional depth reg)
#   4) backward
#   5) (densification 구간이면) gaussians를 늘리거나(prune/densify) opacity reset
#   6) optimizer step + 주기적 저장/테스트
#
# 핵심 키워드:
#   - render() 가 미분 가능(differentiable)하게 2D rasterization을 수행
#   - densify_and_prune() 가 포인트 수를 "학습 중"에 조절(성능의 핵심)
# -----------------------------------------------------------------------------

# ACTIVE (coverage scheduling test, exp66): copy of train.py (the validated batch
# 3DGS path, exp01-47) with view_selector={default,coverage} added. --view_selector
# default is byte-identical to the original file's behavior. See "# ACTIVE:" markers
# for every diff.
import os
import sys
import random as _random_mod
import numpy as np
import torch
from pathlib import Path
from random import randint
sys.path.insert(0, "/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom")  # ACTIVE: this file lives outside 3dgs-custom
sys.path.insert(0, "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/scripts/incremental")  # ACTIVE
from coverage_buffer import SparseCoverageBuffer  # ACTIVE
from utils.loss_utils import l1_loss, ssim
# REVIEW: loss_utils의 ssim은 보통 "SSIM" 반환(높을수록 유사).
# 여기선 (1-SSIM)을 loss로 씁니다. 즉 SSIM을 최대화하는 것과 동일.

from gaussian_renderer import render, network_gui
from scene import Scene, GaussianModel
from utils.general_utils import safe_state, get_expon_lr_func
import uuid
from tqdm import tqdm
from utils.image_utils import psnr
from argparse import ArgumentParser, Namespace
from arguments import ModelParams, PipelineParams, OptimizationParams
from eval.depth_ambiguity import normalized_ambiguity_image, summarize_depth_ambiguity
from eval.gaussian_stats import load_sparse_points, save_gaussian_summary, summarize_gaussians
from eval.sparse_depth_prior import SparseDepthPrior
from eval.plateau_loss import PlateauLoss, PlateauLossConfig
from eval.carve_loss import CarveLoss, CarveLossConfig

try:
    # REVIEW: TensorBoard는 "있으면 쓰고 없으면 안 씀" (optional dependency)
    # 따라서 서버 환경/conda 환경에 따라 로깅이 조용히 꺼질 수 있음.
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_FOUND = True
except ImportError:
    TENSORBOARD_FOUND = False

try:
    # REVIEW: fused_ssim이 있으면 ssim 계산을 더 빠르게(커스텀 CUDA/확장) 수행.
    # 없으면 파이썬 구현/일반 구현 ssim() 사용.
    from fused_ssim import fused_ssim
    FUSED_SSIM_AVAILABLE = True
except:
    FUSED_SSIM_AVAILABLE = False

try:
    # REVIEW: SparseGaussianAdam은 "보이는 가우시안만" 업데이트해서 속도/메모리 최적화.
    # diff_gaussian_rasterization(가속 rasterizer) 설치가 되어 있어야 함.
    # opt.optimizer_type == "sparse_adam" 일 때만 사용.
    from diff_gaussian_rasterization import SparseGaussianAdam
    SPARSE_ADAM_AVAILABLE = True
except:
    SPARSE_ADAM_AVAILABLE = False

def frustum_visible_mask(means, camera, margin=1.15):  # ACTIVE: cheap frustum-only visibility for scoring, no rasterization
    ones = torch.ones(means.shape[0], 1, device=means.device, dtype=means.dtype)
    means_h = torch.cat([means, ones], dim=-1)
    clip = means_h @ camera.full_proj_transform
    w = clip[:, 3]
    in_front = w > camera.znear
    ndc_x = clip[:, 0] / w.clamp_min(1e-6)
    ndc_y = clip[:, 1] / w.clamp_min(1e-6)
    return in_front & (ndc_x.abs() <= margin) & (ndc_y.abs() <= margin)


def score_pool(buf, cams, gaussians_xyz):  # ACTIVE
    candidates = []
    for cam in cams:
        vis = frustum_visible_mask(gaussians_xyz, cam)
        candidates.append((gaussians_xyz[vis], cam.camera_center))
    return buf.score(candidates)


def training(dataset, opt, pipe, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint, debug_from, wandb_logger=None, plateau_loss_config=None, carve_loss_config=None,
             view_selector="default", coverage_rescore_every=50):  # ACTIVE: two new params, both default to original behavior
    # -------------------------------------------------------------------------
    # REVIEW: training() 인자 의미
    #   dataset : 데이터/카메라/이미지/옵션(white_background 등) 포함
    #   opt     : OptimizationParams (iterations, lr schedule, densify 설정 등)
    #   pipe    : PipelineParams (SH 계산 방식, covariance 계산 방식, debug 등)
    #   testing_iterations : 테스트/리포트 수행 iteration 리스트
    #   saving_iterations  : 결과 저장 iteration 리스트
    #   checkpoint_iterations : 체크포인트 저장 iteration 리스트
    #   checkpoint : 재개(restore)할 체크포인트 경로
    #   debug_from : 특정 iteration부터 pipe.debug 켜서 디버깅
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # REVIEW: 1. 초기화 및 준비 단계
    # 데이터셋을 불러오고, 가우시안 모델을 세팅하며, 최적화(Optimizer)를 준비합니다.
    # -------------------------------------------------------------------------

    # Sparse Adam 옵션을 켰으나 설치되지 않은 경우 에러를 띄우고 종료합니다.
    if not SPARSE_ADAM_AVAILABLE and opt.optimizer_type == "sparse_adam":
        sys.exit(f"Trying to use sparse adam but it is not installed, please install the correct rasterizer using pip install [3dgs_accel].")

    first_iter = 0
    # 텐서보드 로거나 출력 폴더를 준비합니다.
    tb_writer = prepare_output_and_logger(dataset)

    # 가우시안 포인트들을 관리하는 핵심 클래스입니다. (SH degree, Optimizer 종류 설정)
    gaussians = GaussianModel(dataset.sh_degree, opt.optimizer_type)

    # Scene 클래스는 데이터셋(카메라, 이미지, 초기 포인트 클라우드)을 로드하고 가우시안 모델에 바인딩합니다.
    scene = Scene(dataset, gaussians)
    gaussians.training_setup(opt)

    # 이전에 멈춘 체크포인트(.pth)가 있다면 로드하여 학습 상태(iter, 파라미터)를 복원합니다.
    if checkpoint:
        (model_params, first_iter) = torch.load(checkpoint, weights_only=False)
        gaussians.restore(model_params, opt)
        
        # 계측·계보 버퍼는 checkpoint에 없으면 복원된 gaussian 수에 맞춰 재생성
        _n = gaussians._xyz.shape[0]
        for _name, _shape in (("accum_rgb_grad", (_n,)), ("accum_rgb_grad_vec", (_n, 3)),
                              ("accum_plateau_grad", (_n,)), ("accum_visibility", (_n,)),
                              ("birth_step", (_n,)), ("generation", (_n,)),
                              ("num_splits", (_n,)), ("num_clones", (_n,))):
            if hasattr(gaussians, _name) and getattr(gaussians, _name).shape[0] != _n:
                _old = getattr(gaussians, _name)
                setattr(gaussians, _name, torch.zeros(_shape, dtype=_old.dtype, device="cuda"))
        if hasattr(gaussians, "ancestor_idx") and gaussians.ancestor_idx.shape[0] != _n:
            gaussians.ancestor_idx = torch.arange(_n, dtype=gaussians.ancestor_idx.dtype, device="cuda")

    # 배경색 설정 (데이터셋 옵션에 따라 흰색 또는 검은색)
    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    # GPU 연산 시간을 측정하기 위한 CUDA Event 객체
    iter_start = torch.cuda.Event(enable_timing = True)
    iter_end = torch.cuda.Event(enable_timing = True)

    use_sparse_adam = opt.optimizer_type == "sparse_adam" and SPARSE_ADAM_AVAILABLE 
    # Depth 기반의 정규화(Regularization) loss를 사용할 경우, 학습 진행에 따른 가중치 감소 함수를 설정합니다.
    depth_l1_weight = get_expon_lr_func(opt.depth_l1_weight_init, opt.depth_l1_weight_final, max_steps=opt.iterations)
    sparse_depth_weight = get_expon_lr_func(
        getattr(opt, "sparse_depth_weight_init", 0.0),
        getattr(opt, "sparse_depth_weight_final", 0.0),
        max_steps=opt.iterations,
    )

    # 학습에 사용할 카메라 뷰포인트들을 리스트(스택)로 복사해옵니다.
    viewpoint_stack = scene.getTrainCameras().copy()
    viewpoint_indices = list(range(len(viewpoint_stack)))

    # ACTIVE: full camera set known from the start (batch, not streaming) -- no
    # sliding window / IMU-gating / cold-start logic needed, unlike the incremental
    # harness. Score the WHOLE train set every coverage_rescore_every iterations.
    all_train_cams = scene.getTrainCameras().copy()
    buf = SparseCoverageBuffer(device="cuda")
    pool_weights = None

    # 로깅을 위한 지수 이동 평균(EMA) 변수
    ema_loss_for_log = 0.0
    ema_Ll1depth_for_log = 0.0
    ema_sparse_depth_for_log = 0.0

    # 학습 진행률을 보여주는 tqdm 프로그레스 바
    progress_bar = tqdm(range(first_iter, opt.iterations), desc="Training progress")
    first_iter += 1
    # Plateau loss (optional — controlled by --plateau_loss_config YAML)
    if plateau_loss_config is not None:
        _pl_cfg = PlateauLossConfig.from_yaml(plateau_loss_config)
        plateau_loss = PlateauLoss(_pl_cfg, dataset.source_path)
    else:
        plateau_loss = PlateauLoss(PlateauLossConfig(enabled=False), dataset.source_path)

    # Carve loss (optional — controlled by --carve_loss_config YAML)
    if carve_loss_config is not None:
        carve_loss = CarveLoss(CarveLossConfig.from_yaml(carve_loss_config), dataset.source_path)
    else:
        carve_loss = CarveLoss(CarveLossConfig(enabled=False), dataset.source_path)

    sparse_points = load_sparse_points(dataset.source_path)
    sparse_depth_prior = SparseDepthPrior(
        sparse_points,
        max_points_per_view=int(getattr(opt, "sparse_depth_max_points", 2048)),
        global_max_points=int(getattr(opt, "sparse_depth_global_max_points", 100000)),
        min_depth=float(getattr(opt, "sparse_depth_min_depth", 0.2)),
        require_rendered=bool(getattr(opt, "sparse_depth_require_rendered", True)),
    )
    
    # -------------------------------------------------------------------------
    # REVIEW: 2. 메인 학습 루프 시작
    # 매 이터레이션마다 카메라 1개를 뽑아 렌더링하고, 실제 이미지와 비교해 Loss를 구합니다.
    # -------------------------------------------------------------------------
    for iteration in range(first_iter, opt.iterations + 1):
        # [GUI 처리 로직] SIBR 실시간 뷰어와 통신하여 현재 화면을 렌더링해서 보내거나 조작을 받습니다.
        if network_gui.conn == None:
            network_gui.try_connect()
        while network_gui.conn != None:
            try:
                net_image_bytes = None
                custom_cam, do_training, pipe.convert_SHs_python, pipe.compute_cov3D_python, keep_alive, scaling_modifer = network_gui.receive()
                if custom_cam != None:
                    net_image = render(custom_cam, gaussians, pipe, background, scaling_modifier=scaling_modifer, use_trained_exp=dataset.train_test_exp, separate_sh=SPARSE_ADAM_AVAILABLE)["render"]
                    net_image_bytes = memoryview((torch.clamp(net_image, min=0, max=1.0) * 255).byte().permute(1, 2, 0).contiguous().cpu().numpy())
                network_gui.send(net_image_bytes, dataset.source_path)
                if do_training and ((iteration < int(opt.iterations)) or not keep_alive):
                    break
            except Exception as e:
                network_gui.conn = None

        iter_start.record()

        # 설정된 스케줄에 따라 가우시안 중심점(XYZ)의 Learning Rate를 점진적으로 줄입니다.
        gaussians.update_learning_rate(iteration)

        # 1000 이터레이션마다 Spherical Harmonics(SH, 보는 각도에 따른 색상 변화 표현)의 차수를 높입니다.
        # 처음부터 고차원 SH를 학습하면 불안정하므로 점진적으로 디테일을 올리는 기법입니다.
        # Every 1000 its we increase the levels of SH up to a maximum degree
        if iteration % 1000 == 0:
            gaussians.oneupSHdegree()

        # ACTIVE: view_selector switch. "default" branch below is byte-identical
        # to the original file (shuffled-stack, no-replacement-per-epoch).
        if view_selector == "coverage":
            if pool_weights is None or iteration % coverage_rescore_every == 0:
                with torch.no_grad():
                    pool_weights = score_pool(buf, all_train_cams, gaussians._xyz.detach())
            viewpoint_cam = _random_mod.choices(all_train_cams, weights=pool_weights, k=1)[0]
        else:
            # 스택에서 무작위로 카메라 뷰포인트 하나를 뽑습니다. (비어있으면 다시 채움)
            # Pick a random Camera
            if not viewpoint_stack:
                viewpoint_stack = scene.getTrainCameras().copy()
                viewpoint_indices = list(range(len(viewpoint_stack)))
            rand_idx = randint(0, len(viewpoint_indices) - 1)
            viewpoint_cam = viewpoint_stack.pop(rand_idx)
            vind = viewpoint_indices.pop(rand_idx)

        # Render
        if (iteration - 1) == debug_from:
            pipe.debug = True

        # 배경을 랜덤으로 할지 고정색으로 할지 결정합니다.
        bg = torch.rand((3), device="cuda") if opt.random_background else background

        # -------------------------------------------------------------------------
        # REVIEW: 3. 렌더링 (Forward Pass)
        # 선택된 카메라 위치에서 현재 가우시안들을 2D 이미지로 Rasterization 합니다.
        # 이 함수는 미분 가능(differentiable)하므로 역전파가 가능합니다.
        # -------------------------------------------------------------------------
        render_pkg = render(viewpoint_cam, gaussians, pipe, bg, use_trained_exp=dataset.train_test_exp, separate_sh=SPARSE_ADAM_AVAILABLE)
        # 렌더링된 2D 이미지
        image = render_pkg["render"]                                # 렌더링된 2D 이미지
        viewspace_point_tensor = render_pkg["viewspace_points"]     # 2D 화면상 가우시안 중심 좌표 (기울기 누적용)
        visibility_filter = render_pkg["visibility_filter"]         # 현재 뷰에서 보이는 가우시안 마스크
        radii = render_pkg["radii"]                                 # 화면에 투영된 가우시안의 2D 반지름

        # ACTIVE: buffer bookkeeping every iteration regardless of selector (so
        # "coverage" mode always has a live buffer to score against). NOTE:
        # render_pkg["visibility_filter"] in this codebase is `(radii>0).nonzero()`,
        # an index tensor -- NOT a bool mask (see coverage_buffer.py's own shape
        # check, added after this exact mistake crashed the incremental harness).
        with torch.no_grad():
            _vis_bool = radii > 0
            buf.update(gaussians._xyz[_vis_bool].detach(), viewpoint_cam.camera_center.detach())

        # 객체 마스킹(배경 제거 등) 옵션이 있다면 적용합니다. -> 자동으로 RGBA로 들어오면 alpha mask적용해서 학습하는 듯?
        if viewpoint_cam.alpha_mask is not None:
            alpha_mask = viewpoint_cam.alpha_mask.cuda()
            image *= alpha_mask

        # Loss
        # -------------------------------------------------------------------------
        # REVIEW: 4. Loss 계산 및 역전파 (Backward Pass)
        # 렌더링 이미지와 Ground Truth(실제 정답) 이미지를 비교합니다.
        # -------------------------------------------------------------------------
        gt_image = viewpoint_cam.original_image.cuda()

        # 픽셀 단위의 L1 Loss
        Ll1 = l1_loss(image, gt_image)

        # exp46 축7: 원거리 photometric 감쇠 (env-gated, 미설정 시 기존 동작 그대로)
        #   w(z) = 1/(1+(z/z0)^k), z0=장면별 round9 분위수(m). 먼 픽셀의 L1 보상↓ → 먼 floater 숏컷 약화.
        _far_z0 = float(os.environ.get("FAR_ATTEN_Z0", "0"))
        if _far_z0 > 0:
            _far_k = float(os.environ.get("FAR_ATTEN_K", "4"))
            _zmap = render_pkg["depth"].detach()               # [1,H,W]
            _w = 1.0 / (1.0 + (_zmap.clamp(min=1e-3) / _far_z0) ** _far_k)
            _w = _w / _w.mean().clamp(min=1e-6)                 # 스케일 보존(lambda_dssim 균형 유지)
            Ll1 = (_w * torch.abs(image - gt_image)).mean()

        # exp46 축7b (사용자): 최대 거리 하드 컷오프 — 렌더 깊이가 z_max보다 먼 픽셀은
        #   1px footprint가 뭉개질 만큼 멀어 photometric 신호가 불신 → 그 픽셀 L1 제외.
        #   (먼 gaussian이 개별 픽셀을 억지로 맞추다 floater 되는 것을 차단하는 취지)
        _far_zmax = float(os.environ.get("FAR_ATTEN_ZMAX", "0"))
        if _far_zmax > 0:
            _zmap = render_pkg["depth"].detach()
            _m = (_zmap < _far_zmax).float()                   # 가까운 픽셀만 1
            _m = _m / _m.mean().clamp(min=1e-6)
            Ll1 = (_m * torch.abs(image - gt_image)).mean()
        
        # 구조적 유사도(SSIM) Loss 계산 (FUSED_SSIM이 빠름)
        if FUSED_SSIM_AVAILABLE:
            ssim_value = fused_ssim(image.unsqueeze(0), gt_image.unsqueeze(0))
        else:
            ssim_value = ssim(image, gt_image)

        # 최종 Loss = L1 Loss와 DSSIM(1-SSIM)의 가중합
        loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim_value)

        # (선택적) Depth 정규화: 단안(Monocular) Depth 맵이 있다면 3D 구조를 더 잘 잡도록 도와줍니다.
        # ---------------------------------------------------------------------
        # Depth regularization (깊이 정규화 / 선택적)
        #
        # 목적:
        #   RGB 재구성(loss: L1 + SSIM)만으로도 학습은 되지만,
        #   텍스처가 약하거나 반복무늬/무텍스처 영역에서는 깊이(3D 구조)가 흔들릴 수 있음.
        #   그래서 "외부에서 얻은 단안 depth(prior)"와 렌더된 depth를 맞추는 보조 loss를 추가함.
        #
        # 왜 depth가 아니라 inverse depth(1/depth)를 쓰나?
        #   - 원근 카메라에서는 가까운 곳의 depth 변화가 더 중요하고 민감함
        #   - inverse depth는 가까운 영역의 차이를 더 크게 반영해 최적화가 안정적인 편
        #
        # depth_l1_weight(iteration):
        #   - iteration에 따라 depth loss 가중치를 스케줄링(초반/후반 영향 조절)
        #
        # viewpoint_cam.depth_reliable:
        #   - 이 뷰의 depth prior가 믿을만한지(깨짐/결측/노이즈 심함 등) 표시
        #   - False면 depth loss를 아예 건너뜀
        # ---------------------------------------------------------------------
        # Depth regularization
        Ll1depth_pure = 0.0
        if depth_l1_weight(iteration) > 0 and viewpoint_cam.depth_reliable:
            # render_pkg["depth"]:
            #   - 현재 Gaussian 장면을 이 카메라에서 렌더링했을 때의 "예측 inverse depth" (모델 출력)
            invDepth = render_pkg["depth"]

            # viewpoint_cam.invdepthmap:
            #   - 데이터셋에서 제공되는 "단안 inverse depth prior" (정답이라기보단 힌트/규제항)
            mono_invdepth = viewpoint_cam.invdepthmap.cuda()

            # depth_mask:
            #   - depth prior가 유효한 픽셀만 1, 나머지는 0 (결측/무효 영역 제외)
            depth_mask = viewpoint_cam.depth_mask.cuda()

            # 픽셀 단위 L1: |invDepth - mono_invdepth|
            # 마스크를 곱해서 유효한 픽셀만 남기고,
            # mean()으로 전체 평균을 내서 스칼라 loss로 만듦
            Ll1depth_pure = torch.abs((invDepth  - mono_invdepth) * depth_mask).mean()

            # 스케줄 가중치 적용 (iteration에 따라 depth 규제가 강해지거나 약해짐)
            Ll1depth = depth_l1_weight(iteration) * Ll1depth_pure 
            # 최종 loss에 더해줌 (RGB loss + depth loss)
            loss += Ll1depth
            # 로그 출력을 위해 파이썬 float로 변환
            Ll1depth = Ll1depth.item()
        else:
            # depth loss를 사용하지 않는 경우(가중치=0 or depth가 unreliable)
            Ll1depth = 0

        sparse_depth_raw = 0.0
        sparse_depth_points = 0
        sparse_depth_abs = 0.0
        sparse_depth_loss_value = 0.0
        current_sparse_depth_weight = sparse_depth_weight(iteration)
        if current_sparse_depth_weight > 0 and sparse_depth_prior.available:
            sparse_depth_raw_tensor, sparse_depth_points, sparse_depth_abs = sparse_depth_prior.loss(
                render_pkg["depth"],
                viewpoint_cam,
            )
            sparse_depth_loss = current_sparse_depth_weight * sparse_depth_raw_tensor
            loss += sparse_depth_loss
            sparse_depth_raw = float(sparse_depth_raw_tensor.detach().item())
            sparse_depth_loss_value = float(sparse_depth_loss.detach().item())

        # Plateau loss — applies to ALL Gaussians (cyclic subset), not just visible ones
        loss_rgb = loss
        
        # 1단계: RGB & Depth Loss Backward (Photometric Gradient 누적)
        loss_rgb.backward(retain_graph=True)
        if gaussians._xyz.grad is not None:
            gaussians.accum_rgb_grad += gaussians._xyz.grad.norm(dim=-1)
            gaussians.accum_rgb_grad_vec += gaussians._xyz.grad
            rgb_xyz_grad = gaussians._xyz.grad.clone()
            # xyz의 gradient만 0으로 초기화 (다른 파라미터의 grad는 유지)
            gaussians._xyz.grad.zero_()
        else:
            rgb_xyz_grad = None

        # 2단계: Plateau Loss Backward (Plateau Gradient 누적)
        L_plateau, plateau_metrics = plateau_loss.compute_loss(gaussians, iteration)
        if L_plateau is not None:
            loss_plateau_weighted = plateau_loss._lambda_at(iteration) * L_plateau
            loss_plateau_weighted.backward()
            if gaussians._xyz.grad is not None:
                gaussians.accum_plateau_grad += gaussians._xyz.grad.norm(dim=-1)
            loss = loss_rgb + loss_plateau_weighted
        else:
            loss = loss_rgb

        # 2.5단계: Carve loss backward (opacity 전용 gradient — xyz 저글링과 무간섭)
        L_carve, carve_metrics = carve_loss.compute_loss(gaussians, iteration)
        if L_carve is not None:
            L_carve.backward()
            loss = loss + L_carve.detach()

        # 3단계: RGB xyz gradient를 최종 합산하여 Optimizer Step을 준비
        if rgb_xyz_grad is not None:
            if gaussians._xyz.grad is not None:
                gaussians._xyz.grad += rgb_xyz_grad
            else:
                gaussians._xyz.grad = rgb_xyz_grad

        iter_end.record()
        # -------------------------------------------------------------------------
        # REVIEW: 5. 최적화 및 구조 변경 (No Grad 블록)
        # 기울기를 반영하고, 필요에 따라 가우시안을 쪼개거나 삭제합니다.
        # -------------------------------------------------------------------------
        with torch.no_grad():
            # 진행 바 업데이트용 Loss 기록
            ema_loss_for_log = 0.4 * loss.item() + 0.6 * ema_loss_for_log
            ema_Ll1depth_for_log = 0.4 * Ll1depth + 0.6 * ema_Ll1depth_for_log
            ema_sparse_depth_for_log = 0.4 * sparse_depth_loss_value + 0.6 * ema_sparse_depth_for_log

            if iteration % 10 == 0:
                progress_bar.set_postfix({
                    "Loss": f"{ema_loss_for_log:.{7}f}",
                    "Depth Loss": f"{ema_Ll1depth_for_log:.{7}f}",
                    "Sparse Depth": f"{ema_sparse_depth_for_log:.{7}f}",
                })
                progress_bar.update(10)
            if iteration == opt.iterations:
                progress_bar.close()

            ambiguity_log_interval = int(getattr(opt, "ambiguity_log_interval", 2000))
            if wandb_logger and wandb_logger.enabled and ambiguity_log_interval > 0 and iteration % ambiguity_log_interval == 0:
                ambiguity_metrics = summarize_depth_ambiguity(render_pkg["alpha_depth"], render_pkg["modes"])
                train_psnr = psnr(image.unsqueeze(0), gt_image.unsqueeze(0)).mean()
                ambiguity_metrics.update({
                    "train/psnr": float(train_psnr.item()),
                    "train/ssim": float(ssim_value.detach().item()),
                    "train/l1_loss": float(Ll1.detach().item()),
                    "train/total_loss": float(loss.detach().item()),
                    "train/sparse_depth_loss": sparse_depth_loss_value,
                    "train/sparse_depth_raw": sparse_depth_raw,
                    "train/sparse_depth_abs": sparse_depth_abs,
                    "train/sparse_depth_points": sparse_depth_points,
                    "train/sparse_depth_weight": float(current_sparse_depth_weight),
                })
                ambiguity_metrics.update(plateau_metrics)
                ambiguity_metrics.update(carve_metrics)
                wandb_logger.log(ambiguity_metrics, step=iteration)
                ambiguity_image = normalized_ambiguity_image(render_pkg["alpha_depth"], render_pkg["modes"])
                if ambiguity_image is not None:
                    wandb_logger.log_tensor_image(
                        "ambiguity/map",
                        ambiguity_image.cpu(),
                        caption=f"{viewpoint_cam.image_name} @ iter {iteration}",
                        step=iteration,
                    )

            # Round 2 Diagnostic: Z-axis gradient vs X-axis gradient + Z-drift tracking
            # 목적: SLAM horizontal trajectory → Z-axis gradient deficiency (P12) 검증
            diag_grad_interval = int(getattr(opt, "diag_grad_interval", 500))
            if wandb_logger and wandb_logger.enabled and diag_grad_interval > 0 and iteration % diag_grad_interval == 0:
                xyz_grad = gaussians._xyz.grad  # [N, 3] or None
                xyz_world = gaussians.get_xyz.detach()  # [N, 3]
                # Z-drift tracking: 씬 좌표 기준 Z 분포
                z_vals = xyz_world[:, 2].cpu().numpy()
                z_outlier_3m = int((np.abs(z_vals) > 3.0).sum())
                z_p99 = float(np.percentile(np.abs(z_vals), 99))
                z_max = float(np.abs(z_vals).max())

                diag_metrics = {
                    "diag/z_outlier_count_3m": z_outlier_3m,
                    "diag/z_abs_p99": z_p99,
                    "diag/z_abs_max": z_max,
                    "diag/gaussian_count": len(z_vals),
                }
                if xyz_grad is not None:
                    # Per-axis gradient magnitude: key test for P12
                    grad_x = xyz_grad[:, 0].abs().mean().item()
                    grad_y = xyz_grad[:, 1].abs().mean().item()
                    grad_z = xyz_grad[:, 2].abs().mean().item()
                    diag_metrics.update({
                        "diag/grad_x_mean": grad_x,
                        "diag/grad_y_mean": grad_y,
                        "diag/grad_z_mean": grad_z,
                        # Z vs X ratio: P12 predicts this ~0.094 for horizontal cameras
                        "diag/grad_z_vs_x_ratio": grad_z / (grad_x + 1e-10),
                        "diag/grad_z_vs_x_ratio_log": float(np.log10(grad_z / (grad_x + 1e-10) + 1e-10)),
                    })
                wandb_logger.log(diag_metrics, step=iteration)

            gaussian_metrics_log_interval = int(getattr(opt, "gaussian_metrics_log_interval", 2000))
            should_log_gaussians = (
                gaussian_metrics_log_interval > 0
                and (iteration % gaussian_metrics_log_interval == 0 or iteration == opt.iterations)
            )
            if should_log_gaussians:
                gaussian_summary = summarize_gaussians(
                    gaussians,
                    sparse_points=sparse_points,
                    low_opacity_threshold=float(getattr(opt, "low_opacity_threshold", 0.1)),
                    large_scale_threshold=float(getattr(opt, "large_scale_threshold", 0.1)),
                )
                save_gaussian_summary(
                    gaussian_summary,
                    Path(dataset.model_path) / "gaussian_metrics" / f"iteration_{iteration}.json",
                )
                if wandb_logger and wandb_logger.enabled:
                    wandb_logger.log(gaussian_summary, step=iteration)

            # 정해진 주기마다 TensorBoard 로깅 및 PSNR 평가, 그리고 .ply 모델 저장을 수행합니다.
            training_report(tb_writer, iteration, Ll1, loss, l1_loss, iter_start.elapsed_time(iter_end), testing_iterations, scene, render, (pipe, background, 1., SPARSE_ADAM_AVAILABLE, None, dataset.train_test_exp), dataset.train_test_exp)
            if (iteration in saving_iterations):
                print("\n[ITER {}] Saving Gaussians".format(iteration))
                scene.save(iteration)
                if getattr(gaussians, "split_log", None):
                    import numpy as _np, pickle as _pk
                    with open(os.path.join(scene.model_path, "split_events.pkl"), "wb") as _f:
                        _pk.dump(gaussians.split_log, _f)

            # --- 핵심: Densification (밀도 제어) 구간 ---
            # 특정 이터레이션(보통 15,000)까지만 포인트 개수를 늘리거나 줄입니다.
            densify_happened = False
            if iteration < opt.densify_until_iter:
                # 가지치기(Pruning)를 위해 각 가우시안이 2D 화면상에서 가졌던 최대 반지름을 기록합니다.
                gaussians.max_radii2D[visibility_filter] = torch.max(gaussians.max_radii2D[visibility_filter], radii[visibility_filter])
                # 위치(XYZ) 변화에 대한 기울기(Gradient)를 누적합니다. (어느 부분이 부족한지 파악)
                gaussians.add_densification_stats(viewspace_point_tensor, visibility_filter)
                # 누적 가시성 카운터 업데이트
                gaussians.accum_visibility[visibility_filter] += 1

                # 일정 주기(densification_interval)마다 실제로 가우시안을 쪼개거나(Split/Clone) 지웁니다(Prune).
                if iteration > opt.densify_from_iter and iteration % opt.densification_interval == 0:
                    densify_happened = True
                    size_threshold = 20 if iteration > opt.opacity_reset_interval else None
                    # 기울기가 큰(복잡한) 곳은 나누고, 투명도(Opacity)가 너무 낮거나 너무 커진 가우시안은 제거합니다.
                    gaussians.densify_and_prune(
                        opt.densify_grad_threshold,
                        opt.min_opacity_prune_threshold,
                        scene.cameras_extent,
                        size_threshold,
                        radii,
                        iteration=iteration
                    )
                    # N changed → invalidate cyclic sampler permutation
                    plateau_loss.reset_sampler()
                    # ACTIVE: N changed -- the only thing cell_gaussian_count depends on.
                    buf.refresh_gaussian_counts(gaussians._xyz.detach())
                    pool_weights = None
                # 가우시안이 구름처럼 퍼지는 현상(Floaters)을 막기 위해 주기적으로 투명도를 리셋(낮춤)합니다. -> 0으로 낮춰서 floater가 이미지에 큰 영향을 주도록...
                if iteration % opt.opacity_reset_interval == 0 or (dataset.white_background and iteration == opt.densify_from_iter):
                    gaussians.reset_opacity()

            # Pop-2 Z-clip: run after densification so Gaussian count is consistent
            plateau_metrics.update(plateau_loss.post_backward(gaussians, iteration))

            # Carve loss: birth gate + budget prune (N이 바뀌면 plateau sampler 무효화)
            _carve_pb = carve_loss.post_backward(gaussians, iteration, densify_happened)
            carve_metrics.update(_carve_pb)
            if _carve_pb.get("carve/gate_pruned", 0) or _carve_pb.get("carve/budget_pruned", 0):
                plateau_loss.reset_sampler()

            # Optimizer Step (실제 파라미터 업데이트)
            if iteration < opt.iterations:
                gaussians.exposure_optimizer.step()
                gaussians.exposure_optimizer.zero_grad(set_to_none = True)
                # Sparse Adam이면 이번 뷰에서 화면에 보인(visible) 가우시안들만 업데이트하여 속도를 높입니다.
                if use_sparse_adam:
                    visible = radii > 0
                    gaussians.optimizer.step(visible, radii.shape[0])
                    gaussians.optimizer.zero_grad(set_to_none = True)
                else:
                    gaussians.optimizer.step()
                    gaussians.optimizer.zero_grad(set_to_none = True)

            # 나중에 이어서 학습할 수 있도록 정해진 이터레이션에 체크포인트(.pth)를 저장합니다.
            if (iteration in checkpoint_iterations):
                print("\n[ITER {}] Saving Checkpoint".format(iteration))
                torch.save((gaussians.capture(), iteration), scene.model_path + "/chkpnt" + str(iteration) + ".pth")

def prepare_output_and_logger(args):    
    if not args.model_path:
        if os.getenv('OAR_JOB_ID'):
            unique_str=os.getenv('OAR_JOB_ID')
        else:
            unique_str = str(uuid.uuid4())
        args.model_path = os.path.join("./output/", unique_str[0:10])
        
    # Set up output folder
    print("Output folder: {}".format(args.model_path))
    os.makedirs(args.model_path, exist_ok = True)
    with open(os.path.join(args.model_path, "cfg_args"), 'w') as cfg_log_f:
        cfg_log_f.write(str(Namespace(**vars(args))))

    # Create Tensorboard writer
    tb_writer = None
    if TENSORBOARD_FOUND:
        tb_writer = SummaryWriter(args.model_path)
    else:
        print("Tensorboard not available: not logging progress")
    return tb_writer

def training_report(tb_writer, iteration, Ll1, loss, l1_loss, elapsed, testing_iterations, scene : Scene, renderFunc, renderArgs, train_test_exp):
    if tb_writer:
        tb_writer.add_scalar('train_loss_patches/l1_loss', Ll1.item(), iteration)
        tb_writer.add_scalar('train_loss_patches/total_loss', loss.item(), iteration)
        tb_writer.add_scalar('iter_time', elapsed, iteration)

    # Report test and samples of training set
    if iteration in testing_iterations:
        torch.cuda.empty_cache()
        validation_configs = ({'name': 'test', 'cameras' : scene.getTestCameras()}, 
                              {'name': 'train', 'cameras' : [scene.getTrainCameras()[idx % len(scene.getTrainCameras())] for idx in range(5, 30, 5)]})

        for config in validation_configs:
            if config['cameras'] and len(config['cameras']) > 0:
                l1_test = 0.0
                psnr_test = 0.0
                for idx, viewpoint in enumerate(config['cameras']):
                    image = torch.clamp(renderFunc(viewpoint, scene.gaussians, *renderArgs)["render"], 0.0, 1.0)
                    gt_image = torch.clamp(viewpoint.original_image.to("cuda"), 0.0, 1.0)
                    if train_test_exp:
                        image = image[..., image.shape[-1] // 2:]
                        gt_image = gt_image[..., gt_image.shape[-1] // 2:]
                    if tb_writer and (idx < 5):
                        tb_writer.add_images(config['name'] + "_view_{}/render".format(viewpoint.image_name), image[None], global_step=iteration)
                        if iteration == testing_iterations[0]:
                            tb_writer.add_images(config['name'] + "_view_{}/ground_truth".format(viewpoint.image_name), gt_image[None], global_step=iteration)
                    l1_test += l1_loss(image, gt_image).mean().double()
                    psnr_test += psnr(image, gt_image).mean().double()
                psnr_test /= len(config['cameras'])
                l1_test /= len(config['cameras'])          
                print("\n[ITER {}] Evaluating {}: L1 {} PSNR {}".format(iteration, config['name'], l1_test, psnr_test))
                if tb_writer:
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - l1_loss', l1_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - psnr', psnr_test, iteration)

        if tb_writer:
            tb_writer.add_histogram("scene/opacity_histogram", scene.gaussians.get_opacity, iteration)
            tb_writer.add_scalar('total_points', scene.gaussians.get_xyz.shape[0], iteration)
        torch.cuda.empty_cache()

if __name__ == "__main__":
    # Set up command line argument parser
    # -------------------------------------------------------------------------
    # REVIEW: 커맨드라인 인자(Argument) 설정 부분
    # 3DGS 학습을 실행할 때 터미널에서 입력받는 다양한 옵션들을 정의합니다.
    # -------------------------------------------------------------------------
    parser = ArgumentParser(description="Training script parameters")
    
    # 1. 외부 파일(arguments.py)에서 정의된 파라미터 그룹을 불러옵니다.
    lp = ModelParams(parser)            # Model: 데이터셋 경로, SH degree, 배경색 등
    op = OptimizationParams(parser)     # Optimization: Learning Rate, densify 시작/종료 시점 등
    pp = PipelineParams(parser)         # Pipeline: 렌더링 시 파이썬 구현체 사용 여부, 디버그 옵션 등

    # 2. SIBR 실시간 뷰어(네트워크 GUI) 연동을 위한 네트워크 설정
    parser.add_argument('--ip', type=str, default="127.0.0.1")
    parser.add_argument('--port', type=int, default=6009)

    # 3. 디버깅 및 에러 추적 옵션
    parser.add_argument('--debug_from', type=int, default=-1)
    # 지정한 이터레이션부터 렌더링 파이프라인의 디버그 모드를 켭니다. (-1은 사용 안 함)
    
    parser.add_argument('--detect_anomaly', action='store_true', default=False)
    # PyTorch의 autograd anomaly detection을 켭니다. Loss가 NaN이 뜨는 등 
    # 그래디언트 역전파 중 문제가 생겼을 때 원인을 찾기 좋습니다. (단, 학습 속도는 느려집니다.)

    # 4. 평가 및 저장 주기 설정
    parser.add_argument("--test_iterations", nargs="+", type=int, default=[7_000, 30_000])
    # 지정한 이터레이션(기본 7000, 30000)에서 테스트 셋을 렌더링하여 PSNR / L1 loss 등을 평가합니다.
    parser.add_argument("--save_iterations", nargs="+", type=int, default=[7_000, 30_000])
    # 지정한 이터레이션에 학습된 가우시안 포인트 클라우드(.ply)를 저장합니다.
    parser.add_argument("--start_checkpoint", type=str, default = None)
    # 모델의 전체 상태(Optimizer 상태 등 포함)를 저장하여 나중에 이어서 학습할 수 있게 합니다.
    
    # 5. 기타 편의 옵션
    parser.add_argument("--quiet", action="store_true")
    # 터미널에 출력되는 로그(진행률 등)를 최소화합니다.
    parser.add_argument('--disable_viewer', action='store_true', default=False)
    # 실시간 GUI 뷰어 서버를 켭니다. SSH 환경 등 뷰어가 필요 없는 서버 환경에서는 이 옵션으로 끌 수 있습니다.
    parser.add_argument("--checkpoint_iterations", nargs="+", type=int, default=[])
    # 이전에 저장해둔 .pth 체크포인트 파일 경로를 입력하면, 해당 시점부터 이어서 학습(Resume)합니다.

    parser.add_argument("--plateau_loss_config", type=str, default=None,
                        help="Path to plateau loss YAML config. None = disabled. "
                             "Example: configs/plateau_loss/spherical.yaml")

    parser.add_argument("--carve_loss_config", type=str, default=None,
                        help="Path to carve loss YAML config. None = disabled. "
                             "Example: configs/carve_loss/exp38_carve.yaml")

    # ACTIVE
    parser.add_argument("--view_selector", type=str, default="default", choices=["default", "coverage"],
                         help="default = byte-identical to the original train.py (shuffled stack, "
                              "no-replacement-per-epoch). coverage = SparseCoverageBuffer-weighted "
                              "random.choices() over the full train camera set.")
    parser.add_argument("--coverage_rescore_every", type=int, default=50,
                         help="recompute pool weights every N iterations")

    # -------------------------------------------------------------------------
    # REVIEW: 인자 파싱 및 학습 준비
    # -------------------------------------------------------------------------
    args = parser.parse_args(sys.argv[1:])
    # 사용자가 따로 지정하지 않았더라도, 전체 학습이 끝나는 시점(args.iterations)에는 무조건 한 번 저장하도록 추가합니다.
    args.save_iterations.append(args.iterations)
    
    print("Optimizing " + args.model_path)
    
    # 난수 시드(seed)를 고정하여 학습 결과의 재현성(reproducibility)을 확보합니다.
    # Initialize system state (RNG)
    safe_state(args.quiet)

    # Start GUI server, configure and run training
    # 뷰어를 비활성화하지 않았다면, 위에서 설정한 IP/PORT로 뷰어와 통신할 서버를 엽니다.
    # Start GUI server, configure and run training
    if not args.disable_viewer:
        network_gui.init(args.ip, args.port)
    torch.autograd.set_detect_anomaly(args.detect_anomaly)

    # 실제 학습을 수행하는 메인 함수 호출. 
    # 파서에서 그룹별로 추출한(extract) 파라미터 묶음들과 리스트 형태의 반복 주기들을 넘겨줍니다.
    training(lp.extract(args), op.extract(args), pp.extract(args), args.test_iterations, args.save_iterations, args.checkpoint_iterations, args.start_checkpoint, args.debug_from,
             plateau_loss_config=args.plateau_loss_config,
             carve_loss_config=args.carve_loss_config,
             view_selector=args.view_selector,
             coverage_rescore_every=args.coverage_rescore_every)

    # All done
    print("\nTraining complete.")
