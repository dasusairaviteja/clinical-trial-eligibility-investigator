import json
import unittest
from clinical_trial.contracts import Criterion, CriterionKind, SourceDocument
from clinical_trial.evidence_tools import check
from clinical_trial.data_adapters import synthetic_source, public_trial_candidate, promote_candidate
from clinical_trial.retrieval import retrieve


class EvidenceToolTests(unittest.TestCase):
    def criterion(self,text):
        return Criterion('c1','trial',CriterionKind.EXCLUSION,text)

    def source(self,**changes):
        record = {'schema':'synthetic-observation-v1','patient_id':'synthetic-1','source_id':'history',
                  'version':'v1','type':'event_history','name':'stroke','events':[],
                  'complete_since':None,'complete_through':None,**changes}
        return synthetic_source(record,synthetic_attested=True)

    def test_absence_requires_complete_window(self):
        criterion=self.criterion('Event stroke within 6 months before 2026-10-06')
        self.assertEqual(check(criterion,[self.source()])['verdict'],'unknown')
        complete=self.source(complete_since='2026-04-06',complete_through='2026-10-06')
        result=check(criterion,[complete])
        self.assertEqual(result['verdict'],'contradicted')
        self.assertEqual(result['citations'][0]['quote'],complete.text)

    def test_inclusive_event_boundaries_and_future_date(self):
        criterion=self.criterion('Event stroke within 6 months before 2026-10-06')
        for day in ['2026-04-06','2026-10-06']:
            self.assertEqual(check(criterion,[self.source(events=[day])])['verdict'],'supported')
        for day in ['2026-04-05','2026-10-07']:
            self.assertEqual(check(criterion,[self.source(events=[day])])['verdict'],'unknown')

    def test_partial_coverage_is_unknown(self):
        criterion=self.criterion('Event stroke within 6 months before 2026-10-06')
        for start,end in [('2026-04-07','2026-10-06'),('2026-04-06','2026-10-05')]:
            self.assertEqual(check(criterion,[self.source(complete_since=start,complete_through=end)])['verdict'],'unknown')

    def test_conflicting_sources_are_unknown(self):
        criterion=self.criterion('Event stroke within 6 months before 2026-10-06')
        self.assertEqual(check(criterion,[self.source(events=['2026-06-01']),self.source(source_id='other')])['verdict'],'unknown')

    def test_measurement_requires_unit_and_exact_date(self):
        record={'schema':'synthetic-observation-v1','patient_id':'p','source_id':'lab','version':'v1',
                'type':'measurement','name':'hemoglobin','date':'2026-10-06','value':'9','unit':'g/dL'}
        criterion=self.criterion('Measurement hemoglobin gte 9 g/dL on 2026-10-06')
        self.assertEqual(check(criterion,[synthetic_source(record,synthetic_attested=True)])['verdict'],'supported')
        for change in [{'unit':'mg/dL'},{'date':'2026-10-05'}]:
            self.assertEqual(check(criterion,[synthetic_source({**record,**change},synthetic_attested=True)])['verdict'],'unknown')

    def test_non_synthetic_and_bad_coverage_rejected(self):
        with self.assertRaises(ValueError): synthetic_source({})
        with self.assertRaises(ValueError): self.source(complete_since='2026-10-06',complete_through='2026-04-06')

    def test_retrieval_finds_late_evidence_with_original_offsets(self):
        source=SourceDocument('s','p','v1','x '*3000+'stroke evidence')
        result=retrieve([source],'stroke')
        self.assertTrue(result)
        self.assertGreater(result[0]['start'],4000)
        self.assertEqual(source.text[result[0]['start']:result[0]['end']],result[0]['text'])

    def candidate(self,text='Inclusion Criteria:\n- Age over 18 years\nExclusion Criteria:\n- Recent stroke\n'):
        return public_trial_candidate({'protocolSection':{'identificationModule':{'nctId':'NCT12345678'},
            'statusModule':{'lastUpdatePostDateStruct':{'date':'2026-10-06'}},
            'eligibilityModule':{'eligibilityCriteria':text}}})

    def test_promotion_requires_all_reviewed_ids(self):
        candidate=self.candidate()
        with self.assertRaises(ValueError): promote_candidate(candidate,'reviewer',['c1'])
        approved=promote_candidate(candidate,'reviewer',['c1','c2'])
        self.assertEqual(approved['trial']['criteria'][1]['kind'],'exclusion')

    def test_promotion_rejects_tampering_and_unparsed_lines(self):
        candidate=self.candidate();candidate['criteria'][0]['kind']='exclusion'
        with self.assertRaises(ValueError): promote_candidate(candidate,'reviewer',['c1','c2'])
        with self.assertRaises(ValueError): promote_candidate(self.candidate('unparsed text'),'reviewer',[])
