#!/usr/bin/env python3
"""Capture authoritative native setup before model construction or optimization.

Run in its own process: the legacy harness installs density hooks while parsing
its recipe. This file is setup provenance, never an online quality measurement.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import run_online_dense_training as trial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--scene', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import torch
    import exp78b_replay_gsslam_mapping as replay
    class SetupCaptured(Exception): pass
    def capture(config, save_dir, mapper_args, use_gui=False):
        torch.save({'config': config, 'args': vars(mapper_args)}, args.output/'native_setup.pt')
        (args.output/'native_setup.json').write_text(json.dumps(
            {'config':config,'args':vars(mapper_args)},indent=2,default=str))
        raise SetupCaptured()
    replay.GSBackEnd = capture
    command = trial.command(SimpleNamespace(arm='growth_ervs',dataset=args.dataset,
        scene=args.scene,seed=0,deadline_reserve_ms=100),args.output/'unused_mapping_output')
    sys.argv = command[1:]
    try:
        replay.main(clocked_time_scale=1.5,include_mapper_setup_in_clock=True)
    except SetupCaptured:
        files=[Path(__file__).resolve(),Path(replay.__file__).resolve(),Path(trial.__file__).resolve()]
        (args.output/'provenance.json').write_text(json.dumps({
            'command':command,'dataset':args.dataset,'scene':args.scene,
            'model_constructed':False,'optimizer_steps':0,
            'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'setup_sha256':hashlib.sha256((args.output/'native_setup.pt').read_bytes()).hexdigest()
        },indent=2))
        print('SETUP_CAPTURED',args.output,flush=True)
        return
    raise RuntimeError('Harness did not reach the expected constructor boundary')


if __name__ == '__main__': main()
