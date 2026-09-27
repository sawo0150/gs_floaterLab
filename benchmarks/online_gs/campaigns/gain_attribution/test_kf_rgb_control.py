"""Control contracts: same KF sequence, different actual loss route."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, '/home/intern/VIGS-SLAM-online-worker-integration/vigs')
from unified_view_training import UnifiedTrainingSet
from online_photometric import OnlinePhotometricTrainer
import torch

class ControlTests(unittest.TestCase):
    def make(self, mode):
        p=UnifiedTrainingSet(membership='immediate', selector='ervs', auxiliary_mode=mode,
            entropy_weight_policy='per_view', tau=1., seed=0)
        return p

    def test_identical_kf_selection_counts_and_lr_including_small_pools(self):
        a,b=self.make('kf_rgb'),self.make('kf_native')
        for last in range(0,200,10):
            for p in (a,b):
                p.register_keyframes([last])
                if last:p.offer(last-5,last-10,last,available_through=last)
            for size in (12,12,12,4):
                sa=a.reserve(size,window=range(max(0,last-30),last+1,10))
                sb=b.reserve(size,window=range(max(0,last-30),last+1,10))
                self.assertEqual(sa.uids,sb.uids)
                self.assertEqual(len(sa.uids),len(set(sa.uids)))
                self.assertTrue(set(sa.uids)<=a.keyframes)
                self.assertEqual(a._pending_batch['lr_render_position'],b._pending_batch['lr_render_position'])
                self.assertEqual(a._pending_batch['actual_quotas'],b._pending_batch['actual_quotas'])
                while sa is not None:
                    sa=a.commit_prefix(sa,1);sb=b.commit_prefix(sb,1)
                self.assertEqual(a.counts,b.counts)
        self.assertGreater(a.counts[0],0)
        self.assertTrue(all(a.counts[u]==0 for u in a.admitted))

    def test_real_loss_dispatch_rgb_kf_matches_dense_and_excludes_geometry(self):
        mapper=SimpleNamespace(opt_params=SimpleNamespace(lambda_dssim=.2),
            _frontier_mapping_view_loss=Mock(return_value=torch.tensor(42.)))
        t=OnlinePhotometricTrainer(mapper,heldout=(),membership='immediate',selector='ervs',
            seed=0,guard=None,schedule='unified',auxiliary_mode='kf_rgb')
        t.policy.register_keyframes([10])
        target=torch.zeros(3,16,16)
        kf=SimpleNamespace(uid=10,depth=torch.ones(16,16),original_image_gpu=target)
        dense=SimpleNamespace(uid=5,depth=None,original_image_gpu=target)
        image=torch.full_like(target,.5,requires_grad=True)
        depth=torch.ones(16,16,requires_grad=True)
        rendered={'render':image,'depth':depth}
        a=t.refinement_loss(kf,rendered,role='keyframe_rgb')
        b=t.refinement_loss(dense,rendered,role='dense')
        self.assertTrue(torch.equal(a,b));a.backward()
        self.assertIsNotNone(image.grad);self.assertIsNone(depth.grad)
        mapper._frontier_mapping_view_loss.assert_not_called()
        for role in ('window','keyframe','keyframe_native'):
            t.refinement_loss(kf,rendered,role=role)
        self.assertEqual(mapper._frontier_mapping_view_loss.call_count,3)
        self.assertEqual([r['loss'] for r in t.loss_routes],['rgb_only']*2+['native_rgbd_normal']*3)

    def test_reset_preserves_mode(self):
        t=OnlinePhotometricTrainer(None,heldout=(),membership='immediate',selector='ervs',
            seed=0,guard=None,schedule='unified',auxiliary_mode='kf_rgb')
        t.policy.register_keyframes([0,10]);s=t.policy.reserve(window=[10]);t.policy.commit(s)
        t.reset();self.assertEqual(t.policy.auxiliary_mode,'kf_rgb')
        self.assertEqual(t.policy.generation,1);self.assertEqual(t.policy.counts,{})

if __name__=='__main__':unittest.main()
