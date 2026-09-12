"""Run legacy train.py with exp77 instrumentation; no dataset generation."""
import argparse
import hashlib
import json
import runpy
import sys
import time
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--arm", choices=("rr", "ercb", "packet", "interval_base", "coverage1", "coverage2", "window", "window_control"), required=True)
    parser.add_argument("--packet-size", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=2)
    args, training_args = parser.parse_known_args()
    if training_args and training_args[0] == "--":
        training_args.pop(0)
    if "--start_checkpoint" in training_args:
        parser.error("Checkpoint branching needs separate history/provenance handling; not enabled in this runner")
    model_flag = "-m" if "-m" in training_args else "--model_path"
    output = Path(training_args[training_args.index(model_flag) + 1])
    if output.exists():
        parser.error(f"Refusing to overwrite existing run: {output}")
    if subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True).strip():
        parser.error("GPU compute process active; wait, do not kill it")
    sys.path.insert(0, str(args.repo.resolve()))
    import runtime.scheduler as scheduling
    from runtime.packet_scheduler import PacketIntervalRandomReshuffling
    import utils.general_utils as general

    factory, summarize, seed_state = scheduling.make_scheduler, scheduling.scheduler_summary, general.safe_state
    audit = {"arm": args.arm, "scheduler_cpu_ns": 0, "first_selected_iteration": {}}
    outer_hash = hashlib.sha256()
    draws = 0
    run_seed = int(training_args[training_args.index("--scheduler_seed") + 1])

    def seeded_state(silent):
        seed_state(silent)
        import random
        import numpy as np
        import torch
        random.seed(run_seed); np.random.seed(run_seed); torch.manual_seed(run_seed)
        torch.cuda.manual_seed_all(run_seed)
    general.safe_state = seeded_state

    def make(name, seed=0, beta=1.0, block_size=128, phase_start=0, loss_alpha=.5):
        nonlocal draws
        expected = "causal_rr" if args.arm == "rr" else "relative_floor_interval_softmax_rr"
        if name != expected:
            raise ValueError(f"arm {args.arm} requires {expected}, got {name}")
        sampler = (PacketIntervalRandomReshuffling(seed, beta, block_size, args.packet_size, args.repeats)
                   if args.arm == "packet" else factory(name, seed, beta, block_size, phase_start, loss_alpha))
        if args.arm == "interval_base":
            sampler = scheduling.SizeAwareIntervalSoftmaxRandomReshuffling(seed, 0.0, block_size)
        elif args.arm in ("coverage1", "coverage2"):
            sampler = scheduling.TwoPassSizeAwareIntervalSoftmaxRandomReshuffling(seed, beta, block_size)
            sampler.coverage_quota = 1.0 if args.arm == "coverage1" else 2.0
        elif args.arm in ("window", "window_control"):
            from runtime.window_ercb import WindowERCB
            sampler = WindowERCB(seed, beta if args.arm == "window" else 0, 32, force_reorder=True)
        original_draw = sampler.draw
        def draw():
            nonlocal draws
            start = time.perf_counter_ns()
            item = original_draw()
            audit["scheduler_cpu_ns"] += time.perf_counter_ns() - start
            draws += 1
            audit["first_selected_iteration"].setdefault(item, draws)
            if hasattr(sampler, "frame_to_interval"):
                outer_hash.update(f"{sampler.frame_to_interval[item]},".encode())
            return item
        sampler.draw = draw
        return sampler

    def summary(sampler, names, arrivals, total):
        result = summarize(sampler, names, arrivals, total)
        first = audit["first_selected_iteration"]
        result.update({"exp77_arm": args.arm, "scheduler_cpu_ns": audit["scheduler_cpu_ns"],
                       "outer_trace_sha256": outer_hash.hexdigest() if args.arm != "rr" else None,
                       "unique_selected": len(first), "zero_service": len(names) - len(first),
                       "first_service_delay_updates": {names[i]: step - arrivals[i] for i, step in first.items()},
                       "packet_size": args.packet_size if args.arm == "packet" else None,
                       "packet_repeats": args.repeats if args.arm == "packet" else None})
        return result
    scheduling.make_scheduler, scheduling.scheduler_summary = make, summary
    sys.argv = [str(args.repo / "train.py"), *training_args]
    started = time.perf_counter()
    try:
        runpy.run_path(str(args.repo / "train.py"), run_name="__main__")
    finally:
        if output.is_dir():
            (output / "exp77_execution.json").write_text(json.dumps({
                "arm": args.arm, "training_entry_wall_seconds": time.perf_counter() - started,
                "includes_loading_and_evaluation": True,
                "repo_head": subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip(),
                "train_py_sha256": hashlib.sha256((args.repo / "train.py").read_bytes()).hexdigest(),
                "packet_py_sha256": hashlib.sha256((args.repo / "runtime/packet_scheduler.py").read_bytes()).hexdigest(),
                "argv": training_args}, indent=2) + "\n")


if __name__ == "__main__":
    main()
