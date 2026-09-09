import json
from pathlib import Path
import tempfile
import unittest

from scripts.reassign_unopened_editorial_audits import reassign
from scripts.verify_editorial_hundred import dump, sha


class ReassignUnopenedEditorialAuditsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / 'run'
        self.worktree = Path(self.tmp.name) / 'worktree'
        self.worktree.mkdir()
        wave = self.run / 'wave-02'
        wave.mkdir(parents=True)
        self.reservation = {
            'assignments': {'editor': {'/root/a': list(range(1, 51))}, 'audit': {'/root/b': list(range(1, 51))}},
            'worktrees': {'/root/a': '/a', '/root/b': '/b'},
        }
        dump(wave / 'reservation.json', self.reservation)
        dump(self.run / 'reservation.json', {'waves': {'wave-02': sha(wave / 'reservation.json')}})

    def tearDown(self):
        self.tmp.cleanup()

    def test_reassigns_only_audit_and_records_history(self):
        result = reassign(self.run, [2], '/root/c', self.worktree)
        changed = json.loads((self.run / 'wave-02/reservation.json').read_text())
        self.assertEqual(changed['assignments']['editor'], self.reservation['assignments']['editor'])
        self.assertEqual(changed['assignments']['audit'], {'/root/c': list(range(1, 51))})
        self.assertEqual(result['scope'].split('.')[0], 'Audit assignment only')
        self.assertTrue((self.run / 'assignment-history/top-before.private.json').is_file())

    def test_refuses_opened_wave(self):
        marker = self.run / 'wave-02/batch-01/editor-actor.private.json'
        marker.parent.mkdir()
        marker.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'opened'):
            reassign(self.run, [2], '/root/c', self.worktree)

    def test_refuses_self_auditor(self):
        with self.assertRaisesRegex(ValueError, 'cannot edit'):
            reassign(self.run, [2], '/root/a', self.worktree)


if __name__ == '__main__':
    unittest.main()
