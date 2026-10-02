"""Uniform sampling WITH replacement (K=1) for the adopted B mapper (runtime patch; locked sources untouched).

B draws a 12-image batch per selection; within a batch the keyframe-pool and dense-pool draws exclude views already
chosen (K-group without replacement). With `B_WITH_REPLACEMENT=1` this patch removes that exclusion for the keyframe
and dense pools, so each draw is independent (K=1). Run with `--tau 1e12` so the Gibbs weights are uniform. The window
role is unchanged. Commits stay one image per Adam step (optimizer batch size 1), so the locked per-chunk
distinct-view check is unaffected.

The patch copies the locked `UnifiedTrainingSet.reserve` (sha256 checked) and changes one line; it counts draws whose
view was already selected earlier in the same batch and writes `<output>/sampling_mode.json` at exit.
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
OLD = "            candidates = [u for u in pools[role] if u not in used]"
NEW = ("            candidates = (list(pools[role]) if role in ('keyframe', 'dense')\n"
       "                          else [u for u in pools[role] if u not in used])")
STAT = "            used.add(uid); selected.append(uid)"
STAT_NEW = "            _STATS['repeat_in_batch', role] += int(uid in used); _STATS['draws', role] += 1; " + STAT.strip()
# Audit record: with repeats, an image's count before its own service includes earlier occurrences in the batch.
CB = "'counts_before': tuple(self.counts[u] for u in selected),"
CB_NEW = "'counts_before': tuple(self.counts[u] + selected[:i].count(u) for i, u in enumerate(selected)),"


def install():
    import unified_view_training as U
    src = textwrap.dedent(inspect.getsource(U.UnifiedTrainingSet.reserve))
    digest = hashlib.sha256(src.encode()).hexdigest()
    if digest != RESERVE_SHA256:
        raise RuntimeError(f'UnifiedTrainingSet.reserve changed: {digest}')
    for old, new in ((OLD, NEW), (STAT, STAT_NEW), (CB, CB_NEW)):
        assert src.count(old.strip()) == 1, old
        src = src.replace(old.strip(), new.strip())
    stats = Counter()
    namespace = dict(vars(U), _STATS=stats)
    exec(compile(src, f'<sampling_mode_patch:{U.__file__}>', 'exec'), namespace)
    patched = namespace['reserve']

    def reserve(self, *args, **kwargs):
        if self.selector != 'ervs' or self.tau < 1e11:
            raise RuntimeError('with-replacement uniform requires --selector ervs and --tau >= 1e11')
        return patched(self, *args, **kwargs)
    U.UnifiedTrainingSet.reserve = reserve
    output = Path(sys.argv[sys.argv.index('--output') + 1]) if '--output' in sys.argv else None

    def dump():
        if output and output.exists():
            (output / 'sampling_mode.json').write_text(json.dumps(dict(
                mode='uniform_with_replacement', reserve_sha256=digest,
                stats={f'{k}/{r}': n for (k, r), n in sorted(stats.items())}), indent=2) + '\n')
    atexit.register(dump)


if __name__ == '__main__':
    import runpy
    worker = Path(os.environ['B_SELECTED_WORKER'])
    sys.path[0] = str(worker.parent)          # keep the official selected_mapping modules first
    if os.environ.get('B_WITH_REPLACEMENT') == '1':
        install()
    sys.argv = [str(worker), *sys.argv[1:]]
    runpy.run_path(str(worker), run_name='__main__')
