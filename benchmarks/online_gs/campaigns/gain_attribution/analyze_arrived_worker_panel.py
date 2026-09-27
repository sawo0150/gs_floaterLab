#!/usr/bin/env python3
"""Verify common-worker paired contracts and summarize measured dense use."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def read(path):return json.loads(path.read_text())


def usage(runtime):
    lower=ambiguous=0
    for generation in runtime['training']['generations']:
        final_kf=set(generation['policy']['keyframes'])
        ever_dense={a['uid'] for a in generation['admissions']}
        # A view that never became a KF was certainly dense when serviced.
        # For promoted views the old ledger lacks an exact promotion timestamp;
        # report an upper/lower interval rather than invent an exact count.
        for service in generation['services']:
            if service['source']!='photometric':continue
            for uid in service['uids']:
                if uid not in final_kf:lower+=1
                elif uid in ever_dense:ambiguous+=1
    audit=runtime.get('deferred_audit') or {}
    pose=runtime.get('visual_pose_audit') or {}
    return {'dense_preparation_calls':len(audit.get('prepared_uids',[])),
        'unique_prepared_dense':len(set(audit.get('prepared_uids',[]))),
        'dense_photometric_steps_lower_bound':lower,
        'dense_photometric_steps_upper_bound':lower+ambiguous,
        'promotion_ambiguous_steps':ambiguous,
        'visual_pose_calls':len(pose.get('calls',[])),
        'visual_pose_seconds':pose.get('wall_seconds',0.),
        'native_steps':runtime['native_commits'],
        'photometric_steps':runtime['photometric_commits'],
        'input_wait_seconds':runtime['worker'].get('input_wait_seconds'),
        'mapping_seconds':runtime['mapping_seconds'],'budget_seconds':runtime['budget_seconds']}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--panel',type=Path,required=True)
    p.add_argument('--seed',type=int,default=0)
    args=p.parse_args()
    summary=[];common_source=None;policies=[]
    for dataset,scene in [('aria','aria1253'),('rpng','table_06'),('utmm','square-1')]:
        arms={};reference=None;cohort=None;budget=None
        for membership in ['growth','kf_only']:
            root=args.panel/(dataset+f'_seed{args.seed}')/membership/f'seed{args.seed}'
            runtime=read(root/'worker_result.json')
            evaluation=read(root/'evaluation_consistency.json')
            metric=read(root/'psnr/strict_fixed_manifest/final_result.json')
            sources={k:v['sha256'] for k,v in read(root/'source_lock.json').items()}
            if common_source is None:common_source=sources
            if sources!=common_source:raise ValueError('Mapper sources differ across paired runs')
            if not(runtime['valid_execution'] and evaluation['pass'] and all(runtime['checks'].values())):
                raise ValueError('Execution/evaluation contract not satisfied: '+str(root))
            trajectory=hashlib.sha256((root/'traj_full_beforeBA.txt').read_bytes()).hexdigest()
            selected=[(r['frame_index'],r['uid'],r['predeclared_fixed_manifest_split']) for r in metric['per_view']]
            if reference is not None and (trajectory!=reference or selected!=cohort or budget!=runtime['budget_seconds']):
                raise ValueError('Paired trajectory/cohort/budget differ')
            reference,cohort,budget=trajectory,selected,runtime['budget_seconds']
            policy=runtime['training']['generations'][-1]['policy']
            policies.append({k:policy[k] for k in ('selector','kappa','tau','entropy_weight_policy',
                'selection_count_scope','growth_budget_scope')})
            if runtime['seed']!=args.seed or runtime['membership']!=membership:
                raise ValueError('Wrong seed or arm')
            arms[membership]={'heldout_psnr':evaluation['fixed_psnr_first'],
                'usage':usage(runtime),'root':str(root),
                'heldout_count':metric['predeclared_fixed_manifest_posthoc']['view_count']}
        summary.append({'dataset':dataset,'scene':scene,'arms':arms,
            'dense_minus_kf_db':arms['growth']['heldout_psnr']-arms['kf_only']['heldout_psnr']})
    if any(p!=policies[0] for p in policies):raise ValueError('Scene-specific common policy differs')
    result={'protocol':'common_arrived_worker_three_scene_comparison_v1','seed':args.seed,
        'rows':summary,'mean_dense_minus_kf_db':statistics.mean(r['dense_minus_kf_db'] for r in summary),
        'policy':policies[0],'same_mapper_sources':True,'same_per_scene_evaluation_contract':True,
        'final_acceptance':False,'strict_tracking_claim':False,
        'remaining':['3-seed final comparisons','production control repeats',
                     'current-policy Growth/ERVS ablations','convergence assessment','paper alignment']}
    (args.panel/'verified_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
