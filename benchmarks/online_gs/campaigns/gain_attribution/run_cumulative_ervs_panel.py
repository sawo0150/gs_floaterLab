#!/usr/bin/env python3
"""Compare cumulative vs explicit recent paired ERVS at exact40 renders/KF."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

import run_online_dense_training as trial

HERE = Path(__file__).resolve().parent
SCENES = {'aria': 'aria1253', 'rpng': 'table_06', 'utmm': 'square-1'}
OLD = trial.BASE.WORKSPACE / 'results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed'
CARD = 'campaigns/06_gain_attribution/cumulative_ervs/README.md'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, indent=2, default=str) + '\n')


def journal(row):
    message = (f"**2026-09-25 cumulative ERVS40 / {row['dataset']} / {row['scope']}:** "
               f"execution={row['valid_execution']}, audit={row['audit_pass']}, held-out PSNR={row['psnr']}; {row['output']}.")
    with (trial.BASE.WORKSPACE/'context/experiments'/CARD).open('a') as f:
        f.write('\n'+message+'\n')
    for name, heading, link in [('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/'+CARD),
                               ('context/experiments/INDEX.md', '# Experiment Index\n', CARD)]:
        path = trial.BASE.WORKSPACE/name; text = path.read_text(); assert heading in text
        path.write_text(text.replace(heading, heading+'\n- '+message+' → [카드]('+link+')\n', 1))


def audit_run(root, old, scope):
    result = read(root/'render_result.json'); reference = read(old/'paired/render_result.json')
    render_audit = read(root/'render_audit.json')
    training = [r for r in render_audit if r['grad_enabled']]
    assert result['valid_execution'] and all(result['checks'].values())
    assert result['native_global_views'] == 0 and result['membership'] == 'immediate'
    assert len(training) == 40 * result['kf_render_budget']['kf_admissions']
    assert all(r['backward'] for r in training)
    assert all(r['uid'] <= r['arrival_uid'] for r in render_audit)
    assert result['render_counts'] == reference['render_counts']
    assert [(r['uid'],r['training_renders'],r['all_renders']) for r in result['render_prefixes']] == [
        (r['uid'],r['training_renders'],r['all_renders']) for r in reference['render_prefixes']]
    assert [r['event_id'] for r in result['submitted_events']] == [r['event_id'] for r in reference['submitted_events']]
    assert all(r['seconds'] <= result['last_input_at'] for r in result['boundaries']['optimizer_completions'])
    by_arrival = Counter(r['arrival_uid'] for r in training)
    cumulative = 0
    for prefix in result['render_prefixes']:
        cumulative += by_arrival[prefix['uid']]
        assert cumulative == prefix['training_renders']
    for generation in result['training']['generations']:
        policy = generation['policy']; services = generation['services']
        assert policy['selection_count_scope'] == scope
        uids = set(policy['keyframes']) | set(policy['admitted_dense'])
        counts = Counter(u for s in services for u in s['uids'])
        photo = Counter(u for s in services if s['source']=='photometric' for u in s['uids'])
        assert {int(k):v for k,v in policy['counts'].items()} == {u:counts[u] for u in uids}
        assert {int(k):v for k,v in policy['photometric_counts'].items()} == {u:photo[u] for u in uids}
        for role, pool in [('keyframe', policy['keyframes']), ('dense', policy['admitted_dense'])]:
            if scope == 'all_rgb':
                expected = counts
            else:
                history = [u for s in services if s.get('role')==role for u in s['uids'] if u in set(pool)]
                expected = Counter(history[-(len(pool)-1):]) if len(pool)>1 else Counter()
            assert {int(k):v for k,v in policy['role_next_draw_counts'][role].items()} == {u:expected[u] for u in pool}
    metric = read(root/'psnr/strict_fixed_manifest/final_result.json')
    cohort = lambda m: [(r['frame_index'],r['uid'],r['predeclared_fixed_manifest_split']) for r in m['per_view']]
    for arm in ('paired','vanilla'):
        old_metric = read(old/arm/'psnr/strict_fixed_manifest/final_result.json')
        assert cohort(metric) == cohort(old_metric)
        for name in ('traj_full_beforeBA.txt','traj_kf_beforeBA.txt'):
            assert sha(root/name) == sha(old/arm/name)
    return {'pass': True, 'same_prefix_work_events_poses_and_cohort': True,
            'independent_cumulative_and_selection_counts': True,
            'training_renders': len(training), 'optimizer_steps': result['main_optimizer_steps'],
            'extra_kf': sum(s.get('role')=='keyframe' for g in result['training']['generations'] for s in g['services']),
            'extra_dense': sum(s.get('role')=='dense' for g in result['training']['generations'] for s in g['services'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output=args.output.resolve(); args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'protocol.json', {'scenes':SCENES,'renders_per_kf':40,'seed':0,
        'scopes':['all_rgb','recent_photometric'], 'batch_size':1,
        'same_sources_for_both_scopes':True,'actual_tracking':False,
        'baseline':'archived verified official vanilla40; same poses/cohort/prefix work checked',
        'quality_rule':'report every scene and differences; no retrospective tuning or equivalence margin'})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files=list((backend/'vigs').rglob('*.py'))+[Path(__file__).resolve(), HERE/'run_kf15_render_worker.py',
        HERE/'run_arrived_online_worker.py', HERE/'keyframe_render_budget.py', HERE/'render_work_audit.py']
    source=args.output/'source';source.mkdir();lock={}
    for path in files:
        digest=sha(path);dest=source/(digest[:12]+'_'+path.name);dest.write_bytes(path.read_bytes())
        lock[str(path)]={'sha256':digest,'copy':str(dest)}
    write(args.output/'source_lock.json',lock)
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    base=trial.ROOT/'live_worker_integration_audit'
    rows=[]
    for dataset,scene in SCENES.items():
        for scope in ('all_rgb','recent_photometric'):
            trial.common.evaluation.panel.v2.gpu_idle()
            out=args.output/dataset/scope;out.parent.mkdir(parents=True,exist_ok=True)
            setup=base/('v5_packet_identity/aria_setup' if dataset=='aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
            command=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(HERE/'run_kf15_render_worker.py'),
                '--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
                '--output',str(out),'--renders-per-kf','40','--seed','0','--membership','immediate',
                '--selector','ervs','--schedule','paired_kf_dense','--selection-count-scope',scope,
                '--reference',str(OLD/dataset/'paired/render_result.json')]
            write(out.parent/(scope+'_command.json'),command)
            print('START',dataset,scope,flush=True)
            with (out.parent/(scope+'_launcher.log')).open('x') as log:
                code=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            result=read(out/'render_result.json') if (out/'render_result.json').exists() else None
            evaluation=audit=None;error=None
            valid=bool(code==0 and result and result['valid_execution'])
            if valid:
                try:
                    evaluation=trial.common.evaluation.panel.run_evaluation_twice(out,dataset,scene,
                        trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                    assert evaluation['pass']
                    audit=audit_run(out,OLD/dataset,scope);write(out/'independent_audit.json',audit)
                except Exception as exc:
                    error=repr(exc)
            changed=[p for p,v in lock.items() if sha(Path(p))!=v['sha256']]
            row={'dataset':dataset,'scene':scene,'scope':scope,'seed':0,'output':str(out),
                'returncode':code,'valid_execution':valid,'audit_pass':bool(audit and audit['pass']),
                'evaluation':evaluation,'error':error,'source_changed':changed,
                'psnr':evaluation['fixed_psnr_first'] if evaluation and evaluation['pass'] else None,
                'mapping_seconds':result['mapping_seconds'] if result else None,'audit':audit}
            rows.append(row);write(args.output/'progress.json',rows);journal(row)
            print('DONE',dataset,scope,'PSNR',row['psnr'],'audit',row['audit_pass'],flush=True)
            if not valid or not row['audit_pass'] or changed or error:
                raise RuntimeError('Invalid run; inspect preserved artifacts: '+str(out))
    write(args.output/'summary.json',rows)
    print('CUMULATIVE_PANEL_COMPLETE',flush=True)


if __name__=='__main__':main()
