"""Preflight for the adopted fixed40 replay; no CUDA imports or silent overrides."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[3]


def load_lock():
    return json.loads((HERE / 'selected_release/source_lock.json').read_text())


def verify_files(files):
    failures = []
    for name, expected in files.items():
        path = Path(name)
        if not path.is_absolute():
            path = WORKSPACE / path
        if not path.is_file():
            failures.append('missing: ' + str(path))
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append('changed: ' + str(path))
    if failures:
        raise RuntimeError('Selected recipe dependency mismatch:\n' + '\n'.join(failures))


def preflight(setup, extensions, output):
    lock = load_lock()
    if Path(sys.prefix).resolve() != Path(lock['python_prefix']).resolve():
        raise RuntimeError('Use ' + lock['python_prefix'] + '/bin/python')
    if output.exists():
        raise RuntimeError('Output must be a new directory: ' + str(output))
    verify_files(lock['sources'])
    provenance = json.loads((setup / 'provenance.json').read_text())
    expected = lock['datasets'].get(provenance['dataset'])
    if not expected or provenance['scene'] != expected['scene']:
        raise RuntimeError('This release supports only the three pinned replay scenes')
    if setup.resolve() != Path(expected['setup']).resolve():
        raise RuntimeError('Use the pinned setup: ' + expected['setup'])
    if extensions.resolve() != Path(lock['extensions']).resolve():
        raise RuntimeError('Use the pinned CUDA extensions: ' + lock['extensions'])
    verify_files(expected['files'])
    verify_files(lock['extension_files'])
    for name in expected['required_paths']:
        if not Path(name).exists():
            raise RuntimeError('Missing dataset/archive input: ' + name)
    return provenance


def gpu_idle():
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name',
                             '--format=csv,noheader'], check=True, capture_output=True, text=True)
    if result.stdout.strip():
        raise RuntimeError('GPU is in use; retry after it becomes idle. No process was stopped.\n' + result.stdout)
