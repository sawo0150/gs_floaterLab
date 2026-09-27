"""CPU tests for relative blur screening, causality, and inventory filtering."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
import cv2
import numpy as np
import torch

sys.path.insert(0, '/home/intern/VIGS-SLAM-online-worker-integration/vigs')
from dense_blur_filter import DenseBlurFilter, sharpness
from arrived_sensor_store import ArrivedSensorStore
from deferred_dense_observations import DeferredDenseObservations


def image_pair():
    rng = np.random.default_rng(12)
    source = cv2.GaussianBlur(rng.random((128, 160)).astype(np.float32), (3, 3), .5)
    kernel = np.zeros((17, 17), np.float32); kernel[8, :] = 1 / 17
    blurred = cv2.filter2D(source, -1, kernel)
    return [torch.from_numpy(np.stack([x] * 3)) for x in (source, blurred)]


class BlurTests(unittest.TestCase):
    def store(self):
        clear, blurred = image_pair()
        archive = ArrivedSensorStore(heldout=(3,))
        for uid, image in enumerate((clear, blurred, clear, clear, clear)):
            archive.append_rgb(uid, float(uid), image)
        return archive

    def test_motion_blur_rejected_without_discarding_clear_candidate(self):
        gate = DenseBlurFilter(self.store())
        self.assertEqual(gate.accept_interval(0, 4, (1, 2)), (2,))
        self.assertEqual(gate.report()['rejected_images'], 1)

    def test_flat_interval_is_not_all_rejected(self):
        archive = ArrivedSensorStore()
        for uid in range(3): archive.append_rgb(uid, uid, torch.ones(3, 64, 64))
        gate = DenseBlurFilter(archive)
        self.assertEqual(gate.accept_interval(0, 2, (1,)), (1,))

    def test_uniform_contrast_change_keeps_frequency_ratio(self):
        image = image_pair()[0]
        self.assertAlmostEqual(sharpness(image)['high_frequency_ratio'],
                               sharpness(image * .2)['high_frequency_ratio'], places=5)

    def test_uniform_contrast_change_is_retained_by_gate(self):
        image = image_pair()[0]; archive = ArrivedSensorStore()
        for uid, value in enumerate((image, image * .2, image)):
            archive.append_rgb(uid, uid, value)
        gate = DenseBlurFilter(archive)
        self.assertEqual(gate.accept_interval(0, 2, (1,)), (1,))

    def test_explicit_thresholds_and_invalid_configuration(self):
        archive = self.store(); interval = {'left_keyframe_uid':0, 'right_keyframe_uid':4}
        store = DeferredDenseObservations(SimpleNamespace(), archive, None,
            blur_filter={'energy_ratio':.5,'frequency_ratio':.75})
        store.ingest(interval, None)
        self.assertEqual(store.blur_filter.report()['energy_ratio'], .5)
        with self.assertRaises(ValueError): DenseBlurFilter(archive, energy_ratio=0)
        with self.assertRaises(ValueError): DenseBlurFilter(archive, frequency_ratio=1.1)

    def test_no_future_or_heldout_reads(self):
        gate = DenseBlurFilter(self.store())
        with self.assertRaises(ValueError): gate.accept_interval(0, 5, (1, 2))
        with self.assertRaises(ValueError): gate.accept_interval(0, 4, (1, 3))

    def test_decisions_cached_without_changing_membership(self):
        gate = DenseBlurFilter(self.store())
        gate.accept_interval(0, 4, (1, 2))
        decisions = dict(gate.decisions)
        self.assertEqual(gate.accept_interval(0, 2, (1,)), ())
        self.assertEqual(gate.decisions, decisions)

    def test_actual_inventory_excludes_rejected_before_pose_preparation(self):
        archive = self.store()
        interval = {'left_keyframe_uid': 0, 'right_keyframe_uid': 4}
        off = DeferredDenseObservations(SimpleNamespace(), archive, None)
        on = DeferredDenseObservations(SimpleNamespace(), archive, None, blur_filter=True)
        off.ingest(interval, None); on.ingest(interval, None)
        self.assertEqual(set(off.records), {1, 2})
        self.assertEqual(set(on.records), {2})
        self.assertEqual(on.audit['prepared_uids'], [])


if __name__ == '__main__': unittest.main()
