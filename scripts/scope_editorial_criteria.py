"""Produce a body-free reassessment queue; never change adoption or criteria."""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from scripts.editorial_acceptance import assess_batch
from scripts.verify_editorial_wave import collect_wave
from scripts.verify_editorial_hundred import read, sha

# Conservative scope from the five archived quality-gate notes. These are
# reassessment boundaries, not new classification rules or adoption approval.
SCOPES = {
    6: ['koshitsu-tenpakai'],
    12: ['koshitsu-tenpakai', 'ai-copyright'],
    26: ['koshitsu-tenpakai'],
    28: ['koshitsu-tenpakai', 'ai-copyright', 'elderly-license-revocation'],
    34: ['koshitsu-tenpakai', 'fukushuto'],
}


def build(root, run):
    ledger_path = root / 'data/verification/editorial-adoption.json'
    ledger = read(ledger_path)
    targets = [r for r in ledger['records'] if r['adoption_basis'] == 'criteria_issue']
    if len(targets) != 65 or {r['batch'] for r in targets} != set(SCOPES):
        raise ValueError('snapshot scope changed; requires a new scope review')
    output = []
    proofs = {}
    for batch, topics in SCOPES.items():
        collected, _ = collect_wave(root, run, batch, batch)
        d = run / f'batch-{batch:02d}'
        proofs.update(collected['proofs'])
        old = {r['index']: r for r in collected['journal']}
        gate = copy.deepcopy(read(d / 'quality_gate.private.json'))
        if gate['systemic_criteria_issue'] is not True:
            raise ValueError('expected archived systemic stop')
        gate['systemic_criteria_issue'] = False
        # Keep original conflicts and audit-topic stops. Only simulate removing
        # the whole-batch stop; never write this gate back to the evidence.
        trial = assess_batch(read(d / 'packet.private.json'),
                             read(d / 'editor.private.json'),
                             read(d / 'audit.private.json'), gate)
        simulated = {r['index']: r for r in trial['journal']}
        for r in targets:
            if r['batch'] != batch:
                continue
            for key, value in old[r['index']].items():
                if r.get(key) != value:
                    raise ValueError(f'ledger/proof mismatch: {batch}/{r["index"]}/{key}')
            s = simulated[r['index']]
            route = ('criteria_review' if r['topic'] in topics else
                     'additional_audit' if s['adoption_status'] != 'accepted' else
                     'reassessment_ready')
            output.append({k: r[k] for k in ('batch', 'index', 'topic', 'record_id_hash', 'body_sha256')} |
                          {'queue': route, 'existing_route': r['route'],
                           'independently_checked': r['independently_checked'],
                           'simulated_status_without_batch_stop': s['adoption_status'],
                           'adoption_unchanged': True})
    assert len(output) == 65
    assert len({(r['batch'], r['index']) for r in output}) == 65
    return {'schema_version': 1, 'purpose': 'scope_only_not_adoption',
            'ledger_sha256': sha(ledger_path),
            'policy_sha256': sha(root / 'scripts/editorial_acceptance.py'),
            'scoped_topics_by_batch': SCOPES, 'proofs': proofs,
            'counts': dict(Counter(r['queue'] for r in output)),
            'topic_counts': {t: dict(Counter(r['queue'] for r in output if r['topic'] == t))
                             for t in sorted({r['topic'] for r in output})},
            'records': output, 'new_body_reviews': 0, 'adoption_changes': 0,
            'canonical_changes': 0, 'registered_reread_increment': 0}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = build(a.root, a.run)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result['counts'], ensure_ascii=False))
