#!/usr/bin/env python3
"""Numerically validate the exp78 official-README TensorRT engines.

The comparison mirrors the released VIGS runtime: PyTorch reference modules
run under CUDA autocast while TensorRT receives FP32 I/O and uses FP16
internally.  Results are emitted as JSON so the exact engine build can be
audited independently of a benchmark trajectory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections import OrderedDict
from pathlib import Path
from time import perf_counter
from typing import Callable

import numpy as np
import tensorrt as trt
import torch


ENGINE_NAMES = (
    "omnidata_depth_512_simplified_fp16.engine",
    "omnidata_normal_512_simplified_fp16.engine",
    "droidnet_fnet_fp16.engine",
    "update_module_partial_fp16.engine",
    "update_module_partial_pgba_fp16.engine",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_metrics(reference: torch.Tensor, candidate: torch.Tensor) -> dict:
    reference = reference.detach().float().reshape(-1)
    candidate = candidate.detach().float().reshape(-1)
    difference = candidate - reference
    ref_rms = torch.sqrt(torch.mean(reference.square()))
    rmse = torch.sqrt(torch.mean(difference.square()))
    denominator = torch.linalg.vector_norm(reference) * torch.linalg.vector_norm(candidate)
    cosine = torch.dot(reference, candidate) / denominator.clamp_min(1e-30)
    return {
        "shape": list(reference.shape) if reference.ndim > 1 else list(candidate.shape),
        "elements": int(reference.numel()),
        "reference_rms": float(ref_rms),
        "rmse": float(rmse),
        "relative_rmse": float(rmse / ref_rms.clamp_min(1e-30)),
        "mean_abs": float(difference.abs().mean()),
        "max_abs": float(difference.abs().max()),
        "cosine": float(cosine),
        "reference_finite": bool(torch.isfinite(reference).all()),
        "candidate_finite": bool(torch.isfinite(candidate).all()),
    }


def inspect_engine(path: Path) -> dict:
    logger = trt.Logger(trt.Logger.ERROR)
    with trt.Runtime(logger) as runtime:
        engine = runtime.deserialize_cuda_engine(path.read_bytes())
    if engine is None:
        raise RuntimeError(f"could not deserialize {path}")
    tensors = []
    for index in range(engine.num_io_tensors):
        name = engine.get_tensor_name(index)
        mode = str(engine.get_tensor_mode(name)).split(".")[-1].lower()
        item = {
            "name": name,
            "mode": mode,
            "dtype": str(engine.get_tensor_dtype(name)),
            "shape": list(engine.get_tensor_shape(name)),
        }
        if mode == "input" and engine.num_optimization_profiles:
            minimum, optimum, maximum = engine.get_tensor_profile_shape(name, 0)
            item["profile"] = {
                "min": list(minimum),
                "opt": list(optimum),
                "max": list(maximum),
            }
        tensors.append(item)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "profiles": int(engine.num_optimization_profiles),
        "tensors": tensors,
    }


def time_cuda(function: Callable[[], object], warmup: int = 3, repeats: int = 10) -> float:
    for _ in range(warmup):
        function()
    torch.cuda.synchronize()
    begin = perf_counter()
    for _ in range(repeats):
        function()
    torch.cuda.synchronize()
    return 1000.0 * (perf_counter() - begin) / repeats


def load_droidnet(source: Path):
    sys.path.insert(0, str(source / "vigs"))
    from modules.droid_net import DroidNet

    network = DroidNet()
    state = OrderedDict(
        (key.replace("module.", ""), value)
        for key, value in torch.load(
            source / "pretrained_models" / "droid.pth", map_location="cpu"
        ).items()
    )
    for key in (
        "update.weight.2.weight",
        "update.weight.2.bias",
        "update.delta.2.weight",
        "update.delta.2.bias",
    ):
        state[key] = state[key][:2]
    network.load_state_dict(state)
    return network.cuda().eval()


def validate_fnet(source: Path, engines: Path) -> dict:
    from modules.trt_base import TrtRunner

    network = load_droidnet(source)
    runner = TrtRunner(
        str(engines / "droidnet_fnet_fp16.engine"), use_torch_stream=True
    )
    generator = torch.Generator(device="cpu").manual_seed(7801)
    image = torch.randn((1, 1, 3, 344, 616), generator=generator).cuda()
    with torch.no_grad(), torch.amp.autocast("cuda", enabled=True):
        reference = network.fnet(image)
    candidate = runner.run({"input": image.float()}, synchronize=True)[0].clone()
    result = tensor_metrics(reference, candidate)
    result["logical_shape"] = list(reference.shape)
    result["pytorch_ms"] = time_cuda(
        lambda: network.fnet(image), warmup=3, repeats=20
    )
    result["tensorrt_ms"] = time_cuda(
        lambda: runner.run({"input": image.float()}), warmup=3, repeats=20
    )
    del runner, network, image, reference, candidate
    torch.cuda.empty_cache()
    return result


def validate_update(source: Path, engines: Path, pgba: bool, edges: int) -> dict:
    from modules.trt_base import TrtRunner

    network = load_droidnet(source)
    engine_name = (
        "update_module_partial_pgba_fp16.engine"
        if pgba
        else "update_module_partial_fp16.engine"
    )
    runner = TrtRunner(str(engines / engine_name), use_torch_stream=True)
    generator = torch.Generator(device="cpu").manual_seed(7802 + edges)

    def random_tensor(channels: int) -> torch.Tensor:
        return torch.randn(
            (1, edges, channels, 43, 77), generator=generator
        ).cuda()

    inputs = {
        "net": random_tensor(128),
        "inp": random_tensor(128),
        "corr": random_tensor(196),
        "flow": random_tensor(4).clamp(-64.0, 64.0),
    }
    with torch.no_grad(), torch.amp.autocast("cuda", enabled=True):
        reference = network.update(
            inputs["net"], inputs["inp"], inputs["corr"], inputs["flow"]
        )
    candidate = runner.run(
        {name: value.float() for name, value in inputs.items()}, synchronize=True
    )
    names = ("net_out", "delta", "weight")
    outputs = {
        name: {
            **tensor_metrics(ref, cand),
            "logical_shape": list(ref.shape),
        }
        for name, ref, cand in zip(names, reference, candidate)
    }
    outputs["pytorch_ms"] = time_cuda(
        lambda: network.update(
            inputs["net"], inputs["inp"], inputs["corr"], inputs["flow"]
        ),
        warmup=2,
        repeats=5,
    )
    outputs["tensorrt_ms"] = time_cuda(
        lambda: runner.run({name: value.float() for name, value in inputs.items()}),
        warmup=2,
        repeats=5,
    )
    outputs["edges"] = edges
    del runner, network, reference, candidate, inputs
    torch.cuda.empty_cache()
    return outputs


def validate_omnidata(source: Path, engines: Path, task: str) -> dict:
    from midas.omnidata import OmnidataModel
    from modules.trt_base import TrtRunner

    checkpoint = source / "pretrained_models" / f"omnidata_dpt_{task}_v2.ckpt"
    model = OmnidataModel(task, str(checkpoint), device="cuda:0").model.eval()
    runner = TrtRunner(
        str(engines / f"omnidata_{task}_512_simplified_fp16.engine"),
        use_torch_stream=True,
    )
    generator = torch.Generator(device="cpu").manual_seed(
        7803 if task == "depth" else 7804
    )
    image = torch.rand((1, 3, 512, 512), generator=generator).cuda()
    # The released runtime passes ImageNet-normalized RGB to both priors.
    mean = torch.tensor([0.485, 0.456, 0.406], device="cuda")[:, None, None]
    std = torch.tensor([0.229, 0.224, 0.225], device="cuda")[:, None, None]
    image = image.sub(mean).div(std)
    with torch.no_grad(), torch.amp.autocast("cuda", enabled=True):
        reference = model(image)
    candidate = runner.run({"input": image.float()}, synchronize=True)[0].clone()
    result = tensor_metrics(reference, candidate)
    result["logical_shape"] = list(reference.shape)
    result["pytorch_ms"] = time_cuda(lambda: model(image), warmup=1, repeats=3)
    result["tensorrt_ms"] = time_cuda(
        lambda: runner.run({"input": image.float()}), warmup=1, repeats=3
    )
    del runner, model, image, reference, candidate
    torch.cuda.empty_cache()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-source", type=Path, required=True)
    parser.add_argument("--engine-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.official_source.resolve()
    engines = args.engine_dir.resolve()
    sys.path.insert(0, str(source))
    sys.path.insert(0, str(source / "vigs"))
    missing = [name for name in ENGINE_NAMES if not (engines / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing engines: {missing}")
    torch.manual_seed(78)
    np.random.seed(78)
    result = {
        "schema": "exp78a-official-readme-trt-validation-v1",
        "official_source": str(source),
        "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996",
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "tensorrt": trt.__version__,
            "gpu": torch.cuda.get_device_name(0),
        },
        "engines": {
            name: inspect_engine(engines / name) for name in ENGINE_NAMES
        },
        "comparisons": {},
    }
    result["comparisons"]["fnet_rpng_344x616"] = validate_fnet(source, engines)
    result["comparisons"]["update_24_edges"] = validate_update(
        source, engines, pgba=False, edges=24
    )
    result["comparisons"]["update_pgba_85_edges"] = validate_update(
        source, engines, pgba=True, edges=85
    )
    result["comparisons"]["omnidata_depth"] = validate_omnidata(
        source, engines, "depth"
    )
    result["comparisons"]["omnidata_normal"] = validate_omnidata(
        source, engines, "normal"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
