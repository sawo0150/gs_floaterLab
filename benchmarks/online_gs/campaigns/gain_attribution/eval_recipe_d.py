#!/usr/bin/env python3
"""Evaluation-only pass for recipe C/D runs (no training): the launcher's own evaluate_run.py + audit commands with
its C environment. usage: python eval_recipe_d.py --scene-contract <...> --run <run dir>"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

LAUNCHER = Path('/home/intern/VIGS-SLAM-custom/scripts/selected_mapping/run_c_large_pool_v2.py')


def main():
    sc = Path(sys.argv[sys.argv.index('--scene-contract') + 1]); run = Path(sys.argv[sys.argv.index('--run') + 1]).resolve()
    spec = importlib.util.spec_from_file_location('run_c_large_pool_v2', Path(os.fspath(LAUNCHER)))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    python, cwd, env = mod.c_environment()
    E = mod.EQUAL
    subprocess.run([python, str(E / 'evaluate_run.py'), '--scene-contract', str(sc), '--run', str(run),
                    '--config', str(run / 'native_sensor_config.yaml'), '--output', str(run / 'evaluation')], cwd=cwd, env=env, check=True)
    subprocess.run([python, str(E / 'audit_custom_c_large_pool_6n.py'), '--scene-contract', str(sc), '--run', str(run),
                    '--evaluation', str(run / 'evaluation'), '--output', str(run / 'audit.json')], cwd=cwd, env=env, check=True)


if __name__ == '__main__':
    main()
