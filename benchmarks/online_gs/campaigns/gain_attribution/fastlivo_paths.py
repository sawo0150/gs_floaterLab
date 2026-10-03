"""B sequence-path entries for FAST-LIVO2 sequences (dataset key 'fastlivo').

Raw inputs are the ETH-preprocessed FAST-LIVO2 release already in the official VIGS layout
(rgb/<ns>.png 1280×1024 radtan, imu.txt, intrinsics.txt, extrinsics.txt). VIGS reads Tcb from ../extrinsics.txt when
the image path contains 'livo2' (official and B). Derived files (heldout.json, config.yaml, mapping_v7.yaml, archive,
setup) live under /ssd/intern/paperExperiments/data/fast_livo2/vigs/<seq>/.
"""
from pathlib import Path

RAW = Path('/ssd/intern/paperExperiments/data/fast_livo2/prepared/fast-livo2-dataset')
PREP = Path('/ssd/intern/paperExperiments/data/fast_livo2/vigs')
SEQUENCES = ('CBD_Building_01', 'CBD_Building_02', 'HKU_Campus', 'Retail_Street', 'SYSU_01')


def paths(seq):
    d = PREP / seq
    return {'archive': d / 'archive', 'fixed_manifest': d / 'heldout.json', 'custom_config': d / 'mapping_v7.yaml',
            'vanilla_config': d / 'config.yaml', 'image_dir': RAW / seq / 'rgb', 'calibration': RAW / seq / 'intrinsics.txt'}


def install(trial):
    old = trial.BASE.sequence_paths

    def sequence_paths(dataset, scene):
        if dataset == 'fastlivo' and scene in SEQUENCES:
            return paths(scene)
        return old(dataset, scene)
    trial.BASE.sequence_paths = sequence_paths
