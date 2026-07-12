#!/usr/bin/env python3
"""Depth Pro inference — 범용 장면 버전 (exp43 depth-anchor 처방).

data/scenes/<scene>/03_rgb_3dgs/images 에서 stride 간격으로 프레임을 뽑아
depth를 results/diagnostic/depth_maps_<scene>/depth_pro/ 에 저장.
1253 전용 inference_depthpro_neworb.py 의 일반화 (kf_frame_map 대신 stride).
"""
import argparse
import os
import sys

import cv2
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

LAB = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
MONO_DEPTH_DIR = f"{LAB}/repos/monoDepth"
DP_DIR = os.path.join(MONO_DEPTH_DIR, "ml-depth-pro/src")

ap = argparse.ArgumentParser()
ap.add_argument("--scene", required=True)
ap.add_argument("--stride", type=int, default=40)
args = ap.parse_args()

IMAGES_DIR = f"{LAB}/data/scenes/{args.scene}/03_rgb_3dgs/images"
OUTPUT_DIR = f"{LAB}/results/diagnostic/depth_maps_{args.scene}/depth_pro"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
sys.path.insert(0, DP_DIR)
import depth_pro
from depth_pro.depth_pro import DepthProConfig

config = DepthProConfig(
    patch_encoder_preset="dinov2l16_384",
    image_encoder_preset="dinov2l16_384",
    checkpoint_uri=os.path.join(MONO_DEPTH_DIR, "ml-depth-pro/checkpoints/depth_pro.pt"),
    decoder_features=256,
    use_fov_head=True,
    fov_encoder_preset="dinov2l16_384",
)
model, transform = depth_pro.create_model_and_transforms(config=config, device=torch.device(DEVICE))
model = model.eval()

f_px_tensor = torch.tensor([500.0], device=DEVICE)

frames = sorted(os.listdir(IMAGES_DIR))[:: args.stride]
print(f"[{args.scene}] Depth Pro on {len(frames)} frames (stride {args.stride})")

for name in tqdm(frames):
    stem = os.path.splitext(name)[0]
    npy_path = os.path.join(OUTPUT_DIR, f"{stem}.npy")
    if os.path.exists(npy_path):
        continue
    raw_rgb = cv2.cvtColor(cv2.imread(os.path.join(IMAGES_DIR, name)), cv2.COLOR_BGR2RGB)
    with torch.no_grad():
        pred = model.infer(transform(Image.fromarray(raw_rgb)), f_px=f_px_tensor)
    np.save(npy_path, pred["depth"].cpu().numpy())

print("done")
