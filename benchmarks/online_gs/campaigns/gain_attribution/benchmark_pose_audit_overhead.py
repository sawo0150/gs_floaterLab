#!/usr/bin/env python3
"""Measure optional diagnostic overhead with identical causal training inputs."""
import argparse
import json
from pathlib import Path
import statistics
import time
from diagnose_pose_correspondence_refresh import (
    torch, FrozenTrackerArchive, QualityAuditedRefiner, trial, cases, triplet,
    engine, digest, fingerprint)
from dense_visual_pose_reuse import CorrespondenceRefiner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    model = trial.BASE.PAPER_ROOT / 'pretrained_models/droid.pth'
    paths = [Path(__file__).resolve(), model, Path(__file__).with_name('diagnose_pose_correspondence_refresh.py'),
             Path(__file__).with_name('diagnose_pose_color_conventions.py')]
    paths += [trial.BACKEND / 'vigs' / n for n in ('dense_visual_pose.py', 'dense_visual_pose_reuse.py',
                                                  'dense_pose_quality_refiner.py', 'dense_pose_quality.py')]
    sources = {str(p): digest(p) for p in paths}
    deps = fingerprint()
    shared = QualityAuditedRefiner(model)
    rows = []
    for dataset, scene in trial.SCENES:
        archive = FrozenTrackerArchive(trial.BASE.sequence_paths(dataset, scene)['archive'])
        for p in (archive.root / 'archive_manifest.json', archive.root / archive.manifest['arrivals'],
                  Path(archive.manifest['input_calibration'])):
            sources[str(p)] = digest(p)
        event, left, right, uid = cases(archive)[1]
        views = triplet(archive, event, (left, right, uid), sources)
        refiner = engine(shared.net)
        refiner.refine(*views)
        times = {'audit': [], 'solver': []}
        maximum = 0.
        for repeat in range(22):
            outputs = {}
            order = ('audit', 'solver') if repeat % 2 else ('solver', 'audit')
            for mode in order:
                method = QualityAuditedRefiner.refine if mode == 'audit' else CorrespondenceRefiner.refine
                torch.cuda.synchronize()
                started = time.monotonic()
                outputs[mode], stats = method(refiner, *views)
                torch.cuda.synchronize()
                seconds = time.monotonic() - started
                assert stats['correspondences_reused']
                if repeat >= 2:
                    times[mode].append(seconds)
            delta = float((outputs['audit'] - outputs['solver']).abs().max())
            maximum = max(maximum, delta)
            assert delta == 0., 'Observer changed pose output'
        row = {'dataset': dataset, 'scene': scene, 'event_id': event['event_id'], 'dense_uid': uid,
            'times_seconds': times, 'median_seconds': {m: statistics.median(t) for m, t in times.items()},
            'max_pose_difference': maximum}
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != 'times_seconds'}), flush=True)
    assert fingerprint() == deps
    assert all(digest(p) == h for p, h in sources.items())
    result = {'protocol': 'pose_audit_overhead_v1', 'cases': rows, 'source_lock': sources,
        'native_dependencies': deps, 'gaussian_updates': 0, 'heldout_or_eval_poses_used': False,
        'limitations': 'Warm-solver microbenchmark only; not an online speed/quality gain.'}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.output / 'runner_source.py').write_bytes(Path(__file__).read_bytes())


if __name__ == '__main__':
    main()
