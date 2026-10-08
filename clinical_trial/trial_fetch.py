"""Fetch one public registry record into a private, review-only snapshot.

No search, patient transmission, automatic promotion or background refresh.
Raw records stay outside git. Source terms must be reviewed before redistribution.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .data_adapters import public_trial_candidate
from .report import _unique_object, _reject_constant

MAX_BYTES = 1_000_000
TERMS_URL = 'https://clinicaltrials.gov/about-site/terms-conditions'


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('registry redirects are not allowed')


def fetch_snapshot(nct_id, *, opener=None):
    if not isinstance(nct_id, str) or not re.fullmatch(r'NCT[0-9]{8}', nct_id):
        raise ValueError('expected an NCT identifier')
    url = 'https://clinicaltrials.gov/api/v2/studies/' + nct_id
    request = Request(url, headers={'Accept': 'application/json',
                                   'User-Agent': 'TrialLens-research-snapshot/1'})
    client = opener if opener is not None else build_opener(NoRedirects())
    with client.open(request, timeout=20) as response:
        if response.status != 200 or response.headers.get_content_type() != 'application/json':
            raise ValueError('unexpected registry response')
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('registry response exceeds size limit')
    record = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    candidate = public_trial_candidate(record)
    if candidate['trial_id'] != nct_id:
        raise ValueError('registry returned a different trial')
    return {'schema_version': 1, 'source_url': url,
            'study_url': 'https://clinicaltrials.gov/study/' + nct_id,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'terms_url': TERMS_URL, 'redistribution_status': 'requires_source_terms_review',
            'raw_record': record, 'candidate': candidate,
            'status': 'human_review_required'}, raw


def save_snapshot(snapshot, raw, destination):
    """Create a new snapshot directory; existing data is never overwritten."""
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        for name, data in [('record.json', raw), ('snapshot.json', json.dumps(snapshot, indent=2).encode())]:
            with (destination / name).open('xb') as stream:
                stream.write(data)
            (destination / name).chmod(0o600)
    except BaseException:
        for name in ('record.json', 'snapshot.json'):
            (destination / name).unlink(missing_ok=True)
        destination.rmdir()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('nct_id')
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.destination.exists():
        parser.error('destination already exists')
    snapshot, raw = fetch_snapshot(args.nct_id)
    save_snapshot(snapshot, raw, args.destination)
    print(json.dumps({'trial_id': snapshot['candidate']['trial_id'],
        'raw_sha256': snapshot['raw_sha256'], 'retrieved_at': snapshot['retrieved_at'],
        'criteria': len(snapshot['candidate']['criteria']),
        'issues': len(snapshot['candidate']['issues']), 'status': snapshot['status']}))


if __name__ == '__main__':
    main()
