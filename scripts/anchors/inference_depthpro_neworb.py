#!/usr/bin/env python3
"""Depth Pro inference on the 57 keyframe-mapped RGB frames of the rebuilt
OpenMAVIS session (data/03_rgb_3dgs_full), for native anchor generation.
Only Depth Pro is run (the only model used by anchors_all_depth_pro downstream).
"""
import os
import sys
import json
import cv2
import torch
import numpy as np
from PIL import Image
from tqdm import tqdm

MONO_DEPTH_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/repos/monoDepth"
DP_DIR = os.path.join(MONO_DEPTH_DIR, "ml-depth-pro/src")

IMAGES_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full/images"
KF_MAP = "/tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/bb6adb02-cf2a-41cb-8c93-b8740eb2e027/scratchpad/kf_frame_map.json"
OUTPUT_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/depth_maps_neworb_301_1253/depth_pro"

os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

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
sys.path.remove(DP_DIR)

FOCAL_LENGTH_PX = 500.0
f_px_tensor = torch.tensor([FOCAL_LENGTH_PX], device=DEVICE)

mapping = json.load(open(KF_MAP))
frames = sorted(set(m["rgb_frame"] for m in mapping))
print(f"Running Depth Pro on {len(frames)} keyframe-mapped RGB frames")

for name in tqdm(frames):
    stem = os.path.splitext(name)[0]
    npy_path = os.path.join(OUTPUT_DIR, f"{stem}.npy")
    if os.path.exists(npy_path):
        continue
    img_path = os.path.join(IMAGES_DIR, name)
    raw_bgr = cv2.imread(img_path)
    raw_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(raw_rgb)
    x_dp = transform(image_pil)
    with torch.no_grad():
        prediction = model.infer(x_dp, f_px=f_px_tensor)
        depth = prediction["depth"].cpu().numpy()
    np.save(npy_path, depth)

print("Depth Pro inference completed.")
