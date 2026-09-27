"""Post-run coordinate alignment for snapshot evaluation; never mapping input."""
import numpy as np


def align_camera_worlds(reference_w2c, snapshot_w2c):
    reference = np.asarray(reference_w2c, dtype=np.float64)
    snapshot = np.asarray(snapshot_w2c, dtype=np.float64)
    if reference.shape != snapshot.shape or reference.ndim != 3 or reference.shape[1:] != (4, 4):
        raise ValueError('Expected paired N x 4 x 4 camera transforms')
    if len(reference) < 3 or not np.isfinite(reference).all() or not np.isfinite(snapshot).all():
        raise ValueError('Insufficient or nonfinite camera correspondences')
    ref_c2w, snap_c2w = np.linalg.inv(reference), np.linalg.inv(snapshot)
    x, y = ref_c2w[:, :3, 3], snap_c2w[:, :3, 3]
    a, b = x - x.mean(0), y - y.mean(0)
    if np.linalg.matrix_rank(a) < 2 or np.linalg.matrix_rank(b) < 2:
        raise ValueError('Degenerate camera centers; no reliable similarity alignment')
    u, singular, vt = np.linalg.svd(b.T @ a / len(a))
    sign = np.ones(3)
    sign[-1] = np.linalg.det(u @ vt)
    rotation = (u * sign) @ vt
    scale = float(np.dot(singular, sign) / np.mean(np.sum(a * a, axis=1)))
    if not scale > 0:
        raise ValueError('Invalid camera-world scale')
    translation = y.mean(0) - scale * rotation @ x.mean(0)
    center_error = y - (scale * (rotation @ x.T).T + translation)
    estimated_rotation = rotation[None] @ ref_c2w[:, :3, :3]
    delta = estimated_rotation.transpose(0, 2, 1) @ snap_c2w[:, :3, :3]
    angles = np.arccos(np.clip((np.trace(delta, axis1=1, axis2=2) - 1) / 2, -1, 1))
    return {'scale': scale, 'rotation': rotation, 'translation': translation,
            'center_rmse': float(np.sqrt(np.mean(np.sum(center_error ** 2, axis=1)))),
            'center_max_error': float(np.linalg.norm(center_error, axis=1).max()),
            'orientation_max_error_degrees': float(np.degrees(angles).max()),
            'reference_center_rms_radius': float(np.sqrt(np.mean(np.sum(a * a, axis=1)))),
            'paired_cameras': len(x)}


def transform_evaluation_cameras(reference_w2c, alignment):
    c2w = np.linalg.inv(np.asarray(reference_w2c, dtype=np.float64))
    output = c2w.copy()
    r, t, scale = alignment['rotation'], alignment['translation'], alignment['scale']
    output[:, :3, :3] = r[None] @ c2w[:, :3, :3]
    output[:, :3, 3] = scale * (r @ c2w[:, :3, 3].T).T + t
    return np.linalg.inv(output)
