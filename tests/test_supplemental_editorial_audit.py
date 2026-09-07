import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.editorial_work_registry import fingerprint
from scripts.supplemental_editorial_audit import prepare, show, save, compare, finish, collect
from scripts.verify_editorial_hundred import dump, read


class SupplementalEditorialAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name); self.root, self.out = base / 'root', base / 'private-run'
        (self.root / 'scripts').mkdir(parents=True)
        (self.root / 'scripts/editorial_acceptance.py').write_text('fixed policy\n')
        (self.root / 'criteria.json').write_text('fixed criteria\n')
        self.current = {'is_relevant': True, 'is_opinion': True, 'main_issue': 'issue', 'stance': 'yes'}
        self.criteria = {'issues': ['issue'], 'stances': ['yes', 'no'], 'source': 'criteria.json',
                         'source_sha256': hashlib.sha256(b'fixed criteria\n').hexdigest()}
        self.journal, self.sources = [], {}
        self.editor_reviews = {}
        for i in range(22):
            topic = 'a' if i < 21 else 'b'; body = f'body {i}'
            raw = {'topic': topic, 'tweet_id': str(i), 'record_id_hash': f'id-{i}', 'text': body,
                   'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
                   'classification': self.current, 'classification_sha256': fingerprint(self.current)}
            row = {'batch': 10 + i, 'index': i % 20, 'topic': topic, 'record_id_hash': f'id-{i}',
                   'body_sha256': raw['body_sha256'], 'classification_sha256': raw['classification_sha256'],
                   'current': self.current, 'proposed': self.current, 'changes': {}, 'route': 'retain_candidate',
                   'first_route': 'no_change',
                   'adoption_status': 'pending_audit', 'adoption_basis': 'additional_audit_required'}
            reason = f'initial reason {i}'
            row['reason_sha256'] = hashlib.sha256(reason.encode()).hexdigest()
            self.journal.append(row); self.sources[(10 + i, i % 20)] = (raw, self.criteria)
            self.editor_reviews[(10 + i, i % 20)] = {
                'record_id_hash': raw['record_id_hash'], 'body_sha256': raw['body_sha256'],
                'classification_sha256': raw['classification_sha256'], 'classification': self.current,
                'uncertain': False, 'evidence_sufficient': True, 'reason': reason}
        ignored = {**self.journal[0], 'batch': 999, 'adoption_status': 'accepted'}
        self.journal.append(ignored)

    def values(self, out, batch):
        packet = read(out / f'batch-{batch:02d}/packet.private.json')
        return [[i, True, True, 'issue', 'yes', False, True, f'independent reason {i}']
                for i in range(len(packet['records']))]

    def complete(self, batch, *, mutate=None, conflicts=None):
        show(self.out, batch); values = self.values(self.out, batch)
        if mutate: mutate(values)
        save(self.out, batch, values, 'independent-auditor')
        return finish(self.out, batch, conflicts or [], 'checked independently')

    def test_prepare_is_private_homogeneous_and_hides_initial_decision(self):
        summary = prepare(self.root, self.out, self.journal, self.sources)
        self.assertEqual(summary['records'], 22); self.assertEqual(summary['batches'], 3)
        for batch in range(1, 4):
            packet = read(self.out / f'batch-{batch:02d}/packet.private.json')
            self.assertLessEqual(len(packet['records']), 20)
            self.assertEqual(len({r['topic'] for r in packet['records']}), 1)
        view = show(self.out, 1)
        self.assertEqual(set(view), {'records'})
        self.assertEqual(set(view['records'][0]), {'index', 'body', 'current', 'criteria'})
        self.assertNotIn('proposed', str(view))
        with self.assertRaises(ValueError): prepare(self.root, self.out, self.journal, self.sources)

    def test_save_preserves_invalid_draft_and_never_overwrites(self):
        prepare(self.root, self.out, self.journal, self.sources); show(self.out, 1)
        values = self.values(self.out, 1); values[0][3] = 'unknown'
        with self.assertRaises(ValueError): save(self.out, 1, values, 'auditor')
        self.assertTrue((self.out / 'batch-01/audit-draft.private.json').exists())
        self.assertFalse((self.out / 'batch-01/audit.private.json').exists())
        with self.assertRaises(ValueError): save(self.out, 1, self.values(self.out, 1), 'auditor')

    def test_compare_only_after_independent_save_and_reveals_original(self):
        prepare(self.root, self.out, self.journal, self.sources); show(self.out, 1)
        with self.assertRaises(FileNotFoundError): compare(self.out, 1)
        save(self.out, 1, self.values(self.out, 1), 'auditor')
        result = compare(self.out, 1)
        self.assertEqual(result['rows'][0]['initial']['reason'], None)
        self.assertEqual(result['rows'][0]['audit']['reason'], 'independent reason 0')

    def test_prepare_pins_full_initial_editor_review_when_supplied(self):
        prepare(self.root, self.out, self.journal, self.sources, self.editor_reviews)
        show(self.out, 1); save(self.out, 1, self.values(self.out, 1), 'auditor')
        initial = compare(self.out, 1)['rows'][0]['initial']
        self.assertEqual(initial['reason'], 'initial reason 0')
        self.assertEqual(initial['evidence_source'], 'editor_review')

    def test_changed_initial_editor_review_stops_show(self):
        prepare(self.root, self.out, self.journal, self.sources, self.editor_reviews)
        path = self.out / 'batch-01/original.private.json'; value = read(path)
        value['records'][0]['reason'] = 'changed'; dump(path, value)
        with self.assertRaises(ValueError): show(self.out, 1)

    def test_finish_applies_strict_resolution_rules(self):
        prepare(self.root, self.out, self.journal, self.sources)
        def changes(values):
            values[0][4] = 'no'
            values[1][5] = True
            values[2][6] = False
        result = self.complete(1, mutate=changes, conflicts=[3])
        self.assertEqual(result['counts'], {'hold': 2, 'pending_evidence': 2, 'accepted': 16})
        with self.assertRaises(ValueError): finish(self.out, 1, [], '')

    def test_collect_returns_overlay_and_revalidates_all_evidence(self):
        prepare(self.root, self.out, self.journal, self.sources)
        for batch in range(1, 4): self.complete(batch)
        result = collect(self.root, self.out)
        self.assertEqual(result['counts'], {'accepted': 22})
        self.assertEqual(result['new_records'], 0)
        self.assertEqual(result['registered_reread_increment'], 0)
        self.assertEqual(len(result['overlay']), 22)
        self.assertEqual(result['overlay'][0]['old']['adoption_status'], 'pending_audit')
        self.assertEqual(result['overlay'][0]['new']['adoption_status'], 'accepted')
        self.assertEqual(result['overlay'][0]['source_key'], [10, 0])
        self.assertEqual(self.journal[0]['adoption_status'], 'pending_audit')
        draft = read(self.out / 'batch-01/audit-draft.private.json'); draft['values'][0][4] = 'no'
        dump(self.out / 'batch-01/audit-draft.private.json', draft)
        with self.assertRaises(ValueError): collect(self.root, self.out)

    def test_prepare_rejects_change_candidate_disguised_as_pending(self):
        self.journal[0] = {**self.journal[0], 'route': 'change_candidate', 'changes': {'stance': 'no'}}
        with self.assertRaises(ValueError): prepare(self.root, self.out, self.journal, self.sources)


if __name__ == '__main__':
    unittest.main()
