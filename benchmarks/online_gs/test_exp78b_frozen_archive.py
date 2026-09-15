#!/usr/bin/env python3
"""Regression tests for bounded frozen-tracker archive geometry loading."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import tempfile
import unittest

import torch

from exp78b_frozen_archive import FrozenTrackerArchive, SCHEMA_VERSION


class FrozenTrackerGeometryCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = FrozenTrackerArchive.__new__(FrozenTrackerArchive)
        self.archive.root = self.root
        self.archive._geometry_cache = OrderedDict()
        self.archive._geometry_cache_max_entries = 2

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_geometry(self, name: str, value: float) -> str:
        relative = f"{name}.pt"
        torch.save(
            {
                "schema_version": SCHEMA_VERSION,
                "depth": torch.full((2, 3), value),
                "normal": torch.full((3, 2, 3), -value),
            },
            self.root / relative,
        )
        return relative

    def test_geometry_cache_is_lru_bounded(self) -> None:
        first = self._write_geometry("first", 1.0)
        second = self._write_geometry("second", 2.0)
        third = self._write_geometry("third", 3.0)

        held_first = self.archive.load_geometry(first)
        self.archive.load_geometry(second)
        self.assertIs(self.archive.load_geometry(first), held_first)
        self.archive.load_geometry(third)

        self.assertEqual(list(self.archive._geometry_cache), [first, third])
        self.assertEqual(len(self.archive._geometry_cache), 2)
        # Eviction removes only the cache's reference. Existing packet/camera
        # ownership remains valid.
        torch.testing.assert_close(
            held_first["depth"], torch.full((2, 3), 1.0)
        )

    def test_evicted_geometry_reloads_bit_exactly(self) -> None:
        first = self._write_geometry("first", 1.25)
        second = self._write_geometry("second", 2.5)
        third = self._write_geometry("third", 3.75)

        original = self.archive.load_geometry(first)
        expected_depth = original["depth"].clone()
        expected_normal = original["normal"].clone()
        self.archive.load_geometry(second)
        self.archive.load_geometry(third)
        self.assertNotIn(first, self.archive._geometry_cache)

        reloaded = self.archive.load_geometry(first)
        self.assertTrue(torch.equal(reloaded["depth"], expected_depth))
        self.assertTrue(torch.equal(reloaded["normal"], expected_normal))
        self.assertLessEqual(len(self.archive._geometry_cache), 2)


if __name__ == "__main__":
    unittest.main()
