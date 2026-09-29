"""Verify removing window allocation preserves access and cumulative counts."""
from collections import Counter
import unittest
import test_unified_view_training as unified_tests
from run_selected_mapping import recipe_args


class WindowQuotaTests(unittest.TestCase):
    def test_no_window_keeps_recent_and_old_keyframes(self):
        p = unified_tests.UnifiedTests().make((0, 6, 6))
        seen = set()
        for _ in range(80):
            s = p.reserve(window=range(100, 200, 10))
            roles = p.selection_roles(s)
            self.assertEqual(Counter(roles), Counter(keyframe=6, dense=6))
            self.assertEqual(len(set(s.uids)), 12)
            seen.update(u for u, role in zip(s.uids, roles) if role == 'keyframe')
            p.commit(s)
        self.assertEqual(seen, set(range(0, 200, 10)))
        counts = Counter(u for s in p.service_ledger for u in s['uids'])
        self.assertEqual(p.counts, {u: counts[u] for u in p.training_uids})

    def test_reduced_window_preserves_kf_dense_mix(self):
        p = unified_tests.UnifiedTests().make((1, 5, 6))
        for _ in range(20):
            s = p.reserve(window=range(100, 200, 10))
            self.assertEqual(Counter(p.selection_roles(s)), Counter(window=1, keyframe=5, dense=6))
            p.commit(s)

    def test_adopted_flags_and_quota_override(self):
        a = recipe_args()
        self.assertEqual(a[a.index('--batch-quotas')+1:a.index('--batch-quotas')+4], ['3','3','6'])
        for flag,value in [('--birth-downsample-multiplier','0.8'),('--prune-opacity-threshold','0.1'),('--prune-every-renders','300')]:
            self.assertEqual(a[a.index(flag)+1], value)
        b = recipe_args((0,6,6))
        i = a.index('--batch-quotas')+1
        self.assertEqual(b[:i]+b[i+3:], a[:i]+a[i+3:])


if __name__ == '__main__':
    unittest.main()
