import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import selected_mapping_check as check
from run_selected_mapping import recipe_args


class SelectedReleaseTests(unittest.TestCase):
    def test_adopted_recipe(self):
        args = recipe_args()
        expected = {'--renders-per-kf': '40', '--kappa': '16', '--tau': '4',
                    '--selector': 'ervs', '--selection-count-scope': 'all_rgb',
                    '--optimizer-batch-size': '1', '--birth-downsample-multiplier': '0.8',
                    '--prune-opacity-threshold': '0.1', '--prune-every-renders': '300'}
        for flag, value in expected.items():
            self.assertEqual(args[args.index(flag) + 1], value)
        i = args.index('--batch-quotas') + 1
        self.assertEqual(args[i:i+3], ['3', '3', '6'])

    def test_changed_or_missing_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'worker.py'
            p.write_text('original')
            files = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()}
            check.verify_files(files)
            p.write_text('different setting')
            with self.assertRaisesRegex(RuntimeError, 'changed:'):
                check.verify_files(files)
            p.unlink()
            with self.assertRaisesRegex(RuntimeError, 'missing:'):
                check.verify_files(files)

    def test_busy_gpu_is_rejected_without_killing_processes(self):
        with patch.object(check.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '123, other_job\n')) as run:
            with self.assertRaisesRegex(RuntimeError, 'GPU is in use'):
                check.gpu_idle()
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][0], 'nvidia-smi')

    def test_idle_gpu_is_accepted(self):
        with patch.object(check.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '')):
            check.gpu_idle()


if __name__ == '__main__':
    unittest.main()
