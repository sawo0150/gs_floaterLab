import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
sys.path.insert(0,'/home/intern/VIGS-SLAM-online-worker-integration/vigs')
from arrived_input_boundary import input_preparation
from mapper_execution_guard import MapperExecutionGuard, MappingBoundaryReached
from online_mapping_worker import OnlineMappingWorker


class BoundaryTests(unittest.TestCase):
    def make(self):
        now=[0.]
        g=MapperExecutionGuard(deadline=10.,reserve_seconds=.1,synchronize=lambda:None,clock=lambda:now[0])
        w=OnlineMappingWorker(guard=g,dispatch=lambda p:None,idle=lambda:False)
        return now,SimpleNamespace(guard=g,worker=w,close=w.close)

    def test_submit_close_race_accounts_preparation_and_allows_terminal_arrival(self):
        now,r=self.make();timing={};row={};terminal=False
        with input_preparation(r,row,timing,start=0.,clock=lambda:now[0],
                               synchronize=lambda:now.__setitem__(0,9.97)):
            now[0]=9.95;r.close();r.worker.submit({})
        now[0]=10.;terminal=True # producer can continue through sensor EOS
        self.assertTrue(terminal);self.assertEqual(timing['end'],9.97)
        self.assertIn('preparation_cancelled',row);self.assertEqual(r.guard.completions,[])

    def test_early_close_is_not_suppressed(self):
        now,r=self.make();timing={};r.close()
        with self.assertRaises(MappingBoundaryReached):
            with input_preparation(r,{},timing,start=0.,clock=lambda:now[0]):r.worker.submit({})
        self.assertEqual(timing['end'],0.)

    def test_worker_failure_and_preparation_overrun_are_not_hidden(self):
        now,r=self.make();now[0]=9.95;r.worker.error=ValueError('broken');r.close();timing={}
        with self.assertRaisesRegex(RuntimeError,'broken'):
            with input_preparation(r,{},timing,start=0.,clock=lambda:now[0]):
                now[0]=10.1;raise MappingBoundaryReached('closed')
        self.assertGreater(timing['end'],r.guard.deadline)


if __name__=='__main__':unittest.main()
