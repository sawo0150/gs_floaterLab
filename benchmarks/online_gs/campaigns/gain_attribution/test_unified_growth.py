"""Completed-update growth inside unified packets, not raw arrivals."""
import copy
import sys
import unittest
sys.path.insert(0,'/home/intern/VIGS-SLAM-online-worker-integration/vigs')
from unified_view_training import UnifiedTrainingSet
from test_paired_cumulative_counts import audit

class GrowthTests(unittest.TestCase):
    def make(self):
        p=UnifiedTrainingSet(membership='growth',selector='ervs',growth_budget_scope='dense_only',
            kappa=4,tau=1.,entropy_weight_policy='per_view')
        p.register_keyframes([0,100])
        for u in range(1,100):p.offer(u,0,100,available_through=100)
        return p
    def test_only_completed_steps_earn_admissions_and_kfs_ungated(self):
        p=self.make();self.assertEqual(p.keyframes,{0,100});self.assertFalse(p.admitted)
        for i in range(24):
            s=p.reserve(1,window=[100]);p.cancel(s)
            self.assertEqual(len(p.admitted),i//4)
            s=p.reserve(1,window=[100]);p.commit(s)
            self.assertEqual(len(p.admitted),(i+1)//4)
        self.assertEqual([a['rgb_steps'] for a in p.admission_ledger],[4,8,12,16,20,24])
    def test_reserved_batch_admission_keeps_successful_prefix_and_does_not_spend_on_cancel(self):
        p=self.make()
        for _ in range(7):s=p.reserve(1,window=[100]);p.commit(s)
        before=set(p.admitted);s=p.reserve(window=[100]);rest=p.commit_prefix(s,1)
        self.assertEqual(len(p.admitted),2);self.assertTrue(before<=p.admitted)
        p.cancel(rest);self.assertEqual(p.rgb_steps_completed,8)
        report={'schedule':'unified','photometric_steps':8,'generations':[{'policy':p.snapshot(),'services':p.service_ledger,'admissions':p.admission_ledger}]}
        self.assertTrue(all(audit(report,8).values()))
        broken=copy.deepcopy(report);broken['generations'][0]['admissions'][0]['rgb_steps']=3
        self.assertFalse(audit(broken,8)['growth_capacity'])
    def test_pool_entropy_weight_tracks_actual_separate_pools(self):
        p=self.make()
        for _ in range(12):s=p.reserve(1,window=[100]);p.commit(s)
        self.assertEqual(p.snapshot()['sampler_pool_tau'],{'keyframe':.5,'dense':1/3})

if __name__=='__main__':unittest.main()
