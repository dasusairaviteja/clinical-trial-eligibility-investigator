from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from clinical_trial.reviews import ConflictError, ReviewStore


class ReviewTests(unittest.TestCase):
    def test_read_snapshot_survives_interleaved_correction(self):
        created = self.store.create(self.report)
        connection = self.store.connect()
        connection.execute('PRAGMA journal_mode=WAL')
        connection.close()
        reader = self.store.connect()
        writer = ReviewStore(self.path)

        class InterleavedConnection:
            def execute(inner, sql, *args):
                if sql.startswith('SELECT body, previous_hash'):
                    writer.correct(created['id'], 0, 'age', 'supported',
                                   'Interleaved correction', 'reviewer')
                return reader.execute(sql, *args)

            def close(inner):
                reader.close()

        with patch.object(self.store, 'connect', return_value=InterleavedConnection()):
            snapshot = self.store.get(created['id'])
        self.assertEqual(snapshot['revision'], 0)
        self.assertEqual(len(snapshot['audit']), 1)
        self.assertEqual(writer.get(created['id'])['revision'], 1)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "reviews.db"
        self.store = ReviewStore(self.path)
        self.report = {"criteria": [{"criterion_id": "age", "verdict": "unknown"}]}

    def test_correction_keeps_original_and_persists_history(self):
        created = self.store.create(self.report)
        corrected = self.store.correct(created["id"], 0, "age", "supported", "Reviewed source", "local-reviewer")
        self.assertEqual(corrected["report"], self.report)
        self.assertEqual(corrected["revision"], 1)
        self.assertEqual(len(corrected["audit"]), 2)
        self.assertEqual(ReviewStore(self.path).get(created["id"]), corrected)
        self.assertEqual(corrected["audit"][1]["previous_hash"], corrected["audit"][0]["hash"])

    def test_stale_review_and_invalid_criterion_are_atomic(self):
        identifier = self.store.create(self.report)["id"]
        with self.assertRaises(ConflictError):
            self.store.correct(identifier, 1, "age", "supported", "reason", "reviewer")
        with self.assertRaises(ValueError):
            self.store.correct(identifier, 0, "missing", "supported", "reason", "reviewer")
        self.assertEqual(self.store.get(identifier)["revision"], 0)
        self.assertEqual(len(self.store.get(identifier)["audit"]), 1)

    def test_backup_can_restore_reports(self):
        report = self.store.create(self.report)
        backup = Path(self.temp.name) / "backup.db"
        self.store.backup(backup)
        self.assertEqual(ReviewStore(backup).get(report["id"]), report)
