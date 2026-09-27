"""CPU contracts for unified batches and their independent service audit."""
from collections import Counter
import ast
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, '/home/intern/VIGS-SLAM-online-worker-integration/vigs')
from unified_view_training import UnifiedTrainingSet
from test_paired_cumulative_counts import audit


class UnifiedTests(unittest.TestCase):
    def make(self, quotas=(4,4,4)):
        p=UnifiedTrainingSet(membership='immediate',selector='ervs',selection_count_scope='all_rgb',
            entropy_weight_policy='per_view',growth_budget_scope='whole_pool',tau=1.,batch_quotas=quotas)
        p.register_keyframes(range(0,200,10))
        for u in range(1,190):
            if u%10: p.offer(u,u//10*10,u//10*10+10,available_through=190)
        return p

    def test_quota_disjointness_and_full_pool(self):
        p=self.make(); seen=set()
        for _ in range(100):
            s=p.reserve(window=range(100,200,10));p.commit(s)
            row=p.service_ledger[-1]
            self.assertEqual(row['actual_quotas'],(4,4,4));self.assertEqual(len(set(s.uids)),12)
            self.assertTrue(all(u>=100 for u,r in zip(s.uids,row['roles']) if r=='window'))
            seen.update(u for u,r in zip(s.uids,row['roles']) if r=='keyframe')
        self.assertTrue(any(u<100 for u in seen))
        expected=Counter(u for s in p.service_ledger for u in s['uids'])
        self.assertEqual(p.counts,{u:expected[u] for u in p.training_uids})

    def test_ervs_counts_include_window_and_cancellation_earns_nothing(self):
        p=self.make((1,1,1));before=dict(p.counts)
        s=p.reserve(window=(190,));p.cancel(s)
        self.assertEqual(p.counts,before);self.assertEqual(p.rgb_steps_completed,0)
        for _ in range(40):
            s=p.reserve(window=(190,));p.commit(s)
        self.assertEqual(p.counts[190],40)
        self.assertEqual(p.photometric_counts[190],40)
        self.assertGreater(p.counts[190],p.counts[0])

    def test_short_packets_rotate_equal_remainders(self):
        p=self.make();totals=Counter()
        for _ in range(3):
            s=p.reserve(4,window=range(100,200,10));p.commit(s)
            totals.update(p.service_ledger[-1]['roles'])
        self.assertEqual(totals,{'window':4,'keyframe':4,'dense':4})

    def test_bootstrap_and_shortage_never_duplicate(self):
        p=UnifiedTrainingSet(membership='immediate',selector='ervs')
        self.assertIsNone(p.reserve(window=()))
        p.register_keyframes([0]);s=p.reserve(window=[0]);self.assertEqual(s.uids,(0,));p.commit(s)
        p.register_keyframes([10]);s=p.reserve(window=[10]);self.assertEqual(len(s.uids),2);p.commit(s)
        p.offer(5,0,10,available_through=10);s=p.reserve(window=[10]);self.assertEqual(set(s.uids),{0,5,10});p.commit(s)

    def test_promotion_and_generation_reset(self):
        p=self.make();s=p.reserve(window=range(100,200,10));p.commit(s)
        uid=next(u for u,r in zip(s.uids,p.service_ledger[-1]['roles']) if r=='dense')
        count=p.counts[uid];p.register_keyframes([uid]);self.assertEqual(p.counts[uid],count)
        self.assertNotIn(uid,p.admitted)
        with self.assertRaises(RuntimeError):p.commit_native([uid])
        fresh=self.make();self.assertTrue(all(n==0 for n in fresh.counts.values()))

    def test_independent_audit_detects_count_and_role_corruption(self):
        p=self.make()
        for _ in range(3):s=p.reserve(window=range(100,200,10));p.commit(s)
        r={'schedule':'unified','photometric_steps':3,
           'generations':[{'policy':p.snapshot(),'services':p.service_ledger,'admissions':p.admission_ledger}]}
        self.assertTrue(all(audit(r,3).values()))
        bad=copy.deepcopy(r);bad['generations'][0]['services'][0]['counts_before']=(999,)*12
        self.assertFalse(audit(bad,3)['unified_cumulative_before_draw'])
        bad=copy.deepcopy(r);bad['generations'][0]['services'][0]['window_uids']=()
        self.assertFalse(audit(bad,3)['unified_window_membership'])

    def test_partial_commit_preserves_success_and_cancels_only_remainder(self):
        p=self.make();s=p.reserve(window=range(100,200,10))
        rest=p.commit_prefix(s,2)
        self.assertEqual(p.rgb_view_services,2);self.assertEqual(p.rgb_steps_completed,1)
        self.assertTrue(all(p.counts[u]==1 for u in s.uids[:2]))
        self.assertTrue(all(p.counts[u]==0 for u in s.uids[2:]))
        with self.assertRaises(RuntimeError):p.reserve(window=range(100,200,10))
        p.cancel(rest)
        self.assertEqual(p.rgb_view_services,2);self.assertIsNone(p._pending)

    def test_same_selection_sequence_with_different_optimizer_grouping(self):
        grouped=self.make();single=self.make();window=range(100,200,10)
        for size in [12,12,12,4]*12:
            a=grouped.reserve(size,window=window);b=single.reserve(size,window=window)
            self.assertEqual(a.uids,b.uids)
            self.assertEqual(grouped._pending_batch['roles'],single._pending_batch['roles'])
            grouped.commit(a)
            while b is not None:b=single.commit_prefix(b,1)
            self.assertEqual(grouped.counts,single.counts)
        self.assertNotEqual(grouped.rgb_steps_completed,single.rgb_steps_completed)

    def test_existing_scale_projection_preserves_parameter_and_protected_rows(self):
        import torch
        source=Path('/home/intern/VIGS-SLAM-online-worker-integration/vigs/gs_backend.py')
        tree=ast.parse(source.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GSBackEnd')
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_project_mapping_scales')
        ns={'torch':torch};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),ns)
        class Model:
            _scaling=torch.nn.Parameter(torch.tensor([[.2,.05,.3],[.4,.5,.6]]).log())
            scaling_inverse_activation=staticmethod(torch.log)
            @property
            def get_scaling(self):return self._scaling.exp()
        m=Model();parameter=m._scaling;before=m.get_scaling.detach().clone()
        ns['_project_mapping_scales'](SimpleNamespace(gaussians=m),torch.tensor([False,True]))
        self.assertIs(m._scaling,parameter)
        self.assertTrue(torch.allclose(m.get_scaling[0],torch.tensor([.1,.05,.1])))
        self.assertTrue(torch.allclose(m.get_scaling[1],before[1]))
        self.assertIsNone(m._scaling.grad)

    def test_runtime_defaults_match_recommended_recipe(self):
        from online_mapper_runtime import OnlineMapperRuntime
        noop=lambda *a,**k:None
        modules={
            'live_dense_imu':SimpleNamespace(LiveDenseImuShaper=lambda *a:object()),
            'live_dense_pose_refresh':SimpleNamespace(install=noop),
            'dense_visual_pose':SimpleNamespace(install=noop),
            'dense_visual_pose_reuse':SimpleNamespace(CorrespondenceRefiner=object),
            'dense_pose_lazy_refresh':SimpleNamespace(install=noop),
            'deferred_dense_observations':SimpleNamespace(DeferredDenseObservations=lambda *a,**k:None)}
        cfg=json.loads(Path('/home/intern/VIGS-SLAM-online-worker-integration/configs/online_mapping_unified.json').read_text())
        for options in (cfg,{'schedule':'unified','membership':'immediate'},
                        {'schedule':'unified','membership':'growth','growth_budget_scope':'dense_only','kappa':8,'tau':.25}):
            host=SimpleNamespace(gs=SimpleNamespace(),_gs_stream=SimpleNamespace(synchronize=noop),
                                 config={'IMU':{'Tcb_np':None}},args=SimpleNamespace(weights=None))
            with patch.dict(sys.modules,modules):runtime=OnlineMapperRuntime(host,options)
            self.assertEqual(runtime.mapper.online_view_trainer.policy.batch_quotas,tuple(cfg['batch_quotas']))
            self.assertEqual(runtime.mapper.online_view_trainer.optimizer_batch_size,cfg['optimizer_batch_size'])
            if options.get('membership')=='growth':
                self.assertEqual(runtime.mapper.online_view_trainer.policy.membership,'growth')
                self.assertEqual(runtime.mapper.online_view_trainer.policy.kappa,8)
                self.assertEqual(runtime.mapper.online_view_trainer.policy.tau,.25)
                self.assertEqual(runtime.mapper.online_view_trainer.policy.growth_budget_scope,'dense_only')
            self.assertEqual(runtime.unified_budget.renders_per_kf,cfg['renders_per_kf'])
            self.assertTrue(runtime.mapper._mapping_disable_densify_prune)
            self.assertTrue(runtime.mapper.online_unified_scale_projection)
            self.assertFalse(runtime.mapper._mapping_observation_topology_gate)
            runtime.close()


if __name__=='__main__':unittest.main()
