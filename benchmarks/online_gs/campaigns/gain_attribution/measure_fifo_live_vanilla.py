#!/usr/bin/env python3
"""Official VIGS tracker + mapper at native timestamps, with render cap/telemetry.

Official Python source is untouched. Process-local adapters enforce heldout
exclusion, packet-local indices, the shared finite reciprocal loss, and the
declared rendering/deadline budget. No stored tracking results are consumed.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time
import traceback
import threading
import inspect
import textwrap
from types import SimpleNamespace, MethodType

import run_online_dense_training as trial


def write(p, x): p.write_text(json.dumps(x, indent=2, default=str)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['aria','rpng','utmm','rot'], default='aria')
    parser.add_argument('--time-scale',type=float,default=1.)
    parser.add_argument('--queue-size',type=int,default=2)
    parser.add_argument('--renders-per-kf',type=int,default=15)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--worker',action='store_true')
    a=parser.parse_args()
    official=trial.BASE.OFFICIAL_ROOT
    if not a.worker:
        a.output.mkdir(parents=True,exist_ok=False)
        trial.common.evaluation.panel.v2.gpu_idle()
        env=trial.BASE.mapping_environment(False)
        env['PYTHONPATH'] += ':'+str(trial.BASE.BUILT_THIRDPARTY_ROOT)
        cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--worker',
             '--dataset',a.dataset,'--renders-per-kf',str(a.renders_per_kf),'--output',str(a.output.resolve())]
        write(a.output/'command.json',cmd)
        cwd=trial.BASE.WORKSPACE/'results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090'
        with (a.output/'run.log').open('x') as log:
            result=subprocess.run(cmd,env=env,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
        print('COMPLETE',a.output,result.returncode,flush=True)
        raise SystemExit(result.returncode)

    import main_validation_rot_adapter as rot
    rot.install()
    import cv2
    import numpy as np
    import torch
    import yaml
    import vigs as vigs_module
    import gs_backend
    import gaussian.utils.slam_utils as losses
    from exp78b_frozen_archive import FrozenTrackerArchive
    from exp78b_replay_vanilla_mapping import (DeadlineGuard,DeadlineReached,
        install_mapping_disjoint_first_birth_fix)
    from render_work_audit import RenderWorkAudit
    assert Path(gs_backend.__file__).resolve()==official/'vigs/gs_backend.py'
    scene={'aria':'aria1253','rpng':'table_06','utmm':'square-1','rot':'aria1253rot'}[a.dataset]
    dataset='aria' if a.dataset=='rot' else a.dataset
    paths=trial.BASE.sequence_paths(dataset,scene)
    raw=FrozenTrackerArchive(paths['archive'])
    def forbidden(*args,**kwargs):raise RuntimeError('Stored tracker state forbidden in live run')
    raw.load_geometry=raw.load_event_payload=raw.mapping_packet=forbidden
    config=yaml.safe_load(paths['vanilla_config'].read_text())
    config['Training']['parallel']=True
    setup_root=trial.ROOT/'live_worker_integration_audit'
    setup=setup_root/('v5_packet_identity/aria_setup' if a.dataset=='aria' else f'v9_productive_worker/three_scene/{a.dataset}_setup')
    if a.dataset=='rot':setup=rot.INPUT/'setup'
    args=SimpleNamespace(**json.loads((setup/'native_setup.json').read_text())['args'])
    args.output=str(a.output);args.config=str(paths['vanilla_config']);args.buffer=700
    args.IMU_poseinit_after = 15 if a.dataset == 'utmm' else 20
    args.weights=str(official/'pretrained_models/droid.pth')
    args.image_size=raw.preprocessing['output_image_size_hw']
    try: args.imus=np.loadtxt(raw.manifest['input_imu'],delimiter=',')
    except ValueError: args.imus=np.loadtxt(raw.manifest['input_imu'])
    vigs_module.load_config=lambda path:config
    write(a.output/'effective_config.json', {'config':config,
        'args':{k:v for k,v in vars(args).items() if k!='imus'},
        'frontend_iterations':[4,2], 'tracking_packets_replayed':False,
        'renders_per_kf_cap':a.renders_per_kf, 'time_scale':a.time_scale})
    safe=Path('/home/intern/VIGS-SLAM-online-worker-integration/vigs/gaussian/utils/slam_utils.py')
    node=next(n for n in ast.parse(safe.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='get_loss_mapping_rgbd')
    scope=dict(vars(losses));exec(compile(ast.Module(body=[node],type_ignores=[]),str(safe),'exec'),scope)
    gs_backend.get_loss_mapping_rgbd=scope['get_loss_mapping_rgbd']
    files=list((official/'vigs').rglob('*.py'))+[Path(__file__).resolve(),safe,paths['vanilla_config']]
    source=a.output/'source';source.mkdir();lock={}
    for path in files:
        data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
        dest=source/(digest[:12]+'_'+path.name);dest.write_bytes(data)
        lock[str(path)]={'sha256':digest,'copy':str(dest)}
    write(a.output/'source_lock.json',lock)
    random.seed(0);np.random.seed(0);torch.manual_seed(0);torch.cuda.manual_seed_all(0)
    audit=RenderWorkAudit(gs_backend,torch)
    from mapper_execution_guard import MapperExecutionGuard,MappingBoundaryReached
    from online_mapping_worker import OnlineMappingWorker
    from concurrent.futures import CancelledError
    guard=MapperExecutionGuard(deadline=None,reserve_seconds=.5,synchronize=torch.cuda.default_stream().synchronize)
    guard.optimizer_completion_times=[]
    ready=threading.Event()
    state={'generation':0,'seen':set(),'admissions':[],'services':[],'errors':[], 'latest_uid':-1,'dispatch_uid':-1}
    original_constructor=vigs_module.GSBackEnd
    def constructor(*values,**kwargs):
        mapper=original_constructor(*values,**kwargs)
        install_mapping_disjoint_first_birth_fix(mapper)
        def bind():
            guard.bind_optimizer(mapper.gaussians.optimizer,generation=state['generation'],replace_binding=True)
            def after(opt,args,kwargs):
                now=time.monotonic();guard.optimizer_completion_times.append(now)
                state['services'].append({'time':now,'renders':audit.counts['backward'],'uid':state['dispatch_uid']})
            mapper.gaussians.optimizer.register_step_post_hook(after)
        bind()
        old_remove=mapper.remove_all_gaussians
        old_rescale=mapper.rescale
        def remove():
            with mapper._gaussian_lock:
                result=old_remove();state['generation']+=1;bind();return result
        state['controls']={'mapper_reset':remove,'metric_rescale':old_rescale}
        def control(kind,value=None):
            if guard.is_owner_thread():
                return state['controls'][kind](value) if kind=='metric_rescale' else state['controls'][kind]()
            w=state.get('worker')
            if w is None:raise RuntimeError('Control before worker ready')
            if w.report()['closed']:w.raise_on_error();return None
            return w.submit({'_mapper_control':kind,'value':value,'_arrival_uid':state['latest_uid']}).result()
        mapper.remove_all_gaussians=lambda:control('mapper_reset')
        mapper.rescale=lambda value:control('metric_rescale',value)
        old_map=mapper.map
        def budgeted(instance,current_window,iters,prune=False,include_global=True,max_viewpoints=20):
            for uid in sorted(mapper.viewpoints):
                key=(state['generation'],int(uid))
                if key not in state['seen']:
                    state['seen'].add(key)
                    state['admissions'].append({'generation':key[0],'uid':key[1],'arrival_uid':state['dispatch_uid']})
            # Preserve native batching/loss/window+2; use all earned credit in
            # this causal packet, including one partial batch when needed.
            target=a.renders_per_kf*len(state['seen']) if a.renders_per_kf else None
            loops=0
            while (audit.training<target if target is not None else loops<int(iters)):
                guard.reject_if_unsafe('optimizer')
                window=[k for k in current_window if k in mapper.viewpoints]
                if not window: break
                allowed=min(max_viewpoints,target-audit.training) if target is not None else max_viewpoints
                before=audit.training
                old_map(window,iters=1,prune=prune,include_global=include_global,max_viewpoints=allowed)
                loops+=1
                if audit.training==before: break
        mapper.map=MethodType(budgeted,mapper)
        original_process=mapper.process_track_data
        def process(packet):
            if guard.deadline is not None and time.monotonic()>=guard.deadline-.5: return
            packet['viz_idx']=torch.arange(len(packet['tstamp']),dtype=torch.long)
            audit.context={'arrival_uid':state['dispatch_uid'],'phase':'native'}
            try: return original_process(packet)
            except MappingBoundaryReached: raise
            except BaseException:
                state['errors'].append(traceback.format_exc());raise
        mapper.process_track_data=process
        return mapper
    vigs_module.GSBackEnd=constructor
    def mapper_worker(host):
        def dispatch(packet):
            state['dispatch_uid']=packet['_arrival_uid']
            audit.context={'arrival_uid':state['dispatch_uid'],'phase':'native'}
            producer=packet.get('_producer_event')
            if producer is not None:torch.cuda.default_stream().wait_event(producer)
            if '_mapper_control' in packet:
                guard.reject_if_unsafe('control')
                kind=packet['_mapper_control']
                result=state['controls'][kind](packet['value']) if kind=='metric_rescale' else state['controls'][kind]()
                guard.complete_mutation('control:'+kind);return result
            return host.gs.process_track_data(packet)
        w=OnlineMappingWorker(guard=guard,dispatch=dispatch,idle=lambda:False,max_pending_packets=a.queue_size)
        state['worker']=w;host._gs_queue=w.queue;ready.set();w.run()
    vigs_module.VIGS._gs_worker=mapper_worker
    # Original tracker flushes its legacy queue before blocking PGBA. The common
    # worker instead retains corrections FIFO and waits on the correction future.
    tree=ast.parse(textwrap.dedent(inspect.getsource(vigs_module.VIGS.track)))
    class RemoveLegacyDrain(ast.NodeTransformer):
        def visit_If(self,node):
            if isinstance(node.test,ast.Attribute) and node.test.attr=='_gs_parallel':
                if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='join' for n in ast.walk(node)):
                    return ast.Pass()
            return self.generic_visit(node)
    tree=ast.fix_missing_locations(RemoveLegacyDrain().visit(tree));scope=dict(vigs_module.VIGS.track.__globals__)
    exec(compile(tree,'<official-track-fifo-adapter>','exec'),scope);vigs_module.VIGS.track=scope['track']
    def filtered_call(host,idx,dposes=None,dscale=None,final=False,update_idx=None,blocking=False):
        w=state['worker']
        if w.report()['closed']:w.raise_on_error();return
        if not host.video.IMU_initialized:return
        if final:raise RuntimeError('Offline refinement forbidden')
        ts=host.video.tstamp[idx.to(host.video.tstamp.device)]
        keep=torch.tensor([i for i,uid in enumerate(ts.tolist()) if int(uid) not in raw.heldout_uids],device=idx.device,dtype=torch.long)
        if not len(keep):return
        if dposes is not None:dposes=dposes[keep.to(dposes.device)];dscale=dscale[keep.to(dscale.device)]
        idx=idx[keep];cpu=idx.cpu()
        data={'viz_idx':torch.arange(len(idx),dtype=torch.long),'tstamp':host.video.tstamp[idx].cpu(),
            'poses':host.video.poses[idx].cpu(),'images':host.video.images[cpu],
            'normals':host.video.normals[cpu],'depths':(1./host.video.disps_up[cpu]).cpu(),
            'intrinsics':host.video.intrinsics[idx].cpu()*8,'pose_updates':dposes.cpu() if dposes is not None else None,
            'scale_updates':dscale.cpu() if dscale is not None else None,
            'update_idx':update_idx.cpu() if update_idx is not None else None,'final':False,
            '_arrival_uid':state['latest_uid']}
        event=torch.cuda.Event();event.record(torch.cuda.current_stream());data['_producer_event']=event
        f=w.submit(data)
        if blocking:f.result()
    vigs_module.VIGS.call_gs=filtered_call
    load_start=time.monotonic();host=vigs_module.VIGS(args)
    if not ready.wait(10):raise RuntimeError('Mapper worker did not start')
    image0=cv2.imread(str(raw.image_dir/raw.arrivals[0]['source_name']))
    h0,w0=image0.shape[:2];crop=int(raw.preprocessing['cropborder'])
    intrinsics=torch.tensor(raw.calibration[:4],dtype=torch.float32);intrinsics[2:]-=crop
    h0-=2*crop;w0-=2*crop;h,w=args.image_size
    intrinsics[[0,2]]*=w/w0;intrinsics[[1,3]]*=h/h0
    torch.cuda.synchronize();model_load=time.monotonic()-load_start
    started=time.monotonic();sensor0=float(raw.arrivals[0]['sensor_timestamp'])
    sensor_duration=float(raw.arrivals[-1]['sensor_timestamp'])-sensor0
    duration=a.time_scale*sensor_duration;guard.deadline=started+duration
    rows=[];error=None
    try:
        for rec in raw.arrivals:
            uid=int(rec['frame_uid']);ts=float(rec['sensor_timestamp']);due=started+a.time_scale*(ts-sensor0)
            if due>time.monotonic():time.sleep(due-time.monotonic())
            begin=time.monotonic();state['latest_uid']=uid
            image=raw.load_rgb(uid)[None]
            state['worker'].raise_on_error()
            if rec is raw.arrivals[-1]:state['worker'].close()
            try:host.track(uid,ts,image,intrinsics=intrinsics[None].clone(),is_last=(rec is raw.arrivals[-1]))
            except (MappingBoundaryReached,CancelledError):
                state['worker'].raise_on_error()
                if time.monotonic()<guard.deadline-guard.reserve_seconds:raise
            if state['errors']:raise RuntimeError(state['errors'][-1])
            end=time.monotonic()
            rows.append({'uid':uid,'sensor_seconds':ts-sensor0,'start_seconds':begin-started,'end_seconds':end-started,
                'start_lag_ms':1000*(begin-due),'end_lag_ms':1000*(end-due),'track_call_ms':1000*(end-begin),
                'training_renders':audit.training,'tracking_kfs':int(host.video.counter.value),
                'kf_admissions':len(state['seen']),'mapper_queue':host._gs_queue.qsize()})
            if uid%200==0:write(a.output/'progress.json',rows[-1]);print('PROGRESS',json.dumps(rows[-1]),flush=True)
    except BaseException:error=traceback.format_exc();print(error,flush=True)
    finally:
        tracking_end=time.monotonic();guard.deadline=min(guard.deadline,time.monotonic())
        state['worker'].close();host._gs_thread.join(timeout=20)
        if host.pgba:host.video.pgobuf.stop();host.mp_backend.join(timeout=5)
        torch.cuda.synchronize()
    def quantile(key):
        values=[r[key] for r in rows]
        return {str(q):float(np.percentile(values,q)) for q in [50,95,99,100]} if values else {}
    committed=state['services'][-1]['renders'] if state['services'] else 0
    result={'dataset':dataset,'key':a.dataset,'time_scale':a.time_scale,'scene':scene,'arm':'official_vanilla_budgeted','gpu':torch.cuda.get_device_name(),
        'image_size_hw':args.image_size,'duration_seconds':duration,'sensor_duration_seconds':sensor_duration,'tracking_elapsed_seconds':tracking_end-started,
        'model_load_seconds':model_load,'input_frames':len(raw.arrivals),'tracked_frames':len(rows),
        'training_renders':audit.training,'backward_renders':audit.counts['backward'],'committed_renders':committed,
        'kf_admissions':len(state['seen']),'unique_mapper_kfs':len({u for _,u in state['seen']}),
        'renders_per_kf_admission':committed/len(state['seen']) if state['seen'] else None,
        'frontend_iterations':[4,2], 'IMU_poseinit_after':args.IMU_poseinit_after,
        'tracking_kfs_final':int(host.video.counter.value),'renders_per_kf_cap':a.renders_per_kf,
        'start_lag_ms':quantile('start_lag_ms'),'end_lag_ms':quantile('end_lag_ms'),'track_call_ms':quantile('track_call_ms'),
        'mapper_queue_max':max((r['mapper_queue'] for r in rows),default=0),
        'zero_tail_observed':all(t<=started+duration for t in guard.optimizer_completion_times),
        'worker':state['worker'].report(),'overruns':guard.overruns,'error':error,'worker_errors':state['errors'],'quality_evaluated':False,
        'source_unchanged':all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v['sha256'] for f,v in lock.items()),
        'official_commit':subprocess.check_output(['git','-C',str(official),'rev-parse','HEAD'],text=True).strip()}
    write(a.output/'frames.json',rows);write(a.output/'result.json',result)
    write(a.output/'renders.json',{'counts':dict(audit.counts),'rows':audit.rows,'errors':audit.errors})
    write(a.output/'kf_admissions.json',state['admissions']);write(a.output/'services.json',state['services'])
    print('RESULT',json.dumps(result),flush=True)
    if error or state['errors'] or state['worker'].error:raise SystemExit(1)
    from export_live_capacity_map import export
    export(host,raw,a.output,len(guard.optimizer_completion_times))


if __name__=='__main__':main()
