"""B sequence-path entries for prepared Oxford Spires sequences (dataset key 'oxford').

Inputs come from prepare_oxford_vigs.py (/ssd/intern/paperExperiments/data/oxford_spires/vigs/<seq>); archives and
setups from prepare_oxford_capture.py under the same folder (archive/, setup/). Distortion is zero after
rectification, so the evaluator's optional undistort is a no-op.
"""
from pathlib import Path

PREP = Path('/ssd/intern/paperExperiments/data/oxford_spires/vigs')
SEQUENCES = ('2024-07-09-new-college-01', '2024-07-09-new-college-02', '2024-03-20-christ-church-05',
             '2024-07-09-new-college-04', '2024-05-20-bodleian-library-02')


def paths(seq):
    d = PREP / seq
    # mapping_v7.yaml: vigs_final_v7_aria.yaml with this sequence's IMU block (written by prepare_oxford_capture.py)
    return {'archive': d / 'archive', 'fixed_manifest': d / 'heldout.json', 'custom_config': d / 'mapping_v7.yaml',
            'vanilla_config': d / 'config.yaml', 'image_dir': d / 'rgb', 'calibration': d / 'calib.txt'}


def install(trial):
    old = trial.BASE.sequence_paths

    def sequence_paths(dataset, scene):
        if dataset == 'oxford' and scene in SEQUENCES:
            return paths(scene)
        return old(dataset, scene)
    trial.BASE.sequence_paths = sequence_paths
