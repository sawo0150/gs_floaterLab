#!/usr/bin/env python3
"""B ablation chain pilot (PREREG: context/experiments/campaigns/06_gain_attribution/b_ablation_chain/PREREG.md).

Every arm = the official adopted-B worker (run_selected_worker.py) with the official recipe arguments and
B environment, plus only the override arguments below (argparse: last value wins). Same preflight and
execution audit as scripts/selected_mapping/run.py, followed by the twice-run held-out evaluation.

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile \
    python run_b_ablation_chain.py [--only chain|ervs_regime] [--scenes rot rpng] [--limit N]
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
MAIN = Path('/home/intern/VIGS-SLAM-custom')            # relocated by the machine profile
SEL = MAIN / 'scripts/selected_mapping'
RECIPE = MAIN / 'configs/selected_mapping_fixed40.json'
OUT = ROOT / 'results/campaigns/gain_attribution/b_ablation_chain/v1'
PREREG = ROOT / 'context/experiments/campaigns/06_gain_attribution/b_ablation_chain/PREREG.md'

CHAIN = [('R1', ['--batch-quotas', '12', '0', '0']),
         ('R2', ['--auxiliary-mode', 'kf_native']),
         ('R3', ['--membership', 'immediate']),
         ('R4', []),
         ('R4rr', ['--selector', 'rr'])]
ERVS_REGIME = [('K4_ervs', ['--kappa', '4']),
               ('K4_rr', ['--kappa', '4', '--selector', 'rr'])]
PLAN = ([('chain', s, b, a, x) for s in ('rot', 'rpng') for b in (15, 40) for a, x in CHAIN]
        + [('ervs_regime', s, 15, a, x) for s in ('rot', 'rpng') for a, x in ERVS_REGIME])


def read(p):
    return json.loads(Path(p).read_text())


def write(p, x):
    Path(p).write_text(json.dumps(x, indent=2, default=str) + '\n')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def head(repo):
    return subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()


def service_stats(report):
    """Completed service counts per uid and role in the final mapper generation."""
    gen = report['training']['generations'][-1]
    pol = gen['policy']
    counts = {'keyframe_pool': {}, 'dense': {}, 'window': {}}
    for s in gen['services']:
        for uid, role in zip(s['uids'], s['roles']):
            key = {'keyframe': 'keyframe_pool', 'keyframe_native': 'keyframe_pool', 'dense': 'dense',
                   'window': 'window'}.get(role)
            if key:
                counts[key][int(uid)] = counts[key].get(int(uid), 0) + 1
    out = dict(generations=len(report['training']['generations']), final_keyframes=len(pol.get('keyframes', [])),
               final_admitted_dense=len(pol.get('admitted_dense', [])))
    for key, pool in (('keyframe_pool', pol.get('keyframes', [])), ('dense', pol.get('admitted_dense', []))):
        values = [counts[key].get(int(u), 0) for u in pool]
        if values and statistics.mean(values) > 0:
            out[key] = dict(n=len(values), mean=statistics.mean(values), min=min(values), max=max(values),
                            cv=statistics.pstdev(values) / statistics.mean(values),
                            never=sum(v == 0 for v in values))
    out['role_services'] = {k: sum(v.values()) for k, v in counts.items()}
    return out


def recent_third(final_result):
    rows = final_result['per_view']
    held = [r for r in rows if r.get('predeclared_fixed_manifest_split')]
    rows = held or rows
    last = max(r['frame_index'] for r in rows)
    sel = [r['psnr'] for r in rows if r['frame_index'] >= 2 * last / 3]
    return dict(n=len(sel), psnr=statistics.mean(sel) if sel else None)


def run_one(phase, key, budget, arm, extra, ctx):
    lock, trial, preflight, gpu_idle, recipe_environment = ctx
    out = OUT / phase / key / f'render{budget}' / arm
    done = out.parent / f'{arm}.row.json'
    if done.exists():
        return read(done)
    setup, ext = Path(lock['datasets'][key]['setup']), Path(lock['extensions'])
    provenance = preflight(setup, ext, out)                     # refuses an existing output directory
    args = list(read(RECIPE)['worker_args']) + ['--renders-per-kf', str(budget)] + extra
    cmd = [sys.executable, str(SEL / 'run_selected_worker.py'), *args,
           '--setup', str(setup), '--extensions', str(ext), '--output', str(out)]
    env = recipe_environment(trial.BASE.mapping_environment(True), lock)
    out.parent.mkdir(parents=True, exist_ok=True)
    write(out.parent / f'{arm}.command.json', dict(cmd=cmd, overrides=extra, budget=budget,
          environment={k: env[k] for k in read(RECIPE)['environment']}))
    gpu_idle()
    t0 = time.monotonic()
    with (out.parent / f'{arm}.log').open('x') as f:
        subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
    wall = time.monotonic() - t0
    report = read(out / 'render_result.json')
    runtime = read(out / 'geometry_runtime.json')
    if not report['valid_execution'] or not all(report['checks'].values()):
        raise RuntimeError(f'execution audit failed: {report["checks"]}')
    if runtime['dense_config']['mode'] != 'off' or runtime['stats']['aux_renders'] != 0:
        raise RuntimeError('unexpected dense depth or auxiliary render')
    dataset, scene = provenance['dataset'], provenance['scene']
    ev = trial.common.evaluation.panel.run_evaluation_twice(
        out, dataset, scene, trial.BASE.sequence_paths(dataset, scene)['fixed_manifest'])
    if not ev['pass']:
        raise RuntimeError(f'evaluation consistency failed: {ev}')
    final = read(out / 'psnr/strict_fixed_manifest/final_result.json')
    fixed = final['predeclared_fixed_manifest_posthoc']
    row = dict(phase=phase, scene=scene, budget=budget, arm=arm, overrides=' '.join(extra),
               psnr=ev['fixed_psnr_first'], ssim=fixed.get('mean_ssim'), lpips=fixed.get('mean_lpips'),
               views=fixed['view_count'], recent_third=recent_third(final), gaussians=report['gaussians'],
               training_renders=report['render_counts']['training'], mapping_seconds=report['mapping_seconds'],
               process_wall_s=wall, services=service_stats(report),
               trajectory_sha=sha(out / 'traj_full_beforeBA.txt'), raster_sha=runtime['raster_sha'],
               warp_backward=runtime['warp_backward'], output=str(out))
    write(done, row)
    return row


def summarize(rows):
    fields = ['phase', 'scene', 'budget', 'arm', 'overrides', 'psnr', 'ssim', 'lpips', 'recent_third_psnr',
              'gaussians', 'training_renders', 'mapping_seconds', 'dense_pool', 'dense_cv', 'dense_min',
              'kf_cv', 'kf_min', 'output']
    with (OUT / 'summary.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            s = r['services']
            w.writerow(dict({k: r[k] for k in fields if k in r}, recent_third_psnr=r['recent_third']['psnr'],
                            dense_pool=s['final_admitted_dense'], dense_cv=s.get('dense', {}).get('cv'),
                            dense_min=s.get('dense', {}).get('min'), kf_cv=s.get('keyframe_pool', {}).get('cv'),
                            kf_min=s.get('keyframe_pool', {}).get('min')))
    write(OUT / 'summary.json', rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--only', choices=['chain', 'ervs_regime'])
    p.add_argument('--scenes', nargs='+', choices=['rot', 'rpng'], default=['rot', 'rpng'])
    p.add_argument('--limit', type=int, help='stop after N new runs (smoke test)')
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(SEL))
    from selected_mapping_check import load_lock, preflight, gpu_idle
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / 'protocol.json').exists():
        write(OUT / 'protocol.json', dict(prereg=str(PREREG), prereg_sha256=sha(PREREG), main_head=head(MAIN),
              lab_head=head(ROOT), recipe=read(RECIPE), plan=PLAN, seed=0,
              machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
              machine_profile_sha256=sha(os.environ['ROGO_MACHINE_PROFILE']),
              gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                           '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows, new = [], 0
    for phase, key, budget, arm, extra in PLAN:
        if (a.only and phase != a.only) or key not in a.scenes:
            continue
        fresh = not (OUT / phase / key / f'render{budget}' / f'{arm}.row.json').exists()
        if fresh and a.limit is not None and new >= a.limit:
            break
        print('START', phase, key, budget, arm, flush=True)
        try:
            row = run_one(phase, key, budget, arm, extra, ctx)
        except Exception:
            write(OUT / 'failure.json', dict(phase=phase, key=key, budget=budget, arm=arm,
                                             traceback=traceback.format_exc(), time=time.time()))
            raise
        new += int(fresh)
        rows.append(row)
        summarize(rows)
        print('DONE', phase, key, budget, arm, f"psnr={row['psnr']:.4f}",
              f"recent={row['recent_third']['psnr']:.4f}", f"map_s={row['mapping_seconds']:.1f}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
