#!/usr/bin/env python3
"""Locate the preserved v1 failure, without editing its source or active mapper."""
import hashlib
import importlib.util
import json
from pathlib import Path
import torch
from diagnose_geometry_interaction import native_loss as repaired_loss, trial
from gaussian.utils.slam_utils import get_loss_mapping_rgbd, get_loss_normal


class CapturedFailure(Exception):
    pass


def main():
    source = trial.ROOT / 'geometry_interaction/v1/aria/aria1253/runner_source.py'
    output = trial.ROOT / 'geometry_interaction/v1_failure_reproduction'
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('preserved_geometry_v1', source)
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    old.ROOT = output / 'replay'
    original = old.native_loss
    ordinal = 0
    source_paths = [source, Path(__file__).resolve(), Path(__file__).with_name('diagnose_geometry_interaction.py'),
        trial.BACKEND / 'vigs/gaussian/utils/slam_utils.py']
    locks = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}

    def instrumented(packages, views, config, lambda_normal, geometry):
        nonlocal ordinal
        ordinal += 1
        value = original(packages, views, config, lambda_normal, geometry)
        if torch.isfinite(value):
            return value
        with torch.no_grad():
            rows = []
            for view, pkg in zip(views, packages):
                raw = get_loss_mapping_rgbd(config, pkg['render'], pkg['depth'], view,
                                            geometry_scale=float(geometry))
                normal = get_loss_normal(pkg['depth'], view)
                row = {'uid': view.uid, 'legacy_rgbd_finite': bool(torch.isfinite(raw)),
                    'normal_finite': bool(torch.isfinite(normal)),
                    'render_depth_zero': int((pkg['depth'] == 0).sum()),
                    'render_depth_nonfinite': int((~torch.isfinite(pkg['depth'])).sum()),
                    'gt_depth_zero': int((view.depth_gpu == 0).sum()),
                    'gt_depth_nonfinite': int((~torch.isfinite(view.depth_gpu)).sum())}
                rows.append(row)
                if not row['legacy_rgbd_finite'] and not (output / 'first_bad_view.pt').exists():
                    torch.save({'uid': view.uid, 'render': pkg['render'].detach().cpu(),
                        'depth': pkg['depth'].detach().cpu(), 'gt_image': view.original_image.detach().cpu(),
                        'gt_depth': view.depth_gpu.detach().cpu(), 'normal': view.normal_gpu.detach().cpu(),
                        'config': config}, output / 'first_bad_view.pt')
            safe = repaired_loss(packages, views, config, lambda_normal, geometry)
        result = {'protocol': 'geometry_loss_failure_reproduction_v1', 'failure_native_batch': ordinal,
            'completed_photo_steps': ordinal * old.NATIVE_PERIOD, 'completed_native_steps': ordinal - 1,
            'geometry_weight_enabled': geometry, 'legacy_total_finite': False,
            'repaired_total_finite': bool(torch.isfinite(safe)), 'views': rows,
            'source_lock': locks, 'strict_online': False,
            'active_mapper_changed': False}
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        raise CapturedFailure

    old.native_loss = instrumented
    try:
        old.worker('aria', 'aria1253', 'kf_rgb')
    except CapturedFailure:
        pass
    else:
        raise RuntimeError('Preserved failure did not reproduce')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in locks.items())
    (output / 'reproducer_source.py').write_bytes(Path(__file__).read_bytes())


if __name__ == '__main__':
    main()
