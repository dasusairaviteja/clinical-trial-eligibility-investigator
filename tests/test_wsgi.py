import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from clinical_trial.registry import registry_from_json
from clinical_trial.reviews import ReviewStore
from clinical_trial.wsgi import Application, create_app

ROOT = Path(__file__).resolve().parents[1]
TOKEN = 'test-only-credential-not-for-deployment'


class WsgiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        registry = registry_from_json((ROOT/'examples/synthetic_sources.json').read_bytes())
        self.store = ReviewStore(Path(self.temp.name)/'reviews.db')
        self.app = Application(registry, self.store, {TOKEN:'verified-reviewer'})

    def call(self, path, body=None, token=TOKEN, **overrides):
        payload = json.dumps(body).encode() if body is not None else b''
        env = {'PATH_INFO':path,'REQUEST_METHOD':'POST' if body is not None else 'GET',
               'HTTP_AUTHORIZATION':'Bearer '+token,'CONTENT_TYPE':'application/json',
               'CONTENT_LENGTH':str(len(payload)),'wsgi.input':io.BytesIO(payload), **overrides}
        result = {}
        def start(status, headers):
            result.update(status=int(status.split()[0]), headers=dict(headers))
        data = b''.join(self.app(env,start))
        result['body'] = json.loads(data) if 'application/json' in result['headers']['Content-Type'] else data
        return result

    def test_auth_required_for_all_data(self):
        for path in ['/v1/demo','/v1/me','/v1/reports/anything']:
            self.assertEqual(self.call(path,token='wrong')['status'],401)
        self.assertEqual(self.call('/health',token='')['status'],200)

    def test_corrections_use_authenticated_identity(self):
        request = self.call('/v1/demo')['body']
        created = self.call('/v1/investigate',request)['body']
        correction = {'identifier':created['id'],'revision':0,
                      'criterion_id':created['report']['criteria'][0]['criterion_id'],
                      'verdict':'unknown','reason':'Need more evidence','reviewer':'impersonated'}
        response = self.call('/v1/reviews',correction)
        self.assertEqual(response['status'],200)
        self.assertEqual(response['body']['audit'][-1]['event']['reviewer'],'verified-reviewer')
        self.assertEqual(self.call('/v1/reviews',correction)['status'],409)

    def test_limits_and_security_headers(self):
        self.app.rate_limit = 1
        first = self.call('/v1/me')
        self.assertIn("frame-ancestors 'none'",first['headers']['Content-Security-Policy'])
        self.assertEqual(first['headers']['Cache-Control'],'no-store')
        self.assertEqual(self.call('/v1/me')['status'],429)

    def test_capacity_rejects_without_model_call(self):
        request = self.call('/v1/demo')['body']
        self.app.active.acquire(); self.app.active.acquire()
        self.assertEqual(self.call('/v1/investigate',request)['status'],503)

    def test_bad_bodies_fail_closed(self):
        self.assertEqual(self.call('/v1/investigate',{}, CONTENT_LENGTH='999999999')['status'],413)
        self.assertEqual(self.call('/v1/investigate',{}, CONTENT_TYPE='text/plain')['status'],415)
        self.assertEqual(self.call('/v1/investigate',{}, HTTP_TRANSFER_ENCODING='chunked')['status'],400)
        self.assertEqual(self.call('/v1/investigate',[])['status'],400)

    def test_no_sensitive_request_data_in_telemetry(self):
        with self.assertLogs('trial.requests',level='INFO') as logs:
            result = self.call('/v1/reports/secret-patient-id')
        self.assertEqual(result['status'],404)
        self.assertNotIn('secret-patient-id',str(logs.output))
        self.assertNotIn(TOKEN,str(logs.output))
        self.assertIn('duration_ms',str(logs.output))

    def test_startup_refuses_missing_or_weak_credentials(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(KeyError): create_app()
        for credentials in [{},{'short':'reviewer'},{TOKEN:42}]:
            with self.assertRaises(ValueError): Application(self.app.registry,self.store,credentials)

    def test_static_routes_are_allowlisted(self):
        self.assertEqual(self.call('/')['status'],200)
        self.assertEqual(self.call('/../README.md')['status'],404)
