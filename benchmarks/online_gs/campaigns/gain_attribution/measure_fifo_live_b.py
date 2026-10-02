#!/usr/bin/env python3
"""B-recipe copy of measure_fifo_live_ours.py (adds --selector; loss comes from the B environment set by the driver).

Measure real tracker + paired mapper throughput at native sensor timing.

The archive is used ONLY as a raw RGB/timestamp/calibration/heldout manifest.
No recorded tracker packets, poses, depths, or evaluation trajectories are read.
Model loading is reported separately before the first sensor arrival. All runtime
tracking, mapping initialization, dense pose fitting and transfers are timed.
This is a throughput probe, not a quality or hard-real-time certification.
"""
import argparse
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace

import run_online_dense_training as trial

ROOT = trial.BASE.WORKSPACE
BACKEND = Path('/home/intern/VIGS-SLAM-custom')
AUDIT_ROOT = trial.ROOT / 'live_worker_integration_audit'


def write(path, value):
    path.write_text(json.dumps(value, indent=2, default=str) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', choices=['aria', 'rpng', 'utmm', 'rot'], default='aria')
    p.add_argument('--time-scale',type=float,default=1.)
    p.add_argument('--queue-size',type=int,default=2)
    p.add_argument('--renders-per-kf', type=int, default=0,
                   help='0: uncapped idle refinement; positive: shared render credit')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--frontend-iters', choices=['current','official'], default='official')
    p.add_argument('--selector', choices=['ervs','rr'], default='ervs')
    a = p.parse_args()
    if not a.worker:
        a.output.mkdir(parents=True, exist_ok=False)
        trial.common.evaluation.panel.v2.gpu_idle()
        env = trial.environment()
        env['EXP78B_CUSTOM_ROOT'] = str(BACKEND)
        env['PYTHONPATH'] = str(BACKEND/'vigs')+':'+str(BACKEND)+':'+env['PYTHONPATH']
        env['VIGS_PIPELINE_TELEMETRY'] = '1'
        cmd = [str(trial.BASE.PYTHON_ENV/'bin/python'), str(Path(__file__).resolve()),
               '--worker', '--dataset', a.dataset, '--renders-per-kf', str(a.renders_per_kf),
               '--frontend-iters', a.frontend_iters,
               '--output', str(a.output.resolve())]
        write(a.output/'command.json', cmd)
        engine_root = ROOT/'results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090'
        write(a.output/'runtime_assets.json', {'cwd':str(engine_root), 'source_root':str(BACKEND)})
        with (a.output/'run.log').open('x') as log:
            result = subprocess.run(cmd, env=env, cwd=engine_root, stdout=log, stderr=subprocess.STDOUT)
        print('COMPLETE', a.output, result.returncode, flush=True)
        raise SystemExit(result.returncode)

    import main_validation_rot_adapter as rot
    rot.install()
    extensions = AUDIT_ROOT/'v6_current_stream_extensions'
    for name in ('vigs_backends', 'lietorch_backends'):
        sys.path.insert(0, str(extensions/name))
    import cv2
    import numpy as np
    import torch
    import yaml
    import vigs_backends, lietorch_backends
    import vigs as vigs_module
    import gs_backend
    import exp78b_replay_gsslam_mapping as replay
    from exp78b_frozen_archive import FrozenTrackerArchive
    from render_work_audit import RenderWorkAudit
    from keyframe_render_budget import KeyframeRenderBudget
    from mapper_execution_guard import MappingBoundaryReached
    from concurrent.futures import CancelledError

    expected = json.loads((extensions/'manifest.json').read_text())['built']
    for module in (vigs_backends, lietorch_backends):
        actual = {'path': module.__file__, 'sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()}
        # Machine-relocated copies: the binary must be byte-identical (sha); the path may differ.
        assert actual['sha256'] == expected[module.__name__]['sha256'], actual
    scene = {'aria':'aria1253', 'rpng':'table_06', 'utmm':'square-1','rot':'aria1253rot'}[a.dataset]
    dataset='aria' if a.dataset=='rot' else a.dataset
    setup_dir = AUDIT_ROOT/('v5_packet_identity/aria_setup' if a.dataset == 'aria'
                           else f'v9_productive_worker/three_scene/{a.dataset}_setup')
    if a.dataset=='rot':setup_dir=rot.INPUT/'setup'
    setup = json.loads((setup_dir/'native_setup.json').read_text())
    raw = FrozenTrackerArchive(trial.BASE.sequence_paths(dataset, scene)['archive'])
    # Fail loudly if this measurement accidentally requests an archived estimate.
    def forbidden(*args, **kwargs):
        raise RuntimeError('Recorded tracker state is forbidden in live capacity measurement')
    raw.load_geometry = forbidden
    raw.load_event_payload = forbidden
    raw.mapping_packet = forbidden
    config = copy.deepcopy(setup['config'])
    sensor = yaml.safe_load(Path(raw.manifest['input_config']).read_text())
    config['IMU'] = sensor['IMU']
    density = replay.configure_density_policy(config, 'online_rank', 2.5, 2.0)[1]
    replay.install_online_density_policy(density)
    for key in ('pcd_downsample_init','pcd_downsample'):config['Dataset'][key]*=.8
    config['Training']['parallel'] = True
    config['Training']['gs_dedicated_stream'] = True
    args = SimpleNamespace(**setup['args'])
    args.output = args.save_dir = str(a.output)
    args.buffer = 700
    args.gs_dedicated_stream = True
    args.replay_time_scale = a.time_scale
    args.mapping_disable_densify_prune=True
    args.mapping_observation_topology_gate=False
    args.mapping_model_scheduler=False
    args.mapping_after_imu_init=True
    args.image_size = raw.preprocessing['output_image_size_hw']
    args.weights = str(BACKEND/'pretrained_models/droid.pth')
    args.seed = 0
    # Restore the live benchmark setting, not the mapper-replay placeholder.
    # Official eval_rpng_mono.py uses 20; eval_utmm_mono.py uses 15.
    # Aria live scripts use 20. This enables IMU pose prediction, not IMU BA.
    args.IMU_poseinit_after = 15 if a.dataset == 'utmm' else 20
    if a.frontend_iters == 'official':
        args.frontend_iters1, args.frontend_iters2 = 4, 2
    try:
        args.imus = np.loadtxt(raw.manifest['input_imu'], delimiter=',')
    except ValueError:
        args.imus = np.loadtxt(raw.manifest['input_imu'])
    # VIGS applies raw IMU scale/timestamp conversion once in its constructor.
    vigs_module.load_config = lambda path: copy.deepcopy(config)
    random.seed(0); np.random.seed(0); torch.manual_seed(0); torch.cuda.manual_seed_all(0)
    source = a.output/'source'; source.mkdir()
    files = list((BACKEND/'vigs').glob('*.py')) + [Path(__file__).resolve(),
        Path(inspect.getfile(RenderWorkAudit)), Path(inspect.getfile(KeyframeRenderBudget)),
        BACKEND/'vigs/gaussian/utils/slam_utils.py']
    lock = {}
    for file in files:
        data = file.read_bytes(); digest = hashlib.sha256(data).hexdigest()
        target = source/(digest[:12]+'_'+file.name); target.write_bytes(data)
        lock[str(file)] = {'sha256':digest, 'copy':str(target)}
    write(a.output/'source_lock.json', lock)
    write(a.output/'effective_config.json', {'config':config, 'args':{k:v for k,v in vars(args).items() if k!='imus'},
        'raw_archive_manifest':str(raw.root/'archive_manifest.json'), 'tracking_packets_replayed':False,
        'native_steps_per_packet':0, 'renders_per_kf_cap':a.renders_per_kf,
        'model_loading_outside_stream_clock':True, 'time_scale':a.time_scale})
    import fixed40_geometry as geometry
    geometry.install()
    from protected_opacity_prune import ProtectedOpacityPrune
    prune_holder={}
    original_constructor=vigs_module.GSBackEnd
    def constructor(*values,**kwargs):
        mapper=original_constructor(*values,**kwargs)
        prune_holder['prune']=ProtectedOpacityPrune(mapper,threshold=.1,every_renders=300)
        return mapper
    vigs_module.GSBackEnd=constructor
    audit = RenderWorkAudit(gs_backend, torch)
    load_start = time.monotonic()
    host = vigs_module.VIGS(args, online_mapping={
        'membership':'growth','selector':a.selector,'schedule':'unified',
        'heldout':raw.heldout_uids,'seed':0,'reserve_seconds':.5,
        'max_pending_packets':a.queue_size,'renders_per_kf':40,
        'optimizer_batch_size':1,'batch_quotas':(3,3,6),'selection_count_scope':'all_rgb',
        'growth_budget_scope':'dense_only','kappa':16,'tau':4.,'scale_projection':True})
    runtime=host._online_runtime;budget=runtime.unified_budget
    dispatch=runtime.worker.dispatch
    def counted_dispatch(packet):
        uid=packet.get('_arrival_uid',int(host._latest_frame_idx))
        audit.context={'arrival_uid':uid,'phase':'unified'}
        result=dispatch(packet)
        with torch.cuda.stream(runtime.stream),host.gs._gaussian_lock:
            prune_holder['prune'].after_packet(audit.training,uid)
            runtime.stream.synchronize()
        return result
    runtime.worker.dispatch=counted_dispatch
    # Camera calibration is fixed and available before streaming.
    image0 = cv2.imread(str(raw.image_dir/raw.arrivals[0]['source_name']))
    h0, w0 = image0.shape[:2]; crop = int(raw.preprocessing['cropborder'])
    intrinsics = torch.tensor(raw.calibration[:4], dtype=torch.float32)
    intrinsics[2:] -= crop; h0 -= 2*crop; w0 -= 2*crop
    h, w = args.image_size
    intrinsics[[0,2]] *= w/w0; intrinsics[[1,3]] *= h/h0
    torch.cuda.synchronize()
    model_load_seconds = time.monotonic()-load_start
    started = time.monotonic()
    first_sensor = float(raw.arrivals[0]['sensor_timestamp'])
    sensor_duration = float(raw.arrivals[-1]['sensor_timestamp'])-first_sensor
    duration = a.time_scale*sensor_duration
    runtime.guard.deadline = started+duration
    rows = []; error = None
    try:
        for rec in raw.arrivals:
            uid = int(rec['frame_uid']); timestamp = float(rec['sensor_timestamp'])
            due = started+a.time_scale*(timestamp-first_sensor)
            host._replay_next_arrival_deadline = due
            if due > time.monotonic():
                time.sleep(due-time.monotonic())
            begin = time.monotonic()
            image = raw.load_rgb(uid)[None]
            try:
                host.track(uid, timestamp, image, intrinsics=intrinsics[None].clone(),
                           is_last=(rec is raw.arrivals[-1]))
            except (MappingBoundaryReached, CancelledError):
                runtime.worker.raise_on_error()
                if time.monotonic() < runtime.guard.deadline-runtime.guard.reserve_seconds:
                    raise
            end = time.monotonic()
            rows.append({'uid':uid, 'sensor_seconds':timestamp-first_sensor,
                'start_seconds':begin-started, 'end_seconds':end-started,
                'start_lag_ms':1000*(begin-due), 'end_lag_ms':1000*(end-due),
                'track_call_ms':1000*(end-begin), 'training_renders':audit.training,
                'backward_renders':audit.counts['backward'], 'kf_admissions':len(budget.seen),
                'tracking_kfs':int(host.video.counter.value),
                'mapper_queue':runtime.worker.queue.qsize()})
            if uid%200 == 0:
                write(a.output/'progress.json', rows[-1])
                print('PROGRESS', json.dumps(rows[-1]), flush=True)
    except BaseException:
        error = traceback.format_exc(); print(error, flush=True)
    finally:
        tracking_end = time.monotonic()
        runtime.close()
        host._gs_thread.join(timeout=20)
        if host.pgba:
            host.video.pgobuf.stop()
            if host.mp_backend is not None: host.mp_backend.join(timeout=5)
        torch.cuda.synchronize()
    report = runtime.report()
    write(a.output/'runtime.json', report)
    write(a.output/'frames.json', rows)
    write(a.output/'renders.json', {'counts':dict(audit.counts),'rows':audit.rows,'errors':audit.errors})
    budget.sync(); write(a.output/'kf_admissions.json', budget.report())
    services = [s for g in report['training']['generations'] for s in g['services']]
    committed = sum(len(s['uids']) for s in services)
    native = sum(len(s['uids']) for s in services if s['source']=='native')
    def quantile(key):
        values = [row[key] for row in rows]
        return {str(q):float(np.percentile(values,q)) for q in [50,95,99,100]} if values else {}
    result = {'dataset':dataset, 'scene':scene,'key':a.dataset,'time_scale':a.time_scale,'gpu':torch.cuda.get_device_name(),
        'image_size_hw':args.image_size,'input_frames':len(raw.arrivals), 'tracked_frames':len(rows),
        'duration_seconds':duration,'sensor_duration_seconds':sensor_duration, 'tracking_elapsed_seconds':tracking_end-started,
        'model_load_seconds':model_load_seconds,'renders_per_kf_cap':a.renders_per_kf,'selector':a.selector,
        'trt_disabled':os.environ.get('VIGS_DISABLE_TRT')=='1',
        'frontend_iterations':[args.frontend_iters1,args.frontend_iters2],
        'IMU_poseinit_after':args.IMU_poseinit_after,
        'training_renders':audit.training,'backward_renders':audit.counts['backward'],
        'committed_renders':committed,'native_committed_renders':native,
        'additional_committed_renders':committed-native,'kf_admissions':len(budget.seen),
        'unique_mapper_kfs':len({uid for _,uid in budget.seen}),
        'renders_per_kf_admission':committed/len(budget.seen) if budget.seen else None,
        'tracking_kfs_final':int(host.video.counter.value),
        'start_lag_ms':quantile('start_lag_ms'),'end_lag_ms':quantile('end_lag_ms'),
        'track_call_ms':quantile('track_call_ms'),
        'mapper_queue_max':max((r['mapper_queue'] for r in rows), default=0),
        'peak_cuda_allocated_bytes':torch.cuda.max_memory_allocated(),
        'geometry':{'config':geometry.CFG,'stats':geometry.STATS},
        'protected_pruning':prune_holder['prune'].report(),
        'worker':report['worker'],'zero_tail_observed':report['boundaries']['zero_tail_observed'],
        'overruns':report['boundaries']['overruns'],'error':error,
        'queue_policy':'bounded FIFO ordinary pending packets; reset/rescale/PGBA protected',
        'source_unchanged':all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v['sha256'] for f,v in lock.items()),
        'quality_evaluated':False}
    write(a.output/'result.json', result)
    print('RESULT', json.dumps(result), flush=True)
    if error or report['worker']['error']: raise SystemExit(1)
    from export_live_capacity_map import export
    export(host, raw, a.output, runtime.guard.main_gaussian_steps_completed)
    assert runtime.guard.main_gaussian_steps_completed == len([
        r for r in report['boundaries']['optimizer_completions'] if r['role']=='main'])


if __name__ == '__main__': main()
