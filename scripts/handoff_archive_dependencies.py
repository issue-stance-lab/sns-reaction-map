"""Pin handoff dependencies before archiving and compare the finished manifest.

Only metadata and file hashes are inspected. No body judgments or review credit
are generated. The returned expected hashes must survive unchanged until verify.
"""
from pathlib import Path
import subprocess

from scripts.editorial_work_registry import resolve_source
from scripts.verify_editorial_hundred import read, sha


def collect_handoff_inputs(root, private, ledger, scope_summary, folders, protected_path, additional_sources=()):
    root, private = Path(root).resolve(), Path(private).resolve()
    paths, expected = {}, {}

    def pin(path, digest=None):
        path = Path(path).resolve()
        if path.is_relative_to(root):
            relative = 'repository/' + str(path.relative_to(root))
        elif path.is_relative_to(private):
            relative = 'private/' + str(path.relative_to(private))
        else:
            raise ValueError('handoff dependency escapes repository/private roots')
        if not path.is_file():
            raise ValueError('missing handoff dependency: ' + relative)
        actual = sha(path)
        if digest is not None and digest != actual:
            raise ValueError('pinned handoff dependency changed: ' + relative)
        digest = actual if digest is None else digest
        if relative in expected and expected[relative] != digest:
            raise ValueError('conflicting handoff dependency hashes')
        paths[relative], expected[relative] = path, digest

    # Keep the exact snapshots whose source lists and scope were just validated.
    for relative, snapshot in (('data/verification/editorial-work.json', ledger),
                               ('data/verification/editorial-review-scope.json', scope_summary)):
        path = root / relative
        digest = sha(path)
        if read(path) != snapshot:
            raise ValueError('handoff registry/scope changed before collection')
        pin(path, digest)
    for source in ledger['sources']:
        path = resolve_source(source, root, private)
        pin(path, source['sha256'])
        if source['kind'] == 'packet':
            for criteria in read(path)['criteria'].values():
                dependency = {'storage': 'repository', 'path': criteria['source'],
                              'sha256': criteria['source_sha256']}
                pin(resolve_source(dependency, root, private), dependency['sha256'])
    # Fresh public-inventory checks also depend on older, limited-review evidence
    # that may never have been a source of the newer work ledger.
    for source in additional_sources:
        pin(resolve_source(source, root, private), source['sha256'])
    resolution = {'storage': 'private', 'path': scope_summary['resolution_path'],
                  'sha256': scope_summary['resolution_sha256']}
    pin(resolve_source(resolution, root, private), resolution['sha256'])
    protected_path = Path(protected_path).resolve()
    if not protected_path.is_relative_to(private):
        raise ValueError('protected manifest must be private')
    pin(protected_path)
    for relative, digest in read(protected_path).items():
        dependency = {'storage': 'repository', 'path': relative, 'sha256': digest}
        pin(resolve_source(dependency, root, private), digest)
    for relative in ('THEMES.yaml', 'quality/designs/body-review/CYCLE_2000_RUNBOOK.md',
                     'quality/designs/body-review/POLICY_STANCE_MAPPING_V3.md'):
        pin(root / relative)
    # Unchanged modules are needed by transitive Python imports after restoration.
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts'], cwd=root)
    for relative in tracked.decode().split('\0'):
        if relative.endswith('.py'):
            pin(root / relative)
    for folder in map(Path, folders):
        folder = folder.resolve()
        if not folder.is_relative_to(private) or not folder.is_dir():
            raise ValueError('missing or nonprivate handoff folder')
        for path in folder.rglob('*'):
            if path.is_file():
                pin(path)
    return [paths[key] for key in sorted(paths)], dict(sorted(expected.items()))


def verify_handoff_manifest(private, receipt, expected):
    """Call after archive returns; never reconstruct expected hashes from disk."""
    private = Path(private).resolve()
    archive = (private / receipt['archive']).resolve()
    if not archive.is_relative_to(private) or not archive.is_file() or sha(archive) != receipt['archive_sha256']:
        raise ValueError('handoff archive missing or changed')
    manifest = archive.parent / 'manifest.private.json'
    if not manifest.is_file() or sha(manifest) != receipt['manifest_sha256']:
        raise ValueError('handoff manifest missing or changed')
    restored = read(manifest)
    if any(restored.get(relative) != digest for relative, digest in expected.items()):
        raise ValueError('archive manifest differs from pre-archive dependency pins')
    if (receipt.get('restore_verified') is not True or receipt['file_count'] != len(restored) or
            receipt['restored_files_verified'] != len(restored)):
        raise ValueError('handoff restore coverage differs')
    return {'pinned_dependencies_verified': len(expected), 'manifest_files': len(restored)}
