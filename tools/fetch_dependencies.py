#!/usr/bin/env python3
"""Fetch exact source revisions. Existing unexpected worktrees are not replaced."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = {
    'pico-sdk': ('https://github.com/raspberrypi/pico-sdk.git',
                 '079c6f39023649b154152db30f1d781e884879bc'),
    'pico-extras': ('https://github.com/raspberrypi/pico-extras.git',
                   '52fd7a786ce47c989afeaee67e0c6aebee56ed2d'),
}

def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()

for name, (url, revision) in DEPENDENCIES.items():
    dest = ROOT / '.deps' / name
    if not dest.exists():
        dest.mkdir(parents=True)
        run('git', 'init', str(dest))
        run('git', 'remote', 'add', 'origin', url, cwd=dest)
        run('git', 'fetch', '--depth', '1', 'origin', revision, cwd=dest)
        run('git', 'checkout', '--detach', revision, cwd=dest)
    actual = run('git', 'rev-parse', 'HEAD', cwd=dest)
    if actual != revision or run('git', 'status', '--porcelain', '--untracked-files=no', cwd=dest):
        raise SystemExit(f'{dest}: unexpected revision or modifications; review manually')
    if name == 'pico-sdk':
        run('git', 'submodule', 'update', '--init', 'lib/tinyusb', cwd=dest)
    print(f'{name}: {actual}')
