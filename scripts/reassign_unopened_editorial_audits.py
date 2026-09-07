#!/usr/bin/env python3
"""Move audits for unopened waves to one independent actor with an immutable history."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

try:
    from scripts.verify_editorial_hundred import dump, read, sha
except ModuleNotFoundError:
    from verify_editorial_hundred import dump, read, sha


def reassign(run: Path, waves: list[int], actor: str, worktree: Path) -> dict:
    run, worktree = run.resolve(), worktree.resolve()
    top_path = run / 'reservation.json'
    top = read(top_path)
    history_dir = run / 'assignment-history'
    if history_dir.exists():
        raise ValueError('assignment history already exists')
    if not worktree.is_dir():
        raise ValueError('auditor worktree is missing')
    originals = {}
    changed = {}
    for wave_number in waves:
        name = f'wave-{wave_number:02d}'
        folder = run / name
        reservation_path = folder / 'reservation.json'
        if sha(reservation_path) != top['waves'][name]:
            raise ValueError('top-level wave hash mismatch: ' + name)
        if list(folder.glob('batch-*/*-actor.private.json')):
            raise ValueError('cannot reassign an opened wave: ' + name)
        reservation = read(reservation_path)
        if actor in reservation['assignments']['editor']:
            raise ValueError('auditor cannot edit the same wave')
        originals[name] = reservation

    history_dir.mkdir()
    dump(history_dir / 'top-before.private.json', top)
    for name, reservation in originals.items():
        dump(history_dir / f'{name}-before.private.json', reservation)
        reservation['assignments']['audit'] = {actor: list(range(1, 51))}
        reservation['worktrees'][actor] = str(worktree)
        reservation['audit_assignment_updated_epoch'] = time.time()
        reservation['audit_assignment_reason'] = 'Add a third independent auditor before this wave is opened; editor assignments are unchanged.'
        path = run / name / 'reservation.json'
        dump(path, reservation)
        changed[name] = {
            'before_sha256': sha(history_dir / f'{name}-before.private.json'),
            'after_sha256': sha(path),
        }
        top['waves'][name] = changed[name]['after_sha256']
    record = {
        'schema_version': 1,
        'recorded_epoch': time.time(),
        'top_before_sha256': sha(history_dir / 'top-before.private.json'),
        'waves': changed,
        'auditor': actor,
        'worktree': str(worktree),
        'scope': 'Audit assignment only. No packet, editor assignment, body, criteria, or decision changed.',
    }
    dump(history_dir / 'change.private.json', record)
    top['assignment_history_sha256'] = sha(history_dir / 'change.private.json')
    dump(top_path, top)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--wave', type=int, action='append', required=True)
    parser.add_argument('--actor', required=True)
    parser.add_argument('--worktree', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(reassign(args.run, args.wave, args.actor, args.worktree), ensure_ascii=False))
