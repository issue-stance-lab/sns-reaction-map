"""Archive the completed work ledger with all of its verified evidence sources."""
from pathlib import Path
import subprocess

from scripts.archive_resolved_review_evidence import archive
from scripts.verify_editorial_hundred import read, sha
from scripts.verify_resolved_review_completion import verify
from scripts.handoff_archive_dependencies import collect_handoff_inputs, verify_handoff_manifest


def archive_handoff(root, private, shared, additional_folders=()):
    root, private, shared = (Path(p).resolve() for p in (root, private, shared))
    pilot = private / 'body-review-pilot'
    runs = [pilot / f'20260908-nonkoshitsu-cycle{i:02d}' for i in range(1, 5)]
    cycles = [(run, f'quality/reviews/2026-09-08-nonkoshitsu-cycle{i:02d}-wave.json')
              for i, run in enumerate(runs, 1)]
    short_run = pilot / '20260908-nonkoshitsu-short352'
    verified = verify(root, private, shared, cycles,
                      (short_run, 'quality/reviews/2026-09-08-nonkoshitsu-short352-wave.json'))
    prefix = '2026-09-08-nonkoshitsu4352-final'
    if read(root / 'quality/reviews' / (prefix + '-results.json')) != verified:
        raise ValueError('final saved result differs from verified evidence')
    ledger = read(root / 'data/verification/editorial-work.json')
    extras = []
    for source in ledger['sources']:
        base = root if source['storage'] == 'repository' else private
        path = (base / source['path']).resolve()
        if not path.is_relative_to(base) or sha(path) != source['sha256']:
            raise ValueError('work evidence changed before handoff archive')
        extras.append(path)
    protected = read(pilot / '20260908-finish5134-handoff/protected-before.private.json')
    extras.extend(root / rel for rel in protected)
    # Include all tracked task changes, including implementation, tests and docs.
    changed = subprocess.check_output(
        ['git', 'diff', '--name-only', '-z', 'aaadb234bc473999b603a93d8a104f8f1d70f824'], cwd=root).decode().split('\0')
    extras.extend(root / rel for rel in changed if rel and (root / rel).is_file())
    folders = [*runs, *map(Path, additional_folders)]
    for _, report in cycles:
        folders.extend(Path(s['path']) for s in read(root / report)['supplements'])
    dependencies, expected = collect_handoff_inputs(
        root, private, ledger, read(root / 'data/verification/editorial-review-scope.json'),
        [short_run, *folders], pilot / '20260908-finish5134-handoff/protected-before.private.json')
    receipt = archive(root, private, short_run, folders, prefix,
                      extra_paths=[*extras, *dependencies])
    verify_handoff_manifest(private, receipt, expected)
    return receipt
