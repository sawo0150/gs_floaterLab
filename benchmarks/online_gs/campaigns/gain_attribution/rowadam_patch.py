"""Per-Gaussian Adam bias correction (runtime patch on GaussianModel's optimizer).

torch.optim.Adam keeps one `step` per parameter tensor. GaussianModel appends new Gaussians as new rows of the same
tensors with zero moments (cat_tensors_to_optimizer) but leaves the shared step unchanged, so rows born at step t get
bias corrections 1/(1-β^t) ≈ 1 while their moments start from 0: their effective step is 2–6× the normal Adam step for
their first hundreds of updates. Offline/D2 never hit this (all rows exist before the first step).

RowAdam keeps a per-row step count `row_step` (rows appended at the end start at 0; pruning masks it; a full moment
reset by replace_tensor_to_optimizer resets it) and applies Adam with per-row bias correction. With no appends it is
identical to torch.optim.Adam (lr, betas, eps, no weight decay / amsgrad). Install before GaussianModel.training_setup.
"""
import torch


class RowAdam(torch.optim.Adam):
    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            b1, b2 = group['betas']; lr, eps = group['lr'], group['eps']
            assert not group.get('amsgrad') and not group.get('weight_decay') and not group.get('maximize')
            for p in group['params']:
                if p.grad is None:
                    continue
                g = p.grad
                st = self.state[p]
                if len(st) == 0 or 'exp_avg' not in st:
                    st['step'] = torch.zeros((), dtype=torch.float32)
                    st['exp_avg'] = torch.zeros_like(p); st['exp_avg_sq'] = torch.zeros_like(p)
                n = p.shape[0]
                rs = st.get('row_step')
                if rs is None:   # state created by the plain Adam path: all existing rows share its step
                    rs = torch.full((n,), float(st['step']), device=p.device, dtype=torch.float32)
                if rs.shape[0] < n:          # rows appended at the end since the last step start at 0
                    rs = torch.cat([rs, torch.zeros(n - rs.shape[0], device=p.device, dtype=rs.dtype)])
                elif rs.shape[0] > n:
                    raise RuntimeError('row_step longer than parameter: pruning bypassed the patched _prune_optimizer')
                rs = rs + 1
                st['row_step'] = rs; st['step'] = st['step'] + 1
                m, v = st['exp_avg'], st['exp_avg_sq']
                m.mul_(b1).add_(g, alpha=1 - b1)
                v.mul_(b2).addcmul_(g, g, value=1 - b2)
                shape = (n,) + (1,) * (p.dim() - 1)
                bc1 = (1 - b1 ** rs).view(shape); bc2 = (1 - b2 ** rs).view(shape)
                denom = (v.sqrt() / bc2.sqrt()).add_(eps)
                p.addcdiv_(m / bc1, denom, value=-lr)
        return loss


def install():
    from gaussian.scene.gaussian_model import GaussianModel
    setup = GaussianModel.training_setup

    def row_setup(self, *a, **k):
        out = setup(self, *a, **k)
        self.optimizer.__class__ = RowAdam
        self.optimizer._patch_step_function()   # wrap RowAdam.step once so step pre/post hooks (mapper guard) fire
        return out
    GaussianModel.training_setup = row_setup

    prune = GaussianModel._prune_optimizer

    def row_prune(self, mask):
        for group in self.optimizer.param_groups:
            st = self.optimizer.state.get(group['params'][0])
            if st is not None and st.get('row_step') is not None:
                rs = st['row_step']
                if rs.shape[0] < mask.shape[0]:
                    rs = torch.cat([rs, torch.zeros(mask.shape[0] - rs.shape[0], device=rs.device, dtype=rs.dtype)])
                st['row_step'] = rs[mask.to(rs.device)]
        return prune(self, mask)
    GaussianModel._prune_optimizer = row_prune

    replace = GaussianModel.replace_tensor_to_optimizer

    def row_replace(self, tensor, name):
        for group in self.optimizer.param_groups:
            if group['name'] == name:
                st = self.optimizer.state.get(group['params'][0])
                if st is not None:
                    st['row_step'] = torch.zeros(tensor.shape[0], device=tensor.device, dtype=torch.float32)
        return replace(self, tensor, name)
    GaussianModel.replace_tensor_to_optimizer = row_replace
