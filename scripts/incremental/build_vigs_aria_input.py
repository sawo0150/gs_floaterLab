"""build_vigs_aria_input.py — 원본 Aria VRS를 VIGS-SLAM 단안 RGB+IMU 입력으로 변환.

exp52에서 aria1253/aria1253rot을 준비할 때 쓴 것과 동일한 절차(projectaria_tools로
RGB pinhole 정류 + imu-right 스트림 추출 + camera-rgb<->imu Tcb 추출)를 임의의 VRS에
일반화한 것. RGB rectification target(1024x1024, fx=fy=500, cx=cy=512)은
scripts/pipeline/full_traj_to_rgb_3dgs.py와 동일하게 맞춰 calib/aria1253.txt를
그대로 재사용할 수 있게 했다.

실행 환경: conda env `aria` (projectaria_tools 설치됨).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from projectaria_tools.core import calibration, data_provider


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vrs", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path, help="e.g. data/aria301_305")
    p.add_argument("--rgb-label", default="camera-rgb")
    p.add_argument("--imu-label", default="imu-right")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--focal", type=float, default=500.0)
    p.add_argument("--jpeg-quality", type=int, default=95)
    p.add_argument(
        "--skip-head",
        type=int,
        default=0,
        help=(
            "drop this many leading RGB frames from the export (IMU stream is "
            "always exported in full, untrimmed -- VIGS-SLAM windows IMU "
            "samples around whatever RGB frames it receives, so there is no "
            "need to trim it to match). Verified against our existing "
            "data/*/rgb by comparing first/last frame timestamps to a fresh "
            "full export of the same source VRS: data/aria1253 used "
            "--skip-head 8 (first-frame timestamp differs from a full export "
            "by exactly 8 * 1/20fps, last frame identical), while "
            "data/aria301_305 and data/aria301_12F used --skip-head 0 (exact "
            "full export, every frame count/timestamp matches). Do not assume "
            "8 applies to a new scene -- always diff against a fresh full "
            "export first."
        ),
    )
    args = p.parse_args()

    provider = data_provider.create_vrs_data_provider(str(args.vrs))
    if provider is None:
        raise RuntimeError(f"failed to open VRS: {args.vrs}")

    device_calib = provider.get_device_calibration()
    rgb_calib = device_calib.get_camera_calib(args.rgb_label)
    imu_calib = device_calib.get_imu_calib(args.imu_label)
    if rgb_calib is None or imu_calib is None:
        raise RuntimeError(f"missing calibration for {args.rgb_label} or {args.imu_label}")

    T_device_rgb = np.asarray(rgb_calib.get_transform_device_camera().to_matrix(), dtype=np.float64)
    T_device_imu = np.asarray(imu_calib.get_transform_device_imu().to_matrix(), dtype=np.float64)
    Tcb = np.linalg.inv(T_device_rgb) @ T_device_imu  # imu -> rgb camera (VIGS convention)

    print("[calib] Tcb (imu -> rgb camera):")
    for row in Tcb:
        print("  [" + ", ".join(f"{v:.8f}" for v in row) + "]")

    dst_rgb_calib = calibration.get_linear_camera_calibration(
        args.width, args.height, args.focal, args.rgb_label
    )

    rgb_dir = args.output / "rgb"
    rgb_dir.mkdir(parents=True, exist_ok=True)

    rgb_stream_id = provider.get_stream_id_from_label(args.rgb_label)
    n_rgb_total = provider.get_num_data(rgb_stream_id)
    if args.skip_head < 0 or args.skip_head >= n_rgb_total:
        raise ValueError(
            f"--skip-head {args.skip_head} out of range for {n_rgb_total} native frames"
        )
    n_rgb = n_rgb_total - args.skip_head
    print(
        f"[rgb] exporting {n_rgb} of {n_rgb_total} native frames from "
        f"{args.rgb_label} (skipping first {args.skip_head})..."
    )
    for out_i, i in enumerate(range(args.skip_head, n_rgb_total)):
        image_data, record = provider.get_image_data_by_index(rgb_stream_id, i)
        ts_ns = int(record.capture_timestamp_ns)
        undistorted = calibration.distort_by_calibration(
            image_data.to_numpy_array(), dst_rgb_calib, rgb_calib
        )
        Image.fromarray(np.ascontiguousarray(undistorted)).save(
            rgb_dir / f"{ts_ns}.jpg", quality=args.jpeg_quality
        )
        if (out_i + 1) % 200 == 0 or out_i + 1 == n_rgb:
            print(f"  {out_i + 1}/{n_rgb}")

    imu_stream_id = provider.get_stream_id_from_label(args.imu_label)
    n_imu = provider.get_num_data(imu_stream_id)
    print(f"[imu] exporting {n_imu} samples from {args.imu_label}...")
    imu_path = args.output / "imu.txt"
    with imu_path.open("w") as f:
        for i in range(n_imu):
            imu_data = provider.get_imu_data_by_index(imu_stream_id, i)
            ts_ns = int(imu_data.capture_timestamp_ns)
            gx, gy, gz = imu_data.gyro_radsec
            ax, ay, az = imu_data.accel_msec2
            f.write(f"{ts_ns},{gx},{gy},{gz},{ax},{ay},{az}\n")

    print(f"[done] rgb -> {rgb_dir} ({n_rgb} frames), imu -> {imu_path} ({n_imu} samples)")
    print("[note] calib.txt is device-model-only (pinhole 500/500/512/512, 0 distortion) "
          "and is identical across all our Aria recordings — reuse calib/aria1253.txt "
          "or copy it verbatim, no need to regenerate per-scene.")


if __name__ == "__main__":
    sys.exit(main())
