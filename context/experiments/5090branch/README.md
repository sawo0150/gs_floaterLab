# 5090 server experiment snapshot

- captured: 2026-09-14 (Asia/Seoul)
- source host: `colin`
- source root: `/home/intern/gs_floaterLab/context/experiments`
- purpose: preserve the 5090-side exp66--exp78 work without merging older
  experiment files over the active local experiment tree

The directory layout below this file mirrors the source server. The server's
`context/STATUS.md` is preserved as `STATUS_5090_SNAPSHOT.md`; it is provenance,
not the active project `context/STATUS.md`.

Only source-like experiment material was copied: cards, scripts, configuration,
HTML reports, and compact JSON/CSV evidence. The 34 GB source experiment tree's
generated payloads remain on the server and were intentionally excluded:

- PLY, images, videos, checkpoints, NumPy/Pickle/TensorBoard artifacts
- `cameras.json`, `exposure.json`, render/train/test/point-cloud directories
- raw `*runs*` evidence directories and `*.log` files
- individual files larger than 5 MiB

The related 5090 VIGS work is preserved by Git commit
`c8e5df85c2f40618b55700541d715e2388290f07` (`Integrate causal XFeat online
carve bridge`). It is kept separately from the active VIGS `main` because that
commit tracks an empty `vigs/gaussian/utils/matcher_online.py` while importing
`OnlineMatcherCarve`; merging it unchanged would break VIGS startup.
