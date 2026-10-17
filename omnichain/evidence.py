"""Trusted append-only SQLite writer, content-addressed artifacts and verifier.

Only this service writes events. Local anchors detect truncation separately from
hash validity; they do not protect against a privileged rewrite of all storage.
"""
import hashlib
import json
import re
import sqlite3
import threading
import uuid
from pathlib import Path
from .contracts import canonical, digest, now

HEX = re.compile(r"^[a-f0-9]{64}$")
MAX_STORAGE = 64*1024*1024
MAX_RUNS = 500


class ClosingConnection(sqlite3.Connection):
    """Commit/rollback and close: sqlite's default context manager leaves it open."""
    def __exit__(self, kind, value, traceback):
        try:
            return super().__exit__(kind, value, traceback)
        finally:
            self.close()


class Ledger:
    def __init__(self, directory):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        with self.connect() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1):
                raise ValueError('Unsupported evidence database version; use a compatible application or a new data directory.')
            db.executescript("""
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, contract TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(run TEXT NOT NULL, seq INTEGER NOT NULL,
              id TEXT NOT NULL UNIQUE, envelope TEXT NOT NULL, previous TEXT NOT NULL,
              hash TEXT NOT NULL, PRIMARY KEY(run,seq));
            CREATE TABLE IF NOT EXISTS anchors(run TEXT PRIMARY KEY, count INTEGER, head TEXT);
            CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
              BEGIN SELECT RAISE(ABORT,'events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
              BEGIN SELECT RAISE(ABORT,'events are append-only'); END;
            """)
            db.execute('PRAGMA user_version=1')

    def connect(self):
        db = sqlite3.connect(self.root / "ledger.sqlite3", timeout=15, factory=ClosingConnection)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def artifact(self, payload):
        data = canonical(payload)
        if len(data) > 131072:
            raise ValueError("Artifact size limit exceeded.")
        key = hashlib.sha256(data).hexdigest()
        target = self.artifacts / (key + ".json")
        if not target.exists():
            size=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
            if size+len(data) > MAX_STORAGE:
                raise ValueError('Local evidence storage limit reached; run remains incomplete.')
            temp = self.artifacts / (uuid.uuid4().hex + ".tmp")
            temp.write_bytes(data)
            temp.replace(target)
        return key

    def start(self, kind, required, context):
        self.check_capacity()
        run = uuid.uuid4().hex
        contract = {"run": run, "kind": kind, "version": 1, "required": required, "context": context}
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES (?,?)", (run, canonical(contract).decode()))
        return run

    def check_capacity(self):
        """Never purge evidence automatically; refuse new work at local limits."""
        size = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        with self.connect() as db:
            count = db.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
        if size >= MAX_STORAGE or count >= MAX_RUNS:
            raise ValueError('Local evidence limit reached (64 MiB / 500 runs). Back up records and choose a new data directory.')

    def contract(self, run):
        with self.connect() as db:
            row=db.execute('SELECT contract FROM runs WHERE id=?',(run,)).fetchone()
        if not row:
            raise ValueError('Unknown run.')
        return json.loads(row[0])

    def finalized(self, run):
        with self.connect() as db:
            return bool(db.execute('SELECT 1 FROM anchors WHERE run=?',(run,)).fetchone())

    def backup(self, destination):
        """Snapshot under the writer lock; caller must also exclude active jobs."""
        destination=Path(destination)
        if destination.exists():
            raise ValueError('Backup destination must be a new directory.')
        # Prevent a recursive copy into this evidence directory.
        if destination.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('Backup destination must be outside the evidence directory.')
        with self.lock:
            destination.mkdir(parents=True)
            (destination/'artifacts').mkdir()
            with self.connect() as src, sqlite3.connect(destination/'ledger.sqlite3',factory=ClosingConnection) as dst:
                src.backup(dst)
            for artifact in self.artifacts.glob('*.json'):
                (destination/'artifacts'/artifact.name).write_bytes(artifact.read_bytes())
        restored=Ledger(destination)
        with restored.connect() as db:
            ids=[r[0] for r in db.execute('SELECT id FROM runs')]
        return {'runs':len(ids),'checks':{r:restored.verify(r) for r in ids}}

    def append(self, run, event, payload, actor="runner", parent=None, logical_id=None):
        """Atomically assign sequence/hash; repeated logical IDs must match bytes."""
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT contract FROM runs WHERE id=?", (run,)).fetchone()
            if not row:
                raise ValueError("Unknown run.")
            if db.execute("SELECT 1 FROM anchors WHERE run=?", (run,)).fetchone():
                raise ValueError("Run already finalized.")
            artifact = self.artifact(payload)
            event_id = logical_id or uuid.uuid4().hex
            prior = db.execute("SELECT envelope FROM events WHERE id=?", (event_id,)).fetchone()
            if prior:
                env = json.loads(prior[0])
                if env["run"] == run and env["type"] == event and env["artifact"] == artifact and env["parent"] == parent and env["actor"] == actor:
                    return event_id
                raise ValueError("Duplicate event ID with different content.")
            if parent and not db.execute("SELECT 1 FROM events WHERE run=? AND id=?", (run, parent)).fetchone():
                raise ValueError("Parent must reference a prior event in this run.")
            last = db.execute("SELECT seq,hash FROM events WHERE run=? ORDER BY seq DESC LIMIT 1", (run,)).fetchone()
            seq, previous = (last[0] + 1, last[1]) if last else (1, digest(json.loads(row[0])))
            if seq > 1500:
                raise ValueError("Run event budget exceeded.")
            env = {"version": 1, "run": run, "seq": seq, "id": event_id, "type": event,
                   "actor": actor, "parent": parent, "recorded_at": now(), "artifact": artifact}
            head = digest({"domain": "omnichain-event-v1", "previous": previous, "event": env})
            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)", (run, seq, event_id, canonical(env).decode(), previous, head))
            return event_id

    def finish(self, run, summary):
        with self.lock:
            self.append(run, "run_finalized", summary)
            with self.connect() as db:
                count, head = db.execute("SELECT seq,hash FROM events WHERE run=? ORDER BY seq DESC LIMIT 1", (run,)).fetchone()
                db.execute("INSERT INTO anchors VALUES (?,?,?)", (run, count, head))

    def events(self, run):
        with self.connect() as db:
            rows = db.execute("SELECT envelope,hash,previous FROM events WHERE run=? ORDER BY seq", (run,)).fetchall()
        result = []
        for raw, head, prev in rows:
            env = json.loads(raw)
            key = env["artifact"]
            if not HEX.fullmatch(key):
                raise ValueError("Invalid artifact reference.")
            env.update(hash=head, previous=prev, payload=json.loads((self.artifacts / (key + ".json")).read_text(encoding="utf-8")))
            result.append(env)
        return result

    def verify(self, run):
        """Check canonical envelopes, row metadata, lineage, digests and finalization."""
        errors, missing, seen, types, decoded = [], [], set(), [], []
        with self.connect() as db:
            row = db.execute("SELECT contract FROM runs WHERE id=?", (run,)).fetchone()
            if not row:
                return {"integrity": False, "complete": False, "errors": ["Unknown run"], "missing": []}
            contract = json.loads(row[0])
            rows = db.execute("SELECT seq,id,envelope,previous,hash FROM events WHERE run=? ORDER BY seq", (run,)).fetchall()
            anchor = db.execute("SELECT count,head FROM anchors WHERE run=?", (run,)).fetchone()
        previous = digest(contract)
        for n, (seq, event_id, raw, prev, head) in enumerate(rows, 1):
            try:
                env = json.loads(raw)
                if (seq != n or env["seq"] != seq or env["id"] != event_id or env["run"] != run or
                    event_id in seen or (env["parent"] and env["parent"] not in seen)):
                    errors.append("Sequence, identity or lineage mismatch")
                if prev != previous or digest({"domain": "omnichain-event-v1", "previous": prev, "event": env}) != head:
                    errors.append("Hash mismatch")
                key = env["artifact"]
                if not HEX.fullmatch(key):
                    raise ValueError("Bad artifact reference")
                data = (self.artifacts / (key + ".json")).read_bytes()
                if hashlib.sha256(data).hexdigest() != key:
                    errors.append("Artifact digest mismatch")
                decoded.append({'type':env['type'],'payload':json.loads(data)})
                seen.add(event_id)
                types.append(env["type"])
                previous = head
            except (KeyError, ValueError, OSError, TypeError):
                errors.append("Missing or malformed evidence")
        missing.extend(t for t in contract["required"] if t not in types)
        if not rows or not types or types[-1] != "run_finalized":
            missing.append("run_finalized")
        if not anchor or anchor != (len(rows), previous):
            missing.append("finalization_anchor")
        missing.extend(manifest_gaps(contract,decoded))
        return {"integrity": not errors, "complete": not missing, "errors": sorted(set(errors)),
                "missing": sorted(set(missing)), "count": len(rows), "head": previous}

    def put(self, key, value):
        with self.connect() as db:
            db.execute("INSERT INTO state VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, canonical(value).decode()))

    def get(self, key, default=None):
        with self.connect() as db:
            row = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def export(self, run):
        with self.connect() as db:
            contract = json.loads(db.execute("SELECT contract FROM runs WHERE id=?", (run,)).fetchone()[0])
        return {"contract": contract, "events": self.events(run), "verification": self.verify(run),
                "limits": "Local tamper evidence; a privileged full rewrite of storage and anchors is outside this trust boundary."}


def _verify_export_run(bundle):
    """Portable check of payload digests, event chain and declared final head.

    The included anchor is not an independent authenticity guarantee. Compare a
    separately retained bundle digest/head when independent provenance is needed.
    """
    errors, types, seen = [], [], set()
    try:
        contract, events = bundle["contract"], bundle["events"]
        previous = digest(contract)
        for n, item in enumerate(events, 1):
            env = {k: v for k, v in item.items() if k not in ("hash", "previous", "payload")}
            if env["run"] != contract["run"] or env["seq"] != n or env["id"] in seen or (env["parent"] and env["parent"] not in seen):
                errors.append("Identity or lineage mismatch")
            if digest(item["payload"]) != env["artifact"]:
                errors.append("Artifact mismatch")
            if item["previous"] != previous or digest({"domain":"omnichain-event-v1","previous":item["previous"],"event":env}) != item["hash"]:
                errors.append("Hash mismatch")
            seen.add(env["id"]); types.append(env["type"]); previous = item["hash"]
        complete = bool(types and types[-1] == "run_finalized" and set(contract["required"]) <= set(types) and
                        not manifest_gaps(contract,events) and
                        bundle["verification"]["head"] == previous and bundle["verification"]["count"] == len(events))
    except (KeyError, TypeError, ValueError):
        errors.append("Malformed export"); complete = False
    return {"integrity": not errors, "complete": complete, "errors": sorted(set(errors))}


def manifest_gaps(contract, events):
    """Check exact expected case/trial counts, not just presence of event types."""
    if (not isinstance(contract,dict) or not isinstance(contract.get('context',{}),dict) or
        any(not isinstance(e.get('payload'),dict) for e in events)):
        return ['malformed_event_payload']
    context=contract.get('context',{})
    expected=context.get('expected_trials',{})
    trials=[e['payload'] for e in events if e['type']=='trial_finished']
    ids=[t.get('trial') for t in trials]
    gaps=[]
    if expected and (len(ids)!=len(expected) or set(ids)!=set(expected)):
        gaps.append('exact_trial_manifest')
    for trial in trials:
        spec=expected.get(trial.get('trial'))
        if spec and any(trial.get(k)!=v for k,v in spec.items()):
            gaps.append('trial_identity')
    cases=context.get('expected_validation_cases',[])
    if cases:
        observed=[e['payload'].get('case') for e in events if e['type']=='validation_test']
        if len(observed)!=len(cases) or set(observed)!=set(cases):
            gaps.append('exact_validation_manifest')
    return gaps


def verify_export(bundle):
    """Verify every included run and require the final report's linked run IDs."""
    try:
        runs = [bundle, *bundle.get("linked_runs", [])]
        checks = [_verify_export_run(run) for run in runs]
        ids = [run["contract"]["run"] for run in runs]
        references = set()
        for run in runs:
            report = run["events"][-1]["payload"] if run["events"] else {}
            if not isinstance(report,dict):
                raise ValueError('Malformed final report')
            references.update(report[k] for k in ("source_run", "comparison_run", "selection_run") if report.get(k))
        complete = all(c["complete"] for c in checks) and references <= set(ids) and len(ids) == len(set(ids))
        return {"integrity": all(c["integrity"] for c in checks), "complete": complete,
                "errors": sorted(set(e for c in checks for e in c["errors"]))}
    except (KeyError, TypeError, ValueError):
        return {"integrity":False,"complete":False,"errors":["Malformed assessment export"]}
