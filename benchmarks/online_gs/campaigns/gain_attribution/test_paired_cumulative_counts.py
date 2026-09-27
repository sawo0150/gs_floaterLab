"""Cumulative ERVS regression tests; CPU only, no quality claim."""
import ast
from collections import Counter
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

BACKEND = Path('/home/intern/VIGS-SLAM-online-worker-integration/vigs')
sys.path.insert(0, str(BACKEND))
from paired_view_training import PairedTrainingSet
from online_photometric import OnlinePhotometricTrainer
from online_mapper_runtime import OnlineMapperRuntime


def audit(report, steps):
    source = Path(__file__).with_name('run_arrived_online_worker.py')
    node = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == 'training_checks')
    namespace = {'Counter': Counter}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['training_checks'](report, steps)


class CumulativeTests(unittest.TestCase):
    def policy(self, **options):
        p = PairedTrainingSet(membership='immediate', selector='ervs', tau=1.,
                              entropy_weight_policy='per_view', **options)
        p.register_keyframes([0, 10, 20])
        p.offer(5, 0, 10, available_through=20)
        p.offer(15, 10, 20, available_through=20)
        return p

    def native(self, p, uids):
        p.commit_native(uids)
        p.service_ledger[-1].update(window_uids=uids, recent_window_uids=uids)

    def test_default_cumulative_counts_do_not_expire(self):
        p = self.policy()
        self.assertEqual(p.selection_count_scope, 'all_rgb')
        for _ in range(100):
            self.native(p, [0])
        for _ in range(20):
            self.native(p, [10, 20])
        self.assertEqual(p.role_counts('keyframe'), {0: 100, 10: 20, 20: 20})
        seen = []
        p.rng.choices = lambda uids, weights, k: (seen.append(dict(zip(uids, weights))) or [10])
        s = p.reserve()
        self.assertLess(seen[0][0], seen[0][10])
        p.cancel(s)

    def test_success_only_counts_and_native_does_not_consume_turn(self):
        p = self.policy()
        before = p.role_counts('keyframe')
        selected = p.reserve()
        self.assertEqual(p.role_counts('keyframe'), before)
        p.cancel(selected)
        self.assertEqual(p.role_counts('keyframe'), before)
        selected = p.reserve(); uid = selected.uids[0]; p.commit(selected)
        self.assertEqual(p.counts[uid], 1)
        self.assertEqual(p.next_role, 'dense')
        self.native(p, [0, 10, 20])
        self.assertEqual(p.counts[uid], 2)
        self.assertEqual(p.next_role, 'dense')
        selected = p.reserve(); dense_uid = selected.uids[0]; p.commit(selected)
        self.assertEqual(p.role_counts('dense')[dense_uid], 1)
        self.assertEqual(p.next_role, 'keyframe')

    def test_promotion_preserves_dense_service_in_keyframe_count(self):
        p = self.policy()
        p.rng.choices = lambda uids, weights, k: [uids[0]]
        for _ in range(8):
            s = p.reserve(); p.commit(s)
        self.assertEqual(p.role_counts('dense')[5], 4)
        p.register_keyframes([5])
        self.assertNotIn(5, p.role_counts('dense'))
        self.assertEqual(p.role_counts('keyframe')[5], 4)
        self.native(p, [5])
        self.assertEqual(p.role_counts('keyframe')[5], 5)

    def test_explicit_legacy_recent_scope_still_reproduces_old_counts(self):
        p = self.policy(selection_count_scope='recent_photometric')
        for _ in range(10): self.native(p, [0])
        self.assertEqual(p.role_counts('keyframe'), {0: 0, 10: 0, 20: 0})
        p.rng.choices = lambda uids, weights, k: [uids[0]]
        for _ in range(10): s = p.reserve(); p.commit(s)
        self.assertEqual(p.role_counts('keyframe')[0], 2)
        self.assertEqual(p.role_counts('dense')[5], 1)

    def test_runtime_default_and_explicit_override(self):
        def create(options):
            mapper = SimpleNamespace()
            host = SimpleNamespace(gs=mapper, _gs_stream=SimpleNamespace(synchronize=lambda: None))
            return OnlineMapperRuntime(host, {'schedule': 'paired_kf_dense',
                 'membership': 'kf_only', **options}).mapper.online_view_trainer
        trainer = create({})
        self.assertEqual(trainer.policy.selection_count_scope, 'all_rgb')
        trainer.policy.register_keyframes([0]); trainer.policy.commit_native([0])
        trainer.reset()
        self.assertEqual(trainer.policy.selection_count_scope, 'all_rgb')
        self.assertEqual(trainer.policy.counts, {})
        self.assertEqual(trainer.histories[0]['policy']['counts'], {0: 1})
        self.assertEqual(create({'selection_count_scope': 'recent_photometric'}).policy.selection_count_scope,
                         'recent_photometric')

    def test_independent_ledger_audit_detects_missing_native_count(self):
        p = self.policy()
        self.native(p, [0, 10, 20])
        for _ in range(20): s = p.reserve(); p.commit(s)
        report = {'generations': [{'policy': p.snapshot(), 'services': p.service_ledger,
                                   'admissions': p.admission_ledger}],
                  'photometric_steps': 20, 'schedule': 'paired_kf_dense'}
        # Runtime uses whole_pool metadata even though immediate has no growth limit.
        p.growth_budget_scope = 'whole_pool'
        report['generations'][0]['policy'] = p.snapshot()
        for row in p.admission_ledger: row['growth_budget_scope'] = 'whole_pool'
        self.assertTrue(all(audit(report, 21).values()))
        damaged = copy.deepcopy(report)
        damaged['generations'][0]['policy']['role_next_draw_counts']['keyframe'][0] -= 1
        self.assertFalse(audit(damaged, 21)['role_selection_counts_match_history'])
        damaged = copy.deepcopy(report)
        damaged['generations'][0]['policy']['counts'][0] -= 1
        self.assertFalse(audit(damaged, 21)['cumulative_counts_match_committed_history'])


if __name__ == '__main__':
    unittest.main()
