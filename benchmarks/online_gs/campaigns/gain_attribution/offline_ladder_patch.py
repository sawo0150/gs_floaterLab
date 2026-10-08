"""Online → offline gap decomposition ("ladder") for the adopted B mapper (runtime patch; offline_patch.py untouched).

Same frozen tracker stream, births and render credit as the online runs. B_LADDER_MODE selects one rung:
  sequence  no photometric step during the stream; right after the last non-terminal arrival the final generation
            replays the exact service sequence of a reference online run (B_SEQ_REF render_result.json, per role in
            order: window+keyframe services → KF queue, dense services → dense queue) with the final map and poses.
            vs the online reference: effect of training *during* the stream (pose updates after training, map still
            growing, births/pruning interleaved with training).
  counts    as `sequence` but the same multiset of services is shuffled (seeded): same per-view counts, no stream
            order. vs `sequence`: effect of chronological order (forgetting/recency).
            (vs the existing offline arm, epoch RR with equal counts: effect of the count allocation.)
  hybrid    online training (ERVS K16 group draws, unchanged weights) until a fraction B_HYBRID_FRAC of the credit
            earned so far is spent; the rest is spent after the last non-terminal arrival with epoch round-robin over
            the KF and dense pools (quotas 0:6:6). Dense admission keeps its causal growth rule throughout.
Final-drain batches use quotas (0, 6, 6) like the offline arm; protected opacity pruning runs every 300 renders inside
the drain. For sequence/counts the final dense pool is preadmitted as the reference run's final admitted set
(identical across online arms and seeds). Pre-reset credit (early, discarded generations) is spent with the normal
draw before each mapper control, as online. Writes <output>/ladder.json.
Usage: B_SELECTED_WORKER=... B_LADDER_MODE=... B_OFFLINE_REF=... B_OFFLINE_LAST_UID=... [B_SEQ_REF=...]
       [B_HYBRID_FRAC=0.85 B_GROUP_K=16] python offline_ladder_patch.py <worker args>
"""
import atexit
from collections import Counter, deque
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import random
import runpy
import sys
import textwrap

MODE = os.environ['B_LADDER_MODE']
assert MODE in ('sequence', 'counts', 'hybrid'), MODE
FRAC = float(os.environ.get('B_HYBRID_FRAC', '0.85'))
K = int(os.environ.get('B_GROUP_K', '16'))
QUOTAS = (0, 6, 6)
STATE = dict(draining=False, final=False, cap=None, runtime=None, drains=[], prune=None, preadmitted=None,
             queues=None, stats=Counter())


def install():
    import online_photometric as P
    import online_mapper_runtime as R
    import unified_view_training as U
    import group_k_patch as GK
    sel = Path(os.environ['B_SELECTED_WORKER']).parent
    sys.path.insert(0, str(sel))
    ref = json.loads(Path(os.environ['B_OFFLINE_REF']).read_text())
    ref_policy = ref['training']['generations'][-1]['policy']
    ref_dense, ref_kf = set(ref_policy['admitted_dense']), set(ref_policy['keyframes'])
    last_uid = int(os.environ['B_OFFLINE_LAST_UID'])
    seq = None
    if MODE in ('sequence', 'counts'):
        sr = json.loads(Path(os.environ['B_SEQ_REF']).read_text())
        lr = sr['training']['loss_routes']; g = max(x['generation'] for x in lr)
        seq = {'keyframe': [x['uid'] for x in lr if x['generation'] == g and x['role'] in ('window', 'keyframe')],
               'dense': [x['uid'] for x in lr if x['generation'] == g and x['role'] == 'dense']}
        if MODE == 'counts':
            rng = random.Random(1234)
            for r in seq:
                rng.shuffle(seq[r])

    # ---- reserve: ERVS path draw replaced; online phase = ERVS K16 group draws, final drain = mode queues / RR
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    if hashlib.sha256(src.encode()).hexdigest() != GK.RESERVE_SHA256:
        raise RuntimeError('UnifiedTrainingSet.reserve changed')
    src = src.replace(GK.OLD, 'uid = _LADDER_DRAW(self, role, pools[role], used, scales[role], candidates, weights)')
    st = STATE['stats']

    def group_draw(self, role, pool, used, scale, candidates):
        q = self.__dict__.setdefault('_k_groups', {}).setdefault(role, deque())
        members = set(pool)
        for attempt in range(2):
            while q:
                u = q.popleft()
                if u in members and u not in used:
                    return u
            if attempt == 0:
                ordered = sorted(members); low = min(self.counts[u] for u in ordered)
                keys = sorted(((-(self.counts[u] - low) / scale - math.log(-math.log(max(self.rng.random(), 1e-15))), u)
                               for u in ordered), reverse=True)
                q.extend(u for _, u in keys[:min(K, len(keys))])
        return self.rng.choice(candidates)

    def rr_draw(self, role, pool, used, candidates):
        e = self.__dict__.setdefault('_ladder_rr', {}).setdefault(role, deque())
        members = set(pool)
        for attempt in range(2):
            for _ in range(len(e)):
                u = e.popleft()
                if u in members and u not in used:
                    return u
                if u in members:
                    e.append(u)          # blocked in this batch: keep for later
            if attempt == 0:
                fresh = [u for u in sorted(members) if u not in e]
                self.rng.shuffle(fresh); e.extend(fresh); st['rr_epoch', role] += 1
        st['rr_fallback', role] += 1
        return self.rng.choice(candidates)

    def ladder_draw(self, role, pool, used, scale, candidates, weights):
        if STATE['final'] and MODE in ('sequence', 'counts'):
            q = STATE['queues'][role]
            for i, u in enumerate(q):
                if u not in used and u in pool:
                    del q[i]; st['queue_draw', role] += 1
                    return u
            st['queue_miss', role] += 1
            return rr_draw(self, role, pool, used, candidates)
        if STATE['final']:
            st['rr_draw', role] += 1
            return rr_draw(self, role, pool, used, candidates)
        st['online_draw', role] += 1
        return group_draw(self, role, pool, used, scale, candidates)

    ns = dict(vars(U), _LADDER_DRAW=ladder_draw)
    exec(compile(src, f'<offline_ladder_patch:{U.__file__}>', 'exec'), ns)
    U.UnifiedTrainingSet.reserve = ns['reserve']

    # ---- gating: no stream training (sequence/counts) or only up to FRAC of earned credit (hybrid)
    step = P.OnlinePhotometricTrainer.step

    def gated_step(self, *a, **k):
        if STATE['draining']:
            return step(self, *a, **k)
        if MODE == 'hybrid' and STATE['runtime'] is not None:
            b = STATE['runtime'].unified_budget
            if b.completed < math.floor(FRAC * b.target):
                k['max_views'] = min(k.get('max_views') or 10 ** 9, math.floor(FRAC * b.target) - b.completed)
                return step(self, *a, **k)
        return False
    P.OnlinePhotometricTrainer.step = gated_step

    import protected_opacity_prune as PP
    init = PP.ProtectedOpacityPrune.__init__

    def keep(self, *a, **k):
        init(self, *a, **k); STATE['prune'] = self
    PP.ProtectedOpacityPrune.__init__ = keep

    def drain(runtime, reason, arrival, final=False):
        import torch
        trainer, budget = runtime.mapper.online_view_trainer, runtime.unified_budget
        with torch.cuda.stream(runtime.stream), runtime.mapper._gaussian_lock, torch.enable_grad():
            budget.sync(); trainer.sync()
            policy = trainer.policy
            if final:
                policy.batch_quotas = QUOTAS
                if MODE in ('sequence', 'counts'):
                    if set(policy.keyframes) != ref_kf:
                        raise RuntimeError('KF pool differs from reference')
                    missing = ref_dense - set(policy.offered)
                    if missing:
                        raise RuntimeError(f'reference dense views not offered: {sorted(missing)[:5]}')
                    extra = sorted(policy.admitted - ref_dense)
                    if extra:
                        raise RuntimeError(f'dense views admitted before the drain: {extra[:5]}')
                    new = sorted(ref_dense - policy.admitted)
                    for uid in new:
                        policy.admitted.add(uid); policy.counts.setdefault(uid, 0); policy.photometric_counts.setdefault(uid, 0)
                        policy.admission_ledger.append({'uid': uid, 'rgb_steps': policy.rgb_steps_completed,
                                                        'generation': policy.generation, 'offline_preadmit': True,
                                                        'pool_size_after': len(policy.keyframes | policy.admitted),
                                                        'keyframe_count': len(policy.keyframes),
                                                        'growth_budget_scope': policy.growth_budget_scope})
                    policy._spent_growth_slots += len(new)
                    policy._admit = lambda: None
                    STATE['preadmitted'] = len(new)
                    STATE['queues'] = {r: list(v) for r, v in seq.items()}
                STATE['final'] = True
            before, gen = budget.completed, trainer.generation
            STATE['draining'] = True
            try:
                while budget.completed < budget.target:
                    services = trainer.policy.rgb_view_services
                    try:
                        ok = trainer.step(max_views=budget.target - budget.completed)
                    finally:
                        budget.completed += trainer.policy.rgb_view_services - services
                    if not ok:
                        break
                    if final and STATE['prune'] is not None:
                        STATE['prune'].after_packet(budget.completed, arrival)
            finally:
                STATE['draining'] = False
            runtime.stream.synchronize()
        STATE['drains'].append(dict(reason=reason, arrival_uid=arrival, generation=gen, renders=budget.completed - before,
                                    completed=budget.completed, target=budget.target, final=final,
                                    pools=dict(keyframe=len(trainer.policy.keyframes), dense=len(trainer.policy.admitted)),
                                    queue_left={r: len(q) for r, q in (STATE['queues'] or {}).items()}))

    apply_control = R.OnlineMapperRuntime._apply_control

    def control(self, kind, value):
        STATE['runtime'] = self
        drain(self, 'control:' + kind, None)
        return apply_control(self, kind, value)
    R.OnlineMapperRuntime._apply_control = control

    dispatch = R.OnlineMapperRuntime.dispatch

    def ladder_dispatch(self, packet):
        STATE['runtime'] = self
        result = dispatch(self, packet)
        if self.schedule == 'unified' and packet.get('_arrival_uid') == last_uid:
            drain(self, 'final', last_uid, final=True)
        return result
    R.OnlineMapperRuntime.dispatch = ladder_dispatch

    import run_arrived_online_worker as W
    checks = W.training_checks

    def ladder_checks(trainer, main_steps):
        res = checks(trainer, main_steps)
        ok = True
        for g in trainer['generations']:
            p = g['policy']
            causal = [a for a in g['admissions'] if not a.get('offline_preadmit')]
            ok &= all(i + 1 <= a['rgb_steps'] // p['kappa'] for i, a in enumerate(causal))
        res['growth_capacity'] = ok
        return res
    W.training_checks = ladder_checks

    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'ladder.json').write_text(json.dumps(dict(
                mode=MODE, frac=FRAC if MODE == 'hybrid' else None, K=K, quotas=QUOTAS, last_uid=last_uid,
                offline_ref=os.environ['B_OFFLINE_REF'], seq_ref=os.environ.get('B_SEQ_REF'),
                preadmitted=STATE['preadmitted'], drains=STATE['drains'],
                final_drained=any(d['final'] for d in STATE['drains']),
                stats={f'{a}/{b}': n for (a, b), n in sorted(st.items())}), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    sys.path.insert(1, str(here))
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
