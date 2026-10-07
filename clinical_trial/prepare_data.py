"""Offline data preparation; never auto-approve trial criteria or download records."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from .data_adapters import public_trial_candidate, promote_candidate, synthetic_source


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('trial-candidate','approve-trial','synthetic-source'))
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--reviewer')
    parser.add_argument('--approved-ids',nargs='+')
    parser.add_argument('--attest-synthetic',action='store_true')
    args=parser.parse_args()
    with args.input.open('rb') as stream: raw=stream.read(1_000_001)
    if len(raw)>1_000_000: parser.error('input exceeds 1MB limit')
    value=json.loads(raw)
    if args.action=='trial-candidate':result=public_trial_candidate(value)
    elif args.action=='approve-trial':result=promote_candidate(value,args.reviewer,args.approved_ids)
    else:result=asdict(synthetic_source(value,synthetic_attested=args.attest_synthetic))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
