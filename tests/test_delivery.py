from concurrent.futures import ThreadPoolExecutor
import tempfile
from pathlib import Path
import unittest
from clinical_trial.reviews import ReviewStore,ConflictError
from clinical_trial.export import html_report


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ReviewStore(Path(self.temp.name)/'reviews.db')

    def test_request_replay_returns_original_and_conflicts_on_changed_body(self):
        self.assertIsNone(self.store.reserve('a','key','digest'))
        saved=self.store.create({'criteria':[]},request_identity=('a','key','digest'))
        self.assertEqual(self.store.reserve('a','key','digest'),saved['id'])
        with self.assertRaises(ConflictError):self.store.reserve('a','key','other')
        self.assertIsNone(self.store.reserve('b','key','digest'))

    def test_concurrent_reservations_only_one_wins(self):
        def reserve(_):
            try:self.store.reserve('a','key','digest');return True
            except ConflictError:return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve,range(8))),1)

    def test_pending_request_can_be_released_after_failure(self):
        self.store.reserve('a','key','digest');self.store.release('a','key','digest')
        self.assertIsNone(self.store.reserve('a','key','digest'))

    def test_history_bounds(self):
        for _ in range(3):self.store.create({'criteria':[]})
        self.assertEqual(len(self.store.list_reports(2)),2)
        with self.assertRaises(ValueError):self.store.list_reports(1000)

    def test_print_export_escapes_source_content(self):
        saved=self.store.create({'criteria':[{'criterion_id':'c','statement':'<script>bad()</script>',
            'kind':'inclusion','verdict':'unknown','citations':[],'missing_information':['<img onerror=bad()>']}]})
        saved=self.store.correct(saved['id'],0,'c','unknown','<script>reason</script>','reviewer')
        page=html_report(saved).decode()
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertIn('Latest reviewer assertion',page)
