import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.editorial_work_registry import build_registry, load_registry, current_attempts, fingerprint, sha, checked_packet
from scripts.prepare_next_editorial_batch import select_batch


def registered_cycle_expectations(reports):
    """Derive ledger growth from formal results, with explicit cycle limits."""
    ordinary = {name: value for name, value in reports.items()
                if name in {f'2026-09-08-nonkoshitsu-cycle{i:02d}-results.json' for i in range(1, 5)}}
    short = [(name, value) for name, value in reports.items() if name not in ordinary]
    if any(name != '2026-09-08-nonkoshitsu-short352-results.json' for name, _ in short):
        raise ValueError('unknown formal non-royal result')
    expected, attempted = 8080, 80
    for i in range(1, 5):
        name = f'2026-09-08-nonkoshitsu-cycle{i:02d}-results.json'
        if name not in ordinary:
            if any(f'2026-09-08-nonkoshitsu-cycle{j:02d}-results.json' in ordinary for j in range(i+1, 5)):
                raise ValueError('formal cycle results have a gap')
            break
        report = ordinary[name]
        if report['new_body_reviews'] != 1000 or report['old_work_rows_preserved'] != expected:
            raise ValueError('ordinary registration coverage changed')
        expected += report['new_body_reviews']
        if report['work_registry_records'] != expected:
            raise ValueError('ordinary registered total differs')
    if short:
        if len(short) != 1 or len(ordinary) != 4:
            raise ValueError('short registration requires all four ordinary cycles')
        report = short[0][1]
        transitions = report['old_attempt_transitions']
        if (report['completed_target_records'] != 352 or report['new_body_reviews'] != 225 or
                report['distinct_id_verifications'] != 127 or len(transitions) != 56 or
                report['route_counts']['resume_unfinished_review'] != 56):
            raise ValueError('short registration coverage changed')
        identities = set()
        for transition in transitions:
            old, new = transition['old'], transition['new']
            identity = tuple(old[k] for k in ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256', 'criteria_sha256'))
            if (old['state'] != 'attempted' or new['state'] not in {'retain_candidate', 'change_candidate', 'hold'} or
                    any(old[k] != new[k] for k in ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256', 'criteria_sha256')) or
                    not set(old['evidence']) <= set(new['evidence']) or old['scope_only_audits'] != new['scope_only_audits']):
                raise ValueError('old attempt transition lost identity or history')
            identities.add(identity)
        if len(identities) != 56:
            raise ValueError('duplicate old attempt transition')
        expected += report['completed_target_records'] - len(transitions)
        attempted -= len(transitions)
        if report['work_registry_records'] != expected or expected != 12376 or attempted != 24:
            raise ValueError('final registry total differs')
    for report in reports.values():
        if any(report[k] != 0 for k in ('canonical_changes', 'adoption_changes', 'public_changes')):
            raise ValueError('work-only registration changed protected data')
    return expected, attempted


class EditorialWorkRegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'criteria.py').write_text('criteria v1')
        self.criteria = {'topic': {'source': 'criteria.py', 'source_sha256': sha(self.root/'criteria.py'), 'text': 'criteria'}}
        self.rows = []
        for i in range(4):
            text = 'test text ' + str(i)
            classification = {'stance': str(i)}
            self.rows.append({'topic': 'topic', 'record_id_hash': 'sha256:' + hashlib.sha256(str(i).encode()).hexdigest(), 'text': text, 'body_sha256': hashlib.sha256(text.encode()).hexdigest(), 'classification': classification, 'classification_sha256': fingerprint(classification), 'sample_id': 'sample' + str(i)})
        self.packet = {'records': self.rows, 'criteria': self.criteria, 'input_sha256': fingerprint(self.rows)}
        journal = [{**r, 'route': route} for r, route in zip(self.rows, ['retain_candidate', 'change_candidate', 'hold'])]
        self.sources = []
        for name, kind, value in [('packet.json', 'packet', self.packet), ('journal.json', 'journal', {'journal': journal}), ('audit.json', 'scope_audit', {'consistent': ['sample3']})]:
            (self.root/name).write_text(json.dumps(value))
            self.sources.append({'storage': 'private', 'path': name, 'sha256': sha(self.root/name), 'kind': kind})

    def build(self):
        return build_registry(self.sources, self.root, self.root)

    def test_counts_candidates_hold_scope_and_no_credit(self):
        ledger = self.build()
        self.assertEqual(ledger['counts'], dict(attempted=1, retain_candidate=1, change_candidate=1, hold=1))
        self.assertTrue(all(not r['canonical_applied'] and not r['counts_as_registered_editorial_reread'] for r in ledger['records']))
        row = next(r for r in ledger['records'] if r['state'] == 'attempted')
        self.assertEqual(len(row['scope_only_audits']), 1)
        self.assertEqual(ledger['automatic_reread_credit'], 0)

    def test_excludes_all_states_and_same_topic_duplicates(self):
        ledger = self.build()
        attempts = current_attempts(ledger, self.criteria)
        duplicate = {**self.rows[0], 'record_id_hash': 'different'}
        self.assertEqual(select_batch({'topic': self.rows + [duplicate]}, attempts), [])
        self.assertEqual(len(select_batch({'other': [duplicate]}, attempts)), 1)
        self.assertEqual(len(select_batch({'topic': [duplicate, duplicate]}, [])), 1)

    def test_body_and_label_change_requeue(self):
        attempts = current_attempts(self.build(), self.criteria)
        for field in ['body_sha256', 'classification_sha256']:
            row = {**self.rows[0], field: 'new-version'}
            self.assertEqual(len(select_batch({'topic': [row]}, attempts)), 1)

    def test_criteria_changes_stop(self):
        ledger = self.build()
        changed = copy.deepcopy(self.criteria)
        changed['topic']['text'] = 'new'
        with self.assertRaises(ValueError): current_attempts(ledger, changed)
        (self.root/'criteria.py').write_text('criteria v2')
        with self.assertRaises(ValueError): self.build()

    def test_missing_and_tampered_evidence_stop(self):
        p = self.root/'audit.json'
        saved = p.read_bytes()
        p.write_text('{}')
        with self.assertRaises(ValueError): self.build()
        p.unlink()
        with self.assertRaises(ValueError): self.build()
        p.write_bytes(saved)
        ledger = self.build()
        ledger['records'][0]['state'] = 'attempted'
        ledger['records'][0]['canonical_applied'] = True
        (self.root/'registry.json').write_text(json.dumps(ledger))
        with self.assertRaises(ValueError): load_registry(self.root/'registry.json', self.root, self.root)

    def test_reservation_packet_checks_content_and_criteria(self):
        self.assertEqual(len(checked_packet(self.packet, self.root)), 4)
        self.packet['records'][0]['classification']['stance'] = 'tampered'
        with self.assertRaises(ValueError): checked_packet(self.packet, self.root)

    def test_committed_summary_and_body_free(self):
        p = Path(__file__).resolve().parents[1]/'data/verification/editorial-work.json'
        ledger = json.loads(p.read_text())
        reports = {f.name: json.loads(f.read_text()) for f in
                   (p.parents[2]/'quality/reviews').glob('2026-09-08-nonkoshitsu-*-results.json')}
        expected, attempted = registered_cycle_expectations(reports)
        # Royal three-domain reviews retain the old taxonomy fingerprint and
        # promote only the explicitly linked unfinished work rows. Count their
        # completed per-batch journals, not an adoption total or target quota.
        royal = [json.loads(f.read_text()) for f in
                 (p.parents[2]/'quality/reviews/royal782').glob('batch-*.json')]
        royal_rows = [row for manifest in royal for row in manifest['journal']]
        self.assertEqual(len({(r['topic'], r['record_id_hash']) for r in royal_rows}), len(royal_rows))
        resumed = sum(r['scope_route'] == 'resume_unfinished_review' for r in royal_rows)
        expected += len(royal_rows) - resumed
        attempted -= resumed
        self.assertTrue(all(r['route'] == 'hold' and not r['canonical_applied'] for r in royal_rows))
        self.assertTrue(all(m['legacy_adoption_allowed'] is False for m in royal))
        self.assertEqual(len(ledger['records']), expected)
        self.assertEqual(sum(ledger['counts'].values()), expected)
        current = json.loads((p.parent/'editorial-adoption-current.json').read_text())
        # The extra 4,000 are completed work only; adoption remains at its baseline.
        self.assertEqual(current['reviewed_records'], 4000)
        self.assertEqual(ledger['counts']['attempted'], attempted)
        self.assertEqual(len({(r['topic'], r['record_id_hash']) for r in ledger['records']}), expected)
        self.assertEqual(sum(bool(r['scope_only_audits']) for r in ledger['records']), 10)
        for row in ledger['records']:
            self.assertFalse({'text', 'tweet_id', 'reason'} & row.keys())
        self.assertTrue(all(not Path(s['path']).is_absolute() for s in ledger['sources']))


class RegisteredCycleExpectationsTest(unittest.TestCase):
    def ordinary(self, n):
        return {f'2026-09-08-nonkoshitsu-cycle{i:02d}-results.json': {
            'new_body_reviews': 1000, 'old_work_rows_preserved': 8080+(i-1)*1000,
            'work_registry_records': 8080+i*1000, 'canonical_changes': 0,
            'adoption_changes': 0, 'public_changes': 0} for i in range(1, n+1)}

    def complete(self):
        reports = self.ordinary(4)
        transitions = []
        for i in range(56):
            old = dict(topic='topic', record_id_hash=str(i), body_sha256='body',
                       classification_sha256='labels', criteria_sha256='criteria',
                       state='attempted', evidence=['old-attempt'], scope_only_audits=[])
            transitions.append({'old': old, 'new': {**old, 'state': 'hold', 'evidence': ['old-attempt', 'completion']}})
        reports['2026-09-08-nonkoshitsu-short352-results.json'] = {
            'completed_target_records': 352, 'new_body_reviews': 225,
            'distinct_id_verifications': 127, 'old_attempt_transitions': transitions,
            'route_counts': {'resume_unfinished_review': 56}, 'work_registry_records': 12376,
            'canonical_changes': 0, 'adoption_changes': 0, 'public_changes': 0}
        return reports

    def test_each_registered_stage_and_final_attempt_reduction(self):
        for count in range(5):
            with self.subTest(cycles=count):
                self.assertEqual(registered_cycle_expectations(self.ordinary(count)), (8080+1000*count, 80))
        self.assertEqual(registered_cycle_expectations(self.complete()), (12376, 24))

    def test_gaps_and_summary_total_mismatch_are_rejected(self):
        reports = self.ordinary(2)
        del reports['2026-09-08-nonkoshitsu-cycle01-results.json']
        with self.assertRaisesRegex(ValueError, 'gap'):
            registered_cycle_expectations(reports)
        reports = self.ordinary(1)
        next(iter(reports.values()))['work_registry_records'] += 1
        with self.assertRaisesRegex(ValueError, 'registered total differs'):
            registered_cycle_expectations(reports)

    def test_short_cannot_precede_four_cycles_or_repeat_old_attempts(self):
        reports = self.complete()
        del reports['2026-09-08-nonkoshitsu-cycle04-results.json']
        with self.assertRaisesRegex(ValueError, 'requires all four'):
            registered_cycle_expectations(reports)
        reports = self.complete()
        transitions = reports['2026-09-08-nonkoshitsu-short352-results.json']['old_attempt_transitions']
        transitions[1] = copy.deepcopy(transitions[0])
        with self.assertRaisesRegex(ValueError, 'duplicate old attempt'):
            registered_cycle_expectations(reports)

    def test_short_preserves_old_evidence(self):
        reports = self.complete()
        reports['2026-09-08-nonkoshitsu-short352-results.json']['old_attempt_transitions'][0]['new']['evidence'] = ['completion']
        with self.assertRaisesRegex(ValueError, 'lost identity or history'):
            registered_cycle_expectations(reports)


if __name__ == '__main__': unittest.main()
