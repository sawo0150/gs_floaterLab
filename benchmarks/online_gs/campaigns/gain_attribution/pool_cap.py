"""FIFO cap on the KF and dense sampling pools of the unified mapper (Oxford long sequences; env B_POOL_CAP).

At each UnifiedTrainingSet.reserve call the instance's `keyframes` and `admitted` sets are temporarily reduced to the
newest B_POOL_CAP uids (uids increase with arrival, so this drops the oldest first) and restored afterwards; reserve
only reads them (pool construction and window intersection). Membership, admission, counts, Gaussians and the window
are unchanged; dropped views simply stop being sampled. Installed as an instance attribute in __init__, so it wraps
whatever reserve (B, group_k_patch, sampling_mode_patch) the class has when the trainer builds its policy, without
touching the sha-checked reserve source. Writes <output>/pool_cap.json.
"""
import atexit
import json
import os
from pathlib import Path
import sys

STATS = dict(reserve_calls=0, capped_calls=0, max_keyframes=0, max_admitted=0, dropped_max_keyframes=0,
             dropped_max_admitted=0)


def install():
    cap = int(os.environ['B_POOL_CAP'])
    import unified_view_training as U
    init = U.UnifiedTrainingSet.__init__

    def __init__(self, *a, **k):
        init(self, *a, **k)
        bound = self.reserve

        def reserve(*ra, **rk):
            kf, ad = self.keyframes, self.admitted
            STATS['reserve_calls'] += 1
            STATS['max_keyframes'] = max(STATS['max_keyframes'], len(kf))
            STATS['max_admitted'] = max(STATS['max_admitted'], len(ad))
            cut = False
            if len(kf) > cap:
                self.keyframes = type(kf)(sorted(kf)[-cap:]); cut = True
                STATS['dropped_max_keyframes'] = max(STATS['dropped_max_keyframes'], len(kf) - cap)
            if len(ad) > cap:
                self.admitted = type(ad)(sorted(ad)[-cap:]); cut = True
                STATS['dropped_max_admitted'] = max(STATS['dropped_max_admitted'], len(ad) - cap)
            STATS['capped_calls'] += cut
            try:
                return bound(*ra, **rk)
            finally:
                self.keyframes, self.admitted = kf, ad
        self.reserve = reserve
    U.UnifiedTrainingSet.__init__ = __init__
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'pool_cap.json').write_text(json.dumps(dict(cap=cap, **STATS), indent=1))
    atexit.register(dump)
