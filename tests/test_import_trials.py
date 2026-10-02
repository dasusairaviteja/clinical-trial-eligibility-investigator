import unittest
from scripts.import_trials import parse_trial

class TrialImportTests(unittest.TestCase):
    def test_extracts_criteria_but_not_contact_fields(self):
        result = parse_trial(b'<clinical_study><id_info><nct_id>NCT00000001</nct_id></id_info><brief_title>Example</brief_title><eligibility><criteria><textblock>Age 18 or older</textblock></criteria></eligibility><contact>Do not retain</contact></clinical_study>')
        self.assertEqual(result['eligibility'], 'Age 18 or older')
        self.assertNotIn('contact', result)

    def test_rejects_entity_declarations(self):
        with self.assertRaises(ValueError):
            parse_trial(b'<!DOCTYPE x [<!ENTITY x "unsafe">]><clinical_study/>')

    def test_rejects_missing_identifier(self):
        with self.assertRaises(ValueError):
            parse_trial(b'<clinical_study/>')
