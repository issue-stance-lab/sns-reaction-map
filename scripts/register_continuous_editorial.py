"""Publish body-free run records locally, preserving the initial adoption ledger."""
import argparse
from collections import Counter
from pathlib import Path
from scripts.verify_continuous_editorial import collect_run, combine
from scripts.editorial_work_registry import load_registry, build_registry
from scripts.verify_editorial_hundred import read, sha, dump

NEW_REPORT = 'quality/reviews/2026-09-07-next1000-sol.json'
CURRENT = 'data/verification/editorial-adoption-current.json'


def current_view(root, base, run):
    combined, _ = combine(root, base, run)
    return {'schema_version': 1, 'scope': 'Current combined editorial adoption; canonical application and legacy reread credit remain separate.',
            'reviewed_records': 2000, 'counts': combined['adoption_counts'],
            'sources': [{'path': 'data/verification/editorial-adoption.json', 'sha256': sha(Path(root) / 'data/verification/editorial-adoption.json')},
                        {'path': NEW_REPORT, 'sha256': sha(Path(root) / NEW_REPORT)}],
            'records': combined['journal'], 'canonical_applied': 0, 'registered_reread_increment': 0}


def register(root, base, run):
    root, base, run = Path(root), Path(base), Path(run)
    aggregate, _ = collect_run(root, run)
    report = root / NEW_REPORT
    if report.exists() and read(report) != aggregate:
        raise ValueError('run report differs; do not overwrite evidence')
    dump(report, aggregate)
    private = base.parent
    work_path = root / 'data/verification/editorial-work.json'
    work = load_registry(work_path, root, private); sources = work['sources'][:]
    def add(path, storage, kind):
        rel = str(path.relative_to(root if storage == 'repository' else private))
        value = {'path': rel, 'storage': storage, 'kind': kind, 'sha256': sha(path)}
        old = next((r for r in sources if r['path'] == rel and r['storage'] == storage), None)
        if old is not None and old != value:
            raise ValueError('work evidence changed')
        if old is None: sources.append(value)
    add(report, 'repository', 'journal')
    for n in range(1, 51):
        for name in ['editor.private.json', 'audit.private.json', 'quality_gate.private.json', 'editor-flags.private.json']:
            add(run / f'batch-{n:02d}' / name, 'private', 'evidence')
    updated = build_registry(sources, root, private)
    if len(updated['records']) != 2080 or updated['counts'].get('attempted') != 80:
        raise ValueError('work registry final coverage mismatch')
    view = current_view(root, base, run)
    dump(work_path, updated); dump(root / CURRENT, view)
    load_registry(work_path, root, private)
    if read(root / CURRENT) != current_view(root, base, run):
        raise ValueError('combined adoption view does not replay')
    return view


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'base', 'run']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); value = register(a.root, a.base, a.run)
    print(value['reviewed_records'], value['counts'])
