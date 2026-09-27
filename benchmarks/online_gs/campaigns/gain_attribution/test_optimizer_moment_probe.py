import copy
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimizer_moment_probe import sample_optimizer, summarize_samples, install


class MomentProbeTests(unittest.TestCase):
    def test_observer_preserves_parameters_gradients_and_adam_state(self):
        left = torch.nn.Parameter(torch.linspace(-1, 1, 100, dtype=torch.float64))
        right = torch.nn.Parameter(left.detach().clone())
        a = torch.optim.Adam([{'params': [left], 'name': 'xyz'}], lr=.003)
        b = torch.optim.Adam([{'params': [right], 'name': 'xyz'}], lr=.003)
        for i in range(6):
            gradient = torch.sin(torch.arange(100, dtype=torch.float64) + i)
            left.grad = gradient.clone(); right.grad = gradient.clone()
            before = copy.deepcopy(a.state_dict())
            samples = sample_optimizer(a, max_coordinates=30)
            self.assertTrue(torch.equal(left.grad, gradient))
            for key, value in before['state'].items():
                for field, tensor in value.items():
                    self.assertTrue(torch.equal(tensor, a.state_dict()['state'][key][field]))
            a.step(); b.step()
            rows = summarize_samples(samples)
            self.assertLess(rows[0]['max_adam_prediction_error'], 1e-15)
            self.assertLessEqual(rows[0]['sample_coordinates'], 30)
            self.assertTrue(torch.equal(left, right))
            self.assertTrue(torch.equal(left.grad, right.grad))
            for field, tensor in a.state[left].items():
                self.assertTrue(torch.equal(tensor, b.state[right][field]))

    def test_reports_conflicting_history_direction(self):
        p = torch.nn.Parameter(torch.ones(8, dtype=torch.float64))
        opt = torch.optim.Adam([p], lr=.01)
        for _ in range(10):
            p.grad = torch.ones_like(p)
            opt.step()
        p.grad = -torch.ones_like(p) * .01
        samples = sample_optimizer(opt)
        opt.step()
        row = summarize_samples(samples)[0]
        self.assertLess(row['gradient_descent_direction_cosine'], -.99)
        self.assertGreater(row['history_delta_rms'], row['current_delta_rms'])
        self.assertGreater(row['gradient_dot_parameter_delta'], 0)

    def test_zero_or_missing_gradient_and_unsupported_adam(self):
        p = torch.nn.Parameter(torch.ones(8))
        opt = torch.optim.Adam([p])
        self.assertEqual(sample_optimizer(opt), [])
        p.grad = torch.zeros_like(p)
        samples = sample_optimizer(opt); opt.step()
        self.assertEqual(summarize_samples(samples)[0]['gradient_rms'], 0)
        bad = torch.optim.Adam([p], amsgrad=True)
        with self.assertRaises(ValueError):
            sample_optimizer(bad)

    def test_installer_labels_actual_native_and_dense_work(self):
        p = torch.nn.Parameter(torch.ones(8))
        opt = torch.optim.Adam([{'params': [p], 'name': 'xyz'}])
        policy = SimpleNamespace(_pending=None, keyframes={0, 10}, generation=2, rgb_steps_completed=0)
        mapper = SimpleNamespace(gaussians=SimpleNamespace(optimizer=opt, _xyz=p),
            online_view_trainer=SimpleNamespace(policy=policy), map=lambda *a, **k: None,
            _frontier_mapping_view_loss=lambda *a, **k: p.sum())
        guard = SimpleNamespace(reject_if_unsafe=lambda kind: None)
        original = torch.optim.Adam.step
        try:
            report = install(mapper, guard, heldout={8}, every=1)
            for uid in (0, 10):
                mapper._frontier_mapping_view_loss(None, None, SimpleNamespace(uid=uid))
            p.grad = torch.ones_like(p); opt.step()
            policy.rgb_steps_completed += 1
            policy._pending = SimpleNamespace(uids=(5,))
            p.grad = -torch.ones_like(p); opt.step()
            self.assertEqual([r['source'] for r in report['records']], ['native', 'photo_dense'])
            self.assertEqual([r['batch_views'] for r in report['records']], [2, 1])
            self.assertEqual([r['next_service_step'] for r in report['records']], [1, 2])
        finally:
            torch.optim.Adam.step = original


if __name__ == '__main__':
    unittest.main()
