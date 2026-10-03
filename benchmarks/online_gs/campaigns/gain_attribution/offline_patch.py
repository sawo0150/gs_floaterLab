"""Offline (deferred-training) reference for the adopted B mapper (runtime patch only).

Same frozen tracker stream, same Gaussian births (local birth is off, so births do not read the trained map), same
render credit; the only change is *when* photometric training happens:
  * during the stream no photometric step runs (credit accumulates);
  * before every mapper control (metric rescale / reset) the pending credit is spent on the current generation, as the
    online run would have spent it before that control;
  * right after the last non-terminal arrival (B_OFFLINE_LAST_UID; all optimizer work must finish before the terminal
    input), the final generation's dense pool is set to the reference online run's final admitted set
    (B_OFFLINE_REF render_result.json; identical across online arms and seeds) and the remaining credit is spent with
    epoch round-robin over the KF and dense pools at quotas (0, 6, 6), i.e. the same 50:50 KF/dense split as the online
    (3 window + 3 KF) : 6 dense, with equal per-view counts within each pool. Protected opacity pruning runs every
    300 renders inside the drain, as it does at packet boundaries online.
Writes <output>/offline.json. Usage: B_SELECTED_WORKER=... B_OFFLINE_REF=... B_OFFLINE_LAST_UID=... python offline_patch.py <worker args>
"""
import atexit
import json
import os
from pathlib import Path
import runpy
import sys

QUOTAS = (0, 6, 6)
STATE = dict(draining=False, drains=[], preadmitted=None, prune=None)


def install():
    import online_photometric as P
    import online_mapper_runtime as R
    ref = json.loads(Path(os.environ['B_OFFLINE_REF']).read_text())
    ref_policy = ref['training']['generations'][-1]['policy']
    ref_dense, ref_kf = set(ref_policy['admitted_dense']), set(ref_policy['keyframes'])
    last_uid = int(os.environ['B_OFFLINE_LAST_UID'])

    step = P.OnlinePhotometricTrainer.step

    def gated_step(self, *a, **k):
        return step(self, *a, **k) if STATE['draining'] else False
    P.OnlinePhotometricTrainer.step = gated_step

    sel = Path(os.environ['B_SELECTED_WORKER']).parent
    sys.path.insert(0, str(sel))
    import protected_opacity_prune as PP
    init = PP.ProtectedOpacityPrune.__init__

    def keep(self, *a, **k):
        init(self, *a, **k)
        STATE['prune'] = self
    PP.ProtectedOpacityPrune.__init__ = keep

    def drain(runtime, reason, arrival, final=False):
        import torch
        trainer = runtime.mapper.online_view_trainer
        budget = runtime.unified_budget
        with torch.cuda.stream(runtime.stream), runtime.mapper._gaussian_lock:
            budget.sync()
            trainer.sync()
            policy = trainer.policy
            policy.selector = 'rr'
            policy.batch_quotas = QUOTAS
            if final:
                kf = set(policy.keyframes)
                if kf != ref_kf:
                    raise RuntimeError(f'offline KF pool differs from reference ({len(kf)} vs {len(ref_kf)})')
                missing = ref_dense - set(policy.offered)
                if missing:
                    raise RuntimeError(f'reference dense views not offered: {sorted(missing)[:5]}')
                new = sorted(ref_dense - policy.admitted)
                extra = sorted(policy.admitted - ref_dense)
                if extra:
                    raise RuntimeError(f'dense views admitted before the drain: {extra[:5]}')
                for uid in new:
                    policy.admitted.add(uid)
                    policy.counts.setdefault(uid, 0)
                    policy.photometric_counts.setdefault(uid, 0)
                    policy.admission_ledger.append({'uid': uid, 'rgb_steps': policy.rgb_steps_completed,
                                                    'generation': policy.generation, 'offline_preadmit': True,
                                                    'pool_size_after': len(policy.keyframes | policy.admitted),
                                                    'keyframe_count': len(policy.keyframes),
                                                    'growth_budget_scope': policy.growth_budget_scope})
                policy._spent_growth_slots += len(new)
                policy._admit = lambda: None          # the dense pool stays the reference set
                STATE['preadmitted'] = len(new)
            before, gen = budget.completed, trainer.generation
            STATE['draining'] = True
            prune = STATE['prune']
            try:
                while budget.completed < budget.target:
                    remaining = budget.target - budget.completed
                    services = trainer.policy.rgb_view_services
                    try:
                        ok = trainer.step(max_views=remaining)
                    finally:
                        budget.completed += trainer.policy.rgb_view_services - services
                    if not ok:
                        break
                    if prune is not None:
                        prune.after_packet(budget.completed, arrival)
            finally:
                STATE['draining'] = False
            runtime.stream.synchronize()
        STATE['drains'].append(dict(reason=reason, arrival_uid=arrival, generation=gen, renders=budget.completed - before,
                                    completed=budget.completed, target=budget.target, final=final,
                                    pools=dict(keyframe=len(trainer.policy.keyframes),
                                               dense=len(trainer.policy.admitted))))

    apply_control = R.OnlineMapperRuntime._apply_control

    def control(self, kind, value):
        drain(self, 'control:' + kind, None)
        return apply_control(self, kind, value)
    R.OnlineMapperRuntime._apply_control = control

    dispatch = R.OnlineMapperRuntime.dispatch

    def offline_dispatch(self, packet):
        result = dispatch(self, packet)
        if self.schedule == 'unified' and packet.get('_arrival_uid') == last_uid:
            drain(self, 'final', last_uid, final=True)
        return result
    R.OnlineMapperRuntime.dispatch = offline_dispatch

    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'offline.json').write_text(json.dumps(dict(
                reference=os.environ['B_OFFLINE_REF'], last_uid=last_uid, quotas=QUOTAS, selector='rr',
                reference_dense=len(ref_dense), reference_keyframes=len(ref_kf),
                preadmitted=STATE['preadmitted'], drains=STATE['drains'],
                final_drained=any(d['final'] for d in STATE['drains'])), indent=1) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)
    install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
