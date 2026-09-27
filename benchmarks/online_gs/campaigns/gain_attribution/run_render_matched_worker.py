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
    parser.add_argument('--clock-reference',type=Path,required=True,help='Prior clocked baseline; only additional-step timing defines quota')
    parser.add_argument('--extensions',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--membership',choices=['kf_only','growth','immediate'],default='growth')
    parser.add_argument('--selector',choices=['ervs','rr'],default='ervs')
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--schedule',choices=['mixed','paired_kf_dense'],default='mixed')
    args=parser.parse_args()
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
    from online_mapper_runtime import OnlineMapperRuntime
    from online_map_snapshots import StreamSnapshots,install as install_snapshots,capture
    from vigs import VIGS
    from render_work_audit import RenderWorkAudit
    from bisect import bisect_right
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
    # Preserve the raw source's calibrated IMU convention rather than infer it
    # from mapper loss/topology settings. This file contains fixed calibration.
    sensor_config=yaml.safe_load(Path(archive.manifest['input_config']).read_text())
    root=Path(gs_backend.__file__).resolve().parents[1]
    source_files=list((root/'vigs').glob('*.py'))
    source_files += [Path(__file__).resolve(),Path(__file__).with_name('render_work_audit.py').resolve(),Path(__file__).with_name('run_arrived_online_worker.py').resolve(),
        root/'vigs/gaussian/utils/slam_utils.py',root/'vigs/gaussian/utils/loss_utils.py',
        Path(replay.__file__).resolve(),
        Path(sys.modules['exp78b_frozen_archive'].__file__).resolve(),
        Path(sys.modules['exp78b_dense_imu_pose'].__file__).resolve()]
    source_dir=args.output/'source';source_dir.mkdir()
    source_lock={}
    for path in source_files:
        digest=sha(path);copy=source_dir/(digest[:12]+'_'+path.name)
        shutil.copy2(path,copy);source_lock[str(path)]={'sha256':digest,'copy':str(copy)}
    write(args.output/'source_lock.json',source_lock)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed);torch.cuda.manual_seed_all(args.seed)
    duration=1.5*(float(archive.arrivals[-1]['sensor_timestamp'])-float(archive.arrivals[0]['sensor_timestamp']))
    first_sensor=float(archive.arrivals[0]['sensor_timestamp'])
    clock_reference=json.loads(args.clock_reference.read_text())
    if (clock_reference['dataset'],clock_reference['scene'],clock_reference['seed']) != (provenance['dataset'],provenance['scene'],args.seed):
        raise RuntimeError('Clock reference identity mismatch')
    arrival_rows=[r for r in clock_reference['arrivals'] if not r.get('terminal')]
    arrival_times=[clock_reference['start']+r['seconds'] for r in arrival_rows]
    quotas=Counter()
    for completed in clock_reference['training']['completion_times']:
        index=bisect_right(arrival_times,completed)-1
        if index<0:raise RuntimeError('Step before first input')
        quotas[int(arrival_rows[index]['uid'])]+=1
    reference=json.loads(args.reference.read_text()) if args.reference else None
    targets={int(r['uid']):r for r in reference['render_prefixes']} if reference else None
    if reference and (not reference['valid_execution'] or reference['clock_reference_sha256']!=sha(args.clock_reference)):
        raise RuntimeError('Invalid or mismatched fixed-work reference')
    audit=RenderWorkAudit(gs_backend,torch)
    started=time.monotonic();deadline=None
    # All input preparation and mapper setup below is inside the whole budget.
    native_args.imus=load_processed_imu(Path(archive.manifest['input_imu']),sensor_config)
    density=replay.configure_density_policy(config,'online_rank',2.5,2.0)[1]
    replay.install_online_density_policy(density)
    mapper=GSBackEnd(config,str(args.output),native_args,use_gui=False)
    host=SimpleNamespace(gs=mapper,args=native_args,config=config,
        _gs_stream=torch.cuda.Stream(),_tracking_active=threading.Event(),
        _replay_next_arrival_deadline=None)
    host._tracking_active.set()
    runtime=OnlineMapperRuntime(host,{'membership':args.membership,'selector':args.selector,
        'seed':args.seed,'heldout':archive.heldout_uids,'deadline':deadline,'reserve_seconds':.1,
        'schedule':args.schedule})
    host._online_runtime=runtime
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
    prefixes=[];carry=0
    try:
        for i,record in enumerate(archive.arrivals):
            uid=int(record['frame_uid']);sensor=float(record['sensor_timestamp'])
            if i==len(archive.arrivals)-1:
                last_input_at=time.monotonic();runtime.close()
                arrived.append({'uid':uid,'seconds':last_input_at-started,'terminal':True})
                break
            audit.context={'arrival_uid':uid,'phase':'native'}
            arrived.append({'uid':uid,'seconds':time.monotonic()-started})
            rgb=(torch.empty(0) if uid in archive.heldout_uids else archive.load_rgb(uid))
            runtime.observe_rgb(uid,sensor,rgb)
            before_native=audit.training
            for metadata in events_by_uid.get(uid,[]):
                if float(metadata['emitted_at_sensor_timestamp'])>sensor+1e-7:
                    raise RuntimeError('Tracker packet precedes causal emission')
                kind=metadata['kind']
                if kind in ('metric_rescale','mapper_reset'):
                    payload=archive.load_event_payload(metadata)
                    runtime.submit_control(kind,float(payload['scale']) if kind=='metric_rescale' else None)
                    submitted.append({'event_id':metadata['event_id'],'kind':kind,'control':True})
                else:
                    packet=archive.mapping_packet(metadata,filter_heldout=True)
                    if packet is None:continue
                    if any(int(k)>uid for k in packet['tstamp']):raise RuntimeError('Future native view')
                    event=torch.cuda.Event();event.record(torch.cuda.current_stream());packet['_producer_event']=event
                    future=runtime.worker.submit(packet)
                    future.result()
                    submitted.append({'event_id':metadata['event_id'],'kind':kind,'future':future})
            native_renders=audit.training-before_native
            if targets is None:
                carry+=quotas[uid]
                count=carry if mapper.initialized and mapper.current_window else 0
                carry-=count
                target=audit.training+count
            else:
                if uid not in targets:raise RuntimeError('Missing reference prefix')
                target=targets[uid]['training_renders']
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
    service_renders=sum(len(s['uids']) for g in trainer['generations'] for s in g['services'])
    checks.update(render_backward_matches=audit.training==audit.counts['backward'],
                  render_service_matches=audit.training==service_renders,
                  no_render_errors=not audit.errors,
                  no_unused_quota=carry==0,
                  prefix_budget_matches=(targets is None or all(r['training_renders']==targets[r['uid']]['training_renders'] for r in prefixes)),
                  reference_extra_count_matches=(targets is not None or photo==sum(quotas.values())))
    mapping_seconds=max(report['worker']['stopped_at'],producer_work_end)-started
    valid=(error is None and not report['boundaries']['overruns'] and not overlap and finite
           and native+photo==main_steps and last_input_at is not None
           and all(checks.values())
           and all(r['seconds']<=last_input_at for r in runtime.guard.completions))
    report.update({'protocol':'causal_prefix_matched_training_renders_v1',
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
        'native_global_views':mapper.n_global_views,
        'visual_pose_audit':getattr(mapper,'_visual_pose_audit',None),
        'deferred_audit':getattr(getattr(mapper,'deferred_dense_observations',None),'audit',None),
        'quality_validated':False})
    # Exports and evaluation inputs are accessed only after every mapper thread stopped.
    report.update(render_counts=dict(audit.counts),render_prefixes=prefixes,
                  render_errors=audit.errors,clock_reference=str(args.clock_reference),
                  clock_reference_sha256=sha(args.clock_reference),
                  fixed_reference=str(args.reference) if args.reference else None,
                  fixed_reference_sha256=sha(args.reference) if args.reference else None,
                  fixed_time_claim=False,reference_extra_quotas=dict(quotas))
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
