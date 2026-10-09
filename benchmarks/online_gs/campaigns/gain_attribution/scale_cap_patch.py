"""Scale projection with a configurable cap (the B recipe hard-codes 0.1 in GSBackEnd._project_mapping_scales).

install(cap): every per-packet projection clamps Gaussian scales to `cap` instead of 0.1 (same call sites, same
frozen-mask handling). Used to keep normal large Gaussians (walls) while still stopping giant ones.
Optional SMALL registry: Gaussians whose point_id is in SMALL['ids'] (CPU int64 tensor) are clamped to SMALL['cap']
instead (used for transparent births, RTG-SLAM style).
"""

SMALL = dict(ids=None, cap=None)


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
        if SMALL['ids'] is not None and len(SMALL['ids']):
            m = torch.isin(self.gaussians.point_ids, SMALL['ids']).to(n.device)
            if frozen_mask is not None:
                m &= ~frozen_mask
            n[m] = n[m].clamp(max=SMALL['cap'])
        self.gaussians._scaling[:] = self.gaussians.scaling_inverse_activation(n)
    gs_backend.GSBackEnd._project_mapping_scales = project
