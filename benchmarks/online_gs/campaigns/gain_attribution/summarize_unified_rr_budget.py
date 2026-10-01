"""Verify and report an RR/ERVS budget panel against the 40-render panel."""
import argparse
from pathlib import Path
import run_unified_rr_ervs_panel as panel

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    root=args.output.resolve();c=panel.common
    rows=c.read(root/'summary.json');comparison=c.read(root/'comparison.json')
    protocol=c.read(root/'protocol.json');budget=protocol['renders_per_kf']
    assert len(rows)==6 and len(comparison)==3
    previous=c.read(panel.ROOT/'results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/comparison.json')
    lock=c.read(root/'source_lock.json')
    changed=[name for name,v in lock.items() if c.sha(Path(name))!=v['sha256']]
    assert not changed
    details=[]
    for d in c.SCENES:
        arms={row['case']:row for row in rows if row['dataset']==d}
        assert set(arms)=={'rr','ervs'}
        for selector,row in arms.items():
            assert row['valid_execution'] and row['audit_pass'] and not row['error'] and not row['source_changed']
            panel.audit_run(Path(row['output']),d,row['config'])
        pair=next(x for x in comparison if x['dataset']==d)
        old=next(x for x in previous if x['dataset']==d)
        results={key:c.read(Path(row['output'])/'render_result.json') for key,row in arms.items()}
        final={key:r['training']['generations'][-1]['policy'] for key,r in results.items()}
        assert final['rr']['admitted_dense']==final['ervs']['admitted_dense']
        details.append({**pair,'delta_at40':old['ervs_minus_rr'],
            'final_admitted_dense':len(final['ervs']['admitted_dense']),
            'final_keyframes':len(final['ervs']['keyframes']),
            'role_renders':{k:row['audit']['role_renders'] for k,row in arms.items()},
            'dense_prepared':{k:row['dense_prepared'] for k,row in arms.items()},
            'optimizer_steps':{k:r['main_optimizer_steps'] for k,r in results.items()}})
    report={'pass':True,'renders_per_kf':budget,'mean_ervs_minus_rr':sum(x['ervs_minus_rr'] for x in details)/3,
        'mean_ervs_minus_rr_at40':sum(x['ervs_minus_rr'] for x in previous)/3,
        'source_changed':changed,'details':details}
    c.write(root/'budget_comparison.json',report)
    print(report)

if __name__=='__main__':main()
