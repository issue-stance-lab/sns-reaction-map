import hashlib
import io
import json
import tarfile
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
                self.assertEqual(backup_private_data.backup(destination, receipt_path=destination / "receipt.json"), 0)
                self.assertEqual(backup_private_data.backup(destination, receipt_path=destination / "receipt.json"), 0)
            archives = list(destination.glob("*.tar.gz"))
            self.assertEqual(len(archives), 2)
            self.assertNotEqual(archives[0].name, archives[1].name)
            self.assertTrue(all(backup_private_data.verify(path, quiet=True) == 0 for path in archives))

    def test_receipt_binds_archive_commit_and_restored_files(self):
        source = backup_private_data.ROOT / "data/verification/README.md"
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            receipt_path = dest / "receipt.json"
            with patch.object(backup_private_data, "collect_targets", return_value=([source], [])):
                self.assertEqual(backup_private_data.backup(dest, receipt_path=receipt_path), 0)
            receipt = json.loads(receipt_path.read_text())
            archive = dest / receipt["archive_name"]
            self.assertTrue(receipt["restore_verified"])
            self.assertRegex(receipt["git_commit"], r"^[0-9a-f]{40}$")
            self.assertEqual(receipt["archive_sha256"], backup_private_data.sha256_of(archive))
            self.assertEqual(receipt["file_count"], 1)
            self.assertEqual(receipt["total_bytes"], source.stat().st_size)
            self.assertEqual(set(receipt["files"][0]), {"path", "bytes", "sha256", "records"})
            self.assertNotIn(str(backup_private_data.ROOT), receipt_path.read_text())

    def test_failed_restore_does_not_replace_success_receipt(self):
        source = backup_private_data.ROOT / "data/verification/README.md"
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            receipt = dest / "receipt.json"
            receipt.write_text("previous success")
            with patch.object(backup_private_data, "collect_targets", return_value=([source], [])), \
                 patch.object(backup_private_data, "verify", return_value=1):
                self.assertEqual(backup_private_data.backup(dest, receipt_path=receipt), 1)
            self.assertEqual(receipt.read_text(), "previous success")
            self.assertEqual(list(dest.glob("*.tar.gz")), [])

    def make_archive(self, path, *, entries=None, extra=None):
        payload = b'[{"text":"fixture"}]'
        item = {"path": "social-samples/a.json", "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(), "records": 1}
        manifest = {"created_at": "fixture", "files": entries if entries is not None else [item]}
        with tarfile.open(path, "w:gz") as tar:
            for name, data in [("manifest.json", json.dumps(manifest).encode()),
                               ("social-samples/a.json", payload)]:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                tar.addfile(member, io.BytesIO(data))
            if extra:
                tar.addfile(extra, io.BytesIO(b"x" * extra.size) if extra.isfile() else None)
        return item

    def test_archive_rejects_unsafe_duplicate_and_extra_members(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "test.tar.gz"
            self.make_archive(archive)
            self.assertEqual(backup_private_data.verify(archive, quiet=True), 0)
            for name, kind in [("../escape", tarfile.REGTYPE),
                               ("/absolute", tarfile.REGTYPE),
                               ("social-samples/a.json", tarfile.REGTYPE),
                               ("manifest.json", tarfile.REGTYPE),
                               ("unexpected", tarfile.REGTYPE),
                               ("link", tarfile.SYMTYPE),
                               ("hardlink", tarfile.LNKTYPE),
                               ("directory", tarfile.DIRTYPE),
                               ("device", tarfile.CHRTYPE)]:
                with self.subTest(name=name):
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.linkname = "/tmp/outside"
                    self.make_archive(archive, extra=member)
                    self.assertEqual(backup_private_data.verify(archive, quiet=True), 1)
            self.assertFalse((Path(directory).parent / "escape").exists())

    def test_archive_rejects_bad_manifest_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "test.tar.gz"
            item = self.make_archive(archive)
            for entries in [[item, item], [{**item, "path": "../escape"}],
                            [{**item, "bytes": item["bytes"] + 1}],
                            [{**item, "sha256": "0" * 64}], [{**item, "records": 2}],
                            [{**item, "path": "missing"}]]:
                with self.subTest(entries=entries):
                    self.make_archive(archive, entries=entries)
                    self.assertEqual(backup_private_data.verify(archive, quiet=True), 1)
            archive.write_bytes(b"broken gzip")
            self.assertEqual(backup_private_data.verify(archive, quiet=True), 1)


if __name__ == "__main__":
    unittest.main()
