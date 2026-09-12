"""Tiny synthetic CUDA operation test. This is NOT a PSNR experiment."""
import argparse
import json
import math
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.repo.resolve()))
    import torch
    from diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
    from simple_knn._C import distCUDA2
    from utils.graphics_utils import getProjectionMatrix
    xyz = torch.tensor([[-.2, -.2, 2.], [.2, -.2, 2.], [-.2, .2, 2.], [.2, .2, 2.]],
                       device="cuda", requires_grad=True)
    screenspace = torch.zeros_like(xyz, requires_grad=True)
    colors = torch.tensor([[.8, .2, .1]] * 4, device="cuda", requires_grad=True)
    settings = GaussianRasterizationSettings(
        image_height=32, image_width=32, tanfovx=1., tanfovy=1.,
        bg=torch.zeros(3, device="cuda"), scale_modifier=1.,
        viewmatrix=torch.eye(4, device="cuda"),
        projmatrix=getProjectionMatrix(.01, 100., math.pi / 2, math.pi / 2).T.contiguous().cuda(),
        sh_degree=0, campos=torch.zeros(3, device="cuda"), prefiltered=False,
        beta=5., debug=False, antialiasing=False)
    result = GaussianRasterizer(settings)(
        means3D=xyz, means2D=screenspace, opacities=torch.full((4, 1), .7, device="cuda"),
        colors_precomp=colors, scales=torch.full((4, 3), .15, device="cuda"),
        rotations=torch.tensor([[1., 0., 0., 0.]] * 4, device="cuda"))
    rendered = result[0]
    rendered.square().mean().backward()
    knn = distCUDA2(xyz.detach())
    torch.cuda.synchronize()
    assert torch.isfinite(rendered).all() and rendered.max() > 0
    assert xyz.grad is not None and torch.isfinite(xyz.grad).all()
    assert colors.grad is not None and colors.grad.abs().sum() > 0
    assert torch.isfinite(knn).all()
    data = {"status": "PASS_SYNTHETIC_NOT_QUALITY", "torch": torch.__version__,
            "cuda_build": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
            "image_shape": list(rendered.shape), "image_max": rendered.max().item(),
            "xyz_grad_norm": xyz.grad.norm().item(), "color_grad_norm": colors.grad.norm().item(),
            "rasterizer_output_count": len(result), "knn_finite": True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
