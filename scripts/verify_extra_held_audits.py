"""Verify additional independent audits of held rows without releasing a hold."""
import hashlib
from pathlib import Path

from scripts.summarize_editorial_batch import verified_reviews
from scripts.verify_editorial_hundred import read, sha


def overlay(run, result):
    run = Path(run)
    folders = sorted(run.glob('extra-held-audit-*'))
    if not folders:
        return result
    code = read(run / 'extra-held-code-integrity.private.json')
    root = Path(__file__).resolve().parents[1]
    expected = {'scripts/verify_extra_held_audits.py',
                'scripts/summarize_editorial_batch.py',
                'scripts/verify_editorial_hundred.py'}
    if set(code['code_sha256']) != expected or any(sha(root / rel) != h for rel, h in code['code_sha256'].items()):
        raise ValueError('held audit verification code changed')
    rows = {(r['batch'], r['index']): dict(r) for r in result['journal']}
    proofs, seen = [], set()
    for folder in folders:
        start = read(folder / 'audit-start.private.json')
        key = (start['source_batch'], start['source_index'])
        if key in seen:
            raise ValueError('duplicate held audit')
        seen.add(key)
        old = rows[key]
        if old['adoption_status'] != 'hold' or old['independently_checked']:
            raise ValueError('extra audit must target an unaudited held row')
        source = run / 'wave-01' / f'batch-{key[0]:02d}'
        if sha(source / 'editor.private.json') != start['source_editor_sha256'] or sha(source / 'packet.private.json') != start['source_packet_sha256']:
            raise ValueError('held audit source changed')
        packet = read(folder / 'packet.private.json')
        original = read(source / 'packet.private.json')
        raw = original['records'][key[1]]
        if packet != {'records': [raw], 'criteria': original['criteria']}:
            raise ValueError('held audit packet differs')
        editor_actor = read(source / 'editor-actor.private.json')
        if not start['actor'] or start['actor'] == editor_actor['actor'] or Path(start['worktree']).resolve() == Path(editor_actor['worktree']).resolve():
            raise ValueError('held self audit')
        audit = read(folder / 'audit.private.json')
        draft = read(folder / 'audit-draft.private.json')
        gate = read(folder / 'quality_gate.private.json')
        if audit.get('identity_writer') != 'manual_held_audit.v1' or any(audit.get(k) != v for k, v in start.items()) or start['new_body_review_credit'] != 0:
            raise ValueError('held audit identity or credit differs')
        if start['packet_sha256'] != sha(folder / 'packet.private.json'):
            raise ValueError('held audit packet hash changed')
        if not read(source / 'editor.private.json')['finished_epoch'] <= start['started_epoch'] <= draft['recorded_epoch'] <= audit['finished_epoch'] <= gate['recorded_epoch']:
            raise ValueError('held audit independence timing differs')
        verified_reviews(packet, audit, [0])
        decision = audit['reviews'][0]
        compact = [[0, *[decision['classification'][k] for k in ('is_relevant', 'is_opinion', 'main_issue', 'stance')], decision['uncertain'], decision['evidence_sufficient'], decision['reason']]]
        if draft['values'] != compact or type(decision['evidence_sufficient']) is not bool:
            raise ValueError('held audit draft differs')
        if gate['source_status'] != 'hold' or gate['result_status'] != 'hold' or gate['compared_after_independent_save'] is not True or gate['audit_sha256'] != sha(folder / 'audit.private.json'):
            raise ValueError('extra audit cannot release a hold')
        if any(raw[k] != old[k] for k in ('record_id_hash', 'body_sha256', 'classification_sha256')):
            raise ValueError('held source journal identity differs')
        rows[key] = {**old, 'independently_checked': True,
                     'independent_proposed': decision['classification'],
                     'independent_reason_sha256': hashlib.sha256(decision['reason'].encode()).hexdigest()}
        proofs.append({'source_key': list(key), 'proofs': {str(p.relative_to(run)): sha(p) for p in sorted(folder.glob('*.private.json'))}})
    return {**result, 'journal': [rows[(r['batch'], r['index'])] for r in result['journal']],
            'supplemental_audits': result['supplemental_audits'] + len(proofs),
            'extra_held_audits': proofs}
