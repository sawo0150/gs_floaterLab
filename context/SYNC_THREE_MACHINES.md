# Three-machine synchronization (2026-09-19)

This extends [SYNC_5090.md](SYNC_5090.md). GitHub and the Colin bare hub share
the integrated `main`; publish topic branches before merging, never force-push.

| Machine | Working repository | Hub remote |
|---|---|---|
| wosasa laptop | `/home/wosasa/Desktop/Incremental_mapping/gs_floaterLab` | `colin-sync` = `chaehyun:/home/intern/git-sync/gs_floaterLab.git` |
| wosas 5070 Ti | `/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab` | `colin-sync` = `colin:/home/intern/git-sync/gs_floaterLab.git` |
| Colin 5090 | `/home/intern/gs_floaterLab` | `colin-sync` = `/home/intern/git-sync/gs_floaterLab.git` |

## What was preserved and merged

- Laptop snapshot: `268f6a7`, including the latest manuscript, HumanTeck LaTeX,
  presentation build scripts, versioned decks, and the final presentation video.
- 5070 Ti snapshot: `d14f168`, including the earlier manuscript, dense-supervision
  analysis, tables, manifests, and experiment history. Additional metric evidence:
  `4898842`.
- Colin snapshot: `5552be8`, including previously untracked experiment summaries
  and research provenance. Additional audit evidence: `ead1068`.
- Integration `6c57231` retains the latest laptop manuscript when older copies
  conflict. Both machines' experiment-history additions were retained. Subsequent
  commits add the remaining audit evidence and this synchronization record.

All `.tex`, `.bib`, `.cls`, `.sty` and manuscript figure sources are ordinary
version-controlled files. Earlier drafts remain recoverable from the snapshots.
The deletion of `paper/latex/SYNC.md` and `.sync-state` already present on the
machines was preserved; **this operation does not synchronize Overleaf**.

## What is deliberately not synchronized by Git

Datasets, checkpoints, PLY maps, rendered frame sequences, TensorBoard files,
raw logs, generated schedules, temporary worktrees, and downloaded paper PDFs
remain on their originating machines. They were not deleted. Lightweight
metrics, manifests, summaries, analysis code, and tables were selected for Git.
Some large or unclassified evidence JSON may remain untracked for later review.

`repos/main/3dgs-custom` is a tracked machine-specific symlink. Colin deliberately
marks it `skip-worktree` and uses a real local directory there. That directory
and other external training repositories are **not** merged by this lab sync.
Their source changes require a separate repository-specific review; do not
clear skip-worktree or replace the directory during a routine pull.

## Routine workflow

1. Check `git status --short` and commit selected source/doc/metric changes on a
   topic branch. Do not use an indiscriminate `git add .` over raw results.
2. `scripts/sync_5090.sh fetch lab` and inspect incoming changes.
3. For a clean new task: `scripts/sync_5090.sh new-work lab <unique-topic>`.
4. Share the work: `scripts/sync_5090.sh publish lab`.
5. Integrate reviewed topic branches on one machine, resolve conflicts by content,
   and validate before pushing `main` to the hub and GitHub.
6. On other machines, with tracked changes committed, fetch the hub and run
   `git merge --ff-only colin-sync/main`. If it fails, merge deliberately; do not
   reset or force-push. Check `git rev-parse HEAD` against the hub afterward.

GitHub publication is separate from the hub and must be explicitly authorized,
as it was for this synchronization. Machine-local files are not evidence of a
failed Git sync; compare committed trees and inspect dirty tracked files first.
