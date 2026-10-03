#!/usr/bin/env python3
"""Collect ERVS K16 vs uniform-with-replacement results (budget 25, seeds 0-2) for 19 scenes and render the artifact page.

Pinned scenes (aria1253, table_06, aria1253rot, square-1) come from ervs_vs_iid_seeds; the 15 others from
ervs_vs_iid_scenes. Writes page_data.json and ervs_scenes.html into results/.../ervs_vs_iid_scenes/v1/.
"""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
R = ROOT / 'results/campaigns/gain_attribution'
OUT = R / 'ervs_vs_iid_scenes/v1'
GRID = np.linspace(0, 1, 101)
NB = 20   # arrival-time bins for service counts
SEEDS, BUDGET, ARMS = (0, 1, 2), 25, ('ervs_k16', 'uniform_iid')
PINNED = [('aria', 'aria1253', 'aria'), ('rpng', 'table_06', 'rpng'), ('rot', 'aria1253rot', 'aria'),
          ('utmm', 'square-1', 'utmm')]
NEW = [('aria301_305', 'aria')] + [(f'table_0{i}', 'rpng') for i in (1, 2, 3, 4, 5, 7, 8)] + \
      [(s, 'utmm') for s in ('ego-centric-1', 'ego-centric-2', 'ego-drive', 'fast-straight', 'slow-straight-1',
                             'slow-straight-2', 'square-2')]


def pinned_dir(key, arm, seed):
    b = BUDGET
    if seed:
        return R / f'ervs_vs_iid_seeds/v1/seeds/{key}/render{b}/{arm}_s{seed}'
    if arm == 'ervs_k16':
        return (R / f'ervs_vs_uniform_k16/v1/cmp/{key}/render{b}/ervs_k16' if key in ('aria', 'rpng')
                else R / f'ervs_group_k/v1/groupk/{key}/render{b}/K16')
    if key in ('aria', 'rpng'):
        return R / f'ervs_vs_uniform_k16/v1/cmp/{key}/render{b}/uniform_iid'
    if key == 'rot':
        return R / f'ervs_vs_uniform/v1/uniform/rot/render{b}/uniform_iid'
    return R / f'ervs_vs_iid_seeds/v1/seeds/{key}/render{b}/uniform_iid_s0'


def views(d):
    f = d / 'psnr/strict_fixed_manifest/final_result.json'
    if not f.exists():
        return None
    final = json.loads(f.read_text())
    pv = sorted((x for x in final['per_view'] if x.get('predeclared_fixed_manifest_split')),
                key=lambda x: x['frame_index'])
    fx = final['predeclared_fixed_manifest_posthoc']
    return (np.array([x['frame_index'] for x in pv], float), np.array([x['psnr'] for x in pv]),
            fx.get('mean_ssim'), fx.get('mean_lpips'))


def counts(d):
    """Mean completed RGB services per view, by arrival-time bin (KF views: window + KF pool; dense views).

    Only the final mapper generation counts: earlier generations are discarded at tracker-driven mapper resets, so
    their services never reach the evaluated map (and ERVS's own counts restart with the generation).
    """
    r = json.loads((d / 'render_result.json').read_text())
    arr = {a['uid']: a['seconds'] for a in r['arrivals']}
    t0, t1 = min(arr.values()), max(arr.values())
    final_gen = max(x['generation'] for x in r['training']['loss_routes'])
    n, kind = {}, {}
    for x in r['training']['loss_routes']:
        if x['generation'] != final_gen:
            continue
        n[x['uid']] = n.get(x['uid'], 0) + 1
        kind[x['uid']] = 'dense' if x['role'] == 'dense' else 'kf'
    out = {}
    for k in ('kf', 'dense'):
        sums, cnt = np.zeros(NB), np.zeros(NB)
        for u, c in n.items():
            if kind[u] != k: continue
            b = min(NB - 1, int((arr[u] - t0) / (t1 - t0) * NB))
            sums[b] += c; cnt[b] += 1
        out[k] = dict(mean=np.where(cnt > 0, sums / np.maximum(cnt, 1), np.nan), views=cnt,
                      overall=float(sum(n[u] for u in n if kind[u] == k) / max(1, sum(kind[u] == k for u in n))),
                      cv=float(np.std([n[u] for u in n if kind[u] == k]) / np.mean([n[u] for u in n if kind[u] == k])))
    return out


def smooth(y, frac):
    k = np.ones(max(3, int(round(frac * len(y)))))
    return np.convolve(y, k, 'same') / np.convolve(np.ones_like(y), k, 'same')


def bins5(y):
    return [float(y[i * len(y) // 5:(i + 1) * len(y) // 5].mean()) for i in range(5)]


def scene_record(scene, dataset, group, dirfn):
    runs = {}
    for arm in ARMS:
        for s in SEEDS:
            v = views(dirfn(arm, s))
            if v is not None:
                runs[(arm, s)] = v
    seeds = [s for s in SEEDS if ('ervs_k16', s) in runs and ('uniform_iid', s) in runs]
    if not seeds:
        return None
    rec = dict(scene=scene, dataset=dataset, group=group, seeds=seeds, n_views=int(len(runs[('ervs_k16', seeds[0])][1])),
               curve={}, bins={}, per_seed=[], count={}, count_scale={}, count_cv={})
    cnt = {(a, s): counts(dirfn(a, s)) for a in ARMS for s in seeds}
    for k in ('kf', 'dense'):
        scale = float(np.mean([cnt[(a, s)][k]['overall'] for a in ARMS for s in seeds]))
        rec['count_scale'][k] = round(scale, 3)
        rec['count'][k], rec['count_cv'][k] = {}, {}
        for a in ARMS:
            with np.errstate(all='ignore'):
                m = np.nanmean([cnt[(a, s)][k]['mean'] for s in seeds], 0)
            rec['count'][k][a] = [None if np.isnan(v) else round(float(v), 3) for v in m]
            rec['count_cv'][k][a] = round(float(np.mean([cnt[(a, s)][k]['cv'] for s in seeds])), 4)
    for arm in ARMS:
        cs, bs = [], []
        for s in seeds:
            f, p, *_ = runs[(arm, s)]
            t = (f - f[0]) / (f[-1] - f[0])
            cs.append(np.interp(GRID, t, smooth(p, 0.10))); bs.append(bins5(p))
        rec['curve'][arm] = np.round(np.mean(cs, 0), 3).tolist()
        rec['bins'][arm] = np.round(np.mean(bs, 0), 3).tolist()
    ds = []
    for s in seeds:
        (fe, pe, se_, le), (fu, pu, su, lu) = runs[('ervs_k16', s)], runs[('uniform_iid', s)]
        assert (fe == fu).all(), scene
        d = pe - pu; t = (fe - fe[0]) / (fe[-1] - fe[0])
        ds.append(np.interp(GRID, t, smooth(d, 0.20)))
        q = max(1, -(-len(pe) // 4))
        m = lambda p, ss, ll: dict(psnr=float(p.mean()), minbin=min(bins5(p)), wq1=float(np.sort(p)[:q].mean()),
                                   ssim=ss, lpips=ll)
        rec['per_seed'].append(dict(seed=s, ervs=m(pe, se_, le), iid=m(pu, su, lu)))
    rec['diff_curve'] = np.round(np.mean(ds, 0), 3).tolist()
    return rec


def main():
    scenes = []
    for key, scene, ds in PINNED:
        r = scene_record(scene, ds, 'pinned', lambda a, s, k=key: pinned_dir(k, a, s))
        if r: scenes.append(r)
    for scene, ds in NEW:
        r = scene_record(scene, ds, 'new',
                         lambda a, s, sc=scene: OUT / f'scenes/{sc}/render{BUDGET}/{a}_s{s}')
        if r: scenes.append(r)
    data = dict(grid=np.round(GRID, 3).tolist(), count_bins=NB, budget=BUDGET, scenes=scenes,
                expected=dict(new=len(NEW), pinned=len(PINNED), seeds=len(SEEDS)))
    (OUT / 'page_data.json').write_text(json.dumps(data))
    tmpl = (HERE / 'ervs_scenes_page.html').read_text()
    (OUT / 'ervs_scenes.html').write_text(tmpl.replace('/*__DATA__*/null', json.dumps(data)))
    print('scenes', len(scenes), 'seed-runs', sum(len(s['seeds']) for s in scenes))


if __name__ == '__main__':
    main()
