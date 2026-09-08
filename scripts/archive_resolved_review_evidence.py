"""Archive completed cycle evidence and verify every restored byte."""
import json
from pathlib import Path
import tarfile
import tempfile
import time

from scripts.verify_editorial_hundred import sha, dump


def archive(root, private, run, supplements, prefix):
    root, private, run = (Path(p).resolve() for p in (root, private, run))
    dest = private / 'body-review-archives' / prefix
    if dest.exists():
        raise ValueError('never overwrite an evidence archive')
    paths = {}
    for folder in [run, *map(Path, supplements)]:
        for path in folder.rglob('*'):
            if path.is_file():
                paths['private/' + str(path.relative_to(private))] = path
    integrity = run / 'decision-code-integrity.private.json'
    if integrity.exists():
        for rel, expected in json.loads(integrity.read_text())['code_sha256'].items():
            if sha(root / rel) != expected:
                raise ValueError('decision code changed before archive')
            paths['repository/' + rel] = root / rel
    for path in [root / 'data/verification/editorial-work.json',
                 root / 'data/verification/editorial-review-scope.json',
                 *sorted((root / 'quality/reviews').glob(prefix + '*')),
                 *sorted((root / 'scripts').glob('*resolved*review*.py')),
                 *sorted((root / 'scripts').glob('*short*resolved*.py')),
                 root / 'scripts/finalize_resolved_review_cycle.py']:
        paths['repository/' + str(path.relative_to(root))] = path
    manifest = {rel: sha(path) for rel, path in sorted(paths.items())}
    dest.mkdir(parents=True)
    dump(dest / 'manifest.private.json', manifest)
    output = dest / 'evidence.tar.gz'
    with tarfile.open(output, 'w:gz') as tar:
        tar.add(dest / 'manifest.private.json', arcname='manifest.private.json')
        for rel, path in sorted(paths.items()):
            tar.add(path, arcname=rel, recursive=False)
    with tempfile.TemporaryDirectory(dir=dest) as tmp:
        with tarfile.open(output, 'r:gz') as tar:
            tar.extractall(tmp, filter='data')
        restored = json.loads((Path(tmp) / 'manifest.private.json').read_text())
        if restored != manifest or any(sha(Path(tmp) / rel) != h for rel, h in manifest.items()):
            raise ValueError('restored evidence differs')
    if any(sha(path) != manifest[rel] for rel, path in paths.items()):
        raise ValueError('source changed during archive')
    receipt = {'recorded_epoch': time.time(), 'file_count': len(manifest),
               'archive': str(output.relative_to(private)), 'archive_sha256': sha(output),
               'manifest_sha256': sha(dest / 'manifest.private.json'),
               'restored_files_verified': len(manifest), 'restore_verified': True}
    dump(dest / 'receipt.private.json', receipt)
    dump(root / 'quality/reviews' / (prefix + '-archive.json'), receipt)
    return receipt
