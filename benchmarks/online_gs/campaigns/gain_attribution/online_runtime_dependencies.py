#!/usr/bin/env python3
"""Fingerprint resolved native libraries without importing Torch or allocating CUDA."""
import argparse
import hashlib
from importlib import machinery, metadata, util
import json
from pathlib import Path
import sys


def native_paths():
    paths = {}
    for name in ('vigs_backends', 'lietorch_backends'):
        spec = util.find_spec(name)
        if spec is None or spec.origin is None:
            raise RuntimeError(f'Native dependency unavailable: {name}')
        paths[name] = Path(spec.origin).resolve()
    # PathFinder inspects the extension directory; importing the parent package
    # here would import Torch and potentially warm up the runtime before timing.
    for name in ('diff_gaussian_rasterization', 'simple_knn'):
        package = util.find_spec(name)
        if package is None or not package.submodule_search_locations:
            raise RuntimeError(f'Native package unavailable: {name}')
        extension = machinery.PathFinder.find_spec('_C', package.submodule_search_locations)
        if extension is None or extension.origin is None:
            raise RuntimeError(f'Native extension unavailable: {name}._C')
        paths[name + '._C'] = Path(extension.origin).resolve()
    return paths


def fingerprint():
    files = {}
    for name, path in native_paths().items():
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        files[name] = {'path': str(path), 'sha256': digest, 'bytes': path.stat().st_size}
    packages = {}
    for name in ('torch', 'torchvision', 'numpy', 'scipy', 'opencv-python', 'plyfile', 'lpips'):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    return {'protocol': 'online_native_dependencies_v1', 'python': sys.version,
            'executable': sys.executable, 'files': files, 'packages': packages,
            'torch_imported_by_probe': 'torch' in sys.modules}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = fingerprint()
    if result['torch_imported_by_probe']:
        raise RuntimeError('Dependency probe unexpectedly imported Torch')
    text = json.dumps(result, indent=2) + '\n'
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')
