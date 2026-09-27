"""Count camera renders (not CUDA calls), independently of optimizer steps."""
from collections import Counter

class RenderWorkAudit:
    def __init__(self, module, torch):
        self.torch = torch
        self.counts = Counter()
        self.rows = []
        self.context = {}
        self.errors = []
        self.originals = {}
        for name in ('render', 'render_batch', 'render_kernel_batch', 'render_filtered', 'render_cg'):
            original = getattr(module, name, None)
            if original is None:
                continue
            self.originals[name] = original
            def wrapped(views, *args, _name=name, _original=original, **kwargs):
                batch = _name in ('render_batch', 'render_kernel_batch')
                cameras = list(views) if batch else [views]
                grad_enabled = bool(torch.is_grad_enabled())
                try:
                    result = _original(views, *args, **kwargs)
                except BaseException as e:
                    self.errors.append({'renderer': _name, 'error': str(e)})
                    raise
                packages = result if batch else [result]
                if len(packages) != len(cameras):
                    self.errors.append({'renderer': _name, 'error': 'batch length mismatch'})
                    raise RuntimeError('Render audit batch length mismatch')
                self.counts['all'] += len(cameras)
                self.counts['training' if grad_enabled else 'no_grad'] += len(cameras)
                for camera, pkg in zip(cameras, packages):
                    row = {**self.context, 'uid': int(camera.uid), 'renderer': _name,
                           'grad_enabled': grad_enabled, 'backward': False}
                    self.rows.append(row)
                    def backward(gradient, _row=row):
                        if not _row['backward']:
                            self.counts['backward'] += 1
                            _row['backward'] = True
                        return gradient
                    for key in ('render', 'depth'):
                        value = pkg.get(key)
                        if grad_enabled and value is not None and value.requires_grad:
                            value.register_hook(backward)
                return result
            setattr(module, name, wrapped)

    @property
    def training(self):
        return self.counts['training']
