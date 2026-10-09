#!/usr/bin/env python3
"""Run colin's C launcher (run_c_large_pool_v2.py, from the local C snapshot) as C or as recipe D.

  python run_recipe_d.py --recipe C|D --scene-contract <...> --output <new dir> [--seed 0] [--evaluate]
Recipe D only rewrites the one training subprocess (run_custom_c_large_pool_6n.py) to go through d_recipe_shim.py
with B_SCALE_CAP=0.5 and B_COVERED_OPACITY=0.02; preflight, evaluation and audit run unchanged. Needs the
rtx5070ti_c_snapshot profile (ROGO_MACHINE_PROFILE) and the relocation hook on PYTHONPATH.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LAUNCHER = Path('/home/intern/VIGS-SLAM-custom/scripts/selected_mapping/run_c_large_pool_v2.py')   # relocated by profile


def main():
    recipe = sys.argv[sys.argv.index('--recipe') + 1]
    assert recipe in ('C', 'D'), recipe
    rest = [a for i, a in enumerate(sys.argv[1:]) if a != '--recipe' and sys.argv[i] != '--recipe']
    spec = importlib.util.spec_from_file_location('run_c_large_pool_v2', Path(os.fspath(LAUNCHER)))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if recipe == 'D':
        run = mod.subprocess.run

        def routed(cmd, *a, **k):
            if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[1]).endswith('run_custom_c_large_pool_6n.py'):
                cmd = [cmd[0], str(HERE / 'd_recipe_shim.py'), *cmd[1:]]
                env = dict(k.get('env') or os.environ); env.update(B_SCALE_CAP='0.5', B_COVERED_OPACITY='0.02'); k['env'] = env
            return run(cmd, *a, **k)
        mod.subprocess = type('S', (), {'run': staticmethod(routed), 'PIPE': subprocess.PIPE})
    sys.argv = [str(LAUNCHER), *rest]
    mod.main()


if __name__ == '__main__':
    main()
