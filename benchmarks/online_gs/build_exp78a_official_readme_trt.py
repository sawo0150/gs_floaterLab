#!/usr/bin/env python3
"""Build the five FP16 TensorRT engines with the official README profiles.

The released TensorRT wheel does not contain ``trtexec`` on this host, so this
uses the equivalent TensorRT 10 builder API.  ONNX inputs may live in separate
directories, which lets the clean official source stay unmodified.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import tensorrt as trt


LOGGER = trt.Logger(trt.Logger.WARNING)
WORKSPACE_MIB = 24_576


def build(
    onnx_path: Path,
    engine_path: Path,
    shapes: dict[str, tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]]
    | None = None,
) -> None:
    builder = trt.Builder(LOGGER)
    network = builder.create_network(
        1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    )
    parser = trt.OnnxParser(network, LOGGER)
    if not parser.parse(onnx_path.read_bytes()):
        errors = "\n".join(str(parser.get_error(i)) for i in range(parser.num_errors))
        raise RuntimeError(f"failed to parse {onnx_path}:\n{errors}")
    config = builder.create_builder_config()
    config.set_memory_pool_limit(
        trt.MemoryPoolType.WORKSPACE, WORKSPACE_MIB * 1024 * 1024
    )
    config.set_flag(trt.BuilderFlag.FP16)
    if shapes:
        profile = builder.create_optimization_profile()
        for name, (minimum, optimum, maximum) in shapes.items():
            profile.set_shape(name, minimum, optimum, maximum)
        config.add_optimization_profile(profile)
    serialized = builder.build_serialized_network(network, config)
    if serialized is None:
        raise RuntimeError(f"TensorRT engine build failed for {onnx_path}")
    engine_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = engine_path.with_suffix(engine_path.suffix + ".tmp")
    temporary.write_bytes(serialized)
    temporary.replace(engine_path)
    print(f"built {engine_path} ({serialized.nbytes} bytes)", flush=True)


def update_shapes(maximum_edges: int, optimum_edges: int):
    def shaped(channels: int):
        return (
            (1, 1, channels, 41, 41),
            (1, optimum_edges, channels, 43, 77),
            (1, maximum_edges, channels, 82, 82),
        )

    return {
        "net": shaped(128),
        "inp": shaped(128),
        "corr": shaped(196),
        "flow": shaped(4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--droid-onnx-dir", type=Path, required=True)
    parser.add_argument("--omnidata-onnx-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    build(
        args.omnidata_onnx_dir / "omnidata_depth_512_simplified.onnx",
        output / "omnidata_depth_512_simplified_fp16.engine",
    )
    build(
        args.omnidata_onnx_dir / "omnidata_normal_512_simplified.onnx",
        output / "omnidata_normal_512_simplified_fp16.engine",
    )
    build(
        args.droid_onnx_dir / "droidnet_fnet.onnx",
        output / "droidnet_fnet_fp16.engine",
        {
            "input": (
                (1, 1, 3, 328, 328),
                (1, 1, 3, 368, 584),
                (1, 1, 3, 656, 656),
            )
        },
    )
    update_onnx = args.droid_onnx_dir / "update_module_partial.onnx"
    build(
        update_onnx,
        output / "update_module_partial_fp16.engine",
        update_shapes(maximum_edges=60, optimum_edges=24),
    )
    build(
        update_onnx,
        output / "update_module_partial_pgba_fp16.engine",
        update_shapes(maximum_edges=120, optimum_edges=85),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
