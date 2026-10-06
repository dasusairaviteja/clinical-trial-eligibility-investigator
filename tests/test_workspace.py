import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from clinical_trial.api import handler_for
from clinical_trial.registry import registry_from_json
from clinical_trial.reviews import ReviewStore

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.registry = registry_from_json((ROOT/'examples/synthetic_sources.json').read_bytes())
        self.store = ReviewStore(Path(self.temp.name)/'reviews.db')
        self.server = ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.registry,self.store))
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self,path,body=None):
        connection = http.client.HTTPConnection(*self.server.server_address,timeout=2)
        connection.request('GET' if body is None else 'POST',path,
                           body=None if body is None else json.dumps(body),
                           headers={} if body is None else {'Content-Type':'application/json'})
        response=connection.getresponse()
        data=response.read()
        result=response.status,data
        connection.close()
        return result

    def test_investigate_correct_reload_and_conflict(self):
        _, body=self.request('/v1/demo')
        status, body=self.request('/v1/investigate',json.loads(body))
        self.assertEqual(status,200)
        original=json.loads(body)
        correction=dict(identifier=original['id'],revision=0,criterion_id='age',verdict='unknown',
                        reason='Review age date',reviewer='Local tester')
        status, body=self.request('/v1/reviews',correction)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['revision'],1)
        self.assertEqual(self.request('/v1/reviews',correction)[0],409)
        _, saved=self.request('/v1/reports/'+original['id'])
        self.assertEqual(json.loads(saved)['report'],original['report'])
        self.assertEqual(len(json.loads(saved)['audit']),2)

    def test_assets_are_allowlisted_and_invalid_requests_leave_no_reports(self):
        self.assertEqual(self.request('/')[0],200)
        self.assertEqual(self.request('/workspace.js')[0],200)
        self.assertEqual(self.request('/../.env')[0],404)
        self.assertEqual(self.request('/v1/investigate',{'sources':'untrusted'})[0],400)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reports').fetchone()[0],0)
