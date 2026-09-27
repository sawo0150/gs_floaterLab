#!/usr/bin/env python3
"""Warm mapper microbenchmark: same views/state, 1/2/4 renders per Adam.

Reconstruct the existing causal40 paired endpoint, then time disposable clones.
This is an offline timing diagnostic, never an online/quality result.
"""
import argparse
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

import run_online_dense_training as trial

HERE = Path(__file__).resolve().parent
SCENES = {'aria': 'aria1253', 'rpng': 'table_06', 'utmm': 'square-1'}


def write(path, data):
    path.write_text(json.dumps(data, indent=2, default=str) + '\n')


def benchmark(mapper, archive, audit, output):
    import torch
    import gs_backend
    from types import SimpleNamespace
    # Remove render-audit hooks; the completed causal replay remains on disk.
    for name, original in audit.originals.items():
        setattr(gs_backend, name, original)
    torch.cuda.synchronize()
    # The replay worker is closed. Only this offline diagnostic may prepare
    # cameras now; its disposable clone uses an independent optimizer.
    mapper.deferred_dense_observations.guard = SimpleNamespace(reject_if_unsafe=lambda kind: None)
    trainer = mapper.online_view_trainer
    trainer.sync()
    policy = copy.deepcopy(trainer.policy)
    policy.next_role = 'keyframe'
    chosen = []
    for _ in range(96):
        selection = policy.reserve(1)
        assert selection is not None
        chosen.append(selection.uids[0])
        policy.commit(selection)
    assert not (set(chosen) & archive.heldout_uids)
    roles = ['keyframe' if uid in trainer.policy.keyframes else 'dense' for uid in chosen]
    assert roles == ['keyframe', 'dense'] * 48
    views = {}
    trainer.cache_images = 128
    for uid in dict.fromkeys(chosen):
        source = (mapper.viewpoints[uid] if uid in trainer.policy.keyframes
                  else mapper.deferred_dense_observations.prepare(uid))
        view = mapper._training_viewpoint(source)
        # Warm resident targets and fixed online-estimated pose; preparation is
        # intentionally excluded to isolate render/backward/update grouping.
        view.original_image_gpu = trainer.image(view)
        if view.depth is not None and view.depth_gpu is None:
            view.depth_gpu = view.depth.to(device='cuda', dtype=torch.float32)[None]
        views[uid] = view
    original_model = mapper.gaussians
    original_state = copy.deepcopy(original_model.optimizer.state_dict())
    model = original_model.detached_clone(mapper.opt_params)
    mapper.gaussians = model
    names = ('xyz', 'features_dc', 'features_rest', 'scaling', 'rotation', 'opacity')
    start_count = trainer.policy.rgb_steps_completed

    def reset():
        with torch.no_grad():
            for name in names:
                getattr(model, '_' + name).copy_(getattr(original_model, '_' + name))
        model.optimizer.load_state_dict(copy.deepcopy(original_state))
        model.optimizer.zero_grad(set_to_none=True)
        for name in names:
            assert torch.equal(getattr(model, '_' + name), getattr(original_model, '_' + name))
        torch.cuda.synchronize()

    def block(batch, n=96, profile=False):
        records = []
        def mark():
            if not profile:
                return None
            event = torch.cuda.Event(enable_timing=True)
            event.record()
            return event
        def finish(stage, begin):
            if profile:
                records.append((stage, begin, mark()))
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        memory_start = torch.cuda.memory_allocated()
        start = time.perf_counter()
        renders = steps = 0
        for offset in range(0, n, batch):
            model.update_learning_rate(start_count + offset + 1)
            losses = []
            for uid in chosen[offset:offset + batch]:
                begin = mark()
                rendered = gs_backend.render(views[uid], model, mapper.background)
                finish('render', begin)
                begin = mark()
                losses.append(trainer.refinement_loss(views[uid], rendered))
                finish('loss', begin)
                renders += 1
            begin = mark()
            loss = losses[0]
            for other in losses[1:]:
                loss = loss + other
            loss.backward()
            finish('backward', begin)
            begin = mark()
            model.optimizer.step()
            model.optimizer.zero_grad(set_to_none=True)
            finish('optimizer_zero', begin)
            torch.cuda.current_stream().synchronize()
            steps += 1
            del loss, losses, rendered
        seconds = time.perf_counter() - start
        assert renders == n and steps == n // batch
        assert all(torch.isfinite(getattr(model, '_' + k)).all() for k in names)
        stages = {}
        for name, begin, end in records:
            stages[name] = stages.get(name, 0.) + begin.elapsed_time(end) / n
        return dict(batch=batch, renders=renders, optimizer_steps=steps,
                    seconds=seconds, ms_per_render=1000 * seconds / n,
                    peak_extra_bytes=torch.cuda.max_memory_allocated() - memory_start,
                    cuda_stage_ms_per_render=stages)

    # All variants warmed, then exact initial parameters and Adam moments reset.
    for batch in (1, 2, 4):
        reset(); block(batch, 16)
    rows = []
    for repeat, order in enumerate(itertools.permutations((1, 2, 4))):
        for batch in order:
            reset()
            row = block(batch)
            row.update(repeat=repeat, order=list(order))
            rows.append(row)
            print('TIMING', archive.manifest.get('dataset'), repeat, batch,
                  round(row['ms_per_render'], 3), flush=True)
    profiles = []
    for batch in (1, 2, 4):
        reset(); profiles.append(block(batch, 32, profile=True))
    medians = {str(b): statistics.median(r['ms_per_render'] for r in rows if r['batch'] == b)
               for b in (1, 2, 4)}
    result = dict(protocol='grouped_render_warm_timing_v1', gpu=torch.cuda.get_device_name(),
                  gaussian_count=len(model.get_xyz), image_hw=[views[chosen[0]].image_height, views[chosen[0]].image_width],
                  selected_uids=chosen, roles=roles, repeats=6, rows=rows, profiles=profiles,
                  median_ms_per_render=medians,
                  speedup={b: medians['1'] / value for b, value in medians.items()},
                  time_reduction_percent={b: 100 * (1 - value / medians['1']) for b, value in medians.items()},
                  exact_initial_parameters_and_adam_reset=True, heldout_overlap=[],
                  loss_reduction='sum (vanilla-style); KF RGBD+normal / dense RGB unchanged',
                  learning_rate_clock='render position; first render in group; no LR scaling',
                  timing='synchronized wall time, resident images/poses, includes render/loss/backward/Adam/zero_grad/group sync',
                  exclusions=['tracking', 'view sampling', 'pose preparation', 'image transfer', 'topology', 'online guard/audit hooks'],
                  quality_claim=False, strict_online=False, production_changed=False)
    write(output / 'timing.json', result)
    mapper.gaussians = original_model
    print('TIMING_COMPLETE', medians, flush=True)


def worker(args):
    # Append a callback to the original main without editing its locked source.
    source = HERE / 'run_kf15_render_worker.py'
    tree = ast.parse(source.read_text())
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    main_node.body.extend(ast.parse('_timing_callback(mapper, archive, audit)').body)
    ast.fix_missing_locations(tree)
    namespace = {'__name__': 'timing_replay', '__file__': str(source),
                 '_timing_callback': lambda m, a, audit: benchmark(m, a, audit, args.output)}
    base = trial.ROOT / 'live_worker_integration_audit'
    setup = base / ('v5_packet_identity/aria_setup' if args.dataset == 'aria'
                    else f'v9_productive_worker/three_scene/{args.dataset}_setup')
    sys.argv = [str(source), '--setup', str(setup), '--extensions', str(base / 'v6_current_stream_extensions'),
                '--output', str(args.output / 'replay'), '--renders-per-kf', '40', '--seed', '0',
                '--membership', 'immediate', '--selector', 'ervs', '--schedule', 'paired_kf_dense',
                '--selection-count-scope', 'recent_photometric']
    exec(compile(tree, str(source), 'exec'), namespace)
    namespace['main']()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', choices=list(SCENES))
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'runner_source.py').write_bytes(Path(__file__).read_bytes())
    backend = Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files = [Path(__file__), HERE / 'run_kf15_render_worker.py'] + list((backend / 'vigs').rglob('*.py'))
    lock = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    write(args.output / 'source_lock.json', lock)
    env = trial.environment()
    env['EXP78B_CUSTOM_ROOT'] = str(backend)
    env['PYTHONPATH'] = str(backend / 'vigs') + ':' + str(backend) + ':' + env['PYTHONPATH']
    results = []
    for dataset in ([args.dataset] if args.dataset else SCENES):
        trial.common.evaluation.panel.v2.gpu_idle()
        out = args.output / dataset
        out.mkdir()
        command = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
                   '--worker', '--dataset', dataset, '--output', str(out)]
        write(out / 'command.json', command)
        print('START', dataset, flush=True)
        with (out / 'run.log').open('x') as log:
            code = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        if code:
            raise RuntimeError(f'{dataset} failed; see {out}/run.log')
        row = json.loads((out / 'timing.json').read_text())
        row.update(dataset=dataset, scene=SCENES[dataset])
        results.append(row)
        write(args.output / 'summary.json', results)
        print('DONE', dataset, row['median_ms_per_render'], flush=True)
    changed = [p for p, sha in lock.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha]
    write(args.output / 'source_check.json', {'changed': changed})
    assert not changed


if __name__ == '__main__':
    main()
