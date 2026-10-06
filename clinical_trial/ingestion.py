"""Conservative line parser retaining source offsets for reviewer approval."""

from datetime import date
import hashlib
import re


def parse_criteria(trial_id: str, updated: str, text: str) -> dict:
    if not re.fullmatch(r"NCT[0-9]{8}", trial_id):
        raise ValueError("invalid trial identifier")
    date.fromisoformat(updated)
    if not isinstance(text, str) or not text.strip() or len(text) > 200_000:
        raise ValueError("invalid eligibility text")
    digest = hashlib.sha256(text.encode()).hexdigest()
    rows, issues, kind, offset = [], [], None, 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        heading = re.fullmatch(r"(Inclusion|Exclusion) Criteria\s*:", stripped, re.I)
        if heading:
            kind = heading[1].lower()
        elif stripped:
            bullet = re.match(r"\s*(?:[-*•]|[0-9]+[.)])\s+(.+?)\s*$", line)
            if kind and bullet:
                start, end = offset + bullet.start(1), offset + bullet.end(1)
                rows.append({"criterion_id": f"c{len(rows)+1}", "trial_id": trial_id,
                             "kind": kind, "statement": text[start:end],
                             "start": start, "end": end})
            else:
                issues.append({"code": "unparsed_line", "start": offset,
                               "end": offset + len(line)})
        offset += len(line)
    return {"trial_id": trial_id, "updated": updated, "source_sha256": digest,
            "parser_version": "conservative-lines-v1", "criteria": rows,
            "issues": issues, "status": "human_review_required",
            "automatic_promotion_allowed": False}
