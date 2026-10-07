"""Transactional local review storage with optimistic concurrency and history."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path


class ConflictError(ValueError):
    pass


class ReviewStore:
    def __init__(self, path, *, read_only=False):
        self.path = str(path)
        self.read_only = read_only
        if read_only:
            return
        with closing(self.connect()) as db, db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY, body TEXT NOT NULL, revision INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL REFERENCES reports(id),
                body TEXT NOT NULL, previous_hash TEXT NOT NULL, hash TEXT NOT NULL);
            """)

    def connect(self):
        target = Path(self.path).resolve().as_uri() + "?mode=ro" if self.read_only else self.path
        db = sqlite3.connect(target, timeout=5, uri=self.read_only)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def create(self, report):
        identifier = uuid.uuid4().hex
        with closing(self.connect()) as db, db:
            db.execute("INSERT INTO reports VALUES (?, ?, 0)",
                       (identifier, json.dumps(report, allow_nan=False)))
            self._event(db, identifier, {"action": "created", "revision": 0,
                                       "report_sha256": hashlib.sha256(
                                           json.dumps(report, sort_keys=True).encode()).hexdigest()})
        return self.get(identifier)

    def get(self, identifier):
        with closing(self.connect()) as db:
            row = db.execute("SELECT body, revision FROM reports WHERE id=?", (identifier,)).fetchone()
            if row is None:
                raise KeyError("report not found")
            events = db.execute("SELECT body, previous_hash, hash FROM events WHERE report_id=? ORDER BY sequence",
                                (identifier,)).fetchall()
        return {"id": identifier, "revision": row[1], "report": json.loads(row[0]),
                "audit": [{"event": json.loads(e[0]), "previous_hash": e[1], "hash": e[2]} for e in events]}

    def correct(self, identifier, revision, criterion_id, verdict, reason, reviewer):
        if type(revision) is not int or verdict not in ("supported", "contradicted", "unknown"):
            raise ValueError("invalid correction")
        if any(not isinstance(s, str) or not s.strip() or len(s) > 2000
               for s in (criterion_id, reason, reviewer)):
            raise ValueError("correction requires criterion, reason and reviewer")
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body, revision FROM reports WHERE id=?", (identifier,)).fetchone()
            if row is None:
                raise KeyError("report not found")
            if row[1] != revision:
                raise ConflictError("report changed; reload before correcting")
            report = json.loads(row[0])
            if criterion_id not in {c["criterion_id"] for c in report["criteria"]}:
                raise ValueError("unknown criterion")
            # Original machine report remains intact; corrections are separate reviewer assertions.
            self._event(db, identifier, {"action": "correction", "revision": revision + 1,
                        "criterion_id": criterion_id, "verdict": verdict,
                        "reason": reason, "reviewer": reviewer})
            db.execute("UPDATE reports SET revision=revision+1 WHERE id=?", (identifier,))
        return self.get(identifier)

    def _event(self, db, identifier, event):
        prior = db.execute("SELECT hash FROM events WHERE report_id=? ORDER BY sequence DESC LIMIT 1",
                           (identifier,)).fetchone()
        previous = prior[0] if prior else "0" * 64
        body = json.dumps({**event, "at": datetime.now(timezone.utc).isoformat()}, sort_keys=True)
        digest = hashlib.sha256((previous + body).encode()).hexdigest()
        db.execute("INSERT INTO events(report_id,body,previous_hash,hash) VALUES(?,?,?,?)",
                   (identifier, body, previous, digest))

    def backup(self, target):
        with closing(self.connect()) as source, closing(sqlite3.connect(str(target))) as destination:
            source.backup(destination)

    def verify(self):
        """Check SQLite integrity, event links, revisions and original report hashes.

        Detects accidental/tampered content, but a database administrator can
        rewrite the whole chain. Export hashes to independent storage for anchoring.
        """
        with closing(self.connect()) as db:
            db.execute("BEGIN")
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("database integrity failed")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("foreign key integrity failed")
            reports = db.execute("SELECT id, body, revision FROM reports").fetchall()
            anchors = {}
            for identifier, body, revision in reports:
                if type(revision) is not int or revision < 0:
                    raise ValueError("invalid stored revision")
                events = db.execute("SELECT body,previous_hash,hash FROM events WHERE report_id=? ORDER BY sequence", (identifier,)).fetchall()
                if len(events) != revision + 1:
                    raise ValueError("revision history incomplete")
                previous = "0" * 64
                for index, (event_body, link, digest) in enumerate(events):
                    if link != previous or hashlib.sha256((link + event_body).encode()).hexdigest() != digest:
                        raise ValueError("audit chain invalid")
                    event = json.loads(event_body)
                    if event["revision"] != index:
                        raise ValueError("audit revision invalid")
                    if index == 0 and (event["action"] != "created" or event["report_sha256"] != hashlib.sha256(json.dumps(json.loads(body), sort_keys=True).encode()).hexdigest()):
                        raise ValueError("original report invalid")
                    if index > 0 and event["action"] != "correction":
                        raise ValueError("audit action invalid")
                    previous = digest
                anchors[identifier] = previous
        return {"reports": len(reports), "anchors": anchors}
