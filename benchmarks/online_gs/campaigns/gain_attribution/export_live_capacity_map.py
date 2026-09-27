"""Export a stopped live map and its OWN tracker trajectory for heldout eval.

Trajectory filling is evaluation only, after saving the immutable Gaussian map.
No frozen tracker estimates, global BA, or Gaussian optimization is run here.
"""
import json
from pathlib import Path
import time


def export(host, raw, output, observed_steps):
    import numpy as np
    import torch
    import lietorch
    output=Path(output)
    start=time.monotonic()
    if not host.images or not len(host.gs.gaussians.get_xyz):
        raise RuntimeError('No completed live map to evaluate')
    host.gs.gaussians.save_ply(str(output/'3dgs_before_final.ply'))
    # The tracker filler consumes post-run tracker state only for rendering
    # evaluation; its poses never return to the stopped training worker.
    trajectory=host.traj_filler(host.images)
    poses=trajectory.inv().data.cpu().numpy()
    times=np.asarray([float(rec['sensor_timestamp']) for rec in raw.arrivals])
    if len(poses)!=len(times):raise RuntimeError('Evaluation trajectory incomplete')
    np.savetxt(output/'traj_full_beforeBA.txt',np.column_stack([times,poses]))
    n=int(host.video.counter.value)
    uids=host.video.tstamp[:n].long().cpu().numpy()
    kfposes=lietorch.SE3(host.video.poses[:n]).inv().data.cpu().numpy()
    np.savetxt(output/'traj_kf_beforeBA.txt',np.column_stack([times[uids],kfposes]))
    np.save(output/'intrinsics.npy',host.video.intrinsics[0].cpu().numpy()*8)
    origins={int(x) for x in host.gs.gaussians.unique_kfIDs.cpu().tolist() if int(x)>=0}
    used=origins|set(map(int,host.gs.viewpoints))
    trainer=getattr(host.gs,'online_view_trainer',None)
    if trainer:
        used|={int(uid) for g in trainer.report()['generations'] for s in g['services'] for uid in s['uids']}
    if used&raw.heldout_uids:raise RuntimeError('Live map used fixed heldout RGB')
    (output/'mapped_uids.json').write_text(json.dumps(sorted(used)))
    finite=all(bool(torch.isfinite(getattr(host.gs.gaussians,'_'+key)).all())
               for key in ['xyz','opacity','scaling','rotation','features_dc'])
    (output/'export.json').write_text(json.dumps({'evaluation_only_seconds':time.monotonic()-start,
        'trajectory_source':'this run online tracker + evaluation-only trajectory filler',
        'gaussians':len(host.gs.gaussians.get_xyz),'finite':finite,
        'mapping_steps_before_export':observed_steps,'frozen_tracker_state_used':False},indent=2))
    if not finite:raise RuntimeError('Nonfinite Gaussian parameters')
