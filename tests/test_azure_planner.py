import io
import json
import unittest
from unittest.mock import patch, MagicMock
from clinical_trial.azure_planner import AzurePlanner, NoRedirects


class AzurePlannerTests(unittest.TestCase):
    def test_credential_exfiltration_endpoints_rejected(self):
        for endpoint in ('http://x.openai.azure.com', 'https://evil.example',
                         'https://x.openai.azure.com.evil.example', 'https://x.openai.azure.com/path'):
            with self.assertRaises(ValueError):
                AzurePlanner(endpoint,'deployment','placeholder')
        with self.assertRaises(RuntimeError):
            NoRedirects().redirect_request(None,None,302,'',{},'https://evil.example')

    def test_mock_provider_response_and_usage(self):
        result = {'choices':[{'finish_reason':'stop','message':{'content':'{"tool":"finish","arguments":{}}'}}],
                  'usage':{'prompt_tokens':12,'completion_tokens':8,'total_tokens':20}}
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = io.BytesIO(json.dumps(result).encode())
        with patch('clinical_trial.azure_planner.build_opener', return_value=opener):
            planner = AzurePlanner('https://example.openai.azure.com','deployment','placeholder')
            self.assertEqual(planner({},[])['tool'],'finish')
        self.assertEqual(planner.usage[0]['total_tokens'],20)

    def test_provider_error_is_generic(self):
        opener = MagicMock()
        opener.open.side_effect = OSError('private diagnostic')
        with patch('clinical_trial.azure_planner.build_opener', return_value=opener):
            with self.assertRaisesRegex(RuntimeError, '^model request failed$'):
                AzurePlanner('https://example.openai.azure.com','deployment','placeholder')({},[])
