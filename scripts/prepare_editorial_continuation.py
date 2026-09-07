#!/usr/bin/env python3
"""Reserve four frozen 1,000-record editorial waves outside the repository."""
from __future__ import annotations

import argparse
from collections import Counter, deque
import importlib
import json
from pathlib import Path
import shutil
import time

import yaml

try:
    from scripts.editorial_work_registry import current_attempts, load_registry
    from scripts.prepare_body_review_pilot import CLASSIFIERS, fingerprint, inventory, sha
    from scripts.verify_editorial_hundred import dump
except ModuleNotFoundError:
    from editorial_work_registry import current_attempts, load_registry
    from prepare_body_review_pilot import CLASSIFIERS, fingerprint, inventory, sha
    from verify_editorial_hundred import dump


WAVES = 4
RECORDS_PER_WAVE = 1000
BATCH_SIZE = 20
RUNBOOK_TOPIC_QUOTAS = {
    'ai-copyright': 560,
    'bukatsu-chiiki': 300,
    'constitutional-amendment': 520,
    'consumption-tax-cut': 520,
    'elderly-license-revocation': 100,
    'fukushuto': 520,
    'henoko-student-accident': 120,
    'koshitsu-tenpakai': 520,
    'school-nickname-ban': 320,
    'takaichi': 520,
}


def build_criteria(root: Path) -> dict:
    titles = {
        topic: value['title']
        for topic, value in yaml.safe_load((root / 'THEMES.yaml').read_text())['themes'].items()
    }
    criteria = {}
    for topic, module_name in CLASSIFIERS.items():
        module = importlib.import_module('classify_' + module_name + '_arena_hermes')
        prompt = module.prompt_for([])
        criteria[topic] = {
            'text': prompt.split('JSON配列')[0].strip(),
            'source': 'scripts/classify_' + module_name + '_arena_hermes.py',
            'source_sha256': sha(Path(module.__file__)),
            'issues': sorted(module.ISSUES),
            'stances': sorted(module.STANCES),
            'title': titles[topic],
        }
    return criteria


def select_records(queues: dict, attempted: list, limit: int = WAVES * RECORDS_PER_WAVE) -> list:
    seen = {(r['topic'], r['body_sha256'], r['classification_sha256']) for r in attempted}
    buckets = {
        topic: deque(
            row for row in rows
            if (topic, row['body_sha256'], row['classification_sha256']) not in seen
        )
        for topic, rows in sorted(queues.items())
        if rows
    }
    chosen = []
    while len(chosen) < limit and any(buckets.values()):
        for topic, queue in buckets.items():
            while queue:
                row = queue.popleft()
                identity = (topic, row['body_sha256'], row['classification_sha256'])
                if identity in seen:
                    continue
                seen.add(identity)
                chosen.append({**row, 'topic': topic})
                break
            if len(chosen) == limit:
                break
    if len(chosen) != limit:
        raise ValueError(f'only {len(chosen)} unattempted records remain; {limit} required')
    identities = {(r['topic'], r['body_sha256'], r['classification_sha256']) for r in chosen}
    if len(identities) != limit:
        raise ValueError('duplicate selected identity')
    return chosen


def select_topic_homogeneous_records(queues: dict, attempted: list, quotas: dict) -> list:
    if any(type(value) is not int or value <= 0 or value % BATCH_SIZE for value in quotas.values()):
        raise ValueError('every topic quota must be a positive multiple of 20')
    seen = {(r['topic'], r['body_sha256'], r['classification_sha256']) for r in attempted}
    chosen = []
    for topic, quota in sorted(quotas.items()):
        topic_rows = []
        for row in queues.get(topic, []):
            identity = (topic, row['body_sha256'], row['classification_sha256'])
            if identity in seen:
                continue
            seen.add(identity)
            topic_rows.append({**row, 'topic': topic})
            if len(topic_rows) == quota:
                break
        if len(topic_rows) != quota:
            raise ValueError(f'{topic} has only {len(topic_rows)} unique unattempted records; {quota} required')
        chosen.extend(topic_rows)
    return chosen


def alternating_assignments(actor_a: str, actor_b: str) -> dict:
    odd = list(range(1, 51, 2))
    even = list(range(2, 51, 2))
    return {
        'editor': {actor_a: odd, actor_b: even},
        'audit': {actor_a: even, actor_b: odd},
    }


def prepare(root: Path, private_root: Path, run: Path, actors: tuple[str, str], worktrees: tuple[Path, Path]) -> dict:
    root = root.resolve()
    private_root = private_root.resolve()
    run = run.resolve()
    if run.exists():
        raise ValueError('refusing to overwrite an existing run')
    if run.is_relative_to(root):
        raise ValueError('private packets must be outside the repository')
    if len(set(actors)) != 2 or len({p.resolve() for p in worktrees}) != 2:
        raise ValueError('two distinct actors and worktrees are required')

    report, queues = inventory(root, private_root)
    criteria = build_criteria(root)
    registry_path = root / 'data/verification/editorial-work.json'
    registry = load_registry(registry_path, root, private_root)
    attempted = current_attempts(registry, criteria)
    selected = select_topic_homogeneous_records(queues, attempted, RUNBOOK_TOPIC_QUOTAS)
    if len(selected) != WAVES * RECORDS_PER_WAVE:
        raise ValueError('topic quotas must total 4,000')

    run.mkdir(parents=True)
    shutil.copy2(root / 'data/verification/editorial-adoption-current.json', run / 'adoption-before.private.json')
    shutil.copy2(registry_path, run / 'work-before.private.json')
    assignments = alternating_assignments(*actors)
    worktree_map = {actor: str(path.resolve()) for actor, path in zip(actors, worktrees)}
    wave_hashes = {}
    packet_identity = set()

    for wave_number in range(1, WAVES + 1):
        wave = run / f'wave-{wave_number:02d}'
        wave.mkdir()
        packet_hashes = {}
        wave_rows = selected[(wave_number - 1) * RECORDS_PER_WAVE:wave_number * RECORDS_PER_WAVE]
        for batch_number in range(1, 51):
            batch = wave / f'batch-{batch_number:02d}'
            batch.mkdir()
            rows = wave_rows[(batch_number - 1) * BATCH_SIZE:batch_number * BATCH_SIZE]
            topics = sorted({row['topic'] for row in rows})
            packet = {
                'schema_version': 1,
                'state': 'prepared_not_reviewed',
                'records': rows,
                'criteria': {topic: criteria[topic] for topic in topics},
                'input_sha256': fingerprint(rows),
                'automatic_reread_credit': 0,
                'additional_model_calls': 0,
                'instructions': (
                    'Read only these 20 records and their criteria. Decide all four classification fields, '
                    'uncertainty, evidence sufficiency and a concise reason for each record. Preserve uncertainty. '
                    'Do not publish or mutate canonical data. The other actor independently audits change '
                    'candidates and reason conflicts; self-audit is forbidden.'
                ),
            }
            packet_path = batch / 'packet.private.json'
            dump(packet_path, packet)
            packet_hashes[str(packet_path.relative_to(wave))] = sha(packet_path)
            for row in rows:
                identity = (row['topic'], row['body_sha256'], row['classification_sha256'])
                if identity in packet_identity:
                    raise ValueError('cross-wave duplicate selected identity')
                packet_identity.add(identity)
        reservation = {
            'schema_version': 1,
            'prepared_epoch': time.time(),
            'new_records': RECORDS_PER_WAVE,
            'packet_hashes': packet_hashes,
            'writer_sha256': sha(root / 'scripts/continuous_editorial_review.py'),
            'cycle_writer_sha256': sha(root / 'scripts/editorial_cycle.py'),
            'assignments': assignments,
            'worktrees': worktree_map,
            'model': 'parent-configured model',
            'reasoning_effort': 'inherited',
            'continuation_of_reviewed_records': 4000 + (wave_number - 1) * RECORDS_PER_WAVE,
        }
        dump(wave / 'reservation.json', reservation)
        wave_hashes[f'wave-{wave_number:02d}'] = sha(wave / 'reservation.json')

    topic_counts = dict(sorted(Counter(row['topic'] for row in selected).items()))
    opinion_counts = dict(sorted(Counter('opinion' if row['opinion'] else 'nonopinion' for row in selected).items()))
    canonical_hashes = {
        topic: value['canonical_sha256']
        for topic, value in report['topics'].items()
        if topic in topic_counts
    }
    top = {
        'schema_version': 1,
        'prepared_epoch': time.time(),
        'new_records': len(selected),
        'baseline_reviewed_records': 4000,
        'baseline_adoption_sha256': sha(run / 'adoption-before.private.json'),
        'baseline_work_sha256': sha(run / 'work-before.private.json'),
        'baseline_work_records': len(registry['records']),
        'waves': wave_hashes,
        'topic_counts': topic_counts,
        'opinion_counts': opinion_counts,
        'canonical_hashes': canonical_hashes,
        'selection': 'Deterministic topic-homogeneous 20-record packets after excluding all 4,080 registered body/classification identities. Topic quotas are multiples of 20 so systemic criteria issues cannot spill into another theme.',
        'status': 'reserved_not_reviewed',
        'canonical_changes': 0,
        'registered_reread_increment': 0,
    }
    dump(run / 'reservation.json', top)
    return top


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--actor-a', required=True)
    parser.add_argument('--actor-b', required=True)
    parser.add_argument('--worktree-a', type=Path, required=True)
    parser.add_argument('--worktree-b', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(
        args.root, args.private_root, args.run,
        (args.actor_a, args.actor_b), (args.worktree_a, args.worktree_b),
    )
    print(json.dumps({
        'new_records': result['new_records'],
        'topic_counts': result['topic_counts'],
        'opinion_counts': result['opinion_counts'],
        'canonical_changes': 0,
        'registered_reread_increment': 0,
    }, ensure_ascii=False))
