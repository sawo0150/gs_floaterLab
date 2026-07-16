#!/usr/bin/env python3
"""각 keyframe 구간에 속하는 조밀한 RGB 프레임(1,303장)을 묶어서 incremental 청크를 만든다.

build_incremental_chunks.py(keyframe당 최근접 프레임 1장)의 dense 버전.
포즈 재계산을 하지 않고 data/03_rgb_3dgs_full이 이미 갖고 있는 정확한 보간 pose
(full_traj_to_rgb_3dgs.py가 dense per-frame trajectory로 slerp/lerp한 결과)를
keyframe timestamp 구간으로 나눠서 재사용한다 — keyframe끼리만 보간하면 오차가 커지므로.

각 청크(keyframe i)가 갖는 프레임 = [keyframe[i-1].timestamp, keyframe[i].timestamp) 구간의
RGB 프레임 전부 (i=0은 씬 시작~keyframe[0], 마지막 청크는 남은 꼬리 프레임까지 포함).
"""
import argparse
import json
import re
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_images_txt(path: Path) -> dict[int, tuple[str, str]]:
    """COLMAP images.txt(짝수줄=POINTS2D 빈줄) -> {image_id: (pose_line_without_id, image_name)}"""
    out = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        image_id = int(parts[0])
        pose_fields = parts[1:9]  # qw qx qy qz tx ty tz camera_id
        image_name = parts[9]
        out[image_id] = (" ".join(pose_fields), image_name)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--orb-export", required=True, type=Path)
    p.add_argument("--full-rgb-dataset", required=True, type=Path,
                    help="data/03_rgb_3dgs_full (dense pose가 이미 계산된 데이터셋)")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    keyframes = load_jsonl(args.orb_export / "keyframes.jsonl")
    keyframes.sort(key=lambda kf: int(kf["kf_id"]))
    map_points = load_jsonl(args.orb_export / "map_points.jsonl")
    observations = load_jsonl(args.orb_export / "observations.jsonl")

    mp_to_first_kf = {}
    for obs in observations:
        mp_id = int(obs["map_point_id"])
        kf_id = int(obs["kf_id"])
        if mp_id not in mp_to_first_kf or kf_id < mp_to_first_kf[mp_id]:
            mp_to_first_kf[mp_id] = kf_id
    kf_to_new_mps = {}
    for mp in map_points:
        mp_id = int(mp["map_point_id"])
        first_kf = mp_to_first_kf.get(mp_id)
        if first_kf is not None:
            kf_to_new_mps.setdefault(first_kf, []).append(mp)

    # dense RGB 프레임: timestamp + pose를 image_id로 조인
    sanity_rows = load_jsonl(args.full_rgb_dataset / "pose_sanity_rows.jsonl")
    ts_by_id = {int(r["image_id"]): int(r["rgb_timestamp_ns"]) for r in sanity_rows}
    images_txt = parse_images_txt(args.full_rgb_dataset / "sparse" / "0" / "images.txt")
    full_images_dir = (args.full_rgb_dataset / "images").resolve()

    # (timestamp_ns, image_id) 오름차순 정렬
    dense_frames = sorted(
        ((ts_by_id[iid], iid) for iid in images_txt if iid in ts_by_id),
        key=lambda x: x[0],
    )
    print(f"Loaded {len(keyframes)} keyframes, {len(dense_frames)} dense RGB frames.")

    manifest = []
    n_frames_used = 0
    di = 0  # dense_frames 커서
    for chunk_idx, kf in enumerate(keyframes):
        kf_id = int(kf["kf_id"])
        kf_ts = int(kf["timestamp_ns"])
        is_last = chunk_idx == len(keyframes) - 1

        bucket = []
        while di < len(dense_frames) and (dense_frames[di][0] < kf_ts or is_last):
            bucket.append(dense_frames[di])
            di += 1
        # (is_last일 때 루프 조건이 항상 참이라 남은 꼬리 프레임까지 전부 이 마지막 버킷으로 흡수됨)

        chunk_dir = args.output / f"chunk_{chunk_idx:03d}"
        images_dir = chunk_dir / "images"
        sparse_dir = chunk_dir / "sparse" / "0"
        images_dir.mkdir(parents=True, exist_ok=True)
        sparse_dir.mkdir(parents=True, exist_ok=True)

        images_lines = []
        for new_id, (ts, iid) in enumerate(bucket, start=1):
            pose_fields, image_name = images_txt[iid]
            link_path = images_dir / image_name
            if not link_path.exists():
                link_path.symlink_to(full_images_dir / image_name)
            images_lines.append(f"{new_id} {pose_fields} {image_name}\n\n")

        (sparse_dir / "images.txt").write_text("".join(images_lines), encoding="utf-8")
        (sparse_dir / "cameras.txt").write_text(
            "1 PINHOLE 1024 1024 500.0 500.0 512.0 512.0\n", encoding="utf-8"
        )

        new_mps = kf_to_new_mps.get(kf_id, [])
        if chunk_idx == 0:
            with (sparse_dir / "points3D.txt").open("w", encoding="utf-8") as f:
                for mp in new_mps:
                    x, y, z = mp["xyz"]
                    f.write(f"{int(mp['map_point_id'])} {x} {y} {z} 128 128 128 0\n")
        else:
            with (sparse_dir / "points3D.txt").open("w", encoding="utf-8") as f:
                f.write("1 0.0 0.0 0.0 128 128 128 0\n")
                f.write("2 0.01 0.0 0.0 128 128 128 0\n")
                f.write("3 0.0 0.01 0.0 128 128 128 0\n")
            with (sparse_dir / "extra_points3D.txt").open("w", encoding="utf-8") as f:
                for mp in new_mps:
                    x, y, z = mp["xyz"]
                    f.write(f"{int(mp['map_point_id'])} {x} {y} {z} 128 128 128 0\n")

        n_frames_used += len(bucket)
        manifest.append({
            "chunk_idx": chunk_idx,
            "kf_id": kf_id,
            "timestamp_ns": kf_ts,
            "num_new_map_points": len(new_mps),
            "num_dense_frames": len(bucket),
        })
        if (chunk_idx + 1) % 10 == 0 or is_last:
            print(f"Processed {chunk_idx + 1}/{len(keyframes)} chunks "
                  f"(cumulative dense frames used: {n_frames_used}/{len(dense_frames)})")

    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Done building dense incremental chunks dataset!")


if __name__ == "__main__":
    main()
