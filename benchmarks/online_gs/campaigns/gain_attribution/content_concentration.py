"""Per-scene image-content concentration (no GPU): how unevenly Sobel gradient energy is spread over the image.

For ~40 evenly spaced training frames (resized to 640 px wide, grayscale) the Sobel magnitude map is computed and summarised:
  gini      Gini coefficient of per-pixel gradient magnitude (0 = even, 1 = all energy in one pixel);
  top50     fraction of pixels holding 50 % of the gradient energy (small = concentrated);
  flat      fraction of pixels whose magnitude is below 10 % of the frame's 95th percentile (flat area share).
Image paths come from the archive arrivals and are relocated with the machine profile prefix map.
"""
import json, os, sys
from pathlib import Path
import cv2, numpy as np

PROFILE = json.loads(Path(os.environ['ROGO_MACHINE_PROFILE']).read_text())
MAP = sorted(((k, v) for k, v in (PROFILE.get('path_prefixes') or PROFILE).items() if isinstance(v, str) and k.startswith('/')),
             key=lambda kv: -len(kv[0]))


def relocate(p):
    for k, v in MAP:
        if p == k or p.startswith(k.rstrip('/') + '/'):
            return v + p[len(k):]
    return p


def measure(contract):
    c = json.loads(Path(contract).read_text())
    arch = Path(relocate(c['archive']))
    train = set(c['training_uids'])
    rows = [json.loads(l) for l in (arch / 'arrivals.jsonl').read_text().splitlines() if l.strip()]
    rows = [r for r in rows if int(r['frame_uid']) in train]
    pick = rows[:: max(1, len(rows) // 40)][:40]
    g, t, f = [], [], []
    for r in pick:
        img = cv2.imread(relocate(r['rgb']), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img = cv2.resize(img, (640, int(round(img.shape[0] * 640 / img.shape[1]))), interpolation=cv2.INTER_AREA).astype(np.float32)
        m = np.hypot(cv2.Sobel(img, cv2.CV_32F, 1, 0), cv2.Sobel(img, cv2.CV_32F, 0, 1)).ravel()
        s = np.sort(m); n = len(s); cum = np.cumsum(s)
        g.append(float((n + 1 - 2 * (cum / cum[-1]).sum()) / n))
        t.append(float((np.searchsorted(np.cumsum(s[::-1]), 0.5 * cum[-1]) + 1) / n))
        f.append(float((m < 0.1 * np.percentile(m, 95)).mean()))
    return dict(frames=len(g), gini=float(np.mean(g)), top50=float(np.mean(t)), flat=float(np.mean(f)))


if __name__ == '__main__':
    out = {}
    for name, contract in (a.split('=', 1) for a in sys.argv[2:]):
        out[name] = measure(contract)
        print(name, {k: round(v, 3) for k, v in out[name].items()}, flush=True)
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + '\n')
