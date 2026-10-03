"""Per-step training signals for the adopted B mapper, and signal-driven replay samplers (runtime patches only).

Logging (always on): after each training render in `OnlinePhotometricTrainer.step` (sha-checked copy, one injected line)
the hook records, without gradients and without extra renders, the view's training PSNR and RGB L1 against its own
target image and the scalar loss. Values stay on the GPU until the process exits; `<output>/train_signal.json` holds one
row per render: [step, generation, uid, role, psnr, l1, loss].

Samplers (`B_SIGNAL_MODE`, ERVS selector + persistent K-group queue as in group_k_patch): replaces the count weight of
the KF and dense pools with a weight built from the per-view signal state of the current generation:
  forget_stale   PLR-style mix: (1-ρ)·rank-prioritized forgetting + ρ·staleness, forgetting = best − last training PSNR
  progress_stale PLR-style mix with learning progress = last − previous training PSNR (positive part)
  loss_stale     PLR-style mix with the last training loss (higher first)
  catchup        Curious-Replay-style: c·β^n + 1 (strong boost until a view has a few services, then uniform)
  age_norm       Gibbs on age-normalized maturity m = n / (services since first service × pool rate)
  loss_per       Prioritized Experience Replay: p ∝ (last training loss + ε)^α, no staleness mix (α = B_SIGNAL_ALPHA, 0.7)
  interference   MIR-inspired: rank of interference exposure since the last visit (log(1+mid) − log(1+near) training
                 steps; near = ±1.5% of the stream, mid = 1.5–9%) mixed with staleness like PLR
Unseen views (never trained in this generation) get the highest priority in every mode (PLR/CR convention).
Usage: B_PATCH_WORKER=<group_k_patch.py|sampling_mode_patch.py> [B_SIGNAL_MODE=...] python train_signal.py <worker args>
"""
import atexit
from collections import Counter, deque
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import runpy
import sys
import textwrap

STEP_SHA = '853b5ea9807c4af75cc09edc167bb79be79c035c5346f08b24f8d36db8422165'
LOSS_LINE = '                loss = self.refinement_loss(view, rendered, role=role)'
STATE = dict(rows=[], step=0, views={}, trainer=None)


def _target(trainer, view):
    img = getattr(view, 'original_image_gpu', None)
    if img is not None:
        return img
    key = (int(view.uid), id(view.original_image))
    if key in trainer.images:          # read the trainer cache without touching its audit counters
        return trainer.images[key]
    return view.original_image.cuda()


def hook(trainer, view, rendered, role, loss):
    import torch
    with torch.no_grad():
        r = rendered['render'].detach().clamp(0, 1)
        t = _target(trainer, view).to(r.dtype)
        mse = ((r - t) ** 2).mean()
        l1 = (r - t).abs().mean()
        psnr = -10 * torch.log10(mse.clamp_min(1e-10))
        STATE['rows'].append((STATE['step'], int(trainer.generation), int(view.uid), str(role),
                              torch.stack([psnr, l1, loss.detach().float()])))
    STATE['step'] += 1
    STATE['trainer'] = trainer


def materialize():
    """Move pending GPU scalars to Python floats and update per-view state (one sync per call)."""
    import torch
    pending = [r for r in STATE['rows'] if not isinstance(r[4], tuple)]
    if not pending:
        return
    vals = torch.stack([r[4] for r in pending]).cpu().tolist()
    j = 0
    for i, r in enumerate(STATE['rows']):
        if isinstance(r[4], tuple):
            continue
        p, l1, loss = vals[j]; j += 1
        STATE['rows'][i] = r[:4] + ((p, l1, loss),)
        step, gen, uid, role = r[:4]
        v = STATE['views'].setdefault((gen, uid), dict(n=0, first=step, best=-1e9, last=None, prev=None,
                                                       last_step=step, loss=None))
        v['n'] += 1; v['prev'] = v['last']; v['last'] = p; v['best'] = max(v['best'], p)
        v['last_step'] = step; v['loss'] = loss


def install_logger():
    import online_photometric as O
    src = textwrap.dedent(inspect.getsource(O.OnlinePhotometricTrainer.step))
    digest = hashlib.sha256(src.encode()).hexdigest()
    if digest != STEP_SHA:
        raise RuntimeError(f'OnlinePhotometricTrainer.step changed: {digest}')
    line = textwrap.dedent(LOSS_LINE) if not src.startswith('    ') else LOSS_LINE
    assert src.count(LOSS_LINE.strip()) == 1
    indent = LOSS_LINE[:len(LOSS_LINE) - len(LOSS_LINE.lstrip())]
    new = src.replace(LOSS_LINE.strip(), LOSS_LINE.strip() + '\n' + indent + '_SIGNAL_HOOK(self, view, rendered, role, loss)')
    ns = dict(vars(O), _SIGNAL_HOOK=hook)
    exec(compile(new, f'<train_signal:{O.__file__}>', 'exec'), ns)
    O.OnlinePhotometricTrainer.step = ns['step']
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if not (output and output.exists()):
            return
        materialize()
        rows = [[s, g, u, r, round(v[0], 4), round(v[1], 6), round(v[2], 6)] for s, g, u, r, v in STATE['rows']]
        (output / 'train_signal.json').write_text(json.dumps(dict(
            step_sha256=digest, columns=['step', 'generation', 'uid', 'role', 'psnr', 'l1', 'loss'],
            mode=os.environ.get('B_SIGNAL_MODE', 'log_only'), rows=rows)))
    atexit.register(dump)


# ---------------------------------------------------------------- signal samplers (stage 2)
RHO = float(os.environ.get('B_SIGNAL_RHO', '0.3'))
TEMP = float(os.environ.get('B_SIGNAL_TEMP', '0.3'))      # rank temperature (PLR uses 0.1–0.5)
CATCH_BETA = float(os.environ.get('B_SIGNAL_BETA', '0.7'))
CATCH_C = float(os.environ.get('B_SIGNAL_C', '30'))
AGE_TAU = float(os.environ.get('B_SIGNAL_TAU', '1'))
PER_ALPHA = float(os.environ.get('B_SIGNAL_ALPHA', '0.7'))
NEAR, MID = 0.015, 0.09


def signal_weights(mode, uids, generation):
    materialize()
    V = STATE['views']; now = STATE['step']
    st = [V.get((generation, u)) for u in uids]
    unseen = [s is None for s in st]
    if mode == 'catchup':
        return [1e6 if s is None else CATCH_C * CATCH_BETA ** s['n'] + 1 for s in st]
    if mode == 'age_norm':
        seen = [s for s in st if s is not None]
        if not seen:
            return [1.0] * len(uids)
        rate = sum(s['n'] for s in seen) / max(1, sum(now - s['first'] for s in seen))
        m = [None if s is None else s['n'] / max(1.0, (now - s['first']) * rate) for s in st]
        return [1e6 if x is None else math.exp(-(x - 1) / AGE_TAU) for x in m]
    if mode == 'loss_per':
        return [1e6 if s is None else (s['loss'] + 1e-3) ** PER_ALPHA for s in st]
    if mode == 'interference':
        import numpy as np
        rows = [r for r in STATE['rows'] if r[1] == generation]
        seq_u = np.array([r[2] for r in rows]); seq_s = np.array([r[0] for r in rows])
        nfr = max(1, int(seq_u.max()) + 1) if len(seq_u) else 1
        near_w, mid_w = max(1, int(NEAR * nfr)), max(2, int(MID * nfr))
        score = []
        for u, s_ in zip(uids, st):
            if s_ is None:
                score.append(None); continue
            after = seq_u[seq_s > s_['last_step']]
            dist = np.abs(after - u)
            score.append(float(np.log1p(((dist > near_w) & (dist <= mid_w)).sum()) - np.log1p((dist <= near_w).sum())))
    elif mode == 'forget_stale':
        score = [None if s is None else s['best'] - s['last'] for s in st]
    elif mode == 'progress_stale':
        score = [None if s is None else max(0.0, (s['last'] - s['prev']) if s['prev'] is not None else 1e3) for s in st]
    elif mode == 'loss_stale':
        score = [None if s is None else s['loss'] for s in st]
    else:
        raise ValueError(mode)
    seen = [i for i, x in enumerate(score) if x is not None]
    w = [0.0] * len(uids)
    if seen:
        order = sorted(seen, key=lambda i: -score[i])
        h = [0.0] * len(uids)
        for r, i in enumerate(order, 1):
            h[i] = (1.0 / r) ** (1.0 / TEMP)
        hs = sum(h)
        stale = [now - st[i]['last_step'] for i in seen]
        ss = sum(stale) or 1.0
        for k, i in enumerate(seen):
            w[i] = (1 - RHO) * h[i] / hs + RHO * stale[k] / ss
    return [1.0 if unseen[i] else w[i] + 1e-9 for i in range(len(uids))]


def install_sampler(mode, K=16):
    import group_k_patch as GK
    import unified_view_training as U
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    if hashlib.sha256(src.encode()).hexdigest() != GK.RESERVE_SHA256:
        raise RuntimeError('UnifiedTrainingSet.reserve changed')
    src = src.replace(GK.OLD, GK.NEW)
    stats = Counter()

    def group_draw(self, role, pool, used, scale, candidates, weights):
        q = self.__dict__.setdefault('_s_groups', {}).setdefault(role, deque())
        members = set(pool)
        for attempt in range(2):
            while q:
                u = q.popleft()
                if u in members and u not in used:
                    stats['draws', role] += 1
                    return u
                stats['skipped', role] += 1
            if attempt == 0:
                ordered = sorted(members)
                ws = signal_weights(mode, ordered, int(self.generation) if hasattr(self, 'generation') else
                                    int(STATE['trainer'].generation) if STATE['trainer'] else 0)
                keys = []
                for u, wt in zip(ordered, ws):
                    g = -math.log(-math.log(max(self.rng.random(), 1e-15)))
                    keys.append((math.log(max(wt, 1e-300)) + g, u))
                keys.sort(reverse=True)
                q.extend(u for _, u in keys[:min(K, len(keys))])
                stats['groups', role] += 1
        stats['fallback', role] += 1
        return self.rng.choices(candidates, weights=weights, k=1)[0]

    ns = dict(vars(U), _GROUP_DRAW=group_draw)
    exec(compile(src, f'<train_signal_sampler:{U.__file__}>', 'exec'), ns)
    patched = ns['reserve']

    def reserve(self, *a, **k):
        if self.selector != 'ervs':
            raise RuntimeError('signal sampler needs the ERVS selector path')
        return patched(self, *a, **k)
    U.UnifiedTrainingSet.reserve = reserve
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'signal_sampler.json').write_text(json.dumps(dict(
                mode=mode, K=K, rho=RHO, temp=TEMP, catch_beta=CATCH_BETA, catch_c=CATCH_C, age_tau=AGE_TAU,
                per_alpha=PER_ALPHA, near=NEAR, mid=MID,
                stats={f'{a}/{b}': n for (a, b), n in sorted(stats.items())}), indent=1))
    atexit.register(dump)


if __name__ == '__main__':
    patch = Path(os.environ['B_PATCH_WORKER'])
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    install_logger()
    mode = os.environ.get('B_SIGNAL_MODE')
    if mode:
        install_sampler(mode)
    sys.argv = [str(patch), *sys.argv[1:]]
    sys.path[0] = str(patch.parent)
    if mode:
        # The sampler already patched reserve; run the official worker directly (no second reserve patch).
        worker = Path(os.environ['B_SELECTED_WORKER'])
        sys.argv[0] = str(worker); sys.path[0] = str(worker.parent)
        runpy.run_path(str(worker), run_name='__main__')
    else:
        runpy.run_path(str(patch), run_name='__main__')
