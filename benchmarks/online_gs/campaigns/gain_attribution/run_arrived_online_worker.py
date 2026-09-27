#!/usr/bin/env python3
"""Timestamp-paced raw-arrival replay through the actual common VIGS worker.

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


def training_checks(report, main_steps):
    generations=report['generations']
    native=sum(s['source']=='native' for g in generations for s in g['services'])
    photo=report['photometric_steps']
    recent=True
    cumulative=True
    for generation in generations:
        p=generation['policy']
        history=[uid for s in generation['services'] if s['source']=='photometric' for uid in s['uids']]
        uids=sorted(set(p['keyframes'])|set(p['admitted_dense']))
        all_counts=Counter(uid for s in generation['services'] for uid in s['uids'])
        photo_counts=Counter(history)
        cumulative &= (p['counts']=={uid:all_counts[uid] for uid in uids}
                       and p['photometric_counts']=={uid:photo_counts[uid] for uid in uids})
        if p['selection_count_scope']=='recent_photometric':
            count=max(0,len(uids)-1);expected=Counter(history[-count:]) if count else Counter()
            recent &= (p['recent_history_length']==len(history) and p['recent_window_size']==len(uids)
                       and p['next_draw_counts']=={uid:expected[uid] for uid in uids})
    checks = {'common_commits_match_adam':native+photo==main_steps,
        'photometric_counts_match_services':sum(sum(g['policy']['photometric_counts'].values()) for g in generations)==sum(len(s['uids']) for g in generations for s in g['services'] if s['source']=='photometric'),
        'cumulative_counts_match_committed_history':cumulative,
        'growth_capacity':all(all(
            a['growth_budget_scope']==g['policy']['growth_budget_scope'] and
            (g['policy']['membership']!='growth' or
             (a['pool_size_after'] if a['growth_budget_scope']=='whole_pool' else i+1)
             <=a['rgb_steps']//g['policy']['kappa'])
            for i,a in enumerate(g['admissions'])) for g in generations)}
    if any(g['policy']['selection_count_scope']=='recent_photometric' for g in generations):
        checks['recent_counts_match_committed_history']=recent
    if report.get('schedule') == 'paired_kf_dense':
        full = alternating = role_counts = local = True
        for g in generations:
            p=g['policy']; histories={'keyframe':[],'dense':[]}; expected='keyframe'
            full &= p['membership']=='kf_only' or set(p['admitted_dense'])==set(p['offered_dense'])
            for s in g['services']:
                if s['source']=='native':
                    local &= (set(s['uids'])<=set(s['window_uids'])
                              and set(s['window_uids'])==set(s['recent_window_uids']))
                    continue
                role=s['role']; histories[role].extend(s['uids'])
                alternating &= len(s['uids'])==1 and (role==expected if s['paired'] else role=='keyframe')
                expected='dense' if s['paired'] and role=='keyframe' else 'keyframe'
            for role,history in histories.items():
                uids=p['keyframes'] if role=='keyframe' else p['admitted_dense']
                history=[u for u in history if u in set(uids)]
                scope=p['selection_count_scope']
                if scope=='recent_photometric':
                    tail=history[-(len(uids)-1):] if len(uids)>1 else []
                    counts=Counter(tail)
                else:
                    counts=Counter(u for s in g['services']
                        if scope=='all_rgb' or s['source']=='photometric' for u in s['uids'])
                role_counts &= p['role_next_draw_counts'][role]=={u:counts[u] for u in uids}
                role_counts &= p['role_commits'][role]==sum(s.get('role')==role for s in g['services'])
        final=generations[-1]
        checks.update(full_available_pools=full,paired_turns=alternating,
                      role_selection_counts_match_history=role_counts,native_window_only=local,
                      final_map_dense_used=(not final['policy']['offered_dense']
                        or any(s.get('role')=='dense' for s in final['services'])))
    if report.get('schedule') == 'unified':
        batches = local = before_counts = anchors = True
        for g in generations:
            counts = Counter()
            for s in g['services']:
                batches &= (s['source']=='photometric' and len(set(s['uids']))==len(s['uids'])
                    and len(s['uids'])==len(s['roles']) and len(s['uids'])<=sum(g['policy']['batch_quotas']))
                local &= all(u in s['window_uids'] for u,r in zip(s['uids'],s['roles']) if r=='window')
                before_counts &= tuple(counts[u] for u in s['uids'])==tuple(s['counts_before'])
                anchors &= all(left < u < right for u,(left,right) in s['dense_anchors'].items())
                counts.update(s['uids'])
        checks.update(unified_batches_distinct=batches,unified_window_membership=local,
                      unified_cumulative_before_draw=before_counts,unified_dense_anchors=anchors,
                      no_separate_native_steps=native==0,
                      membership_matches_admission=all(
                          set(g['policy']['admitted_dense'])<=set(g['policy']['offered_dense'])
                          and (g['policy']['membership']!='immediate' or
                               set(g['policy']['admitted_dense'])==set(g['policy']['offered_dense']))
                          for g in generations))
    return checks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--setup',required=True,type=Path)
    parser.add_argument('--extensions',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--membership',choices=['kf_only','growth','immediate'],default='growth')
    parser.add_argument('--selector',choices=['ervs','rr'],default='ervs')
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--schedule',choices=['mixed','paired_kf_dense'],default='mixed')
    parser.add_argument('--selection-count-scope',choices=['all_rgb','photometric','recent_photometric'])
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
    from arrived_input_boundary import input_preparation
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
    source_files += [Path(__file__).resolve(),Path(__file__).with_name('arrived_input_boundary.py').resolve(),
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
    started=time.monotonic();deadline=started+duration
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
        'schedule':args.schedule,
        **({'selection_count_scope':args.selection_count_scope} if args.selection_count_scope else {})})
    host._online_runtime=runtime
    observer=StreamSnapshots(start=started,deadline=deadline,heldout=archive.heldout_uids)
    install_snapshots(mapper,observer,runtime.guard)
    ready=torch.cuda.Event();ready.record(torch.cuda.current_stream());host._gs_stream.wait_event(ready)
    thread=threading.Thread(target=VIGS._gs_worker,args=(host,),daemon=True)
    thread.start()
    events_by_uid={}
    for event in archive.events:
        events_by_uid.setdefault(int(event['emitted_at_frame_uid']),[]).append(event)
    submitted=[];arrived=[];last_input_at=None;error=None
    preparation_timing={'end':time.monotonic()}
    setup_seconds=time.monotonic()-started
    try:
        for i,record in enumerate(archive.arrivals):
            uid=int(record['frame_uid']);sensor=float(record['sensor_timestamp'])
            due=started+1.5*(sensor-first_sensor)
            host._replay_next_arrival_deadline=due
            host._tracking_active.clear()
            # Sleeping simulates actual arrival, not extra offline work.
            while time.monotonic()<due:
                runtime.worker.raise_on_error()
                time.sleep(min(.01,max(0.,due-time.monotonic())))
            host._tracking_active.set()
            if i==len(archive.arrivals)-1:
                last_input_at=time.monotonic();runtime.close()
                arrived.append({'uid':uid,'seconds':last_input_at-started,'terminal':True})
                break
            if runtime.worker.report()['closed']:
                runtime.worker.raise_on_error()
                continue
            arrived.append({'uid':uid,'seconds':time.monotonic()-started})
            with input_preparation(runtime,arrived[-1],preparation_timing,start=started,
                                   synchronize=torch.cuda.current_stream().synchronize):
                rgb=(torch.empty(0) if uid in archive.heldout_uids else archive.load_rgb(uid))
                runtime.observe_rgb(uid,sensor,rgb)
                for metadata in events_by_uid.get(uid,[]):
                    if float(metadata['emitted_at_sensor_timestamp'])>sensor+1e-7:
                        raise RuntimeError('Tracker packet precedes its causal emission time')
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
                        submitted.append({'event_id':metadata['event_id'],'kind':kind,'future':future})
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
    checks['worker_and_preparation_within_budget']=(report['worker']['stopped_at'] is not None
        and max(report['worker']['stopped_at'],producer_work_end)<=deadline)
    mapping_seconds=max(report['worker']['stopped_at'],producer_work_end)-started
    valid=(error is None and not report['boundaries']['overruns'] and not overlap and finite
           and native+photo==main_steps and last_input_at is not None
           and all(checks.values())
           and all(r['seconds']<=deadline and r['seconds']<=last_input_at for r in runtime.guard.completions))
    report.update({'protocol':'arrived_rgb_imu_frozen_causal_tracker_worker_v1',
        'valid_execution':valid,'error_traceback':error,'strict_tracking_claim':False,
        'start':started,'deadline':deadline,'budget_seconds':duration,'setup_seconds':setup_seconds,
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
    observer.write(args.output/'stream_snapshots')
    torch.save(capture(mapper),args.output/'final_map_state.pt')
    mapper.gaussians.save_ply(str(args.output/'3dgs_before_final.ply'))
    write(args.output/'mapped_uids.json',sorted(used|origins|set(mapper.viewpoints)))
    replay.save_shared_trajectories(archive,args.output)
    for path,entry in source_lock.items():
        if sha(Path(path))!=entry['sha256']:raise RuntimeError('Source changed during run: '+path)
    write(args.output/'worker_result.json',report)
    print('ARRIVED_WORKER',provenance['dataset'],args.membership,'PASS' if valid else 'FAIL',
          'steps',main_steps,'native',native,'photo',photo,flush=True)
    if not valid:raise RuntimeError(error or 'Execution contract failed')


if __name__=='__main__':main()
