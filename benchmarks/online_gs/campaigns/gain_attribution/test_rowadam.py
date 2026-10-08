import torch, unittest
from rowadam_patch import RowAdam


class T(unittest.TestCase):
    def test_matches_adam_without_appends(self):
        torch.manual_seed(0)
        a = torch.nn.Parameter(torch.randn(50, 3)); b = torch.nn.Parameter(a.detach().clone())
        oa = torch.optim.Adam([a], lr=1e-2, eps=1e-15); ob = RowAdam([b], lr=1e-2, eps=1e-15)
        for i in range(30):
            g = torch.randn(50, 3)
            a.grad = g.clone(); b.grad = g.clone(); oa.step(); ob.step()
        self.assertTrue(torch.allclose(a, b, atol=1e-6))

    def test_appended_rows_behave_like_fresh_adam(self):
        torch.manual_seed(1)
        p = torch.nn.Parameter(torch.randn(10, 2)); o = RowAdam([p], lr=1e-2, eps=1e-15)
        for i in range(500):
            p.grad = torch.randn(10, 2); o.step()
        st = o.state[p]
        new = torch.randn(5, 2)
        q = torch.nn.Parameter(torch.cat([p.detach(), new]))
        st['exp_avg'] = torch.cat([st['exp_avg'], torch.zeros(5, 2)]); st['exp_avg_sq'] = torch.cat([st['exp_avg_sq'], torch.zeros(5, 2)])
        del o.state[p]; o.param_groups[0]['params'][0] = q; o.state[q] = st
        ref = torch.nn.Parameter(new.clone()); oref = torch.optim.Adam([ref], lr=1e-2, eps=1e-15)
        for i in range(20):
            g = torch.randn(15, 2); q.grad = g; o.step(); ref.grad = g[10:].clone(); oref.step()
        self.assertTrue(torch.allclose(q[10:], ref, atol=1e-6))


if __name__ == '__main__':
    unittest.main()
