"""B sequence-path entries for M2DGR room_01 / gate_03 (dataset key 'm2dgr'; RealSense D435i colour + handsfree IMU).

Inputs from prepare_m2dgr.py under /ssd/intern/paperExperiments/data/m2dgr/vigs/<seq>/ (rgb/<ns>.jpg byte copies of
the compressed stream, imu.txt, calib.txt with radtan, config.yaml, mapping_v7.yaml, heldout.json).
"""
from pathlib import Path

BAGS = Path('/ssd/intern/paperExperiments/data/m2dgr/prepared')
CALIB = Path('/ssd/intern/paperExperiments/data/m2dgr/calibration')
PREP = Path('/ssd/intern/paperExperiments/data/m2dgr/vigs')
SEQUENCES = ('room_01', 'gate_03')


def paths(seq):
    d = PREP / seq
    return {'archive': d / 'archive', 'fixed_manifest': d / 'heldout.json', 'custom_config': d / 'mapping_v7.yaml',
            'vanilla_config': d / 'config.yaml', 'image_dir': d / 'rgb', 'calibration': d / 'calib.txt'}


def install(trial):
    old = trial.BASE.sequence_paths

    def sequence_paths(dataset, scene):
        if dataset == 'm2dgr' and scene in SEQUENCES:
            return paths(scene)
        return old(dataset, scene)
    trial.BASE.sequence_paths = sequence_paths
