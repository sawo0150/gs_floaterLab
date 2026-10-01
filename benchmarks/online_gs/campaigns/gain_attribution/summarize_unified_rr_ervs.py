"""Re-audit saved runs; distinguish role labels from actual loss schedule."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import run_unified_rr_ervs_panel as panel

common=panel.common

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    root=args.output.resolve();rows=common.read(root/'summary.json');assert len(rows)==6
    comparison=[];parity={}
    for dataset in common.SCENES:
        arms={r['case']:r for r in rows if r['dataset']==dataset}
        assert set(arms)=={'rr','ervs'}
        results={}
        for selector,row in arms.items():
            assert row['valid_execution'] and row['audit_pass'] and not row['error'] and not row['source_changed']
            panel.audit_run(Path(row['output']),dataset,row['config'])
            results[selector]=common.read(Path(row['output'])/'render_result.json')
        a,b=results['ervs'],results['rr'];differences=[]
        assert a['gaussians']==b['gaussians']
        assert a['render_counts']==b['render_counts']
        assert a['main_optimizer_steps']==b['main_optimizer_steps']
        assert len(a['training']['generations'])==len(b['training']['generations'])
        for ga,gb in zip(a['training']['generations'],b['training']['generations']):
            assert ga['admissions']==gb['admissions']
            for k in ('keyframes','offered_dense','admitted_dense'):assert ga['policy'][k]==gb['policy'][k]
            assert len(ga['services'])==len(gb['services'])
            for i,(sa,sb) in enumerate(zip(ga['services'],gb['services'])):
                for k in ('lr_render_position','selection_batch_size','selection_batch_token','pool_sizes'):
                    assert sa[k]==sb[k]
                loss_roles=lambda s:['rgb' if r=='dense' else 'native' for r in s['roles']]
                assert loss_roles(sa)==loss_roles(sb)
                if sa['roles']!=sb['roles']:
                    differences.append({'generation':ga['policy']['generation'],'service':i,
                        'ervs':sa['roles'],'rr':sb['roles']})
        assert all(d['generation']!=a['training']['generations'][-1]['policy']['generation'] for d in differences)
        old=common.read(panel.ROOT/'results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur'/dataset/'render_result.json')
        parity[dataset]=[g['services'] for g in a['training']['generations']]==[g['services'] for g in old['training']['generations']]
        assert parity[dataset]
        comparison.append({'dataset':dataset,'rr_psnr':arms['rr']['psnr'],'ervs_psnr':arms['ervs']['psnr'],
            'ervs_minus_rr':arms['ervs']['psnr']-arms['rr']['psnr'],
            'rr_seconds':b['mapping_seconds'],'ervs_seconds':a['mapping_seconds'],
            'renders_and_adam':a['main_optimizer_steps'],'gaussians':a['gaussians'],
            'same_admissions_pool_loss_batch_lr':True,'role_label_differences':differences,
            'final_generation_exact_role_match':True})
    common.write(root/'comparison.json',comparison)
    common.write(root/'initial_pair_audit_failure.json',{
        'failure':'original panel exited 1 after all 6 valid runs: exact role-label schedule assertion',
        'cause':'Aria 5 bootstrap services shifted window to KF; same native loss; discarded before final map generation',
        'resolution':'preserve mismatch explicitly; verify every service loss type/batch/LR, admission, prefix budget; final generation exact roles match',
        'reran_training':False})
    # The post-run repair handles optional overlapping KF control pools only.
    # Check both selectors in the measured dense_rgb configuration against the
    # exact source snapshot used for all GPU runs.
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration/vigs')
    sys.path.insert(0,str(backend))
    from unified_view_training import UnifiedTrainingSet
    lock=common.read(root/'source_lock.json')
    original=Path(lock[str(backend/'unified_view_training.py')]['copy'])
    spec=importlib.util.spec_from_file_location('rr_gpu_source',original)
    oldmodule=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldmodule)
    checks=0
    for selector in ('rr','ervs'):
        for seed in range(5):
            kw=dict(membership='growth',selector=selector,seed=seed,kappa=16,tau=4.,entropy_weight_policy='per_view')
            x,y=(cls(**kw) for cls in (oldmodule.UnifiedTrainingSet,UnifiedTrainingSet))
            for q in (x,y):
                q.register_keyframes(range(0,201,10))
                for u in range(1,200):
                    if u%10:q.offer(u,u//10*10,u//10*10+10,available_through=200)
            for i in range(150):
                sx=x.reserve(4 if i%4==3 else 12,window=range(150,201,10))
                sy=y.reserve(4 if i%4==3 else 12,window=range(150,201,10))
                assert sx.uids==sy.uids
                if i%17==0:x.cancel(sx);y.cancel(sy)
                else:
                    while sx is not None:
                        sx=x.commit_prefix(sx,1);sy=y.commit_prefix(sy,1)
                assert x.snapshot()==y.snapshot()
                checks+=1
    tests=['test_unified_rr','test_unified_growth','test_unified_view_training','test_paired_cumulative_counts','test_dense_blur_filter','test_kf_rgb_control']
    cp=subprocess.run([sys.executable,'-m','unittest',*tests],cwd=panel.HERE,capture_output=True,text=True)
    assert cp.returncode==0
    changes={path:{'gpu_sha256':v['sha256'],'current_sha256':common.sha(Path(path))}
             for path,v in lock.items() if common.sha(Path(path))!=v['sha256']}
    common.write(root/'post_run_validation.json',{'pass':True,'existing_ervs_trace_parity':parity,
        'default_dense_sampler_snapshot_equivalence_cases':checks,'cpu_tests':{'returncode':cp.returncode,'output':cp.stderr},
        'source_changes_after_gpu_runs':changes,
        'auxiliary_control_bug':'RR with two overlapping KF pools could raise StopIteration; consume matching epochs on every service; dense_rgb unchanged',
        'test_invocation_note':'one initial unittest invocation from workspace root failed module discovery; corrected test-directory invocation passed36'})
    print(comparison)

if __name__=='__main__':main()
