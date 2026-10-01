"""Pinned fixed40 BP/PN/U1 comparison; frozen causal tracker, no final polish."""
import argparse, atexit, hashlib, json, os, runpy, subprocess, sys, traceback
from pathlib import Path
import run_online_dense_training as trial
import main_validation_rot_adapter as rot

ROOT = trial.BASE.WORKSPACE
HERE = Path(__file__).resolve().parent
BACKEND = Path('/tmp/vigs-dense-depth-37fb9152')
GEOM = BACKEND / 'scripts/selected_mapping/geometry_merge'
MAIN = Path('/home/intern/VIGS-SLAM-custom')
RESULT = ROOT / 'results/campaigns/gain_attribution/dense_depth_four_scene/v1'
RASTER = ROOT / 'results/campaigns/gain_attribution/geometry_main_validation/raster_fixed'
SCENES = {'aria': ('aria', 'aria1253'), 'rpng': ('rpng', 'table_06'), 'utmm': ('utmm', 'square-1'), 'rot': ('aria', 'aria1253rot')}
ARMS = ['kf_rgbd_only', 'kf_rgbd_dense_rgb', 'kf_rgbd_dense_rgbd']
def read(p): return json.loads(p.read_text())
def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, default=str) + '\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def previous(key):
    base = ROOT / 'results/campaigns/gain_attribution/main_validation'
    return base / ('rot_gpu40_v1/ours' if key == 'rot' else f'gpu40_v1/{key}/ours')
def environment(arm):
    lock = read(MAIN / 'scripts/selected_mapping/source_lock.json')
    ext = Path(lock['extensions'])
    env = trial.BASE.mapping_environment(True)
    for key in list(env):
        if key.startswith('FIXED40_'): del env[key]
    paths = [RASTER, ext/'vigs_backends', ext/'lietorch_backends', BACKEND/'vigs', BACKEND, BACKEND/'scripts/selected_mapping', GEOM, HERE, ROOT/'benchmarks/online_gs']
    env.update(PYTHONPATH=':'.join(map(str, paths))+':'+env.get('PYTHONPATH',''), EXP78B_CUSTOM_ROOT=str(BACKEND), FR_WARP_BWD='1',
        FIXED40_KF_LOSS='d3', FIXED40_D3_HARD='0', FIXED40_D3_MAIN='0', FIXED40_KF_PLAIN_W='0.25', FIXED40_DENSE_SCOPE='full',
        FIXED40_DENSE_DEPTH='geo' if arm == ARMS[2] else 'off', FIXED40_DD_W='0.25',
        FIXED40_HELPERS=str(ROOT), FIXED40_OUT=str(RESULT), FIXED40_BACKEND=str(BACKEND),
        OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', PYTHONUNBUFFERED='1')
    env['PATH'] = str(trial.BASE.PYTHON_ENV/'bin')+':'+env['PATH']
    return env
def stage(a):
    rot.install()
    sys.path.insert(0, str(GEOM))
    if a.stage == 'map':
        import fixed40_geometry as g
        import fixed40_dense_depth as dd
        cfg, dcfg = g.install(), dd.install()
        import diff_gaussian_rasterization as raster
        assert Path(raster.__file__).resolve().is_relative_to(RASTER)
        def dump():
            if a.output.exists(): write(a.output/'geometry_runtime.json', dict(config=cfg, stats=g.STATS, dense_config=dcfg, dense_stats=dd.stats(), raster_module=raster.__file__, raster_sha=sha(Path(raster._C.__file__))))
        atexit.register(dump)
        lock = read(MAIN/'scripts/selected_mapping/source_lock.json')
        setup = rot.INPUT/'setup' if a.key == 'rot' else Path(lock['datasets'][a.key]['setup'])
        args = read(BACKEND/'configs/selected_mapping_fixed40.json')['worker_args']
        args[args.index('--seed')+1] = str(a.seed)
        path = BACKEND/'scripts/selected_mapping/run_kf15_render_worker.py'
        sys.argv = [str(path), *args, '--auxiliary-mode', 'kf_native' if a.arm == ARMS[0] else 'dense_rgb', '--setup', str(setup), '--extensions', lock['extensions'], '--output', str(a.output), '--reference', str(previous(a.key)/'render_result.json')]
        runpy.run_path(str(path), run_name='__main__')
    elif a.stage == 'ba':
        import local_paths as L
        L.sequence_paths = trial.BASE.sequence_paths
        L.install = lambda: trial
        import evaluate_geometry_fixed40 as ev
        d, s = SCENES[a.key]
        sys.argv = ['evaluate_geometry_fixed40', '--run-dir', str(a.output), '--dataset', d, '--scene', s]
        ev.main()
def panel(a):
    rot.install()
    sys.path.insert(0, str(MAIN/'scripts/selected_mapping'))
    from selected_mapping_check import gpu_idle
    RESULT.mkdir(parents=True, exist_ok=True)
    protocol = dict(branch='fixed40-geometry-merge', commit=subprocess.check_output(['git','-C',str(BACKEND),'rev-parse','HEAD'],text=True).strip(),
        renders_per_kf=40, adam_steps_per_render=1, seeds=[0,1], scenes=SCENES, arms=ARMS, depth='metric L1 weight .25, normals/hard-proxy off',
        regime='causal frozen tracker fixed work replay; no real-time deadline claim', geometry='heldout KF BA-depth agreement is circular auxiliary, not independent GT', recipe=read(BACKEND/'configs/selected_mapping_fixed40.json'))
    write(RESULT/'protocol.json', protocol)
    source = {str(p):sha(p) for p in [*BACKEND.glob('vigs/**/*.py'), *GEOM.glob('*.py'), Path(__file__)]}
    write(RESULT/'source_lock.json', source)
    rows = []
    for seed in a.seeds:
      for key in a.keys:
       for arm in a.arms:
        out = RESULT/key/f'seed{seed}'/arm
        row = dict(key=key, scene=SCENES[key][1], seed=seed, arm=arm, output=str(out), passed=False)
        try:
            env = environment(arm)
            for st, marker in [('map','render_result.json'), ('ba','geometry_fixed40.json')]:
                if (out/marker).exists(): continue
                gpu_idle()
                out.parent.mkdir(parents=True,exist_ok=True)
                cmd = [str(trial.BASE.PYTHON_ENV/'bin/python'), str(Path(__file__).resolve()), '--stage', st, '--key', key, '--arm', arm, '--seed', str(seed), '--output', str(out)]
                write(out.parent/f'{arm}_{st}_command.json', dict(command=cmd, environment={k:v for k,v in env.items() if k.startswith('FIXED40_') or k in ['PYTHONPATH','FR_WARP_BWD','EXP78B_CUSTOM_ROOT']}))
                print('START', key, seed, arm, st, flush=True)
                with (out.parent/f'{arm}_{st}.log').open('a') as f: subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
            x = read(out/'render_result.json')
            assert x['valid_execution'] and all(x['checks'].values()), x['checks']
            old = previous(key)
            assert [(z['uid'],z['training_renders']) for z in x['render_prefixes']] == [(z['uid'],z['training_renders']) for z in read(old/'render_result.json')['render_prefixes']]
            for n in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']: assert sha(out/n)==sha(old/n), n
            geo = read(out/'geometry_runtime.json')
            assert geo['stats']['aux_renders']==0
            if arm==ARMS[2]: assert geo['dense_stats']['transported']>0 and geo['dense_stats']['target_coverage']>0
            ev = trial.common.evaluation.panel.run_evaluation_twice(out,*SCENES[key],trial.BASE.sequence_paths(*SCENES[key])['fixed_manifest'])
            assert ev['pass']
            cohort = lambda p:[(z['uid'],z['frame_index'],z['predeclared_fixed_manifest_split']) for z in read(p/'psnr/strict_fixed_manifest/final_result.json')['per_view']]
            assert cohort(out)==cohort(old)
            assert all(sha(Path(p))==h for p,h in source.items())
            row.update(passed=True, psnr=ev['fixed_psnr_first'], gaussians=x['gaussians'], mapping_seconds=x['mapping_seconds'], renders=x['render_counts'], geometry=read(out/'geometry_fixed40.json'), runtime=geo)
            browse = RESULT/'ply'/SCENES[key][1]
            browse.mkdir(parents=True, exist_ok=True)
            link = browse/f'{SCENES[key][1]}__{arm}__iter40__seed{seed}.ply'
            if not link.exists(): link.symlink_to(out/'3dgs_before_final.ply')
        except Exception: row['error'] = traceback.format_exc()
        write(out.parent/f'{arm}_summary.json',row)
        rows.append(row)
        write(RESULT/'latest_panel.json', rows)
        print('DONE',key,seed,arm,row.get('psnr'),row['passed'],flush=True)
        if not row['passed']: raise RuntimeError(row['error'])
    print('PANEL_COMPLETE', flush=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage', choices=['map','ba']); p.add_argument('--key',choices=list(SCENES)); p.add_argument('--arm',choices=ARMS)
    p.add_argument('--seed',type=int,default=0); p.add_argument('--output',type=Path)
    p.add_argument('--keys',nargs='+',default=list(SCENES)); p.add_argument('--seeds',type=int,nargs='+',default=[0,1]); p.add_argument('--arms',nargs='+',default=ARMS)
    a=p.parse_args()
    stage(a) if a.stage else panel(a)
if __name__=='__main__': main()
