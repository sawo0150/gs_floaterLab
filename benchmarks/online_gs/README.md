# Online GS-SLAM benchmark preparation

The current authorized preparation scope is cleanup plus **RPNG AR Table and
UTMM ETH-preprocessed data** in this workspace. Repository cloning and method
environment installation are deferred until separately discussed.

## Layout

- `data/benchmarks/{rpng,utmm}/raw/`: retained downloaded ZIP and resume metadata.
- `data/benchmarks/{rpng,utmm}/prepared/`: CRC-checked extracted dataset.
- `data/benchmarks/manifests/`: URLs, source identity, exact sizes, SHA256,
  extraction status and progress. These large-data-adjacent files are local.
- `results/benchmarks/`: future run artifacts. No run has been executed.
- This directory: small preparation code and protocol documentation.

`prepare_datasets.py` uses the already-available Python `requests` package. It
installs no dependencies and clones no code. It downloads each archive with
four HTTP range workers, resumes via `.resume.json`, computes a local SHA256,
and checks ZIP member CRCs during extraction. A locally computed SHA256 is
not a publisher-provided checksum. A finished download is not evidence that
SLAM or its evaluator works.

```bash
python benchmarks/online_gs/prepare_datasets.py
```

Do not run multiple copies simultaneously. `.part` files may be sparse after
range downloads begin, so file length is not download progress; use the
`*_progress.json` files. Preserve `.resume.json` alongside `.part` for resume.

Downloaded archives are retained to allow verification and reproducible
re-extraction. New maps/renders/checkpoints belong under `results/benchmarks`,
not `context/experiments`. Common evaluation split, method revisions and
environment locks must be agreed before running the paper benchmark.

See [preflight](../../context/research/online_gs_slam_benchmark_preflight_20260910.md)
and [cleanup audit](../../context/research/intern_cleanup_applied_20260910/README.md).
