"""Opt-in relocation of Colin paths; never change locked mapper source or data.

Activate with ROGO_MACHINE_PROFILE=/absolute/profile.json and put this directory
on PYTHONPATH. Children inherit the same profile even when runners replace their
PYTHONPATH. The JSON contains explicit old/new prefix pairs, longest first.
"""
import builtins
import json
import os
import pathlib
import subprocess

_profile = os.environ.get("ROGO_MACHINE_PROFILE")
if _profile:
    with open(_profile) as _stream:
        _config = json.load(_stream)
    _pairs = sorted(_config["path_prefixes"].items(), key=lambda p: -len(p[0]))
    _hook_dir = os.path.dirname(__file__)

    def relocate(value):
        if not isinstance(value, str):
            return value
        for old, new in _pairs:
            if value == old or value.startswith(old + "/"):
                return new + value[len(old):]
        return value

    _path_new = pathlib.Path.__new__

    def path_new(cls, *args, **kwargs):
        return _path_new(cls, *(relocate(os.fspath(a)) for a in args), **kwargs)

    pathlib.Path.__new__ = path_new
    _open = builtins.open

    def relocated_open(file, *args, **kwargs):
        return _open(relocate(file), *args, **kwargs)

    builtins.open = relocated_open
    _json_loads = json.loads

    def metadata_paths(value):
        if isinstance(value, dict):
            return {relocate(k): metadata_paths(v) for k, v in value.items()}
        if isinstance(value, list):
            return [metadata_paths(v) for v in value]
        return relocate(value)

    def relocated_loads(*args, **kwargs):
        # Binary provenance compares imported module paths with manifest paths.
        # Translate those path strings in memory; hashes and files stay intact.
        return metadata_paths(_json_loads(*args, **kwargs))

    json.loads = relocated_loads
    _popen_init = subprocess.Popen.__init__

    def popen_init(self, args, *positional, **kwargs):
        if isinstance(args, (list, tuple)):
            args = [relocate(os.fspath(a)) if isinstance(a, os.PathLike) else relocate(a) for a in args]
        if "cwd" in kwargs:
            kwargs["cwd"] = relocate(kwargs["cwd"])
        env = dict(kwargs.get("env") or os.environ)
        env["ROGO_MACHINE_PROFILE"] = _profile
        paths = [relocate(p) for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]
        env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys([_hook_dir, *paths]))
        kwargs["env"] = env
        return _popen_init(self, args, *positional, **kwargs)

    subprocess.Popen.__init__ = popen_init
