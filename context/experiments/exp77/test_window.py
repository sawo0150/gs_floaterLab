import sys
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".codex-work/3dgs-custom-main"))
from runtime.window_ercb import WindowERCB
from runtime.scheduler import CausalRandomReshuffling

for seed in range(8):
    a, b = WindowERCB(seed, 0), CausalRandomReshuffling(seed)
    for t in range(1000):
        if t % 17 == 0:
            a.add(range(t,t+7)); b.add(range(t,t+7))
        assert a.draw() == b.draw()
    for n in (1,7,32,33,101):
        a=WindowERCB(seed);a.add(range(n))
        for epoch in range(3):
            assert Counter(a.draw() for _ in range(n)) == Counter(range(n))
    a=WindowERCB(seed)
    for t in range(1000):
        if t%17 == 0:a.add(range(t,t+7))
        assert a.draw() in a.active
    assert sum(a.counts.values()) == 1000
print('PASS: 8 seeds gamma0 exact RR, static epoch coverage, dynamic causality/count')
