#!/usr/bin/env python3
"""Fixed-render causal diagnostic through the actual common VIGS worker.

Tracker packets are frozen causal estimates, not a concurrent tracker result.
Only the mapper receives explicitly arrived RGB/IMU. Evaluation trajectories
are exported after worker shutdown and are never used for pose preparation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import threading
import time
import traceback
from collections import Counter
from types import SimpleNamespace

import run_online_dense_training as trial


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2,default=str)+'\n')


from run_arrived_online_worker import training_checks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--setup',required=True,type=Path)
    parser.add_argument('--reference',type=Path,help='Existing fixed-work baseline render_result.json')
    parser.add_argument('--renders-per-kf',type=int,default=15)
    parser.add_argument('--extensions',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--membership',choices=['kf_only','growth','immediate'],default='growth')
    parser.add_argument('--kappa',type=int,default=64)
    parser.add_argument('--tau',type=float,default=1.)
    parser.add_argument('--growth-budget-scope',choices=['whole_pool','dense_only'],default='whole_pool')
    parser.add_argument('--selector',choices=['ervs','rr'],default='ervs')
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--schedule',choices=['mixed','paired_kf_dense','unified'],default='mixed')
    parser.add_argument('--auxiliary-mode',choices=['dense_rgb','kf_rgb','kf_native'],default='dense_rgb')
    parser.add_argument('--batch-quotas',nargs=3,type=int,default=None)
    parser.add_argument('--optimizer-batch-size',type=int,default=1,help='0: one Adam per full selection batch; default: per-image Adam')
    parser.add_argument('--unified-scale-projection',action=argparse.BooleanOptionalAction,default=True)
    parser.add_argument('--dense-blur-filter',action='store_true')
    parser.add_argument('--blur-energy-ratio',type=float,default=.8)
    parser.add_argument('--blur-frequency-ratio',type=float,default=.9)
    parser.add_argument('--selection-count-scope',choices=['all_rgb','photometric','recent_photometric'])
    parser.add_argument('--disable-densify-prune',action='store_true')
    args=parser.parse_args()
    if args.schedule=='unified': args.disable_densify_prune=True
    args.output.mkdir(parents=True,exist_ok=False)
    for name in ('vigs_backends','lietorch_backends'):
        sys.path.insert(0,str((args.extensions/name).resolve()))
    import numpy as np
    import torch
    import vigs_backends,lietorch_backends
    import yaml
    from exp78b_frozen_archive import FrozenTrackerArchive
    from exp78b_dense_imu_pose import load_processed_imu
    import exp78b_replay_gsslam_mapping as replay
    import gs_backend
    from gs_backend import GSBackEnd
    from unified_view_training import DEFAULT_BATCH_QUOTAS
    args.batch_quotas=tuple(args.batch_quotas or DEFAULT_BATCH_QUOTAS)
    from online_mapper_runtime import OnlineMapperRuntime
    from online_map_snapshots import StreamSnapshots,install as install_snapshots,capture
    from vigs import VIGS
    from render_work_audit import RenderWorkAudit
    from keyframe_render_budget import KeyframeRenderBudget
    expected=json.loads((args.extensions/'manifest.json').read_text())['built']
    binaries={m.__name__:{'path':m.__file__,'sha256':sha(Path(m.__file__))}
              for m in (vigs_backends,lietorch_backends)}
    if binaries!=expected:raise RuntimeError('Selected extension binaries do not match manifest')
    setup=torch.load(args.setup/'native_setup.pt',weights_only=False,map_location='cpu')
    provenance=json.loads((args.setup/'provenance.json').read_text())
    if sha(args.setup/'native_setup.pt')!=provenance['setup_sha256']:
        raise RuntimeError('Setup has changed')
    paths=trial.BASE.sequence_paths(provenance['dataset'],provenance['scene'])
    archive=FrozenTrackerArchive(paths['archive'])
    config=setup['config'];native_args=SimpleNamespace(**setup['args']);native_args.seed=args.seed
    native_args.save_dir=str(args.output)
    if args.disable_densify_prune:
        native_args.mapping_disable_densify_prune=True
        native_args.mapping_observation_topology_gate=False
        native_args.mapping_model_scheduler=False
    # Preserve the raw source's calibrated IMU convention rather than infer it
    # from mapper loss/topology settings. This file contains fixed calibration.
    sensor_config=yaml.safe_load(Path(archive.manifest['input_config']).read_text())
    root=Path(gs_backend.__file__).resolve().parents[1]
    source_files=list((root/'vigs').glob('*.py'))
    source_files += [Path(__file__).resolve(),Path(__file__).with_name('render_work_audit.py').resolve(),Path(__file__).with_name('keyframe_render_budget.py').resolve(),Path(__file__).with_name('run_arrived_online_worker.py').resolve(),
        root/'vigs/gaussian/utils/slam_utils.py',root/'vigs/gaussian/utils/loss_utils.py',
        Path(replay.__file__).resolve(),
        Path(sys.modules['exp78b_frozen_archive'].__file__).resolve(),
        Path(sys.modules['exp78b_dense_imu_pose'].__file__).resolve()]
    if args.disable_densify_prune:
        source_files += [Path(__file__).with_name('densify_prune_ablation_audit.py'),
                         root/'vigs/gaussian/scene/gaussian_model.py']
    source_dir=args.output/'source';source_dir.mkdir()
    source_lock={}
    for path in source_files:
        digest=sha(path);copy=source_dir/(digest[:12]+'_'+path.name)
        shutil.copy2(path,copy);source_lock[str(path)]={'sha256':digest,'copy':str(copy)}
    write(args.output/'source_lock.json',source_lock)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed);torch.cuda.manual_seed_all(args.seed)
    duration=1.5*(float(archive.arrivals[-1]['sensor_timestamp'])-float(archive.arrivals[0]['sensor_timestamp']))
    first_sensor=float(archive.arrivals[0]['sensor_timestamp'])
    reference=json.loads(args.reference.read_text()) if args.reference else None
    targets={int(r['uid']):r for r in reference['render_prefixes']} if reference else None
    if reference and (not reference['valid_execution'] or reference['kf_render_budget']['renders_per_kf']!=args.renders_per_kf):
        raise RuntimeError('Invalid or mismatched fixed-work reference')
    audit=RenderWorkAudit(gs_backend,torch)
    started=time.monotonic();deadline=None
    # All input preparation and mapper setup below is inside the whole budget.
    native_args.imus=load_processed_imu(Path(archive.manifest['input_imu']),sensor_config)
    density=replay.configure_density_policy(config,'online_rank',2.5,2.0)[1]
    replay.install_online_density_policy(density)
    mapper=GSBackEnd(config,str(args.output),native_args,use_gui=False)
    topology_audit=None
    if args.disable_densify_prune:
        from densify_prune_ablation_audit import NoDensifyPruneAudit
        topology_audit=NoDensifyPruneAudit(mapper)
    host=SimpleNamespace(gs=mapper,args=native_args,config=config,
        _gs_stream=torch.cuda.Stream(),_tracking_active=threading.Event(),
        _replay_next_arrival_deadline=None)
    host._tracking_active.set()
    runtime=OnlineMapperRuntime(host,{'membership':args.membership,'selector':args.selector,
        'seed':args.seed,'heldout':archive.heldout_uids,'deadline':deadline,'reserve_seconds':.1,
        'schedule':args.schedule,
        'batch_quotas':tuple(args.batch_quotas),'renders_per_kf':args.renders_per_kf,
        'optimizer_batch_size':args.optimizer_batch_size or None,
        'auxiliary_mode':args.auxiliary_mode,
        'kappa':args.kappa,'tau':args.tau,'growth_budget_scope':args.growth_budget_scope,
        'scale_projection':args.unified_scale_projection,
        'dense_blur_filter':({'energy_ratio':args.blur_energy_ratio,
                              'frequency_ratio':args.blur_frequency_ratio} if args.dense_blur_filter else False),
        **({'selection_count_scope':args.selection_count_scope} if args.selection_count_scope else {})})
    host._online_runtime=runtime
    budget=(runtime.unified_budget if args.schedule=='unified'
            else KeyframeRenderBudget(mapper,audit,args.renders_per_kf))
    # Disable unsolicited idle work; dispatch explicit counted work on the same worker.
    dispatch_native=runtime.worker.dispatch
    def dispatch_counted(packet):
        if '_render_target' not in packet:
            return dispatch_native(packet)
        target=int(packet['_render_target'])
        if audit.training>target:
            raise RuntimeError(f'Native work exceeded prefix budget: {audit.training}>{target}')
        with torch.cuda.stream(host._gs_stream),mapper._gaussian_lock:
            runtime._bind_topology()
            runtime._offer_arrived_intervals()
            mapper.online_view_trainer.next_arrival=None
            while audit.training<target:
                before=audit.training
                if not mapper.map(mapper.current_window,iters=1,photometric_only=True):
                    raise RuntimeError('No training view available for render budget')
                if audit.training!=before+1:
                    raise RuntimeError('Additional step did not render exactly one camera')
            host._gs_stream.synchronize()
        return audit.training
    runtime.worker.dispatch=dispatch_counted
    runtime.worker.idle=lambda:False
    ready=torch.cuda.Event();ready.record(torch.cuda.current_stream());host._gs_stream.wait_event(ready)
    thread=threading.Thread(target=VIGS._gs_worker,args=(host,),daemon=True)
    thread.start()
    events_by_uid={}
    for event in archive.events:
        events_by_uid.setdefault(int(event['emitted_at_frame_uid']),[]).append(event)
    submitted=[];arrived=[];last_input_at=None;error=None
    preparation_timing={'end':time.monotonic()}
    setup_seconds=time.monotonic()-started
    prefixes=[]
    try:
        for i,record in enumerate(archive.arrivals):
            uid=int(record['frame_uid']);sensor=float(record['sensor_timestamp'])
            if i==len(archive.arrivals)-1:
                last_input_at=time.monotonic();runtime.close()
                arrived.append({'uid':uid,'seconds':last_input_at-started,'terminal':True})
                break
            budget.start_arrival(uid)
            audit.context={'arrival_uid':uid,'phase':'native'}
            arrived.append({'uid':uid,'seconds':time.monotonic()-started})
            rgb=(torch.empty(0) if uid in archive.heldout_uids else archive.load_rgb(uid))
            runtime.observe_rgb(uid,sensor,rgb)
            before_native=audit.training
            unified_events=[];unified_submitted=[]
            for metadata in events_by_uid.get(uid,[]):
                if float(metadata['emitted_at_sensor_timestamp'])>sensor+1e-7:
                    raise RuntimeError('Tracker packet precedes causal emission')
                kind=metadata['kind']
                if kind in ('metric_rescale','mapper_reset'):
                    payload=archive.load_event_payload(metadata)
                    value=float(payload['scale']) if kind=='metric_rescale' else None
                    if args.schedule=='unified':
                        event=torch.cuda.Event();event.record(torch.cuda.current_stream())
                        unified_events.append({'_mapper_control':kind,'value':value,'_producer_event':event})
                    else:
                        runtime.submit_control(kind,value)
                    submitted.append({'event_id':metadata['event_id'],'kind':kind,'control':True})
                else:
                    packet=archive.mapping_packet(metadata,filter_heldout=True)
                    if packet is None:continue
                    if any(int(k)>uid for k in packet['tstamp']):raise RuntimeError('Future native view')
                    event=torch.cuda.Event();event.record(torch.cuda.current_stream());packet['_producer_event']=event
                    if args.schedule=='unified':
                        unified_events.append(packet)
                        row={'event_id':metadata['event_id'],'kind':kind}
                        submitted.append(row);unified_submitted.append(row)
                    else:
                        future=runtime.worker.submit(packet)
                        future.result()
                        submitted.append({'event_id':metadata['event_id'],'kind':kind,'future':future})
            if args.schedule=='unified':
                audit.context={'arrival_uid':uid,'phase':'unified'}
                future=runtime.worker.submit({'_mapping_events':unified_events,'_arrival_uid':uid})
                future.result()
                for row in unified_submitted: row['future']=future
            native_renders=0 if args.schedule=='unified' else audit.training-before_native
            budget.sync()
            target=budget.target
            if targets is not None and (uid not in targets or targets[uid]['training_renders']!=target):
                raise RuntimeError('KF credit differs from reference at same input prefix')
            if args.schedule!='unified':
                audit.context={'arrival_uid':uid,'phase':'additional'}
                runtime.worker.submit({'_render_target':target}).result()
            torch.cuda.current_stream().synchronize()
            preparation_timing['end']=time.monotonic()
            prefixes.append({'uid':uid,'training_renders':audit.training,
                             'native_renders_here':native_renders,
                             'all_renders':audit.counts['all'],
                             'main_steps':runtime.guard.main_gaussian_steps_completed,
                             'seconds':time.monotonic()-started})
            if i%100==0:
                print('PREFIX',uid,'renders',audit.training,'seconds',round(time.monotonic()-started,2),flush=True)
    except BaseException:
        error=traceback.format_exc()
    finally:
        runtime.close();thread.join(15)
        if thread.is_alive():raise RuntimeError('Worker did not stop; export forbidden')
    completed_at=time.monotonic()
    producer_work_end=preparation_timing['end']
    if error is None:
        try:runtime.worker.raise_on_error()
        except BaseException:error=traceback.format_exc()
    report=runtime.report()
    for item in submitted:
        future=item.pop('future',None)
        if future is not None:
            item.update(completed=future.done() and not future.cancelled() and future.exception() is None,
                        cancelled=future.cancelled(),error=(str(future.exception()) if future.done() and not future.cancelled() and future.exception() else None))
    trainer=report['training']
    native=sum(s['source']=='native' for g in trainer['generations'] for s in g['services'])
    photo=trainer['photometric_steps']
    observed_steps=len(report['boundaries']['optimizer_completions'])
    main_steps=runtime.guard.main_gaussian_steps_completed
    origins={int(v) for v in mapper.gaussians.unique_kfIDs.cpu().tolist() if int(v)>=0}
    used={int(uid) for g in trainer['generations'] for uid,n in g['policy']['counts'].items() if n>0}
    overlap=sorted(archive.heldout_uids & (origins|used|set(mapper.viewpoints)))
    finite=all(bool(torch.isfinite(getattr(mapper.gaussians,'_'+name)).all())
        for name in ('xyz','scaling','rotation','opacity','features_dc','features_rest'))
    checks=training_checks(trainer,main_steps)
    if topology_audit is not None:
        checks['no_densify_or_prune']=topology_audit.report()['pass']
    service_renders=sum(len(s['uids']) for g in trainer['generations'] for s in g['services'])
    checks.update(render_backward_matches=audit.training==audit.counts['backward'],
                  render_service_matches=audit.training==service_renders,
                  no_render_errors=not audit.errors,
                  exact_kf_credit=audit.training==budget.target,
                  prefix_budget_matches=(targets is None or all(r['training_renders']==targets[r['uid']]['training_renders'] for r in prefixes)),
                  per_kf_budget=(args.renders_per_kf>0 and audit.training==args.renders_per_kf*len(budget.seen)))
    mapping_seconds=max(report['worker']['stopped_at'],producer_work_end)-started
    valid=(error is None and not report['boundaries']['overruns'] and not overlap and finite
           and native+photo==main_steps and last_input_at is not None
           and all(checks.values())
           and all(r['seconds']<=last_input_at for r in runtime.guard.completions))
    report.update({'protocol':f'causal_{args.renders_per_kf}_camera_renders_per_kf_v1',
        'valid_execution':valid,'error_traceback':error,'strict_tracking_claim':False,
        'start':started,'deadline':None,'budget_seconds':None,'former_clock_budget_seconds':duration,'setup_seconds':setup_seconds,
        'last_input_at':last_input_at,'worker_joined_at':completed_at,
        'producer_preparation_end':producer_work_end,'mapping_seconds':mapping_seconds,'checks':checks,
        'optimizer_steps':observed_steps,'main_optimizer_steps':main_steps,
        'native_commits':native,'photometric_commits':photo,'heldout_overlap':overlap,
        'gaussian_parameters_finite':finite,'gaussians':len(mapper.gaussians.get_xyz),
        'arrivals':arrived,'submitted_events':submitted,'extension_binaries':binaries,
        'dataset':provenance['dataset'],'scene':provenance['scene'],
        'seed':args.seed,'membership':args.membership,'selector':args.selector,'schedule':args.schedule,
        'batch_quotas':tuple(args.batch_quotas) if args.schedule=='unified' else None,
        'optimizer_batch_size':args.optimizer_batch_size or None,
        'auxiliary_mode':args.auxiliary_mode,
        'kappa':args.kappa,'tau':args.tau,'growth_budget_scope':args.growth_budget_scope,
        'native_global_views':mapper.n_global_views,
        'densify_prune_ablation':topology_audit.report() if topology_audit else None,
        'visual_pose_audit':getattr(mapper,'_visual_pose_audit',None),
        'deferred_audit':getattr(getattr(mapper,'deferred_dense_observations',None),'audit',None),
        'quality_validated':False})
    # Exports and evaluation inputs are accessed only after every mapper thread stopped.
    report.update(render_counts=dict(audit.counts),render_prefixes=prefixes,
                  render_errors=audit.errors,kf_render_budget=budget.report(),
                  fixed_reference=str(args.reference) if args.reference else None,
                  fixed_reference_sha256=sha(args.reference) if args.reference else None,
                  fixed_time_claim=False)
    write(args.output/'render_audit.json',audit.rows)
    torch.save(capture(mapper),args.output/'final_map_state.pt')
    mapper.gaussians.save_ply(str(args.output/'3dgs_before_final.ply'))
    write(args.output/'mapped_uids.json',sorted(used|origins|set(mapper.viewpoints)))
    replay.save_shared_trajectories(archive,args.output)
    for path,entry in source_lock.items():
        if sha(Path(path))!=entry['sha256']:raise RuntimeError('Source changed during run: '+path)
    write(args.output/'render_result.json',report)
    print('ARRIVED_WORKER',provenance['dataset'],args.membership,'PASS' if valid else 'FAIL',
          'steps',main_steps,'native',native,'photo',photo,flush=True)
    if not valid:raise RuntimeError(error or 'Execution contract failed')


if __name__=='__main__':main()
