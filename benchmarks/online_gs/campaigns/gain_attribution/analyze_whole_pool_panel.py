#!/usr/bin/env python3
"""Summarize the preregistered seed0 panel without declaring final acceptance."""
import hashlib
import json
from pathlib import Path
import run_online_dense_training as trial


def main():
    root = trial.ROOT / 'v18_whole_pool'
    rows = []
    locks = {}
    for dataset, scene in [('rpng','table_06'),('aria','aria1253'),('utmm','square-1')]:
        arms = {}
        cohorts = []
        references = []
        for arm in ('growth_ervs','kf_only','production'):
            path = root / dataset / scene / arm / 'seed0'
            files = ['result.json','contract.json','online_training.json','source_lock.json',
                     'traj_full_beforeBA.txt','psnr/strict_fixed_manifest/final_result.json']
            for name in files:
                source = path / name
                locks[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
            result = trial.common.read(path / 'result.json')
            contract = trial.common.read(path / 'contract.json')
            if not result['valid'] or not contract['include_mapper_setup_in_clock']:
                raise ValueError('Invalid full-time run: '+str(path))
            metrics = trial.common.read(path / 'psnr/strict_fixed_manifest/final_result.json')
            cohorts.append(sorted(row['uid'] for row in metrics['per_view']
                                  if row['predeclared_fixed_manifest_split']))
            references.append(locks[str(path / 'traj_full_beforeBA.txt')])
            arms[arm] = dict(result)
            if arm != 'production':
                audit = trial.common.read(path / 'online_training.json')
                policy = audit['training']['generations'][-1]['policy']
                arms[arm].update(keyframes=len(policy['keyframes']),
                                 admitted_dense=len(policy['admitted_dense']),
                                 native_commits=audit['native_commits'],
                                 photometric_commits=audit['photometric_commits'])
        if cohorts[1:] != [cohorts[0],cohorts[0]] or len(set(references)) != 1:
            raise ValueError('Different held-out cohort or reference trajectory')
        budgets = [a['budget_seconds'] for a in arms.values()]
        if len(set(budgets)) != 1:
            raise ValueError('Different time budgets')
        candidate = arms['growth_ervs']['heldout_psnr']
        old = trial.common.read(trial.ROOT / 'v17_solver_only' / dataset / scene / 'growth_ervs/seed0/result.json')
        rows.append({'dataset':dataset,'scene':scene,'arms':arms,
            'delta_kf':candidate-arms['kf_only']['heldout_psnr'],
            'delta_production':candidate-arms['production']['heldout_psnr'],
            'delta_v17':candidate-old['heldout_psnr'],
            'fixed_view_count':len(cohorts[0]),'same_evaluator_coordinates':True})
    report={'rows':rows,'mean_delta_kf':sum(r['delta_kf'] for r in rows)/len(rows),
            'mean_delta_production':sum(r['delta_production'] for r in rows)/len(rows),
            'mean_delta_v17':sum(r['delta_v17'] for r in rows)/len(rows),
            'regressions_vs_kf':[r['dataset'] for r in rows if r['delta_kf'] < 0],
            'seed':0,'final_acceptance':False,'strict_tracking_claim':False,
            'fast_convergence_claim':False,'source_artifacts_sha256':locks}
    trial.common.write(root / 'summary.json',report)
    print(json.dumps({k:v for k,v in report.items() if k != 'source_artifacts_sha256'},indent=2))


if __name__ == '__main__': main()
