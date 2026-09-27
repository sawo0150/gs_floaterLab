#!/usr/bin/env python3
"""Compare cached and fresh correspondences on successive causal training packets."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from diagnose_pose_color_conventions import (
    torch, SE3, FrozenTrackerArchive, QualityAuditedRefiner, trial,
    camera, cases, matrix, projection_check, reprojection_error, fingerprint)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def triplet(archive, event, uids, sources):
    left, right, uid = uids
    assert not set(uids) & archive.heldout_uids
    assert left < uid < right <= int(event['emitted_at_frame_uid'])
    path = archive.root / event['payload']
    sources[str(path)] = digest(path)
    payload = archive.load_event_payload(event)
    ids = [int(u) for u in payload['frame_uids']]
    anchors, poses = [], []
    for aid in (left, right):
        pos = ids.index(aid)
        ref = payload['geometry_refs'][pos]
        paths = [ref] if isinstance(ref, str) else [ref['depth'], ref['normal']]
        for relative in paths:
            path = archive.root / relative
            sources[str(path)] = digest(path)
        geometry = archive.load_geometry(ref)
        pose = SE3(payload['poses'][pos:pos + 1].cuda())
        poses.append(pose)
        anchors.append(camera(aid, archive.load_rgb(aid), geometry['depth'], pose.matrix()[0], payload['intrinsics'][pos]))
    alpha = (uid - left) / (right - left)
    initial = (SE3.exp((poses[1] * poses[0].inv()).log() * alpha) * poses[0]).matrix()[0]
    dense = camera(uid, archive.load_rgb(uid), None, initial, payload['intrinsics'][ids.index(left)])
    for aid in uids:
        path = archive.image_dir / archive.arrival_by_uid[aid]['source_name']
        sources[str(path)] = digest(path)
    return (*anchors, dense)


def last_revisit(archive, event, left, right, uid):
    """Offline stress-case selection, never an online policy or lookahead input."""
    later = None
    started = False
    for row in archive.events:
        if row['event_id'] == event['event_id']:
            started = True
            continue
        if not started:
            continue
        if row['kind'] == 'mapper_reset':
            break  # Never carry measurements across map generations.
        if row['kind'] != 'keyframe_update':
            continue
        keys = sorted(int(u) for u in row['frame_uids'] if int(u) not in archive.heldout_uids)
        if uid in keys or left not in keys or right not in keys:
            continue
        if keys.index(right) != keys.index(left) + 1:
            continue  # Actual reuse key would invalidate a changed anchor pair.
        later = row
    return later


def engine(net):
    result = QualityAuditedRefiner.__new__(QualityAuditedRefiner)
    result.net, result.cache, result.measurements = net, {}, {}
    return result


def solve(refiner, views):
    torch.cuda.synchronize()
    start = time.monotonic()
    pose, stats = refiner.refine(*views)
    torch.cuda.synchronize()
    return pose, {'seconds': time.monotonic() - start, **stats}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'runner_source.py').write_bytes(Path(__file__).read_bytes())
    deps = fingerprint()
    (args.output / 'runtime_dependencies.json').write_text(json.dumps(deps, indent=2) + '\n')
    model_path = trial.BASE.PAPER_ROOT / 'pretrained_models/droid.pth'
    source_paths = [Path(__file__).resolve(), model_path,
        Path(__file__).with_name('diagnose_pose_color_conventions.py'),
        Path(trial.__file__), trial.BASE.WORKSPACE / 'benchmarks/online_gs/exp78b_frozen_archive.py']
    source_paths += [trial.BACKEND / 'vigs' / name for name in
        ('dense_visual_pose.py', 'dense_visual_pose_reuse.py', 'dense_pose_quality.py', 'dense_pose_quality_refiner.py')]
    sources = {str(p): digest(p) for p in source_paths}
    checks = projection_check()
    shared = QualityAuditedRefiner(model_path)
    rows = []
    for dataset, scene in trial.SCENES:
        archive = FrozenTrackerArchive(trial.BASE.sequence_paths(dataset, scene)['archive'])
        for p in (archive.root / 'archive_manifest.json', archive.root / archive.manifest['arrivals'],
                  Path(archive.manifest['input_calibration'])):
            sources[str(p)] = digest(p)
        for first, left, right, uid in cases(archive):
            later = last_revisit(archive, first, left, right, uid)
            if later is None:
                rows.append({'dataset': dataset, 'dense_uid': uid, 'skipped': 'no same-pair revisit before reset'})
                continue
            initial_views = triplet(archive, first, (left, right, uid), sources)
            current_views = triplet(archive, later, (left, right, uid), sources)
            warm = engine(shared.net)
            _, original_stats = solve(warm, initial_views)
            before = [matrix(a).clone() for a in current_views[:2]]
            poses = {'interpolated': matrix(current_views[2])}
            stats = {}
            poses['cached'], stats['cached'] = solve(warm, current_views)
            fresh = engine(shared.net)
            # Reuse image features so this comparison isolates rebuilding
            # correspondences, not re-encoding identical RGB observations.
            fresh.cache = dict(warm.cache)
            poses['fresh'], stats['fresh'] = solve(fresh, current_views)
            assert stats['cached']['correspondences_reused']
            assert not stats['fresh']['correspondences_reused']
            assert all(torch.equal(matrix(a), p) for a, p in zip(current_views[:2], before))
            errors, masks = {}, {}
            for mode, pose in poses.items():
                pairs = [reprojection_error(a, current_views[2], pose) for a in current_views[:2]]
                errors[mode] = torch.cat([p[0].flatten() for p in pairs])
                masks[mode] = torch.cat([p[1].flatten() for p in pairs])
            common = torch.stack(list(masks.values())).all(0)
            assert common.any()
            row = {'dataset': dataset, 'scene': scene, 'dense_uid': uid, 'anchor_uids': [left, right],
                'first_event': first['event_id'], 'later_event': later['event_id'],
                'first_available_through_uid': first['emitted_at_frame_uid'],
                'later_available_through_uid': later['emitted_at_frame_uid'],
                'initial_solve': original_stats, 'stats': stats,
                'poses_w2c': {m: p.cpu().tolist() for m, p in poses.items()},
                'common_support_fraction': float(common.float().mean()),
                'rgb_l1': {m: float(e[common].mean()) for m, e in errors.items()}}
            rows.append(row)
            print(json.dumps({k: row[k] for k in ('dataset', 'dense_uid', 'first_event', 'later_event', 'rgb_l1')}), flush=True)
            (args.output / 'cases.partial.json').write_text(json.dumps(rows, indent=2) + '\n')
            del warm, fresh
    assert all(digest(p) == sha for p, sha in sources.items())
    assert fingerprint() == deps
    result = {'protocol': 'causal_correspondence_refresh_diagnostic_v1', 'cases': rows,
        'projection_check': checks, 'source_lock': sources, 'gaussian_updates': 0,
        'heldout_or_eval_poses_used': False, 'quality_claim': False,
        'limitations': 'Offline causal-prefix stress cases, not actual service trajectory or streaming cost. Current-packet interpolation is shared by both solvers. RGB residual is not GT pose error. No mapper/evaluator changed.'}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
