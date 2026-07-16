#!/usr/bin/env bash
# exp51: Photo-SLAM trainReplay 출력(<output_dir>/<iter>_replay/)을 3dgs-custom render.py --eval로
# held-out PSNR 평가. savePly()가 이미 point_cloud/iteration_N/point_cloud.ply 구조를 만들어두므로
# cfg_args만 얹으면 그대로 3dgs-custom model_path로 쓸 수 있음.
#
# 사용: eval_replay_psnr.sh <model_path=output_dir/NNN_replay> <iteration>
set -eo pipefail

MODEL_PATH="$1"
ITER="$2"
GF="/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
D3="/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom"
SOURCE_PATH="$GF/data/03_rgb_3dgs_full"

cat > "$MODEL_PATH/cfg_args" <<EOF
Namespace(sh_degree=3, source_path='$SOURCE_PATH', model_path='$MODEL_PATH', images='images', depths='', resolution=-1, white_background=False, train_test_exp=False, data_device='cpu', eval=True)
EOF

source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate 3dgs

cd "$D3"
python render.py -m "$MODEL_PATH" --iteration "$ITER" --skip_train
python metrics.py -m "$MODEL_PATH"

python - "$MODEL_PATH" "$ITER" <<'PYEOF'
import json, sys
model_path, it = sys.argv[1], sys.argv[2]
with open(f"{model_path}/results.json") as f:
    r = json.load(f)
key = f"ours_{it}"
m = r[key]
print(f"PSNR avg={m['PSNR']:.3f}  SSIM={m['SSIM']:.4f}  LPIPS={m['LPIPS']:.4f}")
PYEOF
