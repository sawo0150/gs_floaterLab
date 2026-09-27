import unittest
from types import SimpleNamespace
import torch
from render_work_audit import RenderWorkAudit

class RenderAuditTests(unittest.TestCase):
    def test_batch_cameras_not_calls_and_once_for_rgb_depth_backward(self):
        value=torch.tensor(2.,requires_grad=True)
        def single(view):return {'render':value*2,'depth':value*3}
        module=SimpleNamespace(render=single,render_kernel_batch=lambda views:[single(v) for v in views])
        audit=RenderWorkAudit(module,torch)
        cameras=[SimpleNamespace(uid=i) for i in range(3)]
        outputs=module.render_kernel_batch(cameras)
        sum(o['render']+o['depth'] for o in outputs).backward()
        self.assertEqual(dict(audit.counts),{'all':3,'training':3,'backward':3})
        with torch.no_grad():module.render(cameras[0])
        self.assertEqual(audit.counts['all'],4)
        self.assertEqual(audit.counts['no_grad'],1)
        self.assertEqual(audit.training,3)

    def test_unused_and_failed_render_not_silently_committed(self):
        def single(view):
            if view.uid<0:raise ValueError('bad view')
            return {'render':torch.tensor(1.,requires_grad=True)}
        module=SimpleNamespace(render=single)
        audit=RenderWorkAudit(module,torch)
        module.render(SimpleNamespace(uid=0))
        self.assertNotEqual(audit.training,audit.counts['backward'])
        with self.assertRaises(ValueError):module.render(SimpleNamespace(uid=-1))
        self.assertEqual(audit.training,1)
        self.assertEqual(len(audit.errors),1)

if __name__=='__main__':unittest.main()
