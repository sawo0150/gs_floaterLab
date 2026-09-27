#!/usr/bin/env python3
"""Official vanilla mapper, causal per-prefix 15-render/KF comparison."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import run_online_dense_training as trial

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,default=str)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--scene',required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=0)
    p.add_argument('--renders-per-kf',type=int,default=15)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    import numpy as np
    import torch
    import yaml
    import gs_backend
    import gaussian.renderer
    import gaussian.utils.slam_utils as losses
    import diff_gaussian_rasterization
    from exp78b_frozen_archive import FrozenTrackerArchive
    from exp78b_replay_vanilla_mapping import (GSBackEnd,DeadlineGuard,install_telemetry,
        install_gaussian_hooks,D1RenderBudgetAdapter,install_mapping_disjoint_first_birth_fix,save_shared_trajectories)
    from render_work_audit import RenderWorkAudit
    official=trial.BASE.OFFICIAL_ROOT
    if Path(gs_backend.__file__).resolve()!=official/'vigs/gs_backend.py':raise RuntimeError('Not official mapper')
    commit=subprocess.check_output(['git','-C',str(official),'rev-parse','HEAD'],text=True).strip()
    if commit!=trial.BASE.OFFICIAL_COMMIT:raise RuntimeError('Official source moved')
    reference=json.loads(args.reference.read_text())
    if args.renders_per_kf<=0 or not reference['valid_execution'] or reference['kf_render_budget']['renders_per_kf']!=args.renders_per_kf:
        raise RuntimeError('Invalid reference or mismatched renders/KF')
    if (reference['dataset'],reference['scene'],reference['seed'])!=(args.dataset,args.scene,args.seed):
        raise RuntimeError('Reference identity mismatch')
    targets={r['uid']:r['training_renders'] for r in reference['render_prefixes']}
    paths=trial.BASE.sequence_paths(args.dataset,args.scene)
    archive=FrozenTrackerArchive(paths['archive'])
    config=yaml.safe_load(paths['vanilla_config'].read_text())
    # Same invalid-depth reciprocal fix as both custom comparison arms; official
    # valid-pixel loss and gradient are unchanged, including its alpha and masks.
    safe_source=Path('/home/intern/VIGS-SLAM-online-worker-integration/vigs/gaussian/utils/slam_utils.py')
    tree=ast.parse(safe_source.read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get_loss_mapping_rgbd')
    module=ast.Module(body=[node],type_ignores=[])
    scope=dict(vars(losses));exec(compile(module,str(safe_source),'exec'),scope)
    safe_loss=scope['get_loss_mapping_rgbd']
    gs_backend.get_loss_mapping_rgbd=safe_loss
    files=list((official/'vigs').rglob('*.py'))+[paths['vanilla_config'],safe_source,Path(__file__).resolve(),
        Path(__file__).with_name('render_work_audit.py'),trial.BASE.VANILLA_HARNESS,trial.BASE.ARCHIVE_READER]
    snapshot=args.output/'source';snapshot.mkdir();lock={}
    for file in files:
        digest=sha(file);copy=snapshot/(digest[:12]+'_'+file.name);shutil.copy2(file,copy)
        lock[str(file)]={'sha256':digest,'copy':str(copy)}
    write(args.output/'source_lock.json',lock)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed);torch.cuda.manual_seed_all(args.seed)
    started=time.monotonic()
    mapper_args=SimpleNamespace(output=str(args.output),gsvis=False,
        image_size=archive.manifest['preprocessing']['output_image_size_hw'],
        length=len(archive.arrivals),start=0,stride=1,seed=args.seed)
    mapper=GSBackEnd(config,str(args.output),mapper_args,use_gui=False)
    guard=DeadlineGuard(None,0.)
    telemetry=install_telemetry(mapper,guard)
    birth_fix=install_mapping_disjoint_first_birth_fix(mapper)
    audit=RenderWorkAudit(gs_backend,torch)
    adapter=D1RenderBudgetAdapter(mapper,telemetry)
    completions=[];optimizer_handles=[]
    def bind():
        def completed(opt,a,k):
            torch.cuda.synchronize();completions.append(time.monotonic())
        optimizer_handles.append(mapper.gaussians.optimizer.register_step_post_hook(completed))
    bind()
    events_by_uid={}
    for e in archive.events:events_by_uid.setdefault(int(e['emitted_at_frame_uid']),[]).append(e)
    prefixes=[];submitted=[];last_input_at=None;error=None
    seen_rgb=set();used=set()
    try:
        for i,record in enumerate(archive.arrivals):
            uid=int(record['frame_uid']);sensor=float(record['sensor_timestamp'])
            if i==len(archive.arrivals)-1:
                last_input_at=time.monotonic();break
            seen_rgb.add(uid)
            # Raw non-KF observations are causally available, but vanilla has
            # no dense training path. No future frame is read for training.
            if uid not in archive.heldout_uids:archive.load_rgb(uid)
            target=targets[uid]
            credit=target-audit.training
            if credit<0:raise RuntimeError('Reference work moved backwards')
            adapter.begin_event(credit)
            audit.context={'arrival_uid':uid,'phase':'native'}
            for meta in events_by_uid.get(uid,[]):
                if float(meta['emitted_at_sensor_timestamp'])>sensor+1e-7:raise RuntimeError('Future event')
                kind=meta['kind']
                if kind in ('metric_rescale','mapper_reset'):
                    payload=archive.load_event_payload(meta)
                    with torch.no_grad():
                        if kind=='metric_rescale':mapper.rescale(float(payload['scale']))
                        else:
                            mapper.remove_all_gaussians();install_gaussian_hooks(mapper,telemetry,guard);bind()
                    submitted.append({'event_id':meta['event_id'],'kind':kind,'control':True})
                else:
                    packet=archive.mapping_packet(meta,filter_heldout=True)
                    if packet is None:continue
                    ids={int(k) for k in packet['tstamp']}
                    if not ids<=seen_rgb or ids&archive.heldout_uids:raise RuntimeError('Invalid packet inputs')
                    used.update(ids);mapper.process_track_data(packet)
                    submitted.append({'event_id':meta['event_id'],'kind':kind,'completed':True})
            # Reuse official benchmark budget adapter, but close every input
            # prefix exactly (never accumulate a final offline polishing tail).
            adapter.finish_budget_inside_final_event();adapter.end_event()
            torch.cuda.synchronize()
            if audit.training!=target:raise RuntimeError('Unequal prefix rendering count')
            prefixes.append({'uid':uid,'training_renders':audit.training,'all_renders':audit.counts['all'],
                'main_steps':telemetry['optimizer_steps_completed'],'seconds':time.monotonic()-started})
            if i%100==0:print('PREFIX',uid,'renders',audit.training,'seconds',round(time.monotonic()-started,2),flush=True)
    except BaseException:
        import traceback
        error=traceback.format_exc()
    torch.cuda.synchronize();ended=time.monotonic()
    origins={int(x) for x in mapper.gaussians.unique_kfIDs.cpu().tolist() if int(x)>=0}
    used|=origins|set(mapper.viewpoints)
    overlap=sorted(used&archive.heldout_uids)
    finite=all(bool(torch.isfinite(getattr(mapper.gaussians,'_'+k)).all()) for k in ('xyz','scaling','rotation','opacity','features_dc','features_rest'))
    checks={'prefix_budget_matches':[(r['uid'],r['training_renders']) for r in prefixes]==[(r['uid'],r['training_renders']) for r in reference['render_prefixes']],
        'training_render_matches_telemetry':audit.training==telemetry['training_rasterized_view_updates'],
        'render_backward_matches':audit.training==audit.counts['backward'],
        'no_render_errors':not audit.errors,'all_renders_match':dict(audit.counts)==reference['render_counts'],
        'optimizer_hooks_match':len(completions)==telemetry['optimizer_steps_completed'],
        'heldout_disjoint':not overlap,'finite_gaussians':finite,
        'causal_render_uids':all(x['uid']<=x['arrival_uid'] for x in audit.rows),
        'zero_tail':last_input_at is not None and all(t<=last_input_at for t in completions)}
    valid=error is None and all(checks.values())
    report={'protocol':f'official_vanilla_prefix_matched_{args.renders_per_kf}_renders_per_kf_v1','valid_execution':valid,
        'renders_per_kf':args.renders_per_kf,
        'dataset':args.dataset,'scene':args.scene,'seed':args.seed,'checks':checks,'error_traceback':error,
        'official_root':str(official),'official_commit':commit,'config':str(paths['vanilla_config']),
        'reference':str(args.reference),'reference_sha256':sha(args.reference),
        'render_counts':dict(audit.counts),'render_prefixes':prefixes,'telemetry':telemetry,
        'mapping_seconds':ended-started,'optimizer_completions':completions,'last_input_at':last_input_at,
        'submitted_events':submitted,'heldout_overlap':overlap,'gaussians':len(mapper.gaussians.get_xyz),
        'first_birth_uid_fix':birth_fix,'numeric_fix':'same masked reciprocal RGBD loss as custom arms',
        'fixed_time_claim':False,'concurrent_tracking':False,'budget_adapter':'Official D1RenderBudgetAdapter applied at each arrival prefix',
        'renderer_module':gaussian.renderer.__file__,'rasterizer_module':diff_gaussian_rasterization.__file__}
    write(args.output/'render_result.json',report);write(args.output/'render_audit.json',audit.rows)
    if not valid:raise RuntimeError(error or 'Vanilla audit failed: '+repr(checks))
    mapper.gaussians.save_ply(str(args.output/'3dgs_before_final.ply'))
    write(args.output/'mapped_uids.json',sorted(used));save_shared_trajectories(archive,args.output)
    for f,v in lock.items():
        if sha(f)!=v['sha256']:raise RuntimeError('Source changed during mapping')
    print('VANILLA_PASS',args.dataset,audit.training,telemetry['optimizer_steps_completed'],flush=True)

if __name__=='__main__':main()
