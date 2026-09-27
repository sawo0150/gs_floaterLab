import unittest
from types import SimpleNamespace
from keyframe_render_budget import KeyframeRenderBudget

class FakeMapper:
    def __init__(self,audit):
        self.audit=audit;self.viewpoints={1:SimpleNamespace()}
        self.online_view_trainer=SimpleNamespace(generation=0)
    def map(self,current_window,iters=10,include_global=True,max_viewpoints=20,photometric_only=False):
        count=1 if photometric_only else min(len(current_window)+(6 if include_global else 0),max_viewpoints)*iters
        self.audit.training+=count
        return count

class BudgetTests(unittest.TestCase):
    def test_native_cap_and_single_view_remainder(self):
        a=SimpleNamespace(training=0);m=FakeMapper(a);b=KeyframeRenderBudget(m,a)
        b.start_arrival(1)
        self.assertEqual(m.map(list(range(11))),15)
        self.assertEqual(b.target,15)
        self.assertEqual(m.map(list(range(11))),0)
        self.assertEqual(a.training,15)
    def test_local_window_leaves_four_steps_and_no_credit_on_pose_update(self):
        a=SimpleNamespace(training=0);m=FakeMapper(a);b=KeyframeRenderBudget(m,a)
        b.start_arrival(1);m.map(list(range(11)),include_global=False)
        for _ in range(4):m.map([],photometric_only=True)
        self.assertEqual(a.training,b.target)
        b.start_arrival(2);self.assertEqual(m.map([1]),0)
        self.assertEqual(b.target,15)
    def test_reset_and_heldout_accounting(self):
        a=SimpleNamespace(training=0);m=FakeMapper(a);b=KeyframeRenderBudget(m,a)
        b.start_arrival(1);b.sync();b.sync();self.assertEqual(b.target,15)
        m.viewpoints[2]=SimpleNamespace(mapping_eval_excluded=True);b.sync();self.assertEqual(b.target,15)
        m.online_view_trainer.generation=1;b.sync();self.assertEqual(b.target,30)

if __name__=='__main__':unittest.main()
