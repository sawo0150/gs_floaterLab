import ast
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
from exp78b_timeline_scheduler import (FrozenTimelineScheduler, TimelineItem,
                                      DeadlineReached, ControlPreempted)


class ClockTests(unittest.TestCase):
    def run_ingest_failure(self, category, kind):
        item = TimelineItem('input:0', category, kind, 0., (0, 0), {})
        scheduler = FrozenTimelineScheduler([item], replay_start=0.,
            sensor_timestamp0=0., time_scale=1., deadline=1.)
        calls = []
        def rejected(*args):
            raise DeadlineReached('input')
        with patch('exp78b_timeline_scheduler.time.monotonic', return_value=.95):
            report = scheduler.run(process_control=rejected, process_dense=rejected,
                process_packet=lambda *args: calls.append('map'),
                idle_step=lambda *args: calls.append('optimizer'))
        self.assertTrue(report['deadline_reached'])
        self.assertEqual(report['deadline_source_id'], 'input_preparation')
        self.assertEqual(calls, [])

    def test_dense_preparation_rejection_finishes_cleanly(self):
        self.run_ingest_failure('dense_interval', 'dense_interval')

    def test_control_preparation_rejection_finishes_cleanly(self):
        self.run_ingest_failure('control', 'metric_rescale')

    def test_packet_guard_rejects_before_adam_without_topology_miscount(self):
        # Exercise the real CPU-only guard without importing CUDA mapper code.
        tree = ast.parse((BASE / 'exp78b_replay_gsslam_mapping.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'BoundaryGuard')
        ns = {'time': SimpleNamespace(monotonic=lambda: .95),
              'DeadlineReached': DeadlineReached, 'ControlPreempted': ControlPreempted}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual guard>', 'exec'), ns)
        guard = ns['BoundaryGuard'](1., .1)
        with self.assertRaises(DeadlineReached):
            guard.reject_if_unsafe('packet')
        self.assertEqual(guard.input_actions_rejected_at_deadline, 1)
        self.assertEqual(guard.optimizer_steps_rejected_at_deadline, 0)
        self.assertEqual(guard.topology_actions_rejected_at_deadline, 0)
        ns['time'].monotonic = lambda: .8
        guard.reject_if_unsafe('packet')


if __name__ == '__main__':
    unittest.main()
