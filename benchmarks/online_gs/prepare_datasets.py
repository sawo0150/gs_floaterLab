"""Resumable ETH benchmark download, checksum, CRC-checked extraction.

No package installation or repository setup. Existing wget .part prefixes are
adopted only when no range-resume state exists. Keep state alongside .part.
"""
import concurrent.futures as cf
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import threading
import time
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/benchmarks'
MANIFESTS = DATA / 'manifests'
MANIFESTS.mkdir(parents=True, exist_ok=True)
DATASETS = [('rpng', 'rpngar.zip', 27989564533),
            ('utmm', 'UTMM_Dataset.zip', 22158268512)]
CHUNK = 64 * 1024 * 1024


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2))
    os.replace(tmp, path)


def prepare(item):
    name, filename, expected = item
    root = DATA / name
    raw = root / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / filename
    partial = raw / (filename + '.part')
    state_path = raw / (filename + '.resume.json')
    url = 'https://cvg-data.inf.ethz.ch/vigs-slam/' + filename
    head = requests.head(url, timeout=30)
    head.raise_for_status()
    assert int(head.headers['Content-Length']) == expected
    identity = {k: head.headers.get(k) for k in ('ETag', 'Last-Modified')}
    lock = threading.Lock()
    progress = MANIFESTS / (name + '_progress.json')
    if not archive.exists():
        if state_path.exists():
            state = json.loads(state_path.read_text())
            assert state['url'] == url and state['bytes'] == expected
            assert state['identity'] == identity, 'remote archive identity changed'
            assert partial.exists()
        else:
            prefix = partial.stat().st_size if partial.exists() else 0
            assert 0 <= prefix <= expected
            state = {'url': url, 'bytes': expected, 'identity': identity,
                     'prefix': prefix, 'completed': []}
            atomic_json(state_path, state)
        fd = os.open(partial, os.O_CREAT | os.O_RDWR, 0o644)
        done = set(state['completed'])
        inflight = {}
        ranges = [(a, min(a+CHUNK, expected)-1)
                  for a in range(state['prefix'], expected, CHUNK)]
        def save_state():
            state['completed'] = sorted(done)
            atomic_json(state_path, state)
        def transfer(pair):
            start, end = pair
            if start in done: return
            for attempt in range(6):
                try:
                    headers = {'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'}
                    if identity['ETag']: headers['If-Range'] = identity['ETag']
                    with requests.get(url, headers=headers, stream=True, timeout=(20, 45)) as r:
                        assert r.status_code == 206, f'expected range, got {r.status_code}'
                        assert r.headers.get('Content-Range') == f'bytes {start}-{end}/{expected}'
                        offset = start
                        for buf in r.iter_content(1024*1024):
                            assert offset + len(buf) <= end+1
                            view = memoryview(buf)
                            while view:
                                written = os.pwrite(fd, view, offset)
                                offset += written
                                view = view[written:]
                            with lock: inflight[start] = offset-start
                        assert offset == end+1, 'truncated response'
                    with lock:
                        # Commit completed ranges only after writing them to disk.
                        os.fdatasync(fd)
                        done.add(start)
                        inflight.pop(start, None)
                        save_state()
                    return
                except Exception:
                    with lock: inflight.pop(start, None)
                    if attempt == 5: raise
                    time.sleep(min(2**attempt, 10))
        started = time.monotonic()
        last_report = 0
        try:
            with cf.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(transfer, pair) for pair in ranges if pair[0] not in done]
                while futures:
                    complete, pending = cf.wait(futures, timeout=5, return_when=cf.FIRST_EXCEPTION)
                    for f in complete: f.result()
                    futures = list(pending)
                    with lock:
                        received = state['prefix'] + sum(min(CHUNK, expected-a) for a in done) + sum(inflight.values())
                    info = {'dataset': name, 'status': 'downloading', 'received_bytes': received,
                            'total_bytes': expected, 'percent': round(100*received/expected, 2),
                            'updated': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
                    atomic_json(progress, info)
                    if time.monotonic()-last_report > 30:
                        print(name, 'download', info['percent'], '%', flush=True)
                        last_report = time.monotonic()
            os.fsync(fd)
        finally:
            os.close(fd)
        assert partial.stat().st_size == expected
        os.replace(partial, archive)
    assert archive.stat().st_size == expected
    atomic_json(progress, {'dataset': name, 'status': 'hashing', 'total_bytes': expected})
    sha = hashlib.sha256()
    with archive.open('rb') as f:
        for buf in iter(lambda:f.read(8*1024*1024), b''): sha.update(buf)
    manifest_path = MANIFESTS / (name + '.json')
    prepared = root / 'prepared'
    if prepared.exists() and manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous.get('zip_crc_verified') and previous.get('sha256') == sha.hexdigest() and previous.get('completed'):
            atomic_json(progress, {'dataset': name, 'status': 'complete', 'sha256': sha.hexdigest()})
            print(name, 'already prepared; archive hash verified', flush=True)
            return
    manifest = {'dataset': name, 'source_url': url, 'source_identity': identity,
                'archive': str(archive.relative_to(ROOT)), 'archive_bytes': expected,
                'sha256': sha.hexdigest(), 'checksum_note': 'locally computed; publisher checksum unavailable',
                'download_complete': True, 'zip_crc_verified': False}
    atomic_json(manifest_path, manifest)
    staging = root / 'prepared.extracting'
    if prepared.exists():
        raise RuntimeError(f'{prepared} exists: verify its existing manifest before rerun')
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        expanded = sum(m.file_size for m in members)
        assert shutil.disk_usage(root).free > expanded + 100*1024**3, 'insufficient extraction headroom'
        for m in members:
            p = Path(m.filename)
            assert not p.is_absolute() and '..' not in p.parts, 'unsafe zip member'
            assert not stat.S_ISLNK(m.external_attr >> 16), 'symlink member needs explicit review'
        atomic_json(progress, {'dataset': name, 'status': 'extracting', 'expanded_bytes': expanded,
                               'files_total': len(members), 'files_done': 0})
        staging.mkdir(exist_ok=True)
        for i, m in enumerate(members):
            # zipfile checks each member CRC while extracting it.
            z.extract(m, staging)
            if i % 1000 == 0:
                atomic_json(progress, {'dataset': name, 'status': 'extracting', 'expanded_bytes': expanded,
                                       'files_total': len(members), 'files_done': i+1})
        manifest.update({'expanded_bytes': expanded, 'zip_members': len(members),
                         'zip_crc_verified': True,
                         'top_level_members': sorted({Path(m.filename).parts[0] for m in members if Path(m.filename).parts})})
    os.replace(staging, prepared)
    manifest.update({'prepared': str(prepared.relative_to(ROOT)),
                     'completed': time.strftime('%Y-%m-%dT%H:%M:%S%z')})
    atomic_json(manifest_path, manifest)
    atomic_json(progress, {'dataset': name, 'status': 'complete', 'sha256': sha.hexdigest()})
    print(name, 'COMPLETE', json.dumps(manifest), flush=True)


if __name__ == '__main__':
    with cf.ThreadPoolExecutor(max_workers=2) as executor:
        tasks = {executor.submit(prepare, item): item[0] for item in DATASETS}
        errors = []
        for future in cf.as_completed(tasks):
            try: future.result()
            except Exception as e:
                errors.append([tasks[future], repr(e)])
                print('FAILED', tasks[future], repr(e), flush=True)
        if errors:
            atomic_json(MANIFESTS/'errors.json', errors)
            raise SystemExit(1)
