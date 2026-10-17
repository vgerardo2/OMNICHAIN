"""Loopback-only HTTP UI/API, session-token CSRF protection and bounded jobs.

No request can supply a file path, external URL, model credential or executable
code. Long work uses a single background worker with explicit cancellation.
"""
import json
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .contracts import canonical
from .service import Service
from .graph import reconstruct
from .engine import Cancelled


class AppServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, port, directory):
        self.service = Service(directory)
        self.token = secrets.token_urlsafe(32)
        self.jobs = {}
        self.job_lock = threading.Lock()
        self.worker_lock = threading.Lock()
        self.connection_slots=threading.BoundedSemaphore(16)
        prior=self.service.ledger.get('job')
        if prior and prior.get('status')=='RUNNING':
            self.service.ledger.put('job',{'id':prior['id'],'kind':prior['kind'],'status':'INTERRUPTED',
                                         'error':'The server stopped during this attempt. Partial evidence is retained; start a new run.'})
        self.web = Path(__file__).resolve().parent.parent / "web"
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = "http://127.0.0.1:" + str(self.server_port)

    def process_request(self, request, client_address):
        if not self.connection_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request,client_address)
        except Exception:
            self.connection_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request,client_address)
        finally:
            self.connection_slots.release()

    def submit(self, kind, mode):
        if not self.worker_lock.acquire(blocking=False):
            raise ValueError("One job is already running. Cancel or wait for it.")
        job_id = uuid.uuid4().hex
        cancel = threading.Event()
        job = {"id": job_id, "kind": kind, "status": "RUNNING", "cancel": cancel}
        # Bound in-memory completed results without deleting evidence records.
        for old in list(self.jobs):
            if len(self.jobs)<64:
                break
            if self.jobs[old]['status']!='RUNNING':
                del self.jobs[old]
        self.jobs[job_id] = job
        try:
            self.service.ledger.put('job',{'id':job_id,'kind':kind,'status':'RUNNING'})
        except Exception:
            del self.jobs[job_id]
            self.worker_lock.release()
            raise
        def execute():
            try:
                if kind == "attack":
                    result = self.service.attack(mode, cancel)
                elif kind == "compare":
                    result = self.service.compare(cancel)
                else:
                    result = self.service.validate(cancel)
                job.update(status="FINISHED", result=result)
            except Cancelled as exc:
                job.update(status='CANCELLED',error=str(exc))
            except ValueError as exc:
                job.update(status="INCONCLUSIVE", error=str(exc)[:500])
            except Exception:
                job.update(status="INCONCLUSIVE", error="Unexpected local error. Partial evidence is retained; no passing outcome is claimed.")
            finally:
                saved={k:v for k,v in job.items() if k not in ('cancel','result')}
                if job.get('result'):
                    saved['run']=job['result']['run']
                try:
                    self.service.ledger.put('job',saved)
                finally:
                    self.worker_lock.release()
        threading.Thread(target=execute, daemon=True).start()
        return {"job": job_id}


class Handler(BaseHTTPRequestHandler):
    server_version = "OmniChain/0.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(25)

    def log_message(self, format, *args):
        pass  # Do not log request bodies, tokens, keys or personal paths.

    def respond(self, status, payload, content_type="application/json; charset=utf-8"):
        data = canonical(payload) if content_type.startswith("application/json") else payload
        self.send_response(status)
        for key, value in {"Content-Type": content_type, "Content-Length": str(len(data)),
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"}.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def authorized(self, api=False):
        if self.headers.get("Host") != "127.0.0.1:" + str(self.server.server_port):
            self.respond(403, {"error": "Invalid Host."})
            return False
        origin = self.headers.get("Origin")
        if origin and origin != self.server.origin:
            self.respond(403, {"error": "Cross-origin access denied."})
            return False
        if api and not secrets.compare_digest(self.headers.get("X-OmniChain-Token", ""), self.server.token):
            self.respond(403, {"error": "Invalid local session token."})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if not self.authorized(path.startswith("/api/")):
            return
        try:
            if path == "/":
                body = (self.server.web / "index.html").read_bytes().replace(b"__SESSION_TOKEN__", self.server.token.encode())
                self.respond(200, body, "text/html; charset=utf-8")
            elif path in ("/style.css", "/app.js"):
                name = path[1:]
                self.respond(200, (self.server.web / name).read_bytes(), "text/css; charset=utf-8" if name.endswith("css") else "text/javascript; charset=utf-8")
            elif path == "/api/state":
                state=self.server.service.state()
                state['job']=self.server.service.ledger.get('job')
                self.respond(200,state)
            elif path == "/api/runs":
                with self.server.service.ledger.connect() as db:
                    rows = db.execute("SELECT id,contract FROM runs ORDER BY rowid DESC LIMIT 100").fetchall()
                self.respond(200, [{"id": r, "kind": json.loads(c)["kind"], "verification": self.server.service.ledger.verify(r)} for r, c in rows])
            elif path.startswith("/api/job/"):
                job = self.server.jobs.get(path.rsplit("/", 1)[-1])
                if not job:
                    saved=self.server.service.ledger.get('job')
                    if saved and saved['id']==path.rsplit('/',1)[-1]:
                        self.respond(200,saved)
                        return
                    raise ValueError("Unknown job.")
                self.respond(200, {k: v for k, v in job.items() if k != "cancel"})
            elif path.startswith("/api/evidence/") or path.startswith("/api/export/"):
                run = path.rsplit("/", 1)[-1]
                if len(run) != 32 or any(c not in "0123456789abcdef" for c in run):
                    raise ValueError("Invalid run identifier.")
                if path.startswith('/api/export/'):
                    bundle=self.server.service.export(run)
                else:
                    bundle=self.server.service.ledger.export(run)
                    bundle['graph']=(reconstruct(bundle['events']) if bundle['verification']['integrity'] else
                                     {'error':'Evidence integrity failed; relationships were not reconstructed.'})
                self.respond(200,bundle)
            else:
                self.respond(404, {"error": "Not found."})
        except (ValueError, OSError, TypeError, KeyError):
            self.respond(400, {"error": "Requested evidence is missing, malformed or unavailable."})

    def do_POST(self):
        if not self.authorized(api=True):
            return
        try:
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Use application/json.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384 or self.headers.get("Transfer-Encoding"):
                raise ValueError("Request size is invalid.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Request must be an object.")
            path = urlsplit(self.path).path
            if path in ("/api/attack", "/api/compare", "/api/validate"):
                if set(data) - {"mode"}:
                    raise ValueError("Unexpected request fields.")
                kind = path.rsplit("/", 1)[-1]
                self.respond(202, self.server.submit(kind, data.get("mode", "DETERMINISTIC_FIXTURE")))
            elif path == "/api/select":
                if set(data) != {"candidate", "config_hash", "rationale", "profile", "weights"}:
                    raise ValueError("Selection fields are incomplete.")
                if not self.server.worker_lock.acquire(blocking=False):
                    raise ValueError("Wait for the active job before selection.")
                try:
                    selection = self.server.service.select(**data)
                finally:
                    self.server.worker_lock.release()
                self.respond(200, selection)
            elif path == "/api/cancel":
                job = self.server.jobs.get(data.get("job"))
                if not job:
                    raise ValueError("Unknown job.")
                job["cancel"].set()
                self.respond(200, {"status": "CANCELLATION_REQUESTED"})
            elif path == "/api/fault":
                if not self.server.worker_lock.acquire(blocking=False):
                    raise ValueError('Wait for the active job before testing evidence copies.')
                try:
                    result=self.server.service.fault(data.get('kind'))
                finally:
                    self.server.worker_lock.release()
                self.respond(200,result)
            else:
                self.respond(404, {"error": "Not found."})
        except (ValueError, TypeError, KeyError) as exc:
            self.respond(400, {"error": str(exc)[:500]})
        except Exception:
            self.respond(500, {"error": "Local operation failed; no successful result is claimed."})
