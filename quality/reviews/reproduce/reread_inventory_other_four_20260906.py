#!/usr/bin/env python3
"""Inventory existing reading evidence; never classify posts or change inputs.

Private output contains post IDs. Write only to the private backup volume.
Claim selection is focused reading, not an editorial reread of a whole issue.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

TOPICS = ['consumption-tax-cut', 'fukushuto',
          'constitutional-amendment', 'koshitsu-tenpakai']
BUILDERS = {
    'consumption-tax-cut': 'scripts/build_consumption_tax_page.py',
    'fukushuto': 'scripts/build_fukushuto_process_sections.py',
    'constitutional-amendment': 'scripts/build_constitutional_process_sections.py',
    'koshitsu-tenpakai': 'scripts/build_koshitsu_process_sections.py',
}


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def extract_ids(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from extract_ids(v)
    elif isinstance(value, list):
        for v in value:
            yield from extract_ids(v)
    elif isinstance(value, str) and re.fullmatch(r'\d{15,22}', value):
        yield value


def run(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    assert out != root and root not in out.parents, 'Private output must be outside repo'
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / 'scripts'))
    from public_registry_common import is_opinion_record
    registry = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    refs = run(root, 'for-each-ref', '--format=%(refname)', 'refs/heads').decode().splitlines()
    # Search every local branch for independently named editorial/new-page files.
    discovered = {}
    for ref in refs:
        paths = run(root, 'ls-tree', '-r', '--name-only', ref, 'data', 'configs/planet').decode().splitlines()
        candidates = [p for p in paths if any(t in p for t in TOPICS) and
                      any(w in p.lower() for w in ['reread', 'review', 'editorial', 'veins', 'sunk', 'planet/'])]
        if candidates:
            discovered[ref] = candidates
    assert not discovered, 'New potential evidence requires review before zero editorial claim'
    summaries = {}
    for topic in TOPICS:
        target = out / (topic + '.json')
        assert not target.exists(), 'Use a fresh output directory'
        canonical = root / registry[topic]['sample_file']
        rows = json.loads(canonical.read_text())
        opinion = {str(r['tweet_id']): r for r in rows if is_opinion_record(r)}
        published = json.loads((root / 'data/public/themes' / (topic + '.json')).read_text())
        assert len(opinion) == published['opinion_count']
        relative = 'data/' + topic + '_claim_posts.json'
        content = (root / relative).read_bytes()
        doc = json.loads(content)
        # Method declarations are evidence of historical reading, not a new verification.
        method = doc.get('method') or doc.get('description')
        if not method:
            builder = (root / BUILDERS[topic]).read_text()
            method = next(line.strip() for line in builder.splitlines()
                          if '候補を1件ずつ読み' in line)
        assert any(token in method for token in ('1件ずつ', '一つずつ'))
        all_ids = set(extract_ids(doc))
        versions = {}
        for ref in refs:
            proc = subprocess.run(['git', '-C', str(root), 'rev-parse', ref + ':' + relative],
                                  capture_output=True, text=True)
            if proc.returncode == 0:
                versions.setdefault(proc.stdout.strip(), []).append(ref)
        older_extra = set()
        for blob_oid in versions:
            old = json.loads(run(root, 'cat-file', 'blob', blob_oid))
            older_extra |= set(extract_ids(old)) - all_ids
        assert not older_extra, 'Older branch contains additional IDs needing evidence review'
        focused = all_ids & set(opinion)
        mapping = set()  # Reserved for mapping-only IDs without body-reading evidence.
        source = {
            'path': relative, 'git_ref': run(root, 'rev-parse', 'HEAD').decode().strip(),
            'sha256': sha(content), 'kind': 'focused_body_review', 'method': method,
            'reader': 'AI-assisted editorial work (Claude co-author in git history); human per-post confirmation not established',
            'ids': sorted(focused),
            'notes': 'Only retained claim IDs are countable. Rejected candidates have no exhaustive saved ID list. Current body hash was not bound at reading time.',
            'evidence_builder': BUILDERS[topic],
            'evidence_builder_sha256': sha((root / BUILDERS[topic]).read_bytes()),
            'raw_id_count': len(all_ids), 'nonopinion_count': len(all_ids - set(opinion)),
            'absent_canonical_count': len(all_ids - {str(r['tweet_id']) for r in rows}),
            'distinct_branch_blobs': len(versions),
        }
        counts = Counter(r['classification']['main_issue'] for r in opinion.values())
        by_issue = {issue: {'opinion_count': count, 'editorial_count': 0,
                           'focused_count': sum(opinion[i]['classification']['main_issue'] == issue for i in focused)}
                    for issue, count in counts.items()}
        result = {
            'theme': topic, 'baseline_sha256': sha(canonical.read_bytes()),
            'opinion_ids': sorted(opinion), 'editorial_main_ids': [], 'editorial_all_ids': [],
            'planet_connected_main_ids': [], 'planet_connected_any_ids': [],
            'classification_review_ids': [], 'focused_body_review_ids': sorted(focused),
            'claim_mapping_ids': sorted(mapping), 'sources': [source],
            'by_issue_counts': by_issue,
            'caveats': ['No issue-level editorial reread record found in examined local refs/worktrees.',
                        'Claim selection is limited-purpose reading and does not establish full topic comprehension.',
                        'Automated initial classification and representative-summary difference checks excluded.',
                        'No new reading performed; absence of evidence is not proof nobody read a post.'],
            'branch_scan': {'local_heads': len(refs), 'editorial_candidates': discovered,
                            'claim_file_variants': {oid: values for oid, values in versions.items()}},
        }
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        summaries[topic] = {'opinions': len(opinion), 'editorial': 0,
                            'focused': len(focused), 'unrecorded': len(opinion)-len(focused),
                            'raw_claim_ids': len(all_ids), 'private_sha256': sha(target.read_bytes())}
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
