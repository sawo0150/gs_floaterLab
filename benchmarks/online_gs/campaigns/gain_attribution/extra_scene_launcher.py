"""Worker launcher for scenes outside the pinned B lookup (colin RTX 5090 runs).

`B_EXTRA_SCENES` (JSON: scene → {dataset, archive, manifest, custom_config, vanilla_config, image_dir, calibration})
extends `trial.BASE.sequence_paths` inside the worker process for those scenes only, then applies the legacy-IMU fill
(`legacy_imu_launcher.install`) and runs `B_PATCH_WORKER` like legacy_imu_launcher does.
"""
import json
import os
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    import legacy_imu_launcher
    extra = json.loads(os.environ.get('B_EXTRA_SCENES', '{}'))
    if extra:
        import run_online_dense_training as trial
        old = trial.BASE.sequence_paths

        def paths(dataset, scene):
            s = extra.get(scene)
            if s is None or s['dataset'] != dataset:
                return old(dataset, scene)
            return {k: Path(v) for k, v in s.items() if k != 'dataset'}
        trial.BASE.sequence_paths = paths
    legacy_imu_launcher.install()
    patch = Path(os.environ['B_PATCH_WORKER'])
    sys.argv = [str(patch), *sys.argv[1:]]
    sys.path[0] = str(patch.parent)
    runpy.run_path(str(patch), run_name='__main__')
