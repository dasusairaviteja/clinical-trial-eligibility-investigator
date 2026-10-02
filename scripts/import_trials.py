"""Import a bounded local preview from a legacy clinical_study XML ZIP.

The raw archive and generated JSON are intentionally excluded from Git.
No XML files are extracted, and contact/location fields are not retained.
"""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

MAX_XML_BYTES = 2_000_000


def parse_trial(content: bytes) -> dict:
    if len(content) > MAX_XML_BYTES:
        raise ValueError('XML record exceeds size limit')
    if b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
        raise ValueError('DTD and entity declarations are not accepted')
    root = ET.fromstring(content)
    if root.tag != 'clinical_study':
        raise ValueError('Expected a clinical_study XML record')
    def text(path):
        return (root.findtext(path) or '').strip()
    identifier = text('id_info/nct_id')
    if not identifier.startswith('NCT') or not identifier[3:].isdigit():
        raise ValueError('Missing or invalid NCT identifier')
    return {'id': identifier, 'title': text('brief_title'),
            'status': text('overall_status'), 'updated': text('last_update_posted'),
            'conditions': [(node.text or '').strip() for node in root.findall('condition')],
            'eligibility': text('eligibility/criteria/textblock')}


def import_archive(archive: Path, limit: int) -> dict:
    if not 1 <= limit <= 1000:
        raise ValueError('Preview limit must be 1–1000')
    records, skipped = [], 0
    with zipfile.ZipFile(archive) as source:
        members = [m for m in source.infolist() if m.filename.lower().endswith('.xml')]
        for member in members:
            if len(records) >= limit:
                break
            if member.file_size > MAX_XML_BYTES:
                skipped += 1
                continue
            try:
                with source.open(member) as stream:
                    record = parse_trial(stream.read(MAX_XML_BYTES + 1))
                records.append(record)
            except (ValueError, ET.ParseError):
                skipped += 1
    return {'source': 'User-provided legacy XML archive; historical snapshot',
            'totalXmlEntries': len(members), 'imported': len(records),
            'skippedBeforeLimit': skipped, 'trials': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--output', type=Path, default=Path('web/local-trials.json'))
    args = parser.parse_args()
    result = import_archive(args.archive, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print(f"Imported {result['imported']} of {result['totalXmlEntries']} XML entries locally.")


if __name__ == '__main__':
    main()
