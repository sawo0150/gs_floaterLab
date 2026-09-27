import unittest
from evaluate_online_stream import point, assemble_curve


def result(values):
    return {'per_view': [dict(uid=uid, psnr=value,
        predeclared_fixed_manifest_split=uid != 'training') for uid, value in values]}


class CurveTests(unittest.TestCase):
    def test_fixed_cohort_and_mean_ignore_training_rows_and_input_order(self):
        a = point(result([('b', 22.), ('training', 99.), ('a', 20.)]), 1.)
        b = point(result([('a', 24.), ('b', 26.)]), 2.)
        curve = assemble_curve([b, a])
        self.assertEqual(curve['view_count'], 2)
        self.assertEqual([x['mean_heldout_psnr'] for x in curve['points']], [21., 25.])
        self.assertFalse(curve['exact_first_attainment_claim'])
        self.assertFalse(curve['coordinate_alignment_quality_accepted'])

    def test_changing_cohort_or_duplicate_time_is_rejected(self):
        a = point(result([('a', 20.)]), 1.)
        with self.assertRaises(ValueError):
            assemble_curve([a, point(result([('b', 21.)]), 2.)])
        with self.assertRaises(ValueError):
            assemble_curve([a, a])
        with self.assertRaises(ValueError):
            assemble_curve([a])

    def test_nonfinite_and_duplicate_views_rejected(self):
        with self.assertRaises(ValueError):
            point(result([('a', float('nan'))]), 1.)
        with self.assertRaises(ValueError):
            point(result([('a', 20.), ('a', 21.)]), 1.)

    def test_nonfinite_or_negative_availability_time_rejected(self):
        a = point(result([('a', 20.)]), 1.)
        for seconds in (float('nan'), float('inf'), -1.):
            with self.assertRaises(ValueError):
                assemble_curve([a, point(result([('a', 21.)]), seconds)])


if __name__ == '__main__':
    unittest.main()
