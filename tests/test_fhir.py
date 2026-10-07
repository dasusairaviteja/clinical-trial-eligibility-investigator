import unittest
from clinical_trial.fhir import observations


class FhirTests(unittest.TestCase):
    def bundle(self,**changes):
        resource={'resourceType':'Observation','id':'lab','status':'final','subject':{'reference':'Patient/SYN-1'},
                  'code':{'coding':[{'system':'test-codes','code':'hb'}]},'effectiveDateTime':'2026-10-06T09:00:00-04:00',
                  'valueQuantity':{'value':9,'system':'http://unitsofmeasure.org','code':'g/dL'},**changes}
        return {'resourceType':'Bundle','entry':[{'resource':{'resourceType':'Patient','id':'SYN-1'}},{'resource':resource}]}

    def convert(self,bundle):return observations(bundle,'SYN-1',{('test-codes','hb'):('hemoglobin','g/dL')},synthetic_attested=True)

    def test_maps_valid_quantity_and_retains_hash(self):
        result=self.convert(self.bundle())
        self.assertEqual(len(result['sources']),1)
        self.assertEqual(result['issues'],[])
        self.assertIn('2026-10-06',result['sources'][0].text)
        self.assertEqual(len(result['input_sha256']),64)

    def test_wrong_subject_missing_value_and_nonfinal_rejected(self):
        for changes in [{'subject':{'reference':'Patient/other'}},{'status':'preliminary'},
                        {'valueQuantity':{}},{'effectiveDateTime':'2026-10'},
                        {'effectiveDateTime':'2026-10-06T09:00:00'},{'modifierExtension':[{}]}]:
            result=self.convert(self.bundle(**changes))
            self.assertEqual(len(result['sources']),0)
            self.assertEqual(len(result['issues']),1)

    def test_synthetic_attestation_required(self):
        with self.assertRaises(ValueError):observations(self.bundle(),'SYN-1',{})

    def test_multiple_patients_rejected(self):
        bundle=self.bundle();bundle['entry'].append({'resource':{'resourceType':'Patient','id':'other'}})
        with self.assertRaises(ValueError):self.convert(bundle)
