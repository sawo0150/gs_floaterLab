#!/usr/bin/env python3
"""Build isolated DROID/LieTorch extensions that honor PyTorch's current stream.

Original shared binaries and sources are never overwritten. Add the two
resulting build directories to PYTHONPATH only for the integration runner.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path('/home/intern/VIGS-SLAM-visible-lazy-carve'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    original=args.source.resolve();root=args.output.resolve()/'source';root.mkdir()
    for folder in ('src','thirdparty/lietorch_5090/lietorch/src','thirdparty/lietorch_5090/lietorch/include'):
        shutil.copytree(original/folder,root/folder)
    changed={}
    for path in root.rglob('*.cu'):
        before=path.read_text()
        # These sources use exactly two launch parameters at all launch sites.
        launches=re.findall(r'<<<(.*?)>>>',before,flags=re.S)
        if any(len(text.split(','))!=2 for text in launches):
            raise ValueError('Unexpected launch form: '+str(path))
        after=re.sub(r'<<<(.*?)>>>',lambda m:'<<<'+m[1]+', 0, at::cuda::getCurrentCUDAStream()>>>',before,flags=re.S)
        if launches:
            after='#include <ATen/cuda/CUDAContext.h>\n'+after
            path.write_text(after)
            changed[str(path.relative_to(root))]={'launches':len(launches),
                'original_sha256':digest(original/path.relative_to(root)),
                'patched_sha256':digest(path)}
    manifest={'protocol':'explicit_pytorch_current_stream_v1','changed':changed,
        'source_root':str(original),'script_sha256':digest(Path(__file__).resolve()),
        'quality_validated':False}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    from torch.utils.cpp_extension import load
    eigen=original/'thirdparty/eigen'
    specs=[('vigs_backends',[root/'src'/n for n in
        ('vigs.cpp','vigs_kernels.cu','correlation_kernels.cu','altcorr_kernel.cu')], [eigen]),
        ('lietorch_backends',[root/'thirdparty/lietorch_5090/lietorch/src'/n for n in
        ('lietorch.cpp','lietorch_gpu.cu','lietorch_cpu.cpp')],
        [root/'thirdparty/lietorch_5090/lietorch/include',eigen])]
    outputs={}
    for name,sources,includes in specs:
        build=args.output.resolve()/name;build.mkdir()
        module=load(name=name,sources=[str(p) for p in sources],
            extra_include_paths=[str(p) for p in includes],extra_cflags=['-O2'],
            extra_cuda_cflags=['-O2'],build_directory=str(build),verbose=True)
        path=Path(module.__file__)
        outputs[name]={'path':str(path),'sha256':digest(path)}
        manifest['built']=outputs
        (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('STREAM_EXTENSIONS_BUILT',str(args.output),flush=True)


if __name__=='__main__':main()
