from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from clinical_trial.recovery import snapshot
from clinical_trial.reviews import ReviewStore


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source.db"
        self.target = Path(self.temp.name) / "backup.db"
        self.store = ReviewStore(self.source)
        self.created = self.store.create({"criteria": [{"criterion_id": "age"}]})
        self.store.correct(self.created["id"], 0, "age", "unknown", "Missing evidence", "reviewer")

    def tamper(self, sql):
        with sqlite3.connect(self.source) as db:
            db.execute(sql)

    def test_round_trip_preserves_report_and_audit(self):
        expected = self.store.get(self.created["id"])
        anchors = snapshot(self.source, self.target)
        restored = Path(self.temp.name) / "restored.db"
        self.assertEqual(snapshot(self.target, restored), anchors)
        self.assertEqual(ReviewStore(restored, read_only=True).get(expected["id"]), expected)
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o600)

    def test_refuses_overwrite_and_same_source(self):
        self.target.write_text("keep")
        for target in (self.target, self.source):
            with self.assertRaises(ValueError):
                snapshot(self.source, target)
        self.assertEqual(self.target.read_text(), "keep")

    def test_detects_changed_original_report(self):
        self.tamper("UPDATE reports SET body='{}'")
        with self.assertRaises(ValueError):
            snapshot(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_detects_deleted_event(self):
        self.tamper("DELETE FROM events WHERE sequence=2")
        with self.assertRaises(ValueError):
            self.store.verify()

    def test_detects_changed_hash_link(self):
        self.tamper("UPDATE events SET previous_hash='tampered' WHERE sequence=2")
        with self.assertRaises(ValueError):
            self.store.verify()

    def test_failed_backup_removes_partial_destination(self):
        with patch.object(ReviewStore, "backup", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                snapshot(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_rejects_non_database_without_modifying_source(self):
        invalid = Path(self.temp.name) / "invalid.db"
        invalid.write_bytes(b"not a database")
        with self.assertRaises(sqlite3.DatabaseError):
            snapshot(invalid, self.target)
        self.assertEqual(invalid.read_bytes(), b"not a database")
        self.assertFalse(self.target.exists())

    def test_concurrent_change_requires_retry(self):
        original = ReviewStore.backup
        def changing_backup(store, target):
            self.store.create({"criteria": []})
            original(store, target)
        with patch.object(ReviewStore, "backup", changing_backup):
            with self.assertRaises(ValueError):
                snapshot(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_readonly_store_cannot_write(self):
        with self.assertRaises(sqlite3.OperationalError):
            ReviewStore(self.source, read_only=True).create({"criteria": []})
