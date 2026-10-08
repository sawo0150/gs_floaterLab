"""Scale projection with a configurable cap (the B recipe hard-codes 0.1 in GSBackEnd._project_mapping_scales).

install(cap): every per-packet projection clamps Gaussian scales to `cap` instead of 0.1 (same call sites, same
frozen-mask handling). Used to keep normal large Gaussians (walls) while still stopping giant ones.
"""


def install(cap):
    import gs_backend
    import torch
    cap = float(cap)

    @torch.no_grad()                              # as the original (decorated) method
    def project(self, frozen_mask=None):
        s = self.gaussians.get_scaling
        if frozen_mask is not None:
            n = s.clone(); n[~frozen_mask] = s[~frozen_mask].clamp(max=cap)
        else:
            n = s.clamp(max=cap)
        self.gaussians._scaling[:] = self.gaussians.scaling_inverse_activation(n)
    gs_backend.GSBackEnd._project_mapping_scales = project
