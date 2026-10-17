"""Loopback API boundary tests; no external services are contacted."""
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from omnichain.server import AppServer
from omnichain.evidence import Ledger


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = AppServer(0, cls.temp.name)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self, path, data=None, token=True, headers=None):
        h = {"X-OmniChain-Token": self.server.token} if token else {}
        if data is not None: h["Content-Type"] = "application/json"
        h.update(headers or {})
        req = urllib.request.Request(self.server.origin + path, headers=h, data=None if data is None else json.dumps(data).encode())
        try:
            with urllib.request.urlopen(req, timeout=5) as r: return r.status, r.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read()

    def test_api_requires_session_token(self):
        self.assertEqual(self.request('/api/state', token=False)[0],403)
        self.assertEqual(self.request('/api/state')[0],200)

    def test_origin_and_host_rejected(self):
        self.assertEqual(self.request('/api/state',headers={"Origin":"https://example.com"})[0],403)
        self.assertEqual(self.request('/api/state',headers={"Host":"example.com"})[0],403)

    def test_request_cannot_supply_tool_code_or_endpoint(self):
        self.assertEqual(self.request('/api/attack',{"mode":"DETERMINISTIC_FIXTURE","endpoint":"https://example.com"})[0],400)

    def test_only_static_allowlist_is_served(self):
        self.assertEqual(self.request('/omnichain/models.py')[0],404)
        self.assertEqual(self.request('/runtime/ledger.sqlite3')[0],404)
        status,body=self.request('/')
        self.assertEqual(status,200)
        self.assertIn(self.server.token.encode(),body)
        self.assertNotIn(b'__SESSION_TOKEN__',body)

    def test_pending_workflow_gates(self):
        self.assertEqual(self.request('/api/select',{"candidate":"PUB-SCOPED-TOOLS"})[0],400)

    def test_state_exposes_job_for_browser_recovery(self):
        prior=self.server.service.ledger.get('job')
        try:
            self.server.service.ledger.put('job',{'id':'test-active','kind':'compare','status':'RUNNING'})
            status,body=self.request('/api/state')
            self.assertEqual(status,200)
            self.assertEqual(json.loads(body)['job']['id'],'test-active')
        finally:
            self.server.service.ledger.put('job',prior)

    def test_evidence_route_exposes_recorded_graph(self):
        run=self.server.service.attack()['run']
        status,body=self.request('/api/evidence/'+run)
        self.assertEqual(status,200)
        self.assertIn('edges',json.loads(body)['graph'])


class JobRecovery(unittest.TestCase):
    def test_restart_marks_active_attempt_interrupted(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=Ledger(directory)
            ledger.put('job',{'id':'prior-active','kind':'validate','status':'RUNNING'})
            server=AppServer(0,directory)
            try:
                self.assertEqual(server.service.ledger.get('job')['status'],'INTERRUPTED')
            finally:
                server.server_close()

    def test_failed_registration_releases_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            server=AppServer(0,directory)
            try:
                with patch.object(server.service.ledger,'put',side_effect=OSError('test storage error')):
                    with self.assertRaises(OSError): server.submit('attack','DETERMINISTIC_FIXTURE')
                self.assertFalse(server.worker_lock.locked())
            finally:
                server.server_close()


if __name__ == '__main__': unittest.main()
