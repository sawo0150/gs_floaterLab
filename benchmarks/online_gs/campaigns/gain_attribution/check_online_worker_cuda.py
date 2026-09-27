#!/usr/bin/env python3
"""CUDA integration check on the first causal native packet, NOT a quality run.

Uses captured native configuration and birth calibration unchanged. The fixed
number of test steps only exercises wiring; it is not a mapping/topology phase
policy and must not be used as evidence of online PSNR or convergence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import threading
import time
import traceback
from types import SimpleNamespace

import run_online_dense_training as trial


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--setup',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--membership',choices=['kf_only','growth'],default='growth')
    parser.add_argument('--stream',choices=['owned','default'],default='owned',
                        help='Default stream is a diagnostic control, not the live policy')
    parser.add_argument('--extensions',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    if args.extensions is not None:
        for name in ('vigs_backends','lietorch_backends'):
            sys.path.insert(0,str((args.extensions/name).resolve()))
    import numpy as np
    import torch
    from exp78b_frozen_archive import FrozenTrackerArchive
    from exp78b_dense_imu_pose import load_processed_imu
    import exp78b_replay_gsslam_mapping as replay
    from gs_backend import GSBackEnd
    from online_mapper_runtime import OnlineMapperRuntime
    from vigs import VIGS
    import vigs_backends, lietorch_backends
    binaries={m.__name__:{'path':m.__file__,
        'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
        for m in (vigs_backends,lietorch_backends)}
    if args.extensions is not None:
        expected=json.loads((args.extensions/'manifest.json').read_text())['built']
        if binaries!=expected:raise RuntimeError('Current-stream extension selection failed')
    setup=torch.load(args.setup/'native_setup.pt',weights_only=False,map_location='cpu')
    provenance=json.loads((args.setup/'provenance.json').read_text())
    if hashlib.sha256((args.setup/'native_setup.pt').read_bytes()).hexdigest()!=provenance['setup_sha256']:
        raise ValueError('Setup source changed')
    archive=FrozenTrackerArchive(trial.BASE.sequence_paths(provenance['dataset'],provenance['scene'])['archive'])
    config=setup['config']; native_args=SimpleNamespace(**setup['args'])
    # Same fixed sensor calibration as the recipe, no evaluator trajectory.
    native_args.imus=load_processed_imu(Path(archive.manifest['input_imu']),config)
    random.seed(0);np.random.seed(0);torch.manual_seed(0);torch.cuda.manual_seed_all(0)
    density=replay.configure_density_policy(config,'online_rank',2.5,2.0)[1]
    replay.install_online_density_policy(density)
    started=time.monotonic()
    mapper=GSBackEnd(config,str(args.output),native_args,use_gui=False)
    host=SimpleNamespace(gs=mapper,args=native_args,config=config,
        _gs_stream=(torch.cuda.Stream() if args.stream=='owned' else torch.cuda.default_stream()),
        _tracking_active=threading.Event(),
        _replay_next_arrival_deadline=None)
    host._tracking_active.set()
    runtime=OnlineMapperRuntime(host,{'membership':args.membership,'heldout':archive.heldout_uids})
    host._online_runtime=runtime
    # Model/pose-network construction occurs on the producer stream.
    ready=torch.cuda.Event();ready.record(torch.cuda.current_stream())
    host._gs_stream.wait_event(ready)
    metadata=archive.events[0]
    if metadata['kind']!='keyframe_update':raise ValueError('Expected a first native update fixture')
    latest=int(metadata['emitted_at_frame_uid'])
    for record in archive.arrivals:
        uid=int(record['frame_uid'])
        if uid>latest:break
        image=(torch.empty(0) if uid in archive.heldout_uids else archive.load_rgb(uid))
        runtime.observe_rgb(uid,float(record['sensor_timestamp']),image)
    packet=archive.mapping_packet(metadata,filter_heldout=True)
    event=torch.cuda.Event();event.record(torch.cuda.current_stream());packet['_producer_event']=event
    # Finish on the owning worker only after the last test optimizer has completed.
    real_idle=runtime.idle
    def checked_idle():
        result=real_idle()
        if runtime.mapper.online_view_trainer.policy.rgb_steps_completed>=1024:
            runtime.close()
        return result
    runtime.worker.idle=checked_idle
    thread=threading.Thread(target=VIGS._gs_worker,args=(host,),daemon=True)
    future=runtime.worker.submit(packet);thread.start()
    error=None
    try:
        future.result(timeout=60)
        host._tracking_active.clear()
        while thread.is_alive():
            thread.join(1)
            if time.monotonic()-started>120:
                raise TimeoutError('CUDA integration check exceeded its test watchdog')
        runtime.worker.raise_on_error()
        if runtime.mapper.online_view_trainer.policy.rgb_steps_completed<1024:
            raise AssertionError('Common training did not complete test steps')
        if runtime.guard.overruns:raise AssertionError('Late optimizer completion')
        if args.membership=='growth' and not mapper.polish_viewpoints:
            raise AssertionError('Dense preparation was never exercised')
        for name in ('_xyz','_scaling','_rotation','_opacity','_features_dc','_features_rest'):
            if not torch.isfinite(getattr(mapper.gaussians,name)).all():
                raise AssertionError('Nonfinite Gaussian parameters: '+name)
    except BaseException:
        error=traceback.format_exc()
    finally:
        runtime.close();thread.join(10)
        report=runtime.report()
        report.update({'check':'first_causal_packet_cuda_integration','membership':args.membership,
            'stream':args.stream,
            'extension_binaries':binaries,
            'elapsed_seconds':time.monotonic()-started,'passed':error is None,
            'error_traceback':error,'thread_alive':thread.is_alive(),
            'gaussians':int(mapper.gaussians.get_xyz.shape[0]),
            'native_view_uids':sorted(mapper.viewpoints),'dense_view_uids':sorted(mapper.polish_viewpoints),
            'visual_pose_audit':getattr(mapper,'_visual_pose_audit',None),
            'first_event_metadata':metadata,'quality_validated':False,'whole_stream_validated':False,
            'setup_sha256':provenance['setup_sha256']})
        (args.output/'result.json').write_text(json.dumps(report,indent=2,default=str))
    print('CUDA_CHECK',args.membership,'PASS' if error is None else 'FAIL',flush=True)
    if error:raise RuntimeError(error)


if __name__=='__main__':main()
