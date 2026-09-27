#!/usr/bin/env python3
"""Exact40 cumulative ERVS with native densification and pruning disabled."""
import argparse
import json
from pathlib import Path
import subprocess

import run_cumulative_ervs_panel as common

trial = common.trial
HERE = Path(__file__).resolve().parent
ROOT = trial.BASE.WORKSPACE
CARD = 'campaigns/06_gain_attribution/no_densify_prune/README.md'
ON = ROOT/'results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1'


def journal(row):
    message = (f"**2026-09-25 no densify/prune40 / {row['dataset']}:** "
               f"execution={row['valid_execution']}, audit={row['audit_pass']}, "
               f"held-out PSNR={row['psnr']}; {row['output']}.")
    with (ROOT/'context/experiments'/CARD).open('a') as f:
        f.write('\n'+message+'\n')
    for name, heading, link in [('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/'+CARD),
                               ('context/experiments/INDEX.md', '# Experiment Index\n', CARD)]:
        p=ROOT/name;s=p.read_text();assert heading in s
        p.write_text(s.replace(heading,heading+'\n- '+message+' → [카드]('+link+')\n',1))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    common.write(args.output/'protocol.json',{
        'scenes':common.SCENES,'renders_per_kf':40,'seed':0,'scope':'all_rgb',
        'disable':['densify','prune','densification_stats','observation_topology_gate'],
        'preserve':['observation_birth','tracker_map_reset','opacity_reset','loss','paired_schedule'],
        'reference':str(ON),'actual_tracking':False,'batch_size':1,
        'quality_rule':'all scenes reported without retrospective tuning; seed0 only'})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files=list((backend/'vigs').rglob('*.py'))+[Path(__file__).resolve(),
        HERE/'run_cumulative_ervs_panel.py',HERE/'run_kf15_render_worker.py',
        HERE/'run_arrived_online_worker.py',HERE/'keyframe_render_budget.py',
        HERE/'render_work_audit.py',HERE/'densify_prune_ablation_audit.py']
    source=args.output/'source';source.mkdir();lock={}
    for p in files:
        digest=common.sha(p);dest=source/(digest[:12]+'_'+p.name);dest.write_bytes(p.read_bytes())
        lock[str(p)]={'sha256':digest,'copy':str(dest)}
    common.write(args.output/'source_lock.json',lock)
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    base=trial.ROOT/'live_worker_integration_audit';rows=[]
    for dataset,scene in common.SCENES.items():
        trial.common.evaluation.panel.v2.gpu_idle()
        out=args.output/dataset
        setup=base/('v5_packet_identity/aria_setup' if dataset=='aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
        command=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(HERE/'run_kf15_render_worker.py'),
            '--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
            '--output',str(out),'--renders-per-kf','40','--seed','0','--membership','immediate',
            '--selector','ervs','--schedule','paired_kf_dense','--selection-count-scope','all_rgb',
            '--disable-densify-prune','--reference',str(ON/dataset/'all_rgb/render_result.json')]
        common.write(args.output/(dataset+'_command.json'),command)
        print('START',dataset,flush=True)
        with (args.output/(dataset+'_launcher.log')).open('x') as log:
            code=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        result=common.read(out/'render_result.json') if (out/'render_result.json').exists() else None
        valid=bool(code==0 and result and result['valid_execution'])
        evaluation=audit=None;error=None
        if valid:
            try:
                evaluation=trial.common.evaluation.panel.run_evaluation_twice(out,dataset,scene,
                    trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                assert evaluation['pass']
                audit=common.audit_run(out,common.OLD/dataset,'all_rgb')
                control=common.read(ON/dataset/'all_rgb/render_result.json')
                assert result['render_counts']==control['render_counts']
                assert result['main_optimizer_steps']==control['main_optimizer_steps']
                role_counts=lambda r: {role:sum(len(s['uids']) for g in r['training']['generations']
                    for s in g['services'] if (s['source'] if s['source']=='native' else s['role'])==role)
                    for role in ('native','keyframe','dense')}
                assert role_counts(result)==role_counts(control)
                assert result['densify_prune_ablation']['pass']
                assert not result['densify_prune_ablation']['forbidden_calls']
                text=(args.output/(dataset+'_launcher.log')).read_text()
                assert 'MAP_TOPOLOGY_EVENT' not in text and 'MAP_TOPOLOGY_MUTATION' not in text
                audit.update(no_densify_prune=True,same_work_as_cumulative_control=True,
                             role_renders=role_counts(result))
                common.write(out/'independent_audit.json',audit)
            except Exception as exc:
                error=repr(exc)
        changed=[p for p,v in lock.items() if common.sha(Path(p))!=v['sha256']]
        row={'dataset':dataset,'scene':scene,'output':str(out),'returncode':code,
             'valid_execution':valid,'audit_pass':bool(audit and audit.get('no_densify_prune')),
             'error':error,'evaluation':evaluation,'source_changed':changed,
             'psnr':evaluation['fixed_psnr_first'] if evaluation and evaluation['pass'] else None,
             'mapping_seconds':result['mapping_seconds'] if result else None,
             'gaussians':result['gaussians'] if result else None,'audit':audit}
        rows.append(row);common.write(args.output/'progress.json',rows);journal(row)
        print('DONE',dataset,'PSNR',row['psnr'],'audit',row['audit_pass'],flush=True)
        if not valid or not row['audit_pass'] or error or changed:
            raise RuntimeError('Invalid run; inspect '+str(out))
    common.write(args.output/'summary.json',rows)
    print('NO_DENSIFY_PRUNE_PANEL_COMPLETE',flush=True)


if __name__=='__main__':main()
