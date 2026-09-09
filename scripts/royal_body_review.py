"""Private, immutable <=20-row royal reviews; no classification generation.

The old registry's criteria fingerprint describes the input taxonomy. Actual
review criteria, schema and writer versions are separately pinned in every run.
All records remain on hold for legacy adoption; three-domain agreement is not
permission to map them back into one legacy stance.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from scripts.editorial_work_registry import build_registry, load_registry, fingerprint, sha
from scripts.prepare_body_review_pilot import inventory
from scripts.prepare_editorial_continuation import build_criteria
from scripts.resolve_remaining_review_scope import load_resolution
from scripts.royal_review_schema import validate_decision, SCHEMA_VERSION, CORE_FIELDS

TOPIC = 'koshitsu-tenpakai'
CRITERIA = 'quality/designs/body-review/KOSHITSU_SEPARATE_AXES_V6.md'
WRITER = 'scripts/royal_body_review.py'
SCHEMA = 'scripts/royal_review_schema.py'
KEYS = ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256')
PRIMARY = {'new_body_review', 'resume_unfinished_review', 'restart_invalid_reservation'}


def read(path):
    return json.loads(Path(path).read_text())


def need(test, message):
    if not test:
        raise ValueError(message)


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def key(row):
    return tuple(row[k] for k in KEYS)


def current_remaining(root, private, registry_path=None):
    work = load_registry(registry_path or root / 'data/verification/editorial-work.json', root, private)
    report, queues = inventory(root, private)
    complete = {key(r) for r in work['records'] if r['state'] != 'attempted'}
    rows = [dict(r, topic=t) for t, group in queues.items() for r in group
            if report['topics'][t]['published'] and r['opinion'] and key(dict(r, topic=t)) not in complete]
    need(len(set(map(key, rows))) == len(rows), 'duplicate public identity')
    return rows, work, report


def freeze(root, private, run, assignments, approval):
    root, private, run = map(lambda p: Path(p).resolve(), (root, private, run))
    need(not run.exists() and run.is_relative_to(private) and not run.is_relative_to(root), 'new private run required')
    need(set(assignments) == {'editor_a', 'editor_b', 'audit'}, 'three separate assignments required')
    need(len({a['actor'] for a in assignments.values()}) == 3 and
         len({str(Path(a['worktree']).resolve()) for a in assignments.values()}) == 3, 'assignment separation failed')
    versions = {p: sha(root / p) for p in (CRITERIA, SCHEMA, WRITER)}
    approval = Path(approval).resolve()
    approved = read(approval)
    need(approved['status'] == 'pass' and approved['versions'] == versions, 'independent implementation review required')
    rows, work, report = current_remaining(root, private)
    previous = read(private / 'body-review-pilot/20260909-nonkoshitsu4352-handoff/final-results.private.json')['remaining_ids']
    need(len(rows) == 782 and set(map(key, rows)) == set(map(key, previous)) and
         {r['topic'] for r in rows} == {TOPIC}, '782 identity scope differs; report instead of forcing count')
    summary = read(root / 'data/verification/editorial-review-scope.json')
    scope = load_resolution(summary, private)
    routes = {key(r): r for r in scope['records']}
    rows = [dict(r, scope_route=routes[key(r)]['route'], dependency=routes[key(r)]['dependency']) for r in rows]
    # Existing completed work is already excluded above. Search actual outstanding
    # packets too; historical attempted IDs are allowed only via frozen scope.
    active = set()
    historical_packets = {s['path'] for s in work['sources'] if s['storage'] == 'private' and s['kind'] == 'packet'}
    for path in (private / 'body-review-pilot').rglob('packet.private.json'):
        if str(path.relative_to(private)) in historical_packets:
            continue
        if any((p / 'invalidated.private.json').exists() for p in path.parents if p.is_relative_to(private)):
            continue
        for row in read(path).get('records', []):
            if all(k in row for k in KEYS):
                active.add(key(row))
    need(not active.intersection(map(key, rows)), 'another incomplete reservation owns target IDs')
    criteria = {TOPIC: build_criteria(root)[TOPIC]}
    need({fingerprint(criteria[TOPIC])} == {r['criteria_sha256'] for r in work['records'] if r['topic'] == TOPIC}, 'input taxonomy differs')
    run.mkdir()
    write_new(run / 'work-before.private.json', work)
    write_new(run / 'implementation-review.private.json', approved)
    (run / 'criteria.md').write_bytes((root / CRITERIA).read_bytes())
    baseline = {'versions': versions, 'canonical': {v['canonical_file']: v['canonical_sha256'] for v in report['topics'].values()},
                'THEMES.yaml': sha(root / 'THEMES.yaml'), 'work_before_sha256': sha(run / 'work-before.private.json'),
                'adoption_sha256': sha(root / 'data/verification/editorial-adoption-current.json'),
                'scope_summary_sha256': sha(root / 'data/verification/editorial-review-scope.json'),
                'scope_evidence_sha256': summary['resolution_sha256']}
    write_new(run / 'baseline.private.json', baseline)
    batches = []
    for group in ([r for r in rows if r['scope_route'] in PRIMARY], [r for r in rows if r['scope_route'] not in PRIMARY]):
        group.sort(key=key)
        for offset in range(0, len(group), 20):
            batch = len(batches) + 1
            folder = run / f'batch-{batch:02d}'
            raw = group[offset:offset + 20]
            machine = {'records': raw, 'input_sha256': fingerprint(raw), 'criteria': criteria,
                       'criteria_meaning': 'input taxonomy only; NOT the review decision criteria'}
            write_new(folder / 'registry-packet.private.json', machine)
            packet = {'schema_version': SCHEMA_VERSION, 'versions': versions, 'topic': TOPIC, 'records': [
                {k: r[k] for k in (*KEYS, 'text', 'scope_route', 'dependency')} | {'index': i}
                for i, r in enumerate(raw)]}
            write_new(folder / 'packet.private.json', packet)
            batches.append({'batch': batch, 'count': len(raw), 'editor': 'editor_a' if batch % 2 else 'editor_b',
                            'packet_sha256': sha(folder / 'packet.private.json'),
                            'registry_packet_sha256': sha(folder / 'registry-packet.private.json')})
    reservation = {'schema_version': SCHEMA_VERSION, 'created_epoch': time.time(), 'assignments': assignments,
                   'versions': versions, 'baseline_sha256': sha(run / 'baseline.private.json'),
                   'implementation_review_sha256': sha(run / 'implementation-review.private.json'),
                   'batches': batches, 'target_count': len(rows), 'routes': dict(Counter(r['scope_route'] for r in rows)),
                   'audit_policy': 'every record independently before comparison', 'legacy_adoption_allowed': False}
    write_new(run / 'reservation.json', reservation)
    write_new(run / 'reservation-seal.json', {'sha256': sha(run / 'reservation.json')})
    return reservation


def checked_run(run):
    run = Path(run)
    need(sha(run / 'reservation.json') == read(run / 'reservation-seal.json')['sha256'], 'reservation changed')
    reservation = read(run / 'reservation.json')
    root = Path(__file__).resolve().parents[1]
    need(all(sha(root / p) == h for p, h in reservation['versions'].items()), 'writer/schema/criteria changed')
    need(sha(run / 'criteria.md') == reservation['versions'][CRITERIA], 'frozen criteria changed')
    need(sha(run / 'baseline.private.json') == reservation['baseline_sha256'], 'baseline changed')
    need(sha(run / 'implementation-review.private.json') == reservation['implementation_review_sha256'], 'approval changed')
    need(sha(run / 'work-before.private.json') == read(run / 'baseline.private.json')['work_before_sha256'], 'work baseline changed')
    return reservation


def packet_for(run, batch):
    reservation = checked_run(run)
    need(type(batch) is int, 'invalid batch')
    matches = [b for b in reservation['batches'] if b['batch'] == batch]
    need(len(matches) == 1, 'unreserved batch')
    meta = matches[0]
    folder = Path(run) / f'batch-{batch:02d}'
    need(sha(folder / 'packet.private.json') == meta['packet_sha256'], 'packet changed')
    packet = read(folder / 'packet.private.json')
    need(packet['schema_version'] == reservation['schema_version'] == SCHEMA_VERSION and
         packet['versions'] == reservation['versions'] and packet['topic'] == TOPIC, 'packet schema/version/theme differs')
    rows = packet['records']
    need(1 <= len(rows) <= 20 and len(rows) == meta['count'] and
         [r['index'] for r in rows] == list(range(len(rows))) and
         {r['topic'] for r in rows} == {TOPIC} and len(set(map(key, rows))) == len(rows), 'bad packet scope')
    need(all(hashlib.sha256(r['text'].encode()).hexdigest() == r['body_sha256'] for r in rows), 'body hash differs')
    return reservation, meta, folder, packet


def actor_for(reservation, meta, role, actor):
    need(role in {'editor', 'audit'}, 'invalid role')
    assigned = reservation['assignments'][meta['editor'] if role == 'editor' else 'audit']
    need(assigned['actor'] == actor and Path.cwd().resolve() == Path(assigned['worktree']).resolve(), 'wrong actor/worktree')
    return assigned


def show(run, batch, role, actor):
    reservation, meta, folder, packet = packet_for(run, batch)
    assigned = actor_for(reservation, meta, role, actor)
    path = folder / f'{role}-start.private.json'
    if not path.exists():
        write_new(path, {'actor': actor, 'worktree': assigned['worktree'], 'role': role, 'started_epoch': time.time(),
                         'packet_sha256': meta['packet_sha256'], 'versions': reservation['versions'],
                         'reservation_sha256': sha(Path(run) / 'reservation.json')})
    return packet


def save(run, batch, role, actor, values):
    reservation, meta, folder, packet = packet_for(run, batch)
    actor_for(reservation, meta, role, actor)
    start = read(folder / f'{role}-start.private.json')
    need(start['actor'] == actor, 'start actor differs')
    need(not (folder / f'{role}.private.json').exists(), 'saved decisions are immutable')
    need(isinstance(values, list) and [r.get('index') for r in values if isinstance(r, dict)] == list(range(meta['count'])) and len(values) == meta['count'], 'exact ordered decisions required')
    for row in values:
        validate_decision(row)
    draft = {'records': values, 'recorded_epoch': time.time()}
    draft_path = folder / f'{role}-draft.private.json'
    if draft_path.exists():
        need(read(draft_path)['records'] == values, 'never replace an existing draft')
        draft = read(draft_path)
    else:
        write_new(draft_path, draft)
    output = {**start, 'finished_epoch': time.time(), 'records': values, 'identity': [
        {k: r[k] for k in KEYS} for r in packet['records']], 'independent_values_before_comparison': True,
        'manual_body_review': True, 'legacy_adoption_allowed': False}
    write_new(folder / f'{role}.private.json', output)
    return {'saved': len(values), 'role': role, 'batch': batch}


def verified_pair(run, batch, require_audit=True, role_only=None):
    reservation, meta, folder, packet = packet_for(run, batch)
    decisions = []
    need(role_only in {None, 'editor', 'audit'}, 'invalid verification role')
    roles = [role_only] if role_only else (['editor', 'audit'] if require_audit else ['editor'])
    for role in roles:
        start = read(folder / f'{role}-start.private.json')
        draft = read(folder / f'{role}-draft.private.json')
        final = read(folder / f'{role}.private.json')
        expected = reservation['assignments'][meta['editor'] if role == 'editor' else 'audit']
        need(start['actor'] == expected['actor'] and start['worktree'] == expected['worktree'], 'assigned reviewer differs')
        need(all(final[k] == v for k, v in start.items()), 'start binding differs')
        need(start['versions'] == reservation['versions'] and start['packet_sha256'] == meta['packet_sha256'] and
             start['reservation_sha256'] == sha(Path(run) / 'reservation.json'), 'decision version differs')
        need(start['started_epoch'] <= draft['recorded_epoch'] <= final['finished_epoch'], 'invalid chronology')
        need(final['records'] == draft['records'] and [r['index'] for r in final['records']] == list(range(meta['count'])), 'incomplete/different decisions')
        need(final['identity'] == [{k: r[k] for k in KEYS} for r in packet['records']], 'decision identity differs')
        need(final['manual_body_review'] is True and final['independent_values_before_comparison'] is True and final['legacy_adoption_allowed'] is False, 'invalid method')
        for row in final['records']:
            validate_decision(row)
        decisions.append(final)
    if len(decisions) == 2:
        need(decisions[0]['actor'] != decisions[1]['actor'] and decisions[0]['worktree'] != decisions[1]['worktree'], 'self audit')
    return reservation, meta, folder, packet, decisions


def comparison(run, batch, actor):
    reservation, meta, folder, packet, decisions = verified_pair(run, batch)
    actor_for(reservation, meta, 'audit', actor)
    path = folder / 'comparison-start.private.json'
    if not path.exists():
        write_new(path, {'actor': actor, 'compared_epoch': time.time(), 'editor_sha256': sha(folder / 'editor.private.json'),
                         'audit_sha256': sha(folder / 'audit.private.json')})
    return [{'index': i, 'editor': a, 'audit': b} for i, (a, b) in enumerate(zip(decisions[0]['records'], decisions[1]['records']))]


def validate_checks(checks, count):
    need(isinstance(checks, list) and len(checks) == count and
         all(isinstance(r, dict) for r in checks) and
         [r.get('index') for r in checks] == list(range(count)), 'individual gate checks required')
    for row in checks:
        need(set(row) == {'index', 'semantic_agreement', 'reason_sufficient', 'criteria_issue', 'reason'}, 'invalid gate fields')
        need(type(row['index']) is int and all(type(row[k]) is bool for k in ('semantic_agreement', 'reason_sufficient', 'criteria_issue')) and
             isinstance(row['reason'], str) and bool(row['reason'].strip()), 'invalid individual quality assessment')


def save_gate(run, batch, actor, checks):
    reservation, meta, folder, packet, decisions = verified_pair(run, batch)
    actor_for(reservation, meta, 'audit', actor)
    compared = read(folder / 'comparison-start.private.json')
    need(compared['compared_epoch'] >= max(d['finished_epoch'] for d in decisions), 'comparison preceded independent save')
    validate_checks(checks, meta['count'])
    write_new(folder / 'quality_gate.private.json', {'actor': actor, 'finished_epoch': time.time(), 'checks': checks,
              'comparison_sha256': sha(folder / 'comparison-start.private.json'),
              'editor_sha256': sha(folder / 'editor.private.json'), 'audit_sha256': sha(folder / 'audit.private.json'),
              'versions': reservation['versions']})
    return {'gated': len(checks), 'batch': batch}


def collect_batch(run, batch):
    reservation, meta, folder, packet, decisions = verified_pair(run, batch)
    gate = read(folder / 'quality_gate.private.json')
    compared = read(folder / 'comparison-start.private.json')
    need(gate['comparison_sha256'] == sha(folder / 'comparison-start.private.json') and
         all(gate[k] == compared[k] == sha(folder / f'{k.split("_")[0]}.private.json') for k in ('editor_sha256', 'audit_sha256')), 'comparison/gate source changed')
    need(max(d['finished_epoch'] for d in decisions) <= compared['compared_epoch'] <= gate['finished_epoch'], 'invalid gate chronology')
    need(gate['actor'] == compared['actor'] == reservation['assignments']['audit']['actor'] and gate['versions'] == reservation['versions'], 'gate actor/version differs')
    validate_checks(gate['checks'], meta['count'])
    result = []
    for source, a, b, check in zip(packet['records'], decisions[0]['records'], decisions[1]['records'], gate['checks']):
        # Target names and auxiliary text are checked semantically by the auditor.
        coded = all(a[k] == b[k] for k in CORE_FIELDS if k not in {'provisions', 'unknown_fields'}) and set(a['unknown_fields']) == set(b['unknown_fields'])
        supported = coded and check['semantic_agreement'] and check['reason_sufficient'] and not check['criteria_issue'] and all(not x['uncertain'] and x['evidence_sufficient'] for x in (a, b))
        result.append({**{k: source[k] for k in KEYS}, 'batch': batch, 'index': source['index'],
                       'route': 'hold', 'adoption_status': 'hold' if check['reason_sufficient'] else 'pending_evidence',
                       'three_domain_agreement': supported, 'coded_agreement': coded,
                       'scope_route': source['scope_route'], 'canonical_applied': False,
                       'counts_as_registered_editorial_reread': False})
    return result


def status(run):
    reservation = checked_run(run)
    counts = Counter(); incomplete = []
    for meta in reservation['batches']:
        folder = Path(run) / f"batch-{meta['batch']:02d}"
        for role in ('editor', 'audit'):
            if (folder / f'{role}.private.json').exists():
                # Audit-only saves are legal: blind audits need not wait for editors.
                *_, verified = verified_pair(run, meta['batch'], role_only=role)
                final = verified[0]
                counts[role] += len(final['records'])
            elif (folder / f'{role}-start.private.json').exists() or (folder / f'{role}-draft.private.json').exists():
                incomplete.append({'batch': meta['batch'], 'role': role, 'stage': 'draft' if (folder / f'{role}-draft.private.json').exists() else 'start'})
        if (folder / 'quality_gate.private.json').exists():
            rows = collect_batch(run, meta['batch']); counts['gated'] += len(rows)
            counts.update(r['adoption_status'] for r in rows)
            counts['three_domain_agreement'] += sum(r['three_domain_agreement'] for r in rows)
    return {'target': reservation['target_count'], **counts, 'incomplete': incomplete,
            'remaining_to_gate': reservation['target_count'] - counts['gated'], 'adoption_candidates': 0}


def replace_work(path, candidate):
    """Replace one reviewed ledger atomically; durable intent precedes this call."""
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.royal-work-', delete=False) as stream:
        temp = Path(stream.name)
        stream.write(candidate.read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def register_completed(root, private, run):
    """Register only fully completed batches; replay every saved judgment first."""
    root, private, run = map(lambda p: Path(p).resolve(), (root, private, run))
    reservation = checked_run(run)
    baseline = read(run / 'baseline.private.json')
    for rel, expected in baseline['canonical'].items():
        need(sha(root / rel) == expected, 'canonical source changed')
    need(sha(root / 'THEMES.yaml') == baseline['THEMES.yaml'] and
         sha(root / 'data/verification/editorial-adoption-current.json') == baseline['adoption_sha256'] and
         sha(root / 'data/verification/editorial-review-scope.json') == baseline['scope_summary_sha256'], 'protected source changed')
    work_path = root / 'data/verification/editorial-work.json'
    receipts = sorted(run.glob('registration-*.private.json'))
    if receipts:
        last = read(receipts[-1])
        # Recovery after intent was saved but before the atomic replacement.
        if sha(work_path) == last['work_before_sha256']:
            candidate = run / last['candidate_file']
            need(sha(candidate) == last['work_after_sha256'], 'recovery candidate changed')
            load_registry(candidate, root, private)
            recovery_rows, _, _ = current_remaining(root, private, candidate)
            need([{k: r[k] for k in KEYS} for r in recovery_rows] == last['remaining_ids'], 'recovery inventory changed')
            replace_work(work_path, candidate)
    expected = read(receipts[-1])['work_after_sha256'] if receipts else baseline['work_before_sha256']
    need(sha(work_path) == expected, 'work registry changed outside this run')
    work = load_registry(work_path, root, private)
    before = read(run / 'work-before.private.json')
    sources = work['sources'][:]

    def add(path, storage, kind):
        base = root if storage == 'repository' else private
        entry = {'path': str(path.relative_to(base)), 'storage': storage, 'kind': kind, 'sha256': sha(path)}
        old = next((s for s in sources if (s['path'], s['storage']) == (entry['path'], storage)), None)
        need(old is None or old == entry, 'registered evidence changed')
        if old is None:
            sources.append(entry)

    for name in ('reservation.json', 'reservation-seal.json', 'baseline.private.json', 'work-before.private.json',
                 'implementation-review.private.json'):
        add(run / name, 'private', 'evidence')
    completed = []
    for meta in reservation['batches']:
        folder = run / f"batch-{meta['batch']:02d}"
        if not (folder / 'quality_gate.private.json').exists():
            continue
        rows = collect_batch(run, meta['batch'])
        need(sha(folder / 'registry-packet.private.json') == meta['registry_packet_sha256'], 'registry input changed')
        raw = read(folder / 'registry-packet.private.json')['records']
        need([key(r) for r in raw] == [key(r) for r in rows], 'registry and review packet identities differ')
        completed.extend(rows)
        proofs = []
        for evidence in sorted(folder.glob('*.private.json')):
            kind = 'packet' if evidence.name == 'registry-packet.private.json' else 'evidence'
            add(evidence, 'private', kind)
            proofs.append({'path': str(evidence.relative_to(private)), 'sha256': sha(evidence)})
        manifest = {'schema_version': SCHEMA_VERSION, 'review_versions': reservation['versions'],
                    'input_criteria_meaning': 'source taxonomy, not the three-domain review method',
                    'journal': rows, 'proofs': proofs, 'legacy_adoption_allowed': False,
                    'new_body_reviews': sum(r['scope_route'] in PRIMARY for r in rows),
                    'distinct_id_checks': sum(r['scope_route'] not in PRIMARY for r in rows)}
        path = root / f"quality/reviews/royal782/batch-{meta['batch']:02d}.json"
        if path.exists():
            need(read(path) == manifest, 'never replace completed batch manifest')
        else:
            write_new(path, manifest)
        add(path, 'repository', 'journal')
    need(completed and len(set(map(key, completed))) == len(completed), 'empty or duplicate completion')
    updated = build_registry(sources, root, private)
    old_keys = {r['work_key']: r for r in before['records']}
    new_keys = {r['work_key']: r for r in updated['records']}
    finished_keys = set(map(key, completed))
    for work_key, row in old_keys.items():
        need(work_key in new_keys, 'old work lost')
        new = new_keys[work_key]
        if key(row) not in finished_keys:
            need(row == new, 'unrelated old work changed')
        else:
            need(row['state'] == 'attempted' and new['state'] == 'hold' and
                 set(row['evidence']) <= set(new['evidence']) and row['scope_only_audits'] == new['scope_only_audits'], 'invalid legacy completion')
    old_overlap = sum(key(r) in finished_keys for r in before['records'])
    need(len(updated['records']) == len(before['records']) + len(completed) - old_overlap, 'work coverage differs')
    completed_by_key = {key(r): r for r in updated['records'] if key(r) in finished_keys}
    need(len(completed_by_key) == len(completed) and all(r['state'] == 'hold' for r in completed_by_key.values()), 'completed work not registered')
    next_number = len(receipts) + 1
    candidate = run / f'work-candidate-{next_number:03d}.private.json'
    if candidate.exists():
        need(read(candidate) == updated, 'uncommitted candidate differs')
    else:
        write_new(candidate, updated)
    load_registry(candidate, root, private)
    need(sha(work_path) == expected, 'work changed during validation')
    rows, _, _ = current_remaining(root, private, candidate)
    original = {key(r) for r in read(private / 'body-review-pilot/20260909-nonkoshitsu4352-handoff/final-results.private.json')['remaining_ids']}
    need(set(map(key, rows)) == original - finished_keys, 'public remainder differs by ID/body/classification')
    result = {'completed_ids': len(completed), 'new_body_reviews': sum(r['scope_route'] in PRIMARY for r in completed),
              'distinct_id_checks': sum(r['scope_route'] not in PRIMARY for r in completed),
              'independent_audits': len(completed), 'additional_audits': 0, 'adoption_candidates': 0,
              'hold': sum(r['adoption_status'] == 'hold' for r in completed),
              'pending_evidence': sum(r['adoption_status'] == 'pending_evidence' for r in completed),
              'pending_audit': 0, 'three_domain_agreement': sum(r['three_domain_agreement'] for r in completed),
              'work_records': len(updated['records']), 'work_after_sha256': sha(candidate),
              'work_before_sha256': expected, 'candidate_file': candidate.name,
              'remaining_ids': [{k: r[k] for k in KEYS} for r in rows], 'remaining_public_opinions': len(rows),
              'legacy_attempts_completed': old_overlap, 'created_epoch': time.time(),
              'original_data_changes': 0, 'adoption_changes': 0, 'public_changes': 0}
    write_new(run / f'registration-{next_number:03d}.private.json', result)
    need(sha(work_path) == expected, 'work changed before atomic registration')
    replace_work(work_path, candidate)
    need(sha(work_path) == result['work_after_sha256'], 'atomic registration failed')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['show', 'compare', 'status'])
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--batch', type=int)
    parser.add_argument('--role', choices=['editor', 'audit'])
    parser.add_argument('--actor')
    args = parser.parse_args()
    value = status(args.run) if args.action == 'status' else comparison(args.run, args.batch, args.actor) if args.action == 'compare' else show(args.run, args.batch, args.role, args.actor)
    print(json.dumps(value, ensure_ascii=False))
