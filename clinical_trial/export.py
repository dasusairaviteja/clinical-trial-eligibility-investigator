"""Self-contained, escaped evidence report suitable for printing and archival."""
from html import escape


def html_report(saved):
    def safe(value): return escape(str(value),quote=True)
    report=saved['report']
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>TrialLens evidence report</title>',
           '<body><main><h1>Research evidence report</h1><p>Human review required. No enrollment decision.</p>',
           '<dl><dt>Report</dt><dd>'+safe(saved['id'])+'</dd><dt>Revision</dt><dd>'+safe(saved['revision'])+'</dd></dl>']
    for criterion in report['criteria']:
        parts.extend(['<section><h2>'+safe(criterion['statement'])+'</h2>',
                      '<p>'+safe(criterion['kind'])+' — Original finding: '+safe(criterion['verdict'])+'</p>'])
        for citation in criterion['citations']:
            parts.append('<blockquote>'+safe(citation['quote'])+'</blockquote><p>Source '+safe(citation['source_id'])+
                         ' version '+safe(citation['source_version'])+'; characters '+safe(citation['start'])+'–'+safe(citation['end'])+'</p>')
        for missing in criterion['missing_information']:
            parts.append('<p>Missing information: '+safe(missing)+'</p>')
        corrections=[a['event'] for a in saved['audit'] if a['event'].get('criterion_id')==criterion['criterion_id']]
        if corrections:
            latest=corrections[-1]
            parts.append('<p>Latest reviewer assertion: '+safe(latest['verdict'])+'; reviewer '+safe(latest['reviewer'])+
                         '; reason '+safe(latest['reason'])+'</p>')
        parts.append('</section>')
    parts.append('<h2>Audit history</h2><ol>')
    for event in saved['audit']:
        parts.append('<li>'+safe(event['event']['at'])+' — '+safe(event['event']['action'])+
                     '; hash <code>'+safe(event['hash'])+'</code></li>')
    parts.append('</ol></main></body></html>')
    return ''.join(parts).encode()
