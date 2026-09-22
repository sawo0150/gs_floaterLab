#!/usr/bin/env python3
"""Observe the existing mapping harness without changing its training recipe."""
import argparse
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path

WORK = Path('/home/intern/gs_floaterLab')
sys.path.insert(0, str(WORK / 'benchmarks/online_gs'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=['ours', 'baseline'], required=True)
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-runtime', type=Path)
    parser.add_argument('--checkpoint-interval', type=int, default=50)
    args = parser.parse_args()
    assert args.checkpoint_interval > 0
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / 'mapping_replay_runtime.json').exists(), 'Do not overwrite a completed run'
    checkpoint_dir = output / 'checkpoints'
    checkpoint_dir.mkdir(exist_ok=True)
    assert not list(checkpoint_dir.glob('*.ply')), 'Existing checkpoints; use a fresh output directory'
    command = json.loads((args.source_run / 'mapping_command.json').read_text())
    command[command.index('--output')+1] = str(output)
    if args.reference_runtime:
        command[command.index('--reference-service-runtime')+1] = str(args.reference_runtime)
    (output / 'mapping_command.json').write_text(json.dumps(command, indent=2)+'\n')
    module = importlib.import_module(Path(command[1]).stem)
    import torch
    from exp78b_frozen_archive import FrozenTrackerArchive
    state = {'mapper': None, 'event': {}, 'telemetry': None, 'guard': None,
             'snapshots': [], 'snapshot_seconds': 0., 'count': 0}
    original_load = FrozenTrackerArchive.load_event_payload

    def load_event(archive, metadata):
        result = original_load(archive, metadata)
        state['event'] = {key: metadata.get(key) for key in
                          ('event_id', 'kind', 'emitted_at_frame_uid', 'sensor_timestamp')}
        return result
    FrozenTrackerArchive.load_event_payload = load_event

    def snapshot(count, final=False):
        if not final and count % args.checkpoint_interval:
            return
        mapper = state['mapper']
        torch.cuda.synchronize()
        started = time.monotonic()
        path = checkpoint_dir / f'iter_{count:05d}{"_final" if final else ""}.ply'
        mapper.gaussians.save_ply(path)
        elapsed = time.monotonic() - started
        state['snapshot_seconds'] += elapsed
        record = {'iteration': count, 'path': str(path), 'final': final,
                  'phase': 'after_run' if final else 'immediately_after_gaussian_optimizer_step',
                  'gaussians': int(mapper.gaussians.get_xyz.shape[0]),
                  'training_renders': state['telemetry']['training_rasterized_view_updates'],
                  'event': dict(state['event']), 'save_seconds': elapsed,
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        state['snapshots'].append(record)
        with (output / 'checkpoints.jsonl').open('a') as f:
            f.write(json.dumps(record)+'\n')
        print('FIG3_CHECKPOINT', count, record['gaussians'], flush=True)

    if args.arm == 'ours':
        install_guard = module.install_adam_guard
        install_render = module.install_render_telemetry

        def guard_installer(mapper, guard):
            original = install_guard(mapper, guard)
            guarded = torch.optim.Adam.step
            state['mapper'], state['guard'] = mapper, guard

            def observed_step(optimizer, *a, **kw):
                result = guarded(optimizer, *a, **kw)
                if optimizer is mapper.gaussians.optimizer:
                    state['count'] = guard.main_gaussian_steps_completed
                    snapshot(state['count'])
                return result
            torch.optim.Adam.step = observed_step
            return original

        def render_installer(mapper):
            state['telemetry'] = install_render(mapper)
            return state['telemetry']
        module.install_adam_guard = guard_installer
        module.install_render_telemetry = render_installer
    else:
        install_hooks = module.install_gaussian_hooks

        def hook_installer(mapper, telemetry, guard):
            install_hooks(mapper, telemetry, guard)
            counted = mapper.gaussians.optimizer.step
            state['mapper'], state['telemetry'] = mapper, telemetry

            def observed_step(*a, **kw):
                result = counted(*a, **kw)
                state['count'] = telemetry['optimizer_steps_completed']
                snapshot(state['count'])
                return result
            mapper.gaussians.optimizer.step = observed_step
        module.install_gaussian_hooks = hook_installer

    sys.argv = command[1:]
    result = module.main()
    assert result in (None, 0), result
    snapshot(state['count'], final=True)
    runtime = json.loads((output / 'mapping_replay_runtime.json').read_text())
    assert state['count'] == runtime['optimizer_steps_completed']
    assert runtime.get('auxiliary_adam_steps_completed', 0) == 0
    record = {'source_run': str(args.source_run), 'arm': args.arm,
              'iteration_definition': 'cumulative completed Gaussian Adam steps, including initialization and steps before map resets',
              'checkpoint_interval': args.checkpoint_interval, 'snapshots': state['snapshots'],
              'checkpoint_save_seconds': state['snapshot_seconds'],
              'training_recipe_changed': False, 'evaluation_during_training': False,
              'protocol': 'frozen causal tracker, unbounded fixed-work mapping; not a live wall-time benchmark'}
    (output / 'capture_manifest.json').write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    main()
