#!/usr/bin/env python3
"""Read-only evidence inventory; post IDs are written only to --private-dir."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

BASE = '565e76b'
BUKATSU = 'c12c50b'
BIKE = '70f8792'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ids(data):
    out = set()
    if isinstance(data, dict):
        if data.get('tweet_id'):
            out.add(str(data['tweet_id']))
        for value in data.values():
            out |= ids(value)
    elif isinstance(data, list):
        for value in data:
            out |= ids(value)
    elif isinstance(data, str) and data.isdigit() and len(data) >= 15:
        out.add(data)
    return out


def field(row, key):
    c = row.get('classification') or {}
    return c[key] if key in c else row.get(key)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('repo', type=Path)
    ap.add_argument('--private-dir', type=Path, required=True)
    a = ap.parse_args()
    a.private_dir.mkdir(parents=True, exist_ok=True)

    def git(*args):
        return subprocess.check_output(['git', '-C', str(a.repo), *args])

    def blob(ref, path):
        return git('show', ref + ':' + path)

    refs = git('for-each-ref', '--format=%(refname)', 'refs/heads').decode().splitlines()
    # Inventory every distinct relevant tracked artifact at all local branch tips.
    versions = {}
    for ref in refs:
        for line in git('ls-tree', '-r', ref, 'data').decode().splitlines():
            _, _, obj, path = line.split(None, 3)
            if any(t in path for t in ['bukatsu-chiiki', 'bike-blue-ticket']) and any(
                k in path for k in ['reread', 'claim_posts', 'veins']
            ):
                versions.setdefault((path, obj), []).append(ref)

    worktrees = []
    for line in git('worktree', 'list', '--porcelain').decode().splitlines():
        if line.startswith('worktree '):
            worktrees.append(Path(line[9:]))
    themes = yaml.safe_load(blob(BASE, 'THEMES.yaml'))['themes']
    public = {}
    for theme in ['bukatsu-chiiki', 'bike-blue-ticket']:
        baseline_path = themes[theme]['sample_file']
        raw = (a.repo / baseline_path).read_bytes()
        rows = json.loads(raw)
        all_ids = {str(r['tweet_id']) for r in rows}
        opinions = {str(r['tweet_id']) for r in rows if field(r, 'is_opinion') is True}
        result = dict(theme=theme, baseline_git_ref=git('rev-parse', BASE).decode().strip(),
                      baseline_path=baseline_path, baseline_sha256=sha(raw),
                      opinion_ids=sorted(opinions), sources=[], caveats=[])
        sets = {k: set() for k in ['editorial_main_ids', 'editorial_all_ids',
                'focused_body_review_ids', 'classification_review_ids', 'claim_mapping_ids',
                'planet_connected_main_ids', 'planet_connected_any_ids']}

        def source(ref, path, kind, subset=None, note='', reader='editorial_review; person/AI identity unspecified; human confirmation not evidenced'):
            content = blob(ref, path)
            d = json.loads(content) if path.endswith('.json') else {}
            got = ids(d) if subset is None else set(subset)
            result['sources'].append(dict(path=path, git_ref=git('rev-parse', ref).decode().strip(),
                sha256=sha(content), kind=kind, method=d.get('method', '') if isinstance(d, dict) else '',
                reader=reader, ids=sorted(got & opinions), recorded_ids=sorted(got),
                canonical_nonopinion_count=len((got & all_ids) - opinions),
                absent_from_canonical_count=len(got - all_ids), notes=note))
            return got & opinions

        if theme == 'bukatsu-chiiki':
            for path in ['data/bukatsu-chiiki_teacher-reread.json',
                         'data/bukatsu-chiiki_cost-receiver-reread.json',
                         'data/bukatsu-chiiki_plan-child-reread.json']:
                sets['editorial_main_ids'] |= source(BASE, path, 'full_body_editorial_reread')
            sets['editorial_all_ids'] = sets['editorial_main_ids'] | source(
                BUKATSU, 'data/bukatsu-chiiki_teacher-reread.json', 'full_body_editorial_reread',
                note='54 additional IDs; existing 269 retained.', reader='AI: Codex for additional 54; earlier editorial identity unspecified')
            for path in ['data/bukatsu-chiiki_claim_posts.json', 'data/verification/bukatsu-chiiki-veins.json']:
                sets['focused_body_review_ids'] |= source(BASE, path, 'focused_body_review',
                    note='Only retained explicit IDs count; unlisted rejected candidates and searched population do not count.')
            connection_refs = [BASE, BUKATSU]
            result['caveats'] += ['main detailed reread 912; branch adds 54. 471 note-purpose rereads are not connected as sub-issues.',
                '604 is population of three reread-status issues, not the 441 IDs actually connected at main.',
                'Claim and vein checks establish limited-purpose body review, not full issue subdivision.',
                'Historical reread files lack per-post body hashes. Current IDs match; same body at historical reading time is not proven.']
        else:
            sets['editorial_main_ids'] = source(BASE, 'data/bike-blue-ticket_opposition_reread.json',
                'full_body_editorial_reread', note='Method text still says 77 and date 08-17, but actual buckets contain 180. Theme log and incremental commits document additions.')
            old = json.loads(blob(BASE, 'data/verification/bike-blue-ticket-reread.json'))
            generated_support = {r['tweet_id'] for r in old if r['bucket'] == 'support'}
            old_ids = ids(old)
            branch_data = json.loads(blob(BIKE, 'data/bike-blue-ticket_issues-reread.json'))
            new = ids(branch_data) - old_ids
            assert len(new) == 26
            added = source(BIKE, 'data/bike-blue-ticket_issues-reread.json', 'full_body_editorial_reread',
                subset=new, note='Only 26 newly read IDs. 210 inherited IDs include 93 AI-only support labels.', reader='AI: Claude (commit co-author)')
            sets['editorial_all_ids'] = sets['editorial_main_ids'] | added
            sets['focused_body_review_ids'] = source(BASE, 'data/bike-blue-ticket_claim_posts.json',
                'focused_body_review', note='Candidate posts read one-by-one; retained explicit IDs only.')
            source(BASE, 'data/verification/bike-blue-ticket-reread.json', 'automated_classification_labels',
                subset=generated_support, note='93 support IDs mechanically derived from stance; not classified as classification_review or body reread.', reader='AI classifier; automatic export')
            source(BASE, 'scripts/build_bike_process_sections.py', 'provenance_code', subset=set(),
                note='write_provenance_records creates support rows from classifier. Page explicitly states only opposition was reread.')
            source(BIKE, 'tasks/task-54.md', 'method_evidence', subset=set(),
                note='Completion record distinguishes 26 new body readings from transformation of existing 273.')
            source('1c7155a', 'quality/reviews/2026-09-06-bike-stage-a.md', 'compatibility_audit', subset=set(),
                note='19 old unread found after format compatibility fix; not a reread artifact.')
            result['automated_support_ids'] = sorted(generated_support & opinions)
            connection_refs = [BIKE]
            result['caveats'] += ['468 is current operational opinion definition including all collected posts; not a new semantic opinion judgment.',
                '273 verification rows = 180 opposition rereads + 93 classifier-derived support rows. 77 is stale prose, not an additional set.',
                'Rollout method prose incorrectly generalizes body reread to inherited support rows; only 26 additional body rereads are confirmed.',
                '236 connected IDs in branch include 93 unsupported reread claims; qualified editorial connection is their intersection with confirmed editorial IDs.',
                'main generator cannot reproduce bike branch with nested opinion flags; 1c7155a compatibility fix then rejects 19 skipped IDs, based on overstated 236.',
                'No main planet config exists for bike. Branch connectivity is not a claim of publication or a passed current gate.',
                'June article-usable audit mixes rules and classifier summaries; no identifiable set with explicit one-by-one body reading, so classification_review_ids is empty.',
                'Historical reading records have no per-post body hash; branch canonical text/issue comparison is reported separately.']
            branch_rows = json.loads(blob(BIKE, baseline_path))
            bm = {str(r['tweet_id']): r for r in branch_rows}
            same = [r for r in rows if str(r['tweet_id']) in bm]
            result['branch_canonical_comparison'] = dict(git_ref=BIKE, sha256=sha(blob(BIKE, baseline_path)),
                shared_ids=len(same), body_changed=sum(r.get('text') != bm[str(r['tweet_id'])].get('text') for r in same),
                issue_changed=sum(field(r, 'main_issue') != field(bm[str(r['tweet_id'])], 'main_issue') for r in same))

        for ref in connection_refs:
            cfg_path = f'configs/planet/{theme}.yaml'
            cfg_raw = blob(ref, cfg_path)
            cfg = yaml.safe_load(cfg_raw)
            connected = set()
            mismatches = 0
            by_id = {str(r['tweet_id']): r for r in rows}
            for issue, sc in cfg.get('sub_issues', {}).items():
                section = json.loads(blob(ref, sc['file']))
                for key in sc['path'][:-1]:
                    section = section[key]
                got = ids(section['items'])
                connected |= got & opinions
                mismatches += sum(field(by_id[x], 'main_issue') != issue for x in got & opinions)
            source(ref, cfg_path, 'planet_connection', subset=connected,
                note=f'Sub-issue input IDs; issue assignment mismatch against current canonical: {mismatches}. Connection does not imply body reread evidence.')
            sets['planet_connected_any_ids'] |= connected
            if ref == BASE:
                sets['planet_connected_main_ids'] |= connected

        # All local branch versions are fingerprinted; older versions cannot silently add unreviewed IDs.
        union_known = sets['editorial_all_ids'] | sets['focused_body_review_ids']
        if theme == 'bike-blue-ticket':
            union_known |= set(result['automated_support_ids'])
        result['artifact_versions'] = []
        for (path, obj), vr in versions.items():
            if theme not in path:
                continue
            b = git('cat-file', 'blob', obj)
            got = ids(json.loads(b))
            result['artifact_versions'].append(dict(path=path, git_blob=obj, refs=vr,
                sha256=sha(b), ids=sorted(got & opinions), absent_count=len(got-all_ids),
                additional_opinion_ids_outside_known=sorted((got & opinions)-union_known)))
        result['worktree_artifacts'] = []
        paths = {x['path'] for x in result['artifact_versions']}
        for wt in worktrees:
            for path in sorted(paths):
                p = wt/path
                if p.is_file():
                    b = p.read_bytes()
                    got = ids(json.loads(b))
                    result['worktree_artifacts'].append(dict(path=str(p), sha256=sha(b),
                        additional_opinion_ids_outside_known=sorted((got & opinions)-union_known)))
        confirmed = sets['editorial_all_ids'] | sets['focused_body_review_ids'] | sets['classification_review_ids']
        sets.update(confirmed_body_review_ids=confirmed,
                    no_body_review_record_ids=opinions-confirmed,
                    focused_body_review_only_ids=sets['focused_body_review_ids']-sets['editorial_all_ids'],
                    editorial_branch_only_ids=sets['editorial_all_ids']-sets['editorial_main_ids'],
                    editorial_not_planet_main_ids=sets['editorial_all_ids']-sets['planet_connected_main_ids'],
                    editorial_not_planet_any_ids=sets['editorial_all_ids']-sets['planet_connected_any_ids'],
                    planet_qualified_editorial_any_ids=sets['editorial_all_ids'] & sets['planet_connected_any_ids'])
        result.update({k: sorted(v) for k, v in sets.items()})
        result['by_issue_counts'] = {}
        for issue in sorted({field(r, 'main_issue') for r in rows if str(r['tweet_id']) in opinions}):
            scope = {str(r['tweet_id']) for r in rows if str(r['tweet_id']) in opinions and field(r, 'main_issue') == issue}
            result['by_issue_counts'][issue] = dict(opinions=len(scope), **{k.removesuffix('_ids'): len(v & scope) for k, v in sets.items()})
        assert all(v <= opinions for v in sets.values())
        assert len(sets['editorial_all_ids']) + len(sets['focused_body_review_only_ids']) + len(sets['no_body_review_record_ids']) == len(opinions)
        assert sha((a.repo / baseline_path).read_bytes()) == result['baseline_sha256']
        payload = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+'\n').encode()
        dest = a.private_dir / f'{theme}.json'
        dest.write_bytes(payload)
        public[theme] = dict(baseline_sha256=result['baseline_sha256'], private_path=str(dest),
            private_sha256=sha(payload), opinions=len(opinions), **{k.removesuffix('_ids'): len(v) for k,v in sets.items()},
            by_issue_counts=result['by_issue_counts'], branch_canonical_comparison=result.get('branch_canonical_comparison'),
            unassessed_historical_ids=sum(len(x['additional_opinion_ids_outside_known']) for x in result['artifact_versions']),
            unassessed_worktree_ids=sum(len(x['additional_opinion_ids_outside_known']) for x in result['worktree_artifacts']))
    print(json.dumps(public, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
