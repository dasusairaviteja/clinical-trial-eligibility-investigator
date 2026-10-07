import importlib.util
import unittest

spec=importlib.util.spec_from_file_location('deploy','scripts/azure_deploy.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)


class InfraTests(unittest.TestCase):
    def parameters(self,env):return {'environment':{'value':env},'managementCidr':{'value':'10.2.0.0/24'},'imageVersion':{'value':'test-pinned-version'}}
    def test_all_environments_default_to_what_if(self):
        for env in ['ENG','TEST','PROD']:
            result=deploy.command(env,self.parameters(env))
            self.assertIn('what-if',result);self.assertIn('rg-triallens-'+env.lower(),result)
    def test_paid_apply_requires_budget_and_environment_match(self):
        with self.assertRaises(ValueError):deploy.command('PROD',self.parameters('PROD'),apply=True)
        with self.assertRaises(ValueError):deploy.command('PROD',self.parameters('ENG'))
    def test_rejects_world_management_network(self):
        p=self.parameters('ENG');p['managementCidr']['value']='0.0.0.0/0'
        with self.assertRaises(ValueError):deploy.command('ENG',p)
