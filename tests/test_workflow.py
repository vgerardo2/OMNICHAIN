"""Negative cases and end-to-end checks; no network or API credentials required."""
import copy
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from omnichain.contracts import CONTROLS, CASES, POLICY, digest, parse_actions, validate_profile
from omnichain.evidence import Ledger, verify_export
from omnichain.engine import check_scope
from omnichain.models import Models
from omnichain.service import Service


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.s = Service(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def comparison(self):
        self.s.attack()
        return self.s.compare()

    def selection(self):
        c = self.comparison()["candidates"]["PUB-SCOPED-TOOLS"]
        return self.s.select("PUB-SCOPED-TOOLS", c["config_hash"], "Preserve authorized summaries and deny restricted fields.", "small", [40,30,20,10])

    def test_actual_mock_violation_and_supported_lineage(self):
        result = self.s.attack()
        self.assertTrue(result["finding"])
        events = self.s.ledger.events(result["run"])
        requests = {e["id"] for e in events if e["type"] == "tool_requested"}
        send = [e for e in events if e["type"] == "tool_observed"][-1]
        self.assertTrue(set(send["payload"]["data_lineage"]) <= requests)
        self.assertTrue(send["payload"]["allowed"])
        self.assertTrue(self.s.ledger.verify(result["run"])["complete"])

    def test_controls_raw_tradeoffs_and_clean_state(self):
        c = self.comparison()["candidates"]
        self.assertFalse(c["PUB-PROMPT-FILTER"]["eligible"])
        self.assertFalse(c["PUB-DESTINATION-ALLOWLIST"]["eligible"])
        self.assertTrue(c["PUB-SCOPED-TOOLS"]["eligible"])
        self.assertEqual(c["PUB-SCOPED-TOOLS"]["task_success"], {"numerator":2,"denominator":2})
        self.assertEqual(c["PUB-PROMPT-FILTER"]["false_blocks"], {"numerator":2,"denominator":4})
        self.assertIsNone(c["PUB-SCOPED-TOOLS"]["cost"])

    def test_validation_requires_approval(self):
        with self.assertRaises(ValueError): self.s.validate()

    def test_selection_requires_frozen_hash_and_rationale(self):
        self.comparison()
        for name, hash_, rationale in [("PUB-SCOPED-TOOLS","0"*64,"reason"), ("PUB-SCOPED-TOOLS",digest(CONTROLS["PUB-SCOPED-TOOLS"]),""), ("PUB-PROMPT-FILTER",digest(CONTROLS["PUB-PROMPT-FILTER"]),"high score")]:
            with self.assertRaises(ValueError): self.s.select(name,hash_,rationale,"small",[40,30,20,10])

    def test_full_independent_validation_rollback_and_restart(self):
        chosen = self.selection()
        result = self.s.validate()
        self.assertEqual(result["verdict"], "PASS")
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(result["config_hash"], chosen["config_hash"])
        self.assertEqual(Service(self.temp.name).state()["validation"]["run"], result["run"])
        self.assertEqual(len(result["tests"]), 5)

    def test_different_configuration_rejected(self):
        self.selection()
        config = copy.deepcopy(CONTROLS["PUB-SCOPED-TOOLS"])
        config["scoped"] = False
        with self.assertRaises(ValueError): self.s.validate(configuration=config)

    def test_faults_only_affect_copies(self):
        self.s.attack()
        for kind in ("tamper", "missing"):
            result = self.s.fault(kind)
            self.assertTrue(result["original_unchanged"])
            self.assertTrue(result["original_verification"]["complete"])
            self.assertFalse(result["copy_verification"]["integrity"] and result["copy_verification"]["complete"])

    def test_missing_finalization_differs_from_hash_validity(self):
        run = self.s.ledger.start("partial", ["required", "run_finalized"], {})
        self.s.ledger.append(run, "required", {})
        check = self.s.ledger.verify(run)
        self.assertTrue(check["integrity"])
        self.assertFalse(check["complete"])

    def test_idempotent_writes_and_append_only_trigger(self):
        run = self.s.ledger.start("test", [], {})
        self.s.ledger.append(run, "x", {"x":1}, logical_id="logical-id")
        self.s.ledger.append(run, "x", {"x":1}, logical_id="logical-id")
        with self.assertRaises(ValueError): self.s.ledger.append(run,"x",{"x":2},logical_id="logical-id")
        self.assertEqual(len(self.s.ledger.events(run)),1)
        with self.assertRaises(sqlite3.IntegrityError), self.s.ledger.connect() as db:
            db.execute("DELETE FROM events")

    def test_cross_run_parent_not_causal(self):
        a = self.s.ledger.start("a", [], {})
        parent = self.s.ledger.append(a,"a",{})
        b = self.s.ledger.start("b", [], {})
        with self.assertRaises(ValueError): self.s.ledger.append(b,"b",{},parent=parent)

    def test_expired_scope_and_cancellation(self):
        scope = self.s.scope(); scope["expires"] = (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError): self.s.attack(scope=scope)
        cancel = threading.Event(); cancel.set()
        with self.assertRaises(ValueError): self.s.attack(cancel=cancel)
        with self.s.ledger.connect() as db:
            run = db.execute("SELECT id FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()[0]
        self.assertFalse(self.s.ledger.verify(run)["complete"])
        self.assertEqual(self.s.ledger.events(run)[-1]["payload"]["verdict"],"INCONCLUSIVE")

    def test_bad_profiles(self):
        for weights in ([1,2,3,4], [True,30,20,49], [float("nan"),30,20,10], [-1,31,20,50]):
            with self.assertRaises(ValueError): validate_profile("custom",weights)

    def test_unknown_tools_and_attacker_authority_rejected(self):
        for action in ({"tool":"shell","command":"example"}, {"tool":"send","recipient":"https://example.com","fields":["invoice"]}):
            with self.assertRaises(ValueError): parse_actions({"actions":[action],"summary":"request"})
        with self.assertRaises(ValueError): parse_actions({"actions":[],"summary":"request","approval":True})

    def test_live_requires_explicit_setup(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError): self.s.attack("LIVE_HOSTED_MODEL")

    def test_live_adapter_contract_and_cap_without_network(self):
        response = {"candidates":[{"content":{"parts":[{"text":json.dumps({"actions":[],"summary":"Decline untrusted instruction."})}]}}]}
        model = Models(transport=lambda request: response)
        with patch.dict(os.environ,{"OMNICHAIN_ALLOW_LIVE":"1","OMNICHAIN_MAX_CALLS":"1","GEMINI_API_KEY":"test-only-not-a-real-key"},clear=True):
            proposal,meta=model.propose(CASES["original"],"LIVE_HOSTED_MODEL")
            self.assertEqual(proposal["actions"],[])
            with self.assertRaises(ValueError): model.propose(CASES["original"],"LIVE_HOSTED_MODEL")

    def test_changed_artifact_prevents_selection_and_pass(self):
        result = self.comparison()
        event = self.s.ledger.events(result["run"])[0]
        (self.s.ledger.artifacts/(event["artifact"]+".json")).write_text('{}',encoding="utf-8")
        self.assertFalse(self.s.ledger.verify(result["run"])["integrity"])
        with self.assertRaises(ValueError): self.s.select("PUB-SCOPED-TOOLS",digest(CONTROLS["PUB-SCOPED-TOOLS"]),"reason","small",[40,30,20,10])

    def test_portable_export_detects_mutation_and_truncation(self):
        run = self.s.attack()["run"]
        bundle = self.s.ledger.export(run)
        self.assertEqual(verify_export(bundle),{"integrity":True,"complete":True,"errors":[]})
        altered = copy.deepcopy(bundle); altered["events"][0]["payload"] = {"fake":True}
        self.assertFalse(verify_export(altered)["integrity"])
        del bundle["events"][-1]
        self.assertFalse(verify_export(bundle)["complete"])

    def test_validation_export_requires_linked_approval_and_experiments(self):
        self.selection()
        report=self.s.validate()
        bundle=self.s.export(report["run"])
        self.assertEqual(len(bundle["linked_runs"]),3)
        self.assertTrue(verify_export(bundle)["complete"])
        bundle["linked_runs"].pop()
        self.assertFalse(verify_export(bundle)["complete"])


if __name__ == "__main__":
    unittest.main()
