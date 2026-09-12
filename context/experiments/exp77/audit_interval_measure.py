"""CPU diagnostic of interval top-k exclusion; not a quality experiment."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".codex-work/3dgs-custom-main"))
from runtime.scheduler import SizeAwareIntervalSoftmaxRandomReshuffling

def main():
    result = []
    # With exactly K intervals, every block must allocate one draw per interval,
    # regardless of interval size. This counterexample is exact, not asymptotic.
    for sizes in ([1]*7+[32], [8]*8):
        s = SizeAwareIntervalSoftmaxRandomReshuffling(0, 0, 8)
        offset = 0
        for size in sizes:
            s.add(range(offset, offset+size)); offset += size
        for _ in range(8000):
            s.draw()
        result.append({"sizes": sizes, "target_frame_uniform": [n/sum(sizes) for n in sizes],
            "actual_interval_share": [s.interval_counts[i]/8000 for i in range(len(sizes))]})
    print(json.dumps({"diagnostic": "top-k without replacement does not preserve base mass",
                      "examples": result}, indent=2))

if __name__ == "__main__":
    main()
