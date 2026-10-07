"""Narrow, source-bound rules over operator-approved synthetic observations.

These grammars are deliberately explicit; unsupported clinical language abstains.
All numerical thresholds and event windows come from the trusted criterion,
never from planner-supplied arguments. Completeness is an operator assertion.
"""
from datetime import date
from decimal import Decimal
import json
import re
from .tools import numerical, temporal, calendar_months_before


def check(criterion, sources, *, research_ablation=None):
    if research_ablation not in (None, 'without_temporal', 'without_missing_evidence_control'):
        raise ValueError('unknown ablation')
    result = {"criterion_id":criterion.criterion_id,"verdict":"unknown",
              "citations":[],"missing_information":["Unsupported rule or missing, conflicting, invalid evidence."]}
    age = re.fullmatch(r"Age (over|at least|under|at most) ([0-9]+) years",criterion.statement)
    dated_age=re.fullmatch(r'Age (over|at least|under|at most) ([0-9]+) years on (\d{4}-\d{2}-\d{2})',criterion.statement)
    statement=criterion.statement
    if dated_age:
        operator={'over':'gt','at least':'gte','under':'lt','at most':'lte'}[dated_age[1]]
        statement=f'Measurement age {operator} {dated_age[2]} years on {dated_age[3]}'
    interval=re.fullmatch(r'Measurement ([A-Za-z0-9_-]+) between ([0-9]+(?:\.[0-9]+)?) and ([0-9]+(?:\.[0-9]+)?) (\S+) on (\d{4}-\d{2}-\d{2})',statement)
    if interval:
        if Decimal(interval[2])>Decimal(interval[3]):return result
        statement=f'Measurement {interval[1]} gte {interval[2]} {interval[4]} on {interval[5]}'
    measurement = re.fullmatch(r"Measurement ([A-Za-z0-9_-]+) (gt|gte|lt|lte|eq) ([0-9]+(?:\.[0-9]+)?) (\S+) on (\d{4}-\d{2}-\d{2})",statement)
    event = re.fullmatch(r"Event ([A-Za-z0-9_-]+) within ([0-9]+) months before (\d{4}-\d{2}-\d{2})",criterion.statement)
    matches = []
    for source in sources:
        if age:
            for match in re.finditer(r"\bAge: ([0-9]+) years\.",source.text):
                verdict = numerical(match[1],{"over":"gt","at least":"gte","under":"lt","at most":"lte"}[age[1]],age[2],"years","years")
                matches.append((source,match.start(),match.end(),verdict))
        elif measurement or event:
            try:
                record = json.loads(source.text)
                if record.get('schema') != 'synthetic-observation-v1': continue
                if record.get('patient_id') != source.patient_id: continue
                if measurement and record.get('type') == 'measurement' and record.get('name') == measurement[1]:
                    date.fromisoformat(measurement[5])
                    if record.get('date') != measurement[5] and research_ablation != 'without_temporal': continue
                    verdict = numerical(record.get('value'),measurement[2],measurement[3],record.get('unit'),measurement[4])
                    if interval:
                        upper=numerical(record.get('value'),'lte',interval[3],record.get('unit'),measurement[4])
                        verdict='unknown' if 'unknown' in (verdict,upper) else ('supported' if verdict==upper=='supported' else 'contradicted')
                elif event and record.get('type') == 'event_history' and record.get('name') == event[1]:
                    dates = record.get('events')
                    if not isinstance(dates,list): continue
                    calendar_months_before(date.fromisoformat(event[3]),int(event[2]))
                    lower,upper=record.get('complete_since'),record.get('complete_through')
                    if (lower is None) != (upper is None): continue
                    if lower is not None and date.fromisoformat(lower)>date.fromisoformat(upper): continue
                    verdict = temporal(dates,event[3],int(event[2]),record.get('complete_since'),record.get('complete_through'))
                    # Deliberately weakened research controls. Production callers
                    # never pass this flag; malformed dates are still rejected.
                    for day in dates: date.fromisoformat(day)
                    if research_ablation == 'without_temporal' and dates:
                        verdict = 'supported'
                    elif research_ablation == 'without_missing_evidence_control' and verdict == 'unknown':
                        verdict = 'contradicted'
                else: continue
                matches.append((source,0,len(source.text),verdict))
            except (ValueError,TypeError,AttributeError):
                continue
    # Multiple assessments are ambiguous, even if values agree. Never silently
    # pick a convenient source or merge incompatible coverage statements.
    if len(matches) == 1:
        source,start,end,verdict = matches[0]
        if verdict != 'unknown':
            result.update(verdict=verdict,missing_information=[],citations=[{
                'source_id':source.source_id,'source_version':source.version,
                'start':start,'end':end,'quote':source.text[start:end]}])
    return result
