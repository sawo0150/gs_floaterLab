#!/usr/bin/env python3
"""Exercise the real audited warm-pose path on changed online anchors/depths."""
import check_dense_correspondence_reuse as check
from dense_pose_quality_refiner import QualityAuditedRefiner


class CheckedRefiner(QualityAuditedRefiner):
    def refine(self, *args):
        result, stats = super().refine(*args)
        fit = stats['correspondence_fit_after_refinement']
        assert fit['weighted_rms_grid'] is not None and fit['weighted_rms_grid'] < 1e-4, fit
        assert fit['supported_pixel_fraction'] > .5, fit
        return result, stats


if __name__ == '__main__':
    check.CorrespondenceRefiner = CheckedRefiner
    check.main()
