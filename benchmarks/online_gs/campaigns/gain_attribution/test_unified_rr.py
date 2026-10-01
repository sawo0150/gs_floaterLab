"""RR epoch coverage and transactional progress in unified packets."""
import copy
import sys
import unittest
sys.path.insert(0, '/home/intern/VIGS-SLAM-online-worker-integration/vigs')
from unified_view_training import UnifiedTrainingSet

class RRTests(unittest.TestCase):
    def make(self, quotas=(0,0,3)):
        p=UnifiedTrainingSet(membership='immediate', selector='rr', batch_quotas=quotas, seed=0)
        p.register_keyframes([0,10])
        for u in range(1,8):p.offer(u,0,10,available_through=10)
        return p

    def test_static_epochs_cover_pool_once(self):
        p=self.make(); sequence=[]
        for _ in range(28):
            s=p.reserve(1); sequence.extend(s.uids); p.commit(s)
        for i in range(0,28,7):self.assertEqual(set(sequence[i:i+7]),set(range(1,8)))

    def test_newcomer_joins_current_epoch(self):
        p=self.make();s=p.reserve(1);done=s.uids[0];p.commit(s)
        p.offer(8,0,10,available_through=10)
        rest=[]
        for _ in range(7):s=p.reserve(1);rest.extend(s.uids);p.commit(s)
        self.assertEqual(set(rest),set(range(1,9))-{done})

    def test_cancel_and_partial_commit_do_not_consume_failed_services(self):
        p=self.make();before=copy.deepcopy(p._rr_pools)
        s=p.reserve();p.cancel(s);self.assertEqual(before,p._rr_pools)
        s=p.reserve();uid=s.uids[0];rest=p.commit_prefix(s,1)
        committed=copy.deepcopy(p._rr_pools);p.cancel(rest)
        self.assertEqual(committed,p._rr_pools)
        self.assertEqual(p._rr_pools['dense']['seen'],{uid})
        self.assertEqual(p.rgb_view_services,1)

    def test_window_counts_toward_kf_epoch(self):
        p=self.make((1,1,0));p.register_keyframes([20,30])
        s=p.reserve(window=[30]);p.commit(s)
        self.assertIn(30,p._rr_pools['keyframe']['seen'])
        self.assertNotIn(30,p._rr_pools['keyframe']['remaining'])

    def test_small_pools_rollover_disjointness_and_promotion(self):
        p=self.make((3,3,6))
        for i in range(80):
            if i==20:p.register_keyframes([4])
            s=p.reserve(window=[0,10]);self.assertEqual(len(s.uids),len(set(s.uids)))
            self.assertEqual(len(s.uids),9)
            while s is not None:s=p.commit_prefix(s,1)
        self.assertNotIn(4,p._rr_pools['dense']['remaining'])
        self.assertEqual(sum(p.counts.values()),720)

    def test_shared_kf_control_pools_consume_all_matching_epochs(self):
        for mode in ('kf_native','kf_rgb'):
            p=UnifiedTrainingSet(membership='immediate',selector='rr',auxiliary_mode=mode)
            p.register_keyframes(range(20))
            for _ in range(200):
                s=p.reserve(window=range(12,20))
                self.assertEqual(len(s.uids),12)
                self.assertEqual(len(set(s.uids)),12)
                p.commit(s)

if __name__=='__main__':unittest.main()
