#!/usr/bin/env python3
"""Audit the Aria-1253 Sobel density curve on benchmark RGB inputs.

This reproduces VIGS ``mono_stream`` resizing and the image part of
``GaussianModel.create_pcd_from_image_and_depth``.  It intentionally reports an
all-pixel proxy: the live mapper averages Sobel magnitude only over pixels whose
predicted depth is valid.  Exact live values should therefore be collected with
``VIGS_KF_CONTENT_LOG`` during a controlled run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


TARGET_PIXELS = 341 * 640
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def image_paths(directory: Path) -> list[Path]:
    paths = [p for p in directory.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES]
    try:
        return sorted(paths, key=lambda p: float(p.stem))
    except ValueError:
        return sorted(paths)


def evenly_spaced(paths: list[Path], limit: int) -> list[Path]:
    if limit <= 0 or len(paths) <= limit:
        return paths
    indices = np.linspace(0, len(paths) - 1, limit, dtype=np.int64)
    return [paths[int(i)] for i in np.unique(indices)]


def resized_sobel_mean(path: Path) -> float:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot read image: {path}")
    h0, w0 = image.shape[:2]
    scale = np.sqrt(TARGET_PIXELS / float(h0 * w0))
    h1 = int(h0 * scale)
    w1 = int(w0 * scale)
    h1 -= h1 % 8
    w1 -= w1 % 8
    image = cv2.resize(image, (w1, h1))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    return float(np.hypot(gx, gy).mean())


def multiplier(values: np.ndarray, curve: dict[str, float]) -> np.ndarray:
    x0 = float(curve["sobel_mean_p10"])
    x1 = float(curve["sobel_mean_p90"])
    y0 = float(curve["mult_at_p10"])
    y1 = float(curve["mult_at_p90"])
    scaled = y0 + (values - x0) * (y1 - y0) / (x1 - x0)
    return np.clip(scaled, 0.35, 3.0)


def summarize(paths: list[Path], curve: dict[str, float], available: int) -> dict:
    values = np.asarray([resized_sobel_mean(p) for p in paths], dtype=np.float64)
    mult = multiplier(values, curve)
    x0 = float(curve["sobel_mean_p10"])
    x1 = float(curve["sobel_mean_p90"])
    return {
        "available_images": int(available),
        "sampled_images": int(len(paths)),
        "sobel_mean": float(values.mean()),
        "sobel_p10": float(np.percentile(values, 10)),
        "sobel_p50": float(np.percentile(values, 50)),
        "sobel_p90": float(np.percentile(values, 90)),
        "fraction_below_aria_curve_p10": float(np.mean(values < x0)),
        "fraction_above_aria_curve_p90": float(np.mean(values > x1)),
        "multiplier_mean": float(mult.mean()),
        "multiplier_p10": float(np.percentile(mult, 10)),
        "multiplier_p50": float(np.percentile(mult, 50)),
        "multiplier_p90": float(np.percentile(mult, 90)),
        "multiplier_min": float(mult.min()),
        "multiplier_max": float(mult.max()),
    }


def keyframe_paths(directory: Path, images_txt: Path) -> list[Path]:
    source = image_paths(directory)
    indices: set[int] = set()
    for line in images_txt.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if fields and fields[-1].lower().endswith(tuple(IMAGE_SUFFIXES)):
            indices.add(int(fields[0]))
    return [source[i] for i in sorted(indices) if 0 <= i < len(source)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curve", type=Path, required=True)
    parser.add_argument("--aria-rgb", type=Path, required=True)
    parser.add_argument("--aria-images-txt", type=Path, required=True)
    parser.add_argument("--rpng-root", type=Path, required=True)
    parser.add_argument("--rpng-table06-images-txt", type=Path, required=True)
    parser.add_argument("--utmm-root", type=Path, required=True)
    parser.add_argument("--per-sequence-limit", type=int, default=512)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    curve = json.loads(args.curve.read_text(encoding="utf-8"))
    groups: dict[str, tuple[list[Path], int]] = {}

    aria_all = image_paths(args.aria_rgb)
    groups["aria1253_all_proxy"] = (
        evenly_spaced(aria_all, args.per_sequence_limit),
        len(aria_all),
    )
    aria_kfs = keyframe_paths(args.aria_rgb, args.aria_images_txt)
    groups["aria1253_observed_keyframes_proxy"] = (aria_kfs, len(aria_kfs))

    for sequence_dir in sorted(p for p in args.rpng_root.iterdir() if p.is_dir()):
        rgb_dir = sequence_dir / "rgb"
        if not rgb_dir.is_dir():
            continue
        paths = image_paths(rgb_dir)
        groups[f"rpng/{sequence_dir.name}"] = (
            evenly_spaced(paths, args.per_sequence_limit),
            len(paths),
        )
        if sequence_dir.name == "table_06":
            kfs = keyframe_paths(rgb_dir, args.rpng_table06_images_txt)
            groups["rpng/table_06_observed_keyframes_proxy"] = (kfs, len(kfs))

    for sequence_dir in sorted(p for p in args.utmm_root.iterdir() if p.is_dir()):
        rgb_dir = sequence_dir / "rgb_timestamp"
        if not rgb_dir.is_dir():
            continue
        paths = image_paths(rgb_dir)
        groups[f"utmm/{sequence_dir.name}"] = (
            evenly_spaced(paths, args.per_sequence_limit),
            len(paths),
        )

    output = {
        "method": "all-pixel Sobel proxy after exact VIGS mono_stream resize",
        "caveat": (
            "Live adaptive density averages Sobel only on valid predicted-depth pixels; "
            "use VIGS_KF_CONTENT_LOG for exact values."
        ),
        "curve": curve,
        "per_sequence_limit": args.per_sequence_limit,
        "groups": {
            name: summarize(paths, curve, available)
            for name, (paths, available) in groups.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
