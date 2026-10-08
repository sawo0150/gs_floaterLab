"""D3 (diagnostic, non-causal): online training with end-of-stream camera poses.

Everything is online as usual (births, credit, sampler, pruning, schedule); only the camera used to *render and supervise*
a training view gets the pose that view has at the end of the stream:
  * keyframe u: the final mapper pose of u (keyframe_w2c of a reference run's final_map_state.pt; the frozen tracker
    stream makes it identical across runs);
  * dense view d: its current pose corrected by its left anchor keyframe's correction,
    w2c_d_final = w2c_d_now · inv(w2c_L_now) · w2c_L_final (relative pose to the anchor kept).
The camera is copied before the pose is replaced, so mapper state, births and tracking packets are untouched.
Base sampler: B_POSE_BASE = iid (uniform with replacement, sampling_mode_patch; pass --tau 1e12) or k16 (group_k_patch).
Writes <output>/pose_oracle.json. Usage: B_SELECTED_WORKER=... B_POSE_REF=<final_map_state.pt> python pose_oracle_patch.py ...
"""
import atexit
from collections import Counter
import copy
import json
import os
from pathlib import Path
import runpy
import sys

BASE = os.environ.get('B_POSE_BASE', 'iid')
STATS = Counter()
DELTA = []


def install():
    import torch
    import gs_backend
    ref = torch.load(os.environ['B_POSE_REF'], map_location='cpu', weights_only=False)['keyframe_w2c']
    REF = {int(u): m.double() for u, m in ref.items()}
    cls = gs_backend.GSBackEnd
    orig = cls._training_viewpoint

    def w2c(cam):
        M = torch.eye(4, dtype=torch.float64)
        M[:3, :3] = cam.R.detach().double().cpu(); M[:3, 3] = cam.T.detach().double().cpu()
        return M

    def oracle(self, v):
        u = int(v.uid)
        if u in REF:
            W = REF[u]; STATS['kf'] += 1
        else:
            pol = self.online_view_trainer.policy
            row = pol.offered.get(u)
            L = row.left if row is not None else None
            if L is None or L not in REF or L not in self.viewpoints:
                STATS['miss'] += 1
                return v
            W = w2c(v) @ torch.linalg.inv(w2c(self.viewpoints[L])) @ REF[L]; STATS['dense'] += 1
        now = w2c(v)
        if len(DELTA) < 20000:
            DELTA.append((float(torch.linalg.norm(now[:3, 3] - W[:3, 3])),
                          float(torch.rad2deg(torch.arccos(((torch.trace(now[:3, :3].T @ W[:3, :3]) - 1) / 2).clamp(-1, 1))))))
        c = copy.copy(v)
        c.update_RT(W[:3, :3].float(), W[:3, 3].float())
        return c

    def tv(self, viewpoint):
        return oracle(self, orig(self, viewpoint))
    cls._training_viewpoint = tv

    if BASE == 'iid':
        import sampling_mode_patch as SM
        SM.install()
    else:
        import group_k_patch as GK
        GK.install()
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            d = DELTA or [(0.0, 0.0)]
            (output / 'pose_oracle.json').write_text(json.dumps(dict(
                base=BASE, ref=os.environ['B_POSE_REF'], stats=dict(STATS),
                mean_translation_change=sum(a for a, _ in d) / len(d), mean_rotation_change_deg=sum(b for _, b in d) / len(d),
                p90_rotation_change_deg=sorted(b for _, b in d)[int(.9 * (len(d) - 1))]), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
