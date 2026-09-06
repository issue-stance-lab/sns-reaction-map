#!/usr/bin/env python3
"""Inventory existing evidence only; no collection, rereading, classification or publishing.

All ID sets are strings, intersected with the current canonical opinion population.
Source.ids retains the original evidence population, including non-opinions and
out-of-canonical records. Output contains private IDs and MUST stay outside Git.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

BASE = '565e76bb2590bdcab29c79098780b9e8fd4233b7'
FILES = {
    'elderly-license-revocation': ('social-samples/elderly-license_2d_classified.json', 'f3d2af2d961b9ca6358b75a651e89379e83d2a20c1cf3477daae878aa64a4836'),
    'ai-copyright': ('social-samples/ai-copyright_hermes_classified.json', '66b304bec266758a31cc55c6761d05ed0cdf4f506d6b44cab070cdae2c208098'),
    'school-nickname-ban': ('social-samples/school-nickname-ban_hermes_arena_classified.json', '85c9bc0dc54742d576a035bc6ae1e282497cfd1c32028d61055ae81deaccd3d2'),
    'henoko-student-accident': ('social-samples/henoko/henoko_hermes_arena_classified.json', '3cca77f41e89b60a6a2a9057d6242bd8e149f72150d6ef739d268f38ad8400c2'),
}
KINDS = ['editorial_main_ids', 'editorial_all_ids', 'planet_connected_main_ids',
         'planet_connected_any_ids', 'focused_body_review_ids', 'classification_review_ids',
         'claim_mapping_ids']

def sha(b):
    return hashlib.sha256(b).hexdigest()

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--backup', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    assert a.output.resolve() != a.root.resolve()
    for theme in FILES:
        assert not (a.output / (theme + '.json')).exists(), 'Refuse overwrite'

    # Read all local branch file inventories, and actual worktree data/config files.
    # Save fixed ref/commit and content hashes so later branch moves are visible.
    scan = {'baseline_commit': BASE, 'branches': [], 'worktrees': [], 'candidates': []}
    refs = git(a.root, 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads').decode().splitlines()
    for row in refs:
        ref, commit = row.split()
        scan['branches'].append({'ref': ref, 'commit': commit})
        paths = git(a.root, 'ls-tree', '-r', '--name-only', commit).decode().splitlines()
        for path in paths:
            if any(t in path for t in ['elderly', 'copyright', 'nickname', 'henoko']) and (
                    'reread' in path or 'claim_posts' in path or path.startswith('configs/planet/')):
                blob = git(a.root, 'show', commit + ':' + path)
                scan['candidates'].append({'git_ref': commit, 'path': path, 'sha256': sha(blob)})
        for theme in FILES:
            assert 'configs/planet/' + theme + '.yaml' not in paths, 'New connection requires review'
    for row in git(a.root, 'worktree', 'list', '--porcelain').decode().splitlines():
        if not row.startswith('worktree '):
            continue
        wt = Path(row[9:])
        scan['worktrees'].append(str(wt))
        for sub in ['data', 'configs/planet', 'quality/reviews']:
            folder = wt / sub
            if not folder.exists():
                continue
            for path in folder.rglob('*'):
                if path.is_file() and any(t in path.name for t in ['elderly', 'copyright', 'nickname', 'henoko']) and (
                        'reread' in path.name or 'claim_posts' in path.name or sub == 'configs/planet'):
                    scan['candidates'].append({'git_ref': None, 'path': str(path), 'sha256': sha(path.read_bytes())})
        for theme in FILES:
            assert not (wt / 'configs/planet' / (theme + '.yaml')).exists(), 'New worktree connection requires review'
    dump(a.output / 'four-theme-scan.json', scan)

    for theme, (canon, expected) in FILES.items():
        raw = (a.root / canon).read_bytes()
        assert sha(raw) == expected, 'Canonical input changed'
        rows = json.loads(raw)
        byid = {str(r['tweet_id']): r for r in rows}
        assert len(byid) == len(rows)
        opinions = {i for i, r in byid.items() if r['classification'].get('is_relevant') is not False
                    and r['classification'].get('is_opinion') is not False}
        sets = {k: set() for k in KINDS}
        sources = []
        caveats = ['No new body reading or classification was performed by this inventory.',
                   'No human review confirmation found. Reader identities below describe existing AI records.',
                   'Absence of records is not proof that nobody has read a post.',
                   'Existing 2D automated classification/display is not a connection to the new planet page.',
                   'Reader labels from commit co-author metadata are attribution evidence, not runtime attestation.']

        def source(path, kind, method, reader, ids=(), ref=None, notes='', bodies=None):
            p = Path(path)
            content = git(a.root, 'show', ref + ':' + str(path)) if ref else p.read_bytes()
            ids = {str(x) for x in ids}
            item = {'path': str(path), 'git_ref': ref, 'sha256': sha(content), 'kind': kind,
                    'method': method, 'reader': reader, 'ids': sorted(ids), 'notes': notes,
                    'canonical_opinions': len(ids & opinions),
                    'canonical_non_opinions': len((ids & byid.keys()) - opinions),
                    'outside_canonical': len(ids - byid.keys())}
            if bodies is not None:
                checked = ids & byid.keys() & bodies.keys()
                equal = {i for i in checked if sha(byid[i]['text'].encode()) == bodies[i]}
                assert equal == checked, 'Current body differs from evidence'
                item['body_verification'] = {'equal': len(equal), 'unavailable': len(ids & byid.keys() - checked),
                    'scope': 'Exact UTF-8 text SHA-256; snapshots establish body version, not independent proof of reading.'}
            sources.append(item)
            return ids & opinions

        # Private source path must point at the actual shared root, not an unpopulated worktree.
        source(a.root / canon, 'canonical_population', 'THEMES.yaml sample_file; classification flags are not False', 'not_applicable', byid.keys())
        source('scripts/build_planet_data.py', 'connection_logic', 'sub_issues reads sc.file/sc.path and source_file; no target config exists', 'not_applicable', ref=BASE)
        if theme == 'elderly-license-revocation':
            p = 'data/elderly-license_issues-reread.json'
            d = json.loads(git(a.root, 'show', BASE + ':' + p))
            old = json.loads(git(a.root, 'show', '5da3a48:' + canon))
            bodies = {str(r['tweet_id']): sha(r['text'].encode()) for r in old}
            ids = source(p, 'full_body_editorial_reread', d['method'], 'AI: Claude Sonnet 5 (e0e7e7d co-author)',
                         [r['tweet_id'] for r in d['items']], BASE,
                         'tasks/task-54.md stage 10-2a explicitly records all 250 text bodies read; 221 + 29 issue coverage.', bodies)
            sets['editorial_main_ids'] |= ids
            sets['editorial_all_ids'] |= ids
            source(canon, 'body_version_snapshot', 'Pre-reread snapshot compared exactly to current text', 'not_applicable', ids, '5da3a48')
            source('tasks/task-54.md', 'editorial_procedure_evidence', 'Stage 10-2a all 250 text bodies individually read', 'AI: Claude Sonnet 5', ids, BASE)
            p = 'data/elderly-license-revocation_claim_posts.json'
            claims = json.loads(git(a.root, 'show', BASE + ':' + p))
            old = json.loads(git(a.root, 'show', '24b6749:' + canon))
            bodies = {str(r['tweet_id']): sha(r['text'].encode()) for r in old}
            claimids = {str(i) for v in claims['claims'].values() for i in v}
            sets['focused_body_review_ids'] |= source(p, 'focused_body_review', claims['method'],
                 'AI: Claude Opus 5 (bc5b39e / 24b6749 co-author)', claimids, BASE,
                 '38 IDs mapped to claims after individual body confirmation; not claim_mapping_only.', bodies)
            wave = a.root / 'social-samples/updates/elderly-license-revocation/2026-08-20/classified.json'
            wave_rows = json.loads(wave.read_bytes())
            assert len(wave_rows) == 30
            waveids = {str(r['tweet_id']) for r in wave_rows}
            assert all(i in bodies for i in waveids)
            sets['focused_body_review_ids'] |= source(wave, 'focused_body_review',
                'Claim review record and commit 24b6749 explicitly say all 30 newly added posts were individually read.',
                'AI: Claude Opus 5 (24b6749 co-author)', waveids,
                notes='Saved 2026-08-20 classified wave provides target IDs; report new=classified=30. 6 claims overlap, union=62.', bodies=bodies)
            source('data/verification/updates/elderly-license-revocation/2026-08-20/report.json', 'scope_evidence',
                   'new=classified=30 links the full increment to the explicit reading record', 'not_applicable', waveids, BASE)
            source(canon, 'body_version_snapshot', 'Claim update snapshot; text equals latest canonical for all 62 focused target IDs',
                   'not_applicable', claimids | waveids, '24b6749')
            caveats += ['Editorial result has no per-post text fingerprint; historical canonical 5da3a48 supplies matching body versions for all 250 IDs.',
                        'Brief uses human/editorial wording, but completion commit credits AI; human confirmation is not established.',
                        '38 mapped claim IDs plus full 30-post increment overlap by 6: 62 unique focused targets, 48 current opinions.',
                        'Focused confirmation is a separate purpose from issue subdivision, and is not new-page editorial coverage.']
        elif theme in ['school-nickname-ban', 'henoko-student-accident']:
            folder = 'school-nickname-ban/20260906-u2' if theme == 'school-nickname-ban' else 'henoko-student-accident/20260906-u3'
            p = a.backup / folder / 'decisions.json'
            decisions = json.loads(p.read_bytes())
            decisions = [r for r in decisions if r.get('reviewer') or r.get('reviewer_type')]
            sets['classification_review_ids'] |= source(p, 'classification_review',
                 'Per-post direct body confirmation for relevance/opinion/issue/stance, recorded in repair report.',
                 'AI: Codex GPT-6 for nickname; Codex session exact model unverified for henoko',
                 [r['tweet_id'] for r in decisions], notes='Original review only; existing overlap rows were not reread.',
                 bodies={str(r['tweet_id']): r['text_sha256'] for r in decisions})
            p = a.backup / 'classification-review/20260906-independent-v1/review-decisions.json'
            d = json.loads(p.read_bytes())
            reviews = d['topics'][theme]['reviews']
            sets['classification_review_ids'] |= source(p, 'classification_review',
                 'Independent reviewer explicitly read saved original bodies individually, limited to 3 nickname / 35 henoko.',
                 'AI: Codex GPT-6 (session identity, backend unverified)', [r['tweet_id'] for r in reviews],
                 notes='Set union removes repeated prior/independent review. Does not claim issue editorial subdivision.',
                 bodies={str(r['tweet_id']): r['text_sha256'] for r in reviews})
            source('quality/reviews/2026-09-06-classification-independent-review.md', 'procedure_evidence',
                   'Explicit saved-body review procedure and limitations', 'AI: Codex GPT-6', ref=BASE)
            caveats += ['Older 2026-06-28 classification design/final audits list classification totals, without a full-body individual reading procedure and target ID ledger; excluded.',
                        'Prior review and independent review are deduplicated by ID. Nickname held record is outside canonical; non-opinions are excluded from top-level sets.']
        else:
            caveats += ['No individual full-body editorial/focused review ledger located. Acquisition repair of 339 records is metadata matching, not semantic reading.',
                        'Classification models producing labels and summaries are excluded from confirmed body review.']

        confirmed = sets['editorial_all_ids'] | sets['focused_body_review_ids'] | sets['classification_review_ids']
        issues = collections.defaultdict(set)
        for i in opinions:
            issues[byid[i]['classification'].get('main_issue', 'unknown')].add(i)
        by_issue = {}
        for issue, ids in sorted(issues.items()):
            by_issue[issue] = {'opinions': len(ids), **{k: len(ids & v) for k, v in sets.items()},
                               'confirmed_body_review': len(ids & confirmed),
                               'body_review_record_unconfirmed': len(ids - confirmed)}
        result = {'theme': theme, 'baseline_commit': BASE, 'canonical_root': str(a.root),
                  'baseline_sha256': expected, 'canonical_file': canon, 'canonical_total': len(rows),
                  'opinion_ids': sorted(opinions), **{k: sorted(v) for k, v in sets.items()},
                  'confirmed_body_review_ids': sorted(confirmed),
                  'body_review_record_unconfirmed_ids': sorted(opinions - confirmed),
                  'sources': sources, 'by_issue_counts': by_issue, 'caveats': caveats,
                  'scan_path': str(a.output / 'four-theme-scan.json'),
                  'scan_sha256': sha((a.output / 'four-theme-scan.json').read_bytes()),
                  'set_semantics': 'Top-level *_ids are unique current canonical opinion IDs. Source.ids retains evidence targets. Editorial main=BASE tracked completion; all=union of inspected branches/worktrees. Connected sets require config plus generator wiring; absent for all four. Focused and classification are separate from full_body_editorial_reread. Claim mapping only excludes records with proven body review.'}
        dump(a.output / (theme + '.json'), result)
        assert sha((a.root / canon).read_bytes()) == expected, 'Source changed while reading'
        print(json.dumps({'theme': theme, 'opinions': len(opinions), **{k: len(v) for k, v in sets.items()},
                          'focused_or_classification_only': len(confirmed - sets['editorial_all_ids']),
                          'confirmed_body_review': len(confirmed), 'record_unconfirmed': len(opinions - confirmed),
                          'private_sha256': sha((a.output / (theme + '.json')).read_bytes())}, ensure_ascii=False))

if __name__ == '__main__':
    main()
