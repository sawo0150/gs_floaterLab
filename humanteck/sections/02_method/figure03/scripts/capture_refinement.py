#!/usr/bin/env python3
"""Fork a diagnostic continuation at a common event; never resume its stream."""
import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

WORK = Path('/home/intern/gs_floaterLab')
sys.path.insert(0, str(WORK/'benchmarks/online_gs'))


class BranchComplete(Exception):
    pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--arm', required=True, choices=['ours', 'baseline'])
    p.add_argument('--event', required=True, type=int)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'Use a fresh branch directory'
    out.mkdir(parents=True)
    source = WORK/'results/figure03_convergence_20260921/aria301_305'/args.arm
    command = json.loads((source/'mapping_command.json').read_text())
    command[command.index('--output')+1] = str(out)
    (out/'mapping_command.json').write_text(json.dumps(command, indent=2)+'\n')
    module = importlib.import_module(Path(command[1]).stem)
    import torch
    import numpy as np
    from scipy.spatial.transform import Rotation
    from lietorch import SE3
    from exp78b_frozen_archive import FrozenTrackerArchive
    from exp78b_timeline_scheduler import FrozenTimelineScheduler
    archive = FrozenTrackerArchive(command[command.index('--archive')+1])
    state = {}
    if args.arm == 'ours':
        original = module.install_render_telemetry
        def install(mapper):
            telemetry = original(mapper)
            state.update(mapper=mapper, telemetry=telemetry)
            return telemetry
        module.install_render_telemetry = install
        original_guard = module.install_adam_guard
        def install_guard(mapper, guard):
            state['guard'] = guard
            return original_guard(mapper, guard)
        module.install_adam_guard = install_guard
    else:
        original = module.install_telemetry
        def install(mapper, guard):
            telemetry = original(mapper, guard)
            state.update(mapper=mapper, telemetry=telemetry, guard=guard)
            return telemetry
        module.install_telemetry = install

    def steps():
        return (state['guard'].main_gaussian_steps_completed if args.arm == 'ours'
                else state['telemetry']['optimizer_steps_completed'])

    def poses(mapper):
        result = {}
        for uid, camera in mapper.viewpoints.items():
            matrix = np.eye(4)
            matrix[:3,:3] = camera.R.detach().cpu().numpy()
            matrix[:3,3] = camera.T.detach().cpu().numpy()
            result[int(uid)] = matrix
        return result

    def branch(metadata):
        mapper = state['mapper']
        assert mapper.initialized and len(mapper.current_window)
        state['guard'].next_control_due = None
        before_steps = steps()
        before_renders = state['telemetry']['training_rasterized_view_updates']
        fixed_poses = poses(mapper)
        keys = sorted(fixed_poses)
        assert not set(keys) & archive.heldout_uids
        dense = sorted(int(k) for k in getattr(mapper, 'polish_viewpoints', {}))
        assert not set(dense) & archive.heldout_uids
        prefix = int(metadata['emitted_at_frame_uid'])
        assert max(keys+dense) <= prefix
        # Same formula as causal dense interpolation, using only current KF poses.
        # Last 300 arrived frames, bracketed by available training KFs; fixed cohort.
        uids = sorted(u for u in archive.heldout_uids
                      if max(keys[0], prefix-300) <= u <= keys[-1])
        eval_views = []
        for uid in uids:
            right_pos = int(np.searchsorted(keys, uid))
            assert 0 < right_pos < len(keys)
            left, right = keys[right_pos-1:right_pos+1]
            def se3(matrix):
                vector = np.r_[matrix[:3,3], Rotation.from_matrix(matrix[:3,:3]).as_quat()]
                return SE3(torch.tensor(vector, device='cuda', dtype=torch.float32)[None])
            l, r = se3(fixed_poses[left]), se3(fixed_poses[right])
            alpha = float(uid-left)/float(right-left)
            pose = (SE3.exp((r*l.inv()).log()*alpha)*l).matrix()[0].cpu().tolist()
            eval_views.append({'frame_index':uid,'pose_w2c':pose,'left':left,'right':right})
        assert len(eval_views) >= 20
        checks = [0,5,10,20,30,45,60,90,120]
        snapshots = []
        def save(k):
            path = out/f'additional_{k:03d}.ply'
            mapper.gaussians.save_ply(path)
            snapshots.append({'additional_iteration':k,'path':str(path),
                              'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                              'gaussians':len(mapper.gaussians.get_xyz),
                              'total_optimizer_steps':steps(),
                              'additional_renders':state['telemetry']['training_rasterized_view_updates']-before_renders})
            print('REFINEMENT', args.arm, args.event, k, flush=True)
        save(0)
        for k in range(1,121):
            if args.arm == 'ours':
                mapper._exp78b_replay_scope_active = True
                try:
                    completed = mapper.idle_map_rr_step(iters=1, batch_size=1)
                finally:
                    mapper._exp78b_replay_scope_active = False
                assert completed, 'Native replay refused this diagnostic step'
            else:
                # Outside the closed stream event, native adapter delegates to map.
                # One rendered view / Adam step matches the Ours replay work unit.
                mapper.map(mapper.current_window, iters=1, max_viewpoints=1)
            assert steps()-before_steps == k
            assert state['telemetry']['training_rasterized_view_updates']-before_renders == k
            if k in checks:
                save(k)
        final_poses = poses(mapper)
        for uid in fixed_poses:
            np.testing.assert_array_equal(fixed_poses[uid], final_poses[uid])
        record = {'arm':args.arm,'event_id':args.event,'input_prefix':prefix,
                  'source_run':str(source),'seed':0,'evaluation_views':eval_views,
                  'training_kf_uids':keys,'training_dense_uids':dense,
                  'initial_optimizer_steps':before_steps,'initial_training_renders':before_renders,
                  'snapshots':snapshots,'pose_unchanged':True,'heldout_training_overlap':0,
                  'protocol':'Controlled fixed-input continuation, not live streaming. One rendered view and Gaussian Adam step per iteration. Own online initial maps; native Ours appearance replay versus native vanilla map(max_viewpoints=1). Native topology policies retained. No subsequent stream events, final BA or pose optimization. Event-cohort evaluation uses causal interpolated KF poses frozen at branch entry.'}
        (out/'refinement_manifest.json').write_text(json.dumps(record, indent=2)+'\n')
        raise BranchComplete()

    run = FrozenTimelineScheduler.run
    def observed_run(scheduler, *, process_packet, **kwargs):
        def packet(item, *a):
            result = process_packet(item, *a)
            if int(item.metadata['event_id']) == args.event:
                branch(item.metadata)
            return result
        return run(scheduler, process_packet=packet, **kwargs)
    FrozenTimelineScheduler.run = observed_run
    sys.argv = command[1:]
    try:
        module.main()
    except BranchComplete:
        return
    raise RuntimeError('Target event was not reached')


if __name__ == '__main__':
    main()
