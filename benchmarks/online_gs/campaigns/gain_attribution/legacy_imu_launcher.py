"""Launch a sampling patch (group_k_patch.py / sampling_mode_patch.py) with the cvpr legacy-IMU fix.

Old exp78b frozen-tracker archives (schema v2, e.g. UTMM fast-straight) have no `input_imu` in the manifest. As in
run_cvpr_measurements.install_legacy_imu_metadata, the path is filled in memory only with the inventory rule
`<input_image_directory>/../imu_ours.txt` (UTMM/Aria) or `imu.txt` (RPNG). Archives with the key are untouched.
Usage: B_PATCH_WORKER=<patch.py> python legacy_imu_launcher.py <worker args>
"""
import os
from pathlib import Path
import runpy
import sys


def install():
    import exp78b_frozen_archive as frozen
    original = frozen.FrozenTrackerArchive.__init__

    def init(self, root):
        original(self, root)
        m = self.manifest
        if 'input_imu' not in m:
            image_dir = Path(m['input_image_directory'])
            name = 'imu.txt' if 'rpng' in image_dir.parts else 'imu_ours.txt'
            imu = image_dir.parent / name
            if not imu.exists():
                raise FileNotFoundError(f'legacy IMU fallback missing: {imu}')
            m['input_imu'] = str(imu)
            print(f'[legacy_imu_launcher] input_imu filled: {imu}', flush=True)
    frozen.FrozenTrackerArchive.__init__ = init


if __name__ == '__main__':
    patch = Path(os.environ['B_PATCH_WORKER'])
    install()
    sys.argv = [str(patch), *sys.argv[1:]]
    sys.path[0] = str(patch.parent)
    runpy.run_path(str(patch), run_name='__main__')
