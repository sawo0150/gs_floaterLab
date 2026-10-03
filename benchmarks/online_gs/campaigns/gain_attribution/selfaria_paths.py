"""B sequence-path entries for self-recorded Aria VRS sequences not used before (dataset key 'selfaria').

Inputs from prepare_selfaria.py (scripts/incremental/build_vigs_aria_input.py: camera-rgb rectified to the 1024×1024
pinhole fx=fy=500 used by every Aria scene, imu-right, per-recording Tcb from the VRS factory calibration) under
/ssd/intern/paperExperiments/data/self_aria/vigs/<seq>/.
"""
from pathlib import Path

VRS_ROOT = Path('/ssd/intern/paperExperiments/data/self_aria/0416_Data')
PREP = Path('/ssd/intern/paperExperiments/data/self_aria/vigs')
VRS = {'snu_floor2_1': '0227_snu_floor2_1/snu_floor2_1.vrs', 'snu_floor2_2': '0227_snu_floor2_2/snu_floor2_2.vrs',
       'snu_floor3_1': '0227_snu_floor3_1/snu_floor3_1.vrs', '919c_418': '0408_919C_418/0408_919c-418_test.vrs',
       '301_2F': '0416_301-2F/0416_301-2F.vrs', '301_3F': '0416_301-3F-002/0416_301-3F.vrs'}
SEQUENCES = tuple(VRS)


def paths(seq):
    d = PREP / seq
    return {'archive': d / 'archive', 'fixed_manifest': d / 'heldout.json', 'custom_config': d / 'mapping_v7.yaml',
            'vanilla_config': d / 'config.yaml', 'image_dir': d / 'rgb', 'calibration': d / 'calib.txt'}


def install(trial):
    old = trial.BASE.sequence_paths

    def sequence_paths(dataset, scene):
        if dataset == 'selfaria' and scene in SEQUENCES:
            return paths(scene)
        return old(dataset, scene)
    trial.BASE.sequence_paths = sequence_paths
