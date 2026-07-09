import os
import sys
import glob
import cv2
import torch
import numpy as np
from PIL import Image
from tqdm import tqdm
import matplotlib.pyplot as plt

# 1. Define paths
MONO_DEPTH_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/repos/monoDepth"
DA_DIR = os.path.join(MONO_DEPTH_DIR, "Depth-Anything-V2")
DP_DIR = os.path.join(MONO_DEPTH_DIR, "ml-depth-pro/src")
M3D_DIR = os.path.join(MONO_DEPTH_DIR, "Metric3D")

KEYFRAMES_DIR = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/data/3dgs_data/customdata_fisheye624_v2_30000/aria_0416_data_0416_301_1253_0416_301_1253_stereo_fisheye624_v2/images"  # 구 data/ symlink 실제 타깃 (2026-07-07 data 재구축으로 경로 직접 참조)
OUTPUT_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/depth_maps"  # 구 출력은 data_trash_20260707/depth_maps

# Device configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# Create output directories
os.makedirs(os.path.join(OUTPUT_DIR, "depth_anything_v2"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "depth_pro"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "metric3d"), exist_ok=True)

# 2. Get sorted images
image_paths = sorted(glob.glob(os.path.join(KEYFRAMES_DIR, "*.[jJ][pP][gG]")) + glob.glob(os.path.join(KEYFRAMES_DIR, "*.[pP][nN][gG]")))
print(f"Found {len(image_paths)} keyframe images.")

# Camera parameters (from cameras.txt: fx = 500.0)
FOCAL_LENGTH_PX = 500.0

# ----------------- Model Loader functions -----------------

def load_depth_anything_v2():
    print("Loading Depth-Anything-V2...")
    sys.path.insert(0, DA_DIR)
    from depth_anything_v2.dpt import DepthAnythingV2
    
    # Vit-B config
    model_config = {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]}
    model = DepthAnythingV2(**model_config)
    ckpt_path = os.path.join(DA_DIR, "checkpoints/depth_anything_v2_vitb.pth")
    model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
    model = model.to(DEVICE).eval()
    
    # Clean sys.path
    sys.path.remove(DA_DIR)
    return model

def load_depth_pro():
    print("Loading Depth Pro...")
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
    return model, transform

def load_metric3d():
    print("Loading Metric3D...")
    sys.path.insert(0, M3D_DIR)
    
    # Change CWD briefly to Metric3D to allow internal mmcv imports
    orig_cwd = os.getcwd()
    os.chdir(M3D_DIR)
    
    from mmcv.utils import Config
    from mono.model.monodepth_model import get_configured_monodepth_model
    
    cfg_file = os.path.join(M3D_DIR, "mono/configs/HourglassDecoder/vit.raft5.small.py")
    cfg = Config.fromfile(cfg_file)
    model = get_configured_monodepth_model(cfg)
    
    ckpt_path = os.path.join(M3D_DIR, "weight/metric_depth_vit_small_800k.pth")
    checkpoint = torch.load(ckpt_path, map_location="cpu")
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'], strict=False)
    else:
        model.load_state_dict(checkpoint, strict=False)
        
    model = model.to(DEVICE).eval()
    
    os.chdir(orig_cwd)
    sys.path.remove(M3D_DIR)
    return model

# ----------------- Load Models -----------------
try:
    model_da = load_depth_anything_v2()
except Exception as e:
    print(f"Failed to load Depth-Anything-V2: {e}")
    model_da = None

try:
    model_dp, transform_dp = load_depth_pro()
except Exception as e:
    print(f"Failed to load Depth Pro: {e}")
    model_dp = None
    transform_dp = None

try:
    model_m3d = load_metric3d()
except Exception as e:
    print(f"Failed to load Metric3D: {e}")
    model_m3d = None

cmap = plt.get_cmap('Spectral_r')

# Helper to save color visualization
def save_visualization(depth_map, output_png_path):
    # Normalize depth map to [0, 255] for visualization
    d_min, d_max = depth_map.min(), depth_map.max()
    if d_max > d_min:
        depth_norm = (depth_map - d_min) / (d_max - d_min)
    else:
        depth_norm = np.zeros_like(depth_map)
    
    color_depth = (cmap(depth_norm)[:, :, :3] * 255).astype(np.uint8)
    color_depth = cv2.cvtColor(color_depth, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_png_path, color_depth)

# ----------------- Inference Loop -----------------
print("Starting monocular depth inference...")
f_px_tensor = torch.tensor([FOCAL_LENGTH_PX], device=DEVICE)

for img_path in tqdm(image_paths, desc="Inference"):
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    
    # Load raw image
    raw_image_bgr = cv2.imread(img_path)
    h, w = raw_image_bgr.shape[:2]
    raw_image_rgb = cv2.cvtColor(raw_image_bgr, cv2.COLOR_BGR2RGB)
    
    # 1. Depth Anything V2 Inference
    if model_da is not None:
        da_npy = os.path.join(OUTPUT_DIR, f"depth_anything_v2/{img_name}.npy")
        da_png = os.path.join(OUTPUT_DIR, f"depth_anything_v2/{img_name}.png")
        if not (os.path.exists(da_npy) and os.path.exists(da_png)):
            try:
                with torch.no_grad():
                    # Relative inverse depth map
                    depth_da = model_da.infer_image(raw_image_bgr, input_size=518)
                
                # Save as npy & png
                np.save(da_npy, depth_da)
                save_visualization(depth_da, da_png)
            except Exception as e:
                print(f"Error running Depth-Anything-V2 on {img_name}: {e}")
        
    # 2. Depth Pro Inference
    if model_dp is not None:
        dp_npy = os.path.join(OUTPUT_DIR, f"depth_pro/{img_name}.npy")
        dp_png = os.path.join(OUTPUT_DIR, f"depth_pro/{img_name}.png")
        if not (os.path.exists(dp_npy) and os.path.exists(dp_png)):
            try:
                image_pil = Image.fromarray(raw_image_rgb)
                x_dp = transform_dp(image_pil)
                
                with torch.no_grad():
                    # infer(x, f_px) takes float/tensor focal length
                    prediction = model_dp.infer(x_dp, f_px=f_px_tensor)
                    depth_dp = prediction["depth"].cpu().numpy()
                    
                np.save(dp_npy, depth_dp)
                save_visualization(depth_dp, dp_png)
            except Exception as e:
                print(f"Error running Depth Pro on {img_name}: {e}")
        
    # 3. Metric3D Inference
    if model_m3d is not None:
        m3d_npy = os.path.join(OUTPUT_DIR, f"metric3d/{img_name}.npy")
        m3d_png = os.path.join(OUTPUT_DIR, f"metric3d/{img_name}.png")
        if not (os.path.exists(m3d_npy) and os.path.exists(m3d_png)):
            try:
                # keep ratio resize to fit (616, 1064) input size for vit model
                input_size = (616, 1064)
                scale = min(input_size[0] / h, input_size[1] / w)
                rgb_resized = cv2.resize(raw_image_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
                
                # padding
                padding = [123.675, 116.28, 103.53]
                rh, rw = rgb_resized.shape[:2]
                pad_h = input_size[0] - rh
                pad_w = input_size[1] - rw
                pad_h_half = pad_h // 2
                pad_w_half = pad_w // 2
                rgb_padded = cv2.copyMakeBorder(rgb_resized, pad_h_half, pad_h - pad_h_half, pad_w_half, pad_w - pad_w_half, cv2.BORDER_CONSTANT, value=padding)
                pad_info = [pad_h_half, pad_h - pad_h_half, pad_w_half, pad_w - pad_w_half]
                
                # normalize
                mean = torch.tensor([123.675, 116.28, 103.53]).float()[:, None, None]
                std = torch.tensor([58.395, 57.12, 57.375]).float()[:, None, None]
                rgb_tensor = torch.from_numpy(rgb_padded.transpose((2, 0, 1))).float()
                rgb_tensor = torch.div((rgb_tensor - mean), std)
                rgb_tensor = rgb_tensor[None, :, :, :].to(DEVICE)
                
                # run inference
                with torch.no_grad():
                    pred_depth, confidence, output_dict = model_m3d.inference({'input': rgb_tensor})
                    
                pred_depth = pred_depth.squeeze()
                # un pad
                pred_depth = pred_depth[pad_info[0] : pred_depth.shape[0] - pad_info[1], pad_info[2] : pred_depth.shape[1] - pad_info[3]]
                # upsample to original size
                pred_depth = torch.nn.functional.interpolate(pred_depth[None, None, :, :], (h, w), mode='bilinear').squeeze()
                
                # de-canonical scaling (focal length real / 1000.0)
                canonical_to_real_scale = FOCAL_LENGTH_PX / 1000.0
                depth_m3d = pred_depth * canonical_to_real_scale
                depth_m3d = torch.clamp(depth_m3d, 0, 300).cpu().numpy()
                
                np.save(m3d_npy, depth_m3d)
                save_visualization(depth_m3d, m3d_png)
            except Exception as e:
                print(f"Error running Metric3D on {img_name}: {e}")

print("Inference completed successfully!")
