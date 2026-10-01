# RTX 5070 Ti path profile

The optional `sitecustomize.py` maps Colin absolute paths to local files in the
current Python process and its Python children. It leaves source-lock hashes,
frozen archives, setup tensors, losses, sampling and render budgets unchanged.
Do not use it for a wall-time comparison: the handoff defers those measurements.

Create an untracked JSON file with `path_prefixes` mapping old absolute prefixes
to their local counterparts. More specific prefixes take priority. Activate:

```bash
export ROGO_MACHINE_PROFILE="$PWD/results/local_machine_profiles/rtx5070ti.json"
export PYTHONPATH="$PWD/benchmarks/online_gs/campaigns/gain_attribution/rtx5070ti_profile${PYTHONPATH:+:$PYTHONPATH}"
/home/wosas/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_cvpr_measurements.py --help
```

This is a Python path adapter, not a filesystem mount. Native code must receive
already translated paths; shell strings are not rewritten. Verify every source
and extension hash with the existing `selected_mapping_check.verify_files` before
training. Record the profile and adapter hashes with each experiment. Existing
local RGB can be reused only after a recursive checksum comparison against Colin.

Keep outputs in a new namespace. Never redirect writes into the archived Colin
reference runs, and do not mark an interrupted run complete.
