#!/usr/bin/env python3
"""Verify four review waves and register attempted work without applying adoption."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import yaml

from scripts import editorial_cycle, supplemental_editorial_audit
from scripts.editorial_work_registry import build_registry, load_registry
from scripts.finalize_editorial_cycle import validate_work_lineage, apply_overlay
from scripts.editorial_work_registry import fingerprint
from scripts.verify_editorial_hundred import dump, read, sha


RESULT_PREFIX = '2026-09-08-cycle-next4000-final'


def overlay_supplements(root, run, wave_name, result, folders):
    """Replay only explicitly supplied, completed audits of this exact wave."""
    original = result['journal']
    rows = original
    reports = []
    for folder in folders:
        folder = Path(folder).resolve()
        reservation = read(folder / 'reservation.json')
        baseline = read(folder / 'baseline.private.json')
        provenance = reservation.get('source_provenance', {})
        if provenance != baseline.get('source_provenance'):
            raise ValueError('supplement provenance differs')
        expected = {
            'source_run': str(run.resolve()),
            'source_top_reservation_sha256': sha(run / 'reservation.json'),
            'source_wave': wave_name,
            'source_wave_reservation_sha256': sha(run / wave_name / 'reservation.json'),
        }
        if any(provenance.get(k) != v for k, v in expected.items()):
            raise ValueError('supplement belongs to another source wave or version')
        batches = provenance.get('source_batches', [])
        if not batches or len(set(batches)) != len(batches) or not set(batches) <= {r['batch'] for r in original}:
            raise ValueError('invalid supplemental source batches')
        projection = [r for r in original if r['batch'] in batches]
        if fingerprint(projection) != baseline['source_journal_sha256']:
            raise ValueError('supplement source journal differs')
        report = supplemental_editorial_audit.collect(root, folder)
        for item in baseline['records']:
            audit = read(folder / f"batch-{item['supplemental_batch']:02d}" / 'audit.private.json')
            editor = read(run / wave_name / f"batch-{item['source_key'][0]:02d}" / 'editor-actor.private.json')
            if audit['actor'] == editor['actor']:
                raise ValueError('supplemental self audit')
        rows = apply_overlay(rows, report)
        reports.append({'path': str(folder), 'report': report})
    return {**result, 'journal': rows,
            'adoption_counts': dict(Counter(r['adoption_status'] for r in rows)),
            'supplemental_audits': sum(s['report']['supplemental_audits'] for s in reports),
            'supplements': reports}


def combine_journals(baseline: list, wave_results: list, expected_new: int = 4000) -> dict:
    new_rows = []
    independent = 0
    for wave_number, result in enumerate(wave_results, 1):
        independent += result['independent_records']
        offset = 1_000_000 + wave_number * 100_000
        new_rows.extend({**row, 'batch': row['batch'] + offset} for row in result['journal'])
    if len(new_rows) != expected_new:
        raise ValueError('new review count mismatch')
    if any(row['adoption_status'] == 'pending_audit' for row in new_rows):
        raise ValueError('supplemental audit is still required')
    combined = baseline + new_rows
    record_ids = {(row['topic'], row['record_id_hash']) for row in combined}
    inputs = {(row['topic'], row['body_sha256'], row['classification_sha256']) for row in combined}
    if len(record_ids) != len(combined) or len(inputs) != len(combined):
        raise ValueError('duplicate reviewed record or input identity')
    return {
        'baseline_records': len(baseline),
        'new_records': len(new_rows),
        'reviewed_records_if_adoption_is_applied': len(combined),
        'new_adoption_counts': dict(sorted(Counter(row['adoption_status'] for row in new_rows).items())),
        'cumulative_adoption_counts_if_applied': dict(sorted(Counter(row['adoption_status'] for row in combined).items())),
        'new_routes': dict(sorted(Counter(row['route'] for row in new_rows).items())),
        'independent_new_records': independent,
        'new_journal': new_rows,
        'combined_journal': combined,
    }


def verify_and_collect(root: Path, private_root: Path, run: Path, supplements=None) -> tuple[dict, list]:
    root, private_root, run = root.resolve(), private_root.resolve(), run.resolve()
    reservation = read(run / 'reservation.json')
    supplements = supplements or {}
    if not set(supplements) <= set(reservation['waves']):
        raise ValueError('unknown supplemental wave')
    if reservation['new_records'] != 4000 or len(reservation['waves']) != 4:
        raise ValueError('expected a frozen four-wave reservation')
    if sha(run / 'adoption-before.private.json') != reservation['baseline_adoption_sha256']:
        raise ValueError('baseline adoption snapshot changed')
    if sha(run / 'work-before.private.json') != reservation['baseline_work_sha256']:
        raise ValueError('baseline work snapshot changed')
    if sha(root / 'data/verification/editorial-adoption-current.json') != reservation['baseline_adoption_sha256']:
        raise ValueError('adoption ledger changed; application must remain a separate step')
    if sha(root / 'data/verification/editorial-work.json') != reservation['baseline_work_sha256']:
        raise ValueError('work registry changed after reservation')
    metadata = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    for topic, expected in reservation['canonical_hashes'].items():
        if sha(root / metadata[topic]['sample_file']) != expected:
            raise ValueError('canonical input changed: ' + topic)
    policy = read(root / 'quality/reviews/2026-09-07-cycle-policy-integrity.json')
    if any(sha(root / path) != expected for path, expected in policy['policy_sha256'].items()):
        raise ValueError('acceptance policy changed')

    wave_results = []
    for wave_number in range(1, 5):
        name = f'wave-{wave_number:02d}'
        folder = run / name
        wave_reservation = read(folder / 'reservation.json')
        if sha(folder / 'reservation.json') != reservation['waves'][name]:
            raise ValueError('wave reservation changed: ' + name)
        if sha(root / 'scripts/editorial_cycle.py') != wave_reservation['cycle_writer_sha256']:
            raise ValueError('cycle collector changed')
        result, _ = editorial_cycle.collect(root, folder)
        result = overlay_supplements(root, run, name, result, supplements.get(name, []))
        wave_results.append(result)

    baseline = read(run / 'adoption-before.private.json')
    if baseline['reviewed_records'] != reservation['baseline_reviewed_records']:
        raise ValueError('baseline reviewed count changed')
    combined = combine_journals(baseline['records'], wave_results)
    return combined, wave_results


def register_work_only(root: Path, private_root: Path, run: Path, supplements=None) -> dict:
    root, private_root, run = root.resolve(), private_root.resolve(), run.resolve()
    combined, wave_results = verify_and_collect(root, private_root, run, supplements)
    work_path = root / 'data/verification/editorial-work.json'
    baseline_work = load_registry(run / 'work-before.private.json', root, private_root)
    sources = baseline_work['sources'][:]

    def add(path: Path, storage: str, kind: str) -> None:
        base = root if storage == 'repository' else private_root
        entry = {
            'path': str(path.resolve().relative_to(base)),
            'storage': storage,
            'kind': kind,
            'sha256': sha(path),
        }
        existing = next(
            (source for source in sources if (source['path'], source['storage']) == (entry['path'], entry['storage'])),
            None,
        )
        if existing is not None and existing != entry:
            raise ValueError('registered evidence changed: ' + entry['path'])
        if existing is None:
            sources.append(entry)

    add(run / 'reservation.json', 'private', 'evidence')
    add(run / 'adoption-before.private.json', 'private', 'evidence')
    add(run / 'work-before.private.json', 'private', 'evidence')
    for history in sorted((run / 'assignment-history').glob('*.private.json')):
        add(history, 'private', 'evidence')
    for wave_number in range(1, 5):
        folder = run / f'wave-{wave_number:02d}'
        add(folder / 'reservation.json', 'private', 'evidence')
        for packet in sorted(folder.glob('batch-*/packet.private.json')):
            add(packet, 'private', 'packet')
        for evidence in sorted(folder.glob('batch-*/*.private.json')):
            if evidence.name != 'packet.private.json':
                add(evidence, 'private', 'evidence')

    report_refs = []
    for wave_number, result in enumerate(wave_results, 1):
        for supplement in result['supplements']:
            for proof in supplement['report']['proofs']:
                add(Path(supplement['path']) / proof, 'private', 'evidence')
        path = root / 'quality/reviews' / f'{RESULT_PREFIX}-wave-{wave_number:02d}.json'
        if path.exists() and read(path) != result:
            raise ValueError('refusing to overwrite a different wave report')
        dump(path, result)
        add(path, 'repository', 'journal')
        report_refs.append({'path': str(path.relative_to(root)), 'sha256': sha(path)})

    updated = build_registry(sources, root, private_root)
    validate_work_lineage(baseline_work, updated, 'no-invalidated-retry')
    if len(updated['records']) != reservation_record_count(run) + combined['new_records']:
        raise ValueError('work registry coverage mismatch')
    result = {
        'schema_version': 1,
        'scope': 'Four thousand new body reviews, recorded as work and staged adoption candidates only.',
        'baseline_reviewed_records': combined['baseline_records'],
        'new_records': combined['new_records'],
        'reviewed_records_if_adoption_is_applied': combined['reviewed_records_if_adoption_is_applied'],
        'new_adoption_counts': combined['new_adoption_counts'],
        'cumulative_adoption_counts_if_applied': combined['cumulative_adoption_counts_if_applied'],
        'new_routes': combined['new_routes'],
        'independent_new_records': combined['independent_new_records'],
        'supplemental_audits': sum(w['supplemental_audits'] for w in wave_results),
        'topic_counts': read(run / 'reservation.json')['topic_counts'],
        'opinion_counts': read(run / 'reservation.json')['opinion_counts'],
        'wave_reports': report_refs,
        'work_registry_records': len(updated['records']),
        'adoption_ledger_applied': False,
        'canonical_changes': 0,
        'public_changes': 0,
        'registered_reread_increment': 0,
    }
    result_path = root / 'quality/reviews' / f'{RESULT_PREFIX}-results.json'
    if result_path.exists() and read(result_path) != result:
        raise ValueError('refusing to overwrite a different result report')
    dump(result_path, result)
    if sha(work_path) != sha(run / 'work-before.private.json'):
        raise ValueError('work registry changed during registration')
    dump(work_path, updated)
    load_registry(work_path, root, private_root)
    return result


def reservation_record_count(run: Path) -> int:
    return read(run / 'reservation.json')['baseline_work_records']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--supplement-manifest', type=Path,
                        help='Explicit mapping of wave names to private supplement directories')
    args = parser.parse_args()
    result = register_work_only(args.root, args.private_root, args.run,
                                read(args.supplement_manifest) if args.supplement_manifest else None)
    print(json.dumps(result, ensure_ascii=False))
