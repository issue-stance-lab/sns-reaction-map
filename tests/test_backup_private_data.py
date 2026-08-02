import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import backup_private_data


class BackupPrivateDataTests(unittest.TestCase):
    def test_required_file_errors_stop_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(
                backup_private_data,
                "collect_targets",
                return_value=([], ["theme: 非公開 sample_file が存在しない"]),
            ):
                self.assertEqual(backup_private_data.backup(Path(directory)), 1)
                self.assertEqual(list(Path(directory).glob("*.tar.gz")), [])

    def test_repeated_backup_does_not_overwrite(self):
        source = backup_private_data.ROOT / "data" / "verification" / "README.md"
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            with patch.object(backup_private_data, "collect_targets", return_value=([source], [])):
                self.assertEqual(backup_private_data.backup(destination), 0)
                self.assertEqual(backup_private_data.backup(destination), 0)
            archives = list(destination.glob("*.tar.gz"))
            self.assertEqual(len(archives), 2)
            self.assertNotEqual(archives[0].name, archives[1].name)
            self.assertTrue(all(backup_private_data.verify(path, quiet=True) == 0 for path in archives))


if __name__ == "__main__":
    unittest.main()
