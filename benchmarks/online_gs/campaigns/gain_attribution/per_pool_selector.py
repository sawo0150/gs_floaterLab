"""Per-pool sampler for the adopted B mapper (runtime patch; locked sources untouched).

B's `--selector` applies one sampler to both the keyframe pool and the dense pool. This patch lets RR apply to
only the roles listed in `B_RR_ROLES` (comma separated: keyframe, dense) while the other pool keeps ERVS.

It copies `UnifiedTrainingSet.reserve` from the locked source (sha256 checked) and changes one condition:
`elif rr is not None:` -> `elif rr is not None and role in _RR_ROLES:`. Run the worker with `--selector rr` so the
RR epoch bookkeeping is active; ERVS-role draws then use the unchanged Gibbs branch. Draws per (method, role) are
counted and written to `<output>/per_pool_selector.json` at exit.
"""
import atexit
from collections import Counter
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import textwrap

RESERVE_SHA256 = '93be917d5783296d8328f32af887e13b8c6365199b853b7d1b27301821d709b2'
ANCHORS = {
    "elif rr is not None:": "elif rr is not None and role in _RR_ROLES:",
    "uid = next(u for u in state['remaining'] if u not in used)":
        "uid = next(u for u in state['remaining'] if u not in used); _DRAWS['rr', role] += 1",
    "uid = self.rng.choices(candidates, weights=weights, k=1)[0]":
        "uid = self.rng.choices(candidates, weights=weights, k=1)[0]; _DRAWS['ervs', role] += 1",
}


def install():
    roles = tuple(r for r in os.environ.get('B_RR_ROLES', '').split(',') if r)
    assert roles and set(roles) <= {'keyframe', 'dense'}, roles
    import unified_view_training as U
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    digest = hashlib.sha256(src.encode()).hexdigest()
    if digest != RESERVE_SHA256:
        raise RuntimeError(f'UnifiedTrainingSet.reserve changed: {digest}')
    for old, new in ANCHORS.items():
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    draws = Counter()
    namespace = dict(vars(U), _RR_ROLES=roles, _DRAWS=draws)
    exec(compile(src, f'<per_pool_selector:{U.__file__}>', 'exec'), namespace)
    patched = namespace['reserve']

    def reserve(self, *args, **kwargs):
        if self.selector != 'rr':
            raise RuntimeError('per-pool sampler requires --selector rr (RR bookkeeping)')
        return patched(self, *args, **kwargs)
    U.UnifiedTrainingSet.reserve = reserve
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'per_pool_selector.json').write_text(json.dumps(dict(
                rr_roles=roles, reserve_sha256=digest,
                draws={f'{m}/{r}': n for (m, r), n in sorted(draws.items())}), indent=2) + '\n')
    atexit.register(dump)
    return roles


if __name__ == '__main__':
    # Worker entry: install, then hand over to the official B worker with the same argv.
    import runpy
    install()
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
