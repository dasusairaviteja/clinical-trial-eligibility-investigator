"""Budget-gated infrastructure command builder. Defaults to Azure what-if."""
import argparse
import ipaddress
import json
from pathlib import Path
import subprocess


def command(environment, parameters, *, apply=False, budget_approved=False):
    configs=json.loads(Path('infra/environments.json').read_text())
    if environment not in configs:raise ValueError('ENG, TEST or PROD required')
    if apply and not budget_approved:raise ValueError('explicit resource budget approval required')
    if parameters.get('environment',{}).get('value')!=environment:raise ValueError('parameter environment mismatch')
    cidr=ipaddress.ip_network(parameters['managementCidr']['value'])
    if cidr.prefixlen==0:raise ValueError('unrestricted management access rejected')
    if parameters['imageVersion']['value']=='latest':raise ValueError('pin approved image version')
    return ['az','deployment','group','create' if apply else 'what-if','--resource-group',configs[environment]['resource_group'],
            '--template-file','infra/main.bicep','--parameters']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('environment',choices=('ENG','TEST','PROD'))
    parser.add_argument('parameters',type=Path)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--budget-approved',action='store_true')
    args=parser.parse_args()
    parameters=json.loads(args.parameters.read_text())['parameters']
    cmd=command(args.environment,parameters,apply=args.apply,budget_approved=args.budget_approved)
    subprocess.run(cmd+['@'+str(args.parameters)],check=True)


if __name__=='__main__':main()
