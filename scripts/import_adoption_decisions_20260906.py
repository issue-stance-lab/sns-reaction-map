#!/usr/bin/env python3
"""Import the bounded 2026-09-06 adoption evidence, without classifying posts.

Example:
  python3 scripts/import_adoption_decisions_20260906.py \
    --evidence-root /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs \
    --out data/verification/adoption/decision-evidence.json

Success: 508 unresolved decisions; cohorts 427, 141, and 5. Repeating the
command with unchanged evidence and reports produces identical bytes.
Current canonical/public membership must be calculated by the ledger builder;
this seed deliberately has no adopted decisions, collection dates, or raw IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from verification_data import record_id_hash

ROOT = Path(__file__).resolve().parent.parent
SCHOOL = 'school-nickname-ban'
HENOKO = 'henoko-student-accident'
CONSTITUTION = 'constitutional-amendment'
TAKAICHI = 'takaichi'
SOURCES = {
    'school': 'school-nickname-ban/20260906-u2/decisions.json',
    'review': 'classification-review/20260906-independent-v1/review-decisions.json',
    'takaichi': 'takaichi/20260906-m3-v2/adoption-dispositions.json',
    'constitution': 'constitutional-amendment/20260906-u1/decisions.private.json',
    'old': 'constitutional-amendment/20260906-u1/old-wave-unique.private.json',
    'omitted': 'henoko-student-accident/20260906-u3/omitted-before-classification.json',
}
REPORTS = {
    'school': 'quality/reviews/2026-09-06-classification-independent-review.md',
    'takaichi': 'quality/reviews/2026-09-06-data-repair-takaichi.md',
    'constitution': 'quality/reviews/2026-09-06-data-repair-constitutional-amendment.md',
    'omitted': 'quality/reviews/2026-09-06-data-repair-henoko-student-accident.md',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def identities(rows: Any, count: int, source: str) -> list[str]:
    require(isinstance(rows, list) and len(rows) == count, f'{source}: unexpected row count')
    result = []
    for row in rows:
        require(isinstance(row, dict), f'{source}: expected object')
        tid = str(row.get('tweet_id') or '').strip()
        require(tid.isascii() and tid.isdigit(), f'{source}: missing numeric tweet identity')
        # Pass only tweet_id so a supplied hash/URL cannot override identity.
        result.append(record_id_hash({'tweet_id': tid}))
    require(len(set(result)) == count, f'{source}: duplicate identities')
    return sorted(result)


def generate(evidence_root: Path) -> dict[str, Any]:
    loaded = {}
    fingerprints = {}
    for key, relative in SOURCES.items():
        raw = (evidence_root / relative).read_bytes()
        loaded[key] = json.loads(raw)
        fingerprints[relative] = hashlib.sha256(raw).hexdigest()
    report_hashes = {
        key: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for key, relative in REPORTS.items()
    }

    school = identities(loaded['school'], 31, 'school')
    review = loaded['review']['topics']
    school_review = review[SCHOOL]['reviews']
    reviewed_school = identities(school_review, 3, 'school review')
    require(set(reviewed_school) <= set(school), 'school review outside original cohort')
    held = [r for r in school_review if r.get('disposition') == 'hold']
    school_held = identities(held, 1, 'school held')
    require(all(r.get('disposition') in {'hold', 'recommend'} for r in school_review),
            'school review disposition changed')
    henoko_rows = review[HENOKO]['reviews']
    henoko = identities(henoko_rows, 35, 'henoko review')
    require(all(r.get('disposition') == 'recommend' for r in henoko_rows),
            'henoko review disposition changed')

    takaichi_rows = loaded['takaichi']
    takaichi = identities(takaichi_rows, 134, 'takaichi')
    require(all(r.get('status') == 'intentional_hold' and r.get('already_adopted') is False
                and r.get('semantic_reread_performed') is False for r in takaichi_rows),
            'takaichi evidence no longer describes collection-only holds')
    constitution_rows = loaded['constitution']
    constitution = identities(constitution_rows, 227, 'constitution')
    require(all(r.get('status') == 'unadopted_candidate_current_reason_unknown'
                and r.get('semantic_review') == 'not_performed'
                and r.get('later_nonadoption_reason') == 'unknown'
                and r.get('current_action') == 'hold_pending_semantic_review_and_adoption_decision'
                for r in constitution_rows), 'constitutional decision evidence changed')
    old = identities(loaded['old'], 141, 'old constitutional wave')
    require(not set(old) & set(constitution), 'old unique cohort overlaps original cohort')
    omitted_evidence = loaded['omitted']
    omitted = identities(omitted_evidence['rows'], 5, 'preclassification omissions')
    require(omitted_evidence['in_canon'] == 0 and omitted_evidence['in_missing35'] == 0,
            'omitted cohort membership evidence changed')
    require(not set(omitted) & set(henoko), 'omitted cohort overlaps original cohort')

    decisions: dict[str, dict[str, Any]] = {}

    def add(topic: str, hashes: list[str], status: str, reason: str, report: str) -> None:
        require(status in {'pending_review', 'decision_unknown', 'excluded_confirmed'},
                'unsupported decision status')
        target = decisions.setdefault(topic, {})
        for identity in hashes:
            require(identity not in target, 'decision identity assigned twice')
            target[identity] = {
                'status': status,
                'reason_code': reason,
                'evidence_file': REPORTS[report],
                'evidence_sha256': report_hashes[report],
            }

    add(SCHOOL, school_held, 'pending_review', 'context_missing', 'school')
    add(TAKAICHI, takaichi, 'pending_review', 'collection_only_instruction', 'takaichi')
    add(CONSTITUTION, constitution, 'pending_review',
        'semantic_review_and_later_reason_unknown', 'constitution')
    add(CONSTITUTION, old, 'decision_unknown', 'old_wave_disposition_unknown', 'constitution')
    # Historical text deduplication is NOT a permanent editorial exclusion.
    add(HENOKO, omitted, 'decision_unknown', 'restoration_decision_required', 'omitted')
    cohorts = {
        'original_427': {SCHOOL: school, HENOKO: henoko, TAKAICHI: takaichi,
                         CONSTITUTION: constitution},
        'constitutional_old_141': {CONSTITUTION: old},
        'henoko_preclassification_5': {HENOKO: omitted},
    }
    require(sum(map(len, decisions.values())) == 508, 'expected 508 unresolved decisions')
    require(sum(map(len, cohorts['original_427'].values())) == 427, 'expected original 427')
    require(sum(len(set(ids) - set(decisions.get(topic, {})))
                for topic, ids in cohorts['original_427'].items()) == 65,
            'expected 65 original-cohort records without unresolved decision')
    return {'schema_version': 1, 'decisions': decisions, 'cohorts': cohorts,
            'evidence_sources': fingerprints}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    evidence_root, output = args.evidence_root.resolve(), args.out.resolve()
    require(not output.is_relative_to(evidence_root), 'output must be outside private evidence root')
    require(output not in {(ROOT / p).resolve() for p in REPORTS.values()},
            'output cannot replace an evidence report')
    artifact = generate(evidence_root)
    encoded = json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding='utf-8')
    print(json.dumps({'decisions': sum(map(len, artifact['decisions'].values())),
                      'cohorts': {k: sum(map(len, v.values())) for k, v in artifact['cohorts'].items()},
                      'sha256': hashlib.sha256(encoded.encode('utf-8')).hexdigest()},
                     sort_keys=True))


if __name__ == '__main__':
    main()
