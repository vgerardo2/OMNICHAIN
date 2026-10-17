"""Assessment orchestration with persisted references and independent validation.

The browser selects IDs, never supplies executable patches, oracle verdicts,
fixture bytes, model endpoints or file paths. Every trial starts with fresh tools.
"""
import copy
import json
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from .contracts import (BASELINE, CONTROLS, CASES, SUITE, VALIDATION_CASES, VALIDATION_SUITE,
    POLICY, VERSION, digest, evaluate, validate_profile)
from .engine import trial, check_scope, summarize, Sandbox
from .evidence import Ledger
from .models import Models
from .context import execution_context
from .graph import reconstruct


class Service:
    def __init__(self, directory, models=None):
        self.ledger = Ledger(directory)
        self.models = models or Models()

    def scope(self):
        return {"id": uuid.uuid4().hex, "version": VERSION,
            "expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "assets": ["synthetic-invoice", "mock-tools"], "max_actions": 8}

    def result(self, run, seen=None, cache=None):
        """Present a result only after checking every linked run and frozen context."""
        cache = {} if cache is None else cache
        seen = set() if seen is None else set(seen)
        if run in seen or len(seen) >= 8:
            raise ValueError("Cyclic or excessive assessment dependencies.")
        if run in cache:
            return cache[run]
        seen.add(run)
        check = self.ledger.verify(run)
        if not check["integrity"] or not check["complete"]:
            raise ValueError("Required evidence is altered or incomplete; result is INCONCLUSIVE.")
        report = self.ledger.events(run)[-1]["payload"]
        context = self.ledger.contract(run)['context']
        current = execution_context(context['mode'],self.models.status())
        if context.get('execution_hash') != digest(current):
            raise ValueError("Run uses older or changed evaluation settings; rerun the assessment.")
        for key in ('source_run','comparison_run','selection_run'):
            if report.get(key):
                self.result(report[key],seen,cache)
        cache[run]=report
        return report

    def _begin(self, kind, mode, scope, required, configuration_hash=None):
        check_scope(scope)
        if mode not in ("DETERMINISTIC_FIXTURE", "LIVE_HOSTED_MODEL"):
            raise ValueError("Choose an explicit execution mode.")
        execution = execution_context(mode,self.models.status())
        expected = ({'baseline-original':{'case':'original','config_hash':digest(BASELINE)}} if kind=='attack' else
                    {c['id']+':'+case:{'case':case,'config_hash':digest(c)} for c in [BASELINE,*CONTROLS.values()] for case in SUITE} if kind=='comparison' else
                    {'validate:'+case:{'case':case,'config_hash':configuration_hash} for case in VALIDATION_SUITE} if kind=='validation' else {})
        run = self.ledger.start(kind, ["scope_authorized", *required, "run_finalized"],
            {"scope": scope, "mode": mode, "policy_hash": digest(POLICY), "suite_version": VERSION,
             "execution":execution,"execution_hash":digest(execution),"expected_trials":expected,
             "expected_validation_cases":list(VALIDATION_SUITE) if kind=='validation' else []})
        # Point at this attempt immediately. Failed retries must not retain a current PASS.
        self.ledger.put({'attack':'attack','comparison':'comparison','selection':'selection','validation':'validation'}[kind],run)
        for key in {'attack':('comparison','selection','validation'),'comparison':('selection','validation'),'selection':('validation',),'validation':()}[kind]:
            self.ledger.put(key,None)
        self.ledger.append(run, "scope_authorized", scope, actor="human-operator")
        return run

    def _failed(self, run, exc):
        # Only controlled ValueError messages reach this path; never persist transport secrets.
        # Never append to a finalized run or mask the original failure.
        if self.ledger.finalized(run):
            return
        try:
            self.ledger.append(run, "run_error", {"message": str(exc)[:500], "verdict": "INCONCLUSIVE"})
            self.ledger.finish(run, {"run": run, "verdict": "INCONCLUSIVE", "error": str(exc)[:500]})
        except (ValueError,OSError):
            pass  # Missing finalization remains verifiably incomplete if storage is unavailable.

    def attack(self, mode="DETERMINISTIC_FIXTURE", cancel=None, scope=None):
        scope = scope or self.scope()
        run = self._begin("attack", mode, scope, ["document_ingested", "proposal_recorded", "trial_finished"])
        try:
            result = trial(self.ledger, run, CASES["original"], BASELINE, mode, self.models, scope, cancel, "baseline-original",time.monotonic()+120)
            finding = result["oracle"]["violations"] > 0
            report = {"run": run, "kind": "attack", "mode": mode, "finding": finding, "trial": result,
                      "verdict": "OBSERVED" if finding else "NO_VIOLATION_OBSERVED"}
            self.ledger.finish(run, report)
            self.ledger.put("attack", run)
            # New evidence invalidates previous comparison/approval/validation context.
            for key in ("comparison", "selection", "validation"):
                self.ledger.put(key, None)
            return report
        except (ValueError,OSError) as exc:
            self._failed(run, exc)
            raise

    def compare(self, cancel=None):
        for key in ('comparison','selection','validation'):
            self.ledger.put(key,None)
        source = self.ledger.get("attack")
        if not source or not self.result(source).get("finding"):
            raise ValueError("Observe a synthetic policy violation and inspect its evidence before remediation.")
        mode = self.result(source)["mode"]
        scope = self.scope()
        run = self._begin("comparison", mode, scope, ["trial_finished", "comparison_finished"])
        start = time.monotonic()
        try:
            summaries, all_trials = {}, []
            for config in [BASELINE, *CONTROLS.values()]:
                current = []
                for case_id in SUITE:
                    if time.monotonic() - start > 120:
                        raise ValueError("Comparison time budget exceeded; partial evidence retained.")
                    t = trial(self.ledger, run, CASES[case_id], config, mode, self.models, scope, cancel, config["id"] + ":" + case_id,start+120)
                    current.append(t)
                    all_trials.append(t)
                summaries[config["id"]] = {"config": config, "config_hash": digest(config), **summarize(current)}
            report = {"run": run, "kind": "comparison", "source_run": source, "mode": mode,
                      "candidates": summaries, "trials": all_trials, "verdict": "COMPARED"}
            self.ledger.append(run, "comparison_finished", {"source_run": source, "candidate_hashes": {k: v["config_hash"] for k, v in summaries.items()}}, actor="optimize")
            self.ledger.finish(run, report)
            self.ledger.put("comparison", run)
            self.ledger.put("selection", None)
            self.ledger.put("validation", None)
            return report
        except (ValueError,OSError) as exc:
            self._failed(run, exc)
            raise

    def select(self, candidate, config_hash, rationale, profile, weights):
        if candidate not in CONTROLS or not isinstance(rationale, str) or not 1 <= len(rationale.strip()) <= 1000:
            raise ValueError("Select a known candidate and provide a review rationale.")
        preference = validate_profile(profile, weights)
        comparison_id = self.ledger.get("comparison")
        if not comparison_id:
            raise ValueError("Run matched control comparisons before selection.")
        comparison = self.result(comparison_id)
        if comparison["source_run"] != self.ledger.get("attack"):
            raise ValueError("Comparison no longer matches the current assessment.")
        if config_hash != digest(CONTROLS[candidate]):
            raise ValueError("Selected configuration hash does not match the tested configuration.")
        # Recompute from raw trusted observations, ignoring optimizer score fields.
        raw = [copy.deepcopy(e['payload']) for e in self.ledger.events(comparison_id)
               if e['type']=='trial_finished' and e['payload']['config']==candidate]
        for t in raw:
            t["oracle"] = evaluate(CASES[t["case"]], t["observations"])
        if len(raw)!=len(SUITE) or {t["case"] for t in raw} != set(SUITE) or not summarize(raw)["eligible"]:
            raise ValueError("Candidate fails mandatory security or legitimate-task gates.")
        scope = self.scope()
        run = self._begin("selection", comparison["mode"], scope, ["human_selected"])
        selection = {"run": run, "comparison_run": comparison_id, "source_run": comparison["source_run"],
                     "candidate": candidate, "config_hash": config_hash, "configuration": CONTROLS[candidate],
                     "rationale": rationale.strip(), "profile": preference, "profile_hash": digest(preference),
                     "mode": comparison["mode"], "kind": "selection", "verdict": "SELECTED"}
        self.ledger.append(run, "human_selected", selection, actor="human-operator")
        self.ledger.finish(run, selection)
        self.ledger.put("selection", run)
        self.ledger.put("validation", None)
        return selection

    def validate(self, cancel=None, configuration=None):
        self.ledger.put('validation',None)
        selection_id = self.ledger.get("selection")
        if not selection_id:
            raise ValueError("Human selection and rationale are required before validation.")
        chosen = self.result(selection_id)
        self.result(chosen["comparison_run"])
        self.result(chosen["source_run"])
        config = copy.deepcopy(configuration or CONTROLS[chosen["candidate"]])
        if digest(config) != chosen["config_hash"] or chosen["source_run"] != self.ledger.get("attack"):
            raise ValueError("Configuration or assessment differs from human approval.")
        scope = self.scope()
        run = self._begin("validation", chosen["mode"], scope, ["validation_test", "rollback_checked"],chosen['config_hash'])
        deadline = time.monotonic()+120
        try:
            tests = []
            for case_id in VALIDATION_SUITE:
                raw = trial(self.ledger, run, VALIDATION_CASES[case_id], config, chosen["mode"], self.models, scope, cancel, "validate:" + case_id,deadline)
                # Independent verdict: do not consume Optimize or runner's oracle field.
                verdict = evaluate(VALIDATION_CASES[case_id], raw["observations"])
                tests.append({"case": case_id, "security": verdict["security"], "operations": verdict["operations"], "attack": verdict["attack"],"rollback":raw['rollback']})
                self.ledger.append(run, "validation_test", tests[-1], actor="validate")
            sandbox = Sandbox()
            expected = digest(sandbox.values)
            sandbox.values["invoice"] = "changed mock state"
            sandbox.reset()
            rollback = digest(sandbox.values) == expected and all(t['rollback']['restored'] for t in tests)
            # Verify restored tools can actually complete a permitted task.
            sandbox.execute({'tool':'read','field':'invoice'},BASELINE,'rollback-read')
            allowed,_,_ = sandbox.execute({'tool':'send','recipient':'internal_mock','fields':['invoice']},BASELINE,'rollback-send','Invoice INV-0042, USD 1250.')
            rollback = rollback and allowed
            sandbox.reset()
            self.ledger.append(run, "rollback_checked", {"expected": expected, "actual": digest(sandbox.values), "restored": rollback}, actor="validate")
            gates = {"security": all(t["security"] for t in tests),
                     "operations": all(t["operations"] for t in tests if not t["attack"]),
                     "configuration": digest(config) == chosen["config_hash"], "rollback": rollback,
                     "evidence": all(self.ledger.verify(r)["integrity"] and self.ledger.verify(r)["complete"] for r in (selection_id, chosen["comparison_run"], chosen["source_run"]))}
            report = {"run": run, "kind": "validation", "mode": chosen["mode"], "selection_run": selection_id,
                      "config_hash": chosen["config_hash"], "suite_hash": digest(VALIDATION_CASES),
                      "tests": tests, "gates": gates, "verdict": "PASS" if all(gates.values()) else "FAIL"}
            self.ledger.finish(run, report)
            check = self.ledger.verify(run)
            if not check["integrity"] or not check["complete"]:
                raise ValueError("Validation evidence is incomplete; no passing result is accepted.")
            self.ledger.put("validation", run)
            return report
        except (ValueError,OSError) as exc:
            if not self.ledger.verify(run)["complete"]:
                self._failed(run, exc)
            raise

    def state(self):
        state = {"model": self.models.status(), "policy_hash": digest(POLICY), "configs": CONTROLS,
                 "config_hashes": {k: digest(v) for k, v in CONTROLS.items()}, "version": VERSION}
        verified={}
        for name in ("attack", "comparison", "selection", "validation"):
            run = self.ledger.get(name)
            if run:
                try:
                    state[name] = self.result(run,cache=verified)
                except (ValueError,OSError,KeyError,TypeError):
                    state[name] = {"run": run, "verdict": "INCONCLUSIVE", "error": "Evidence or evaluation settings changed, or this run is incomplete. Start a new assessment; older records remain available as history."}
            else:
                state[name] = None
        return state

    def fault(self, kind):
        """Fault injection runs on an isolated copy; original events stay intact."""
        run = self.ledger.get("validation") or self.ledger.get("comparison") or self.ledger.get("attack")
        if not run or kind not in ("tamper", "missing"):
            raise ValueError("Create evidence first and choose tamper or missing.")
        original = self.ledger.verify(run)
        with tempfile.TemporaryDirectory(prefix="omnichain-fault-") as directory:
            target = Ledger(directory)
            with self.ledger.connect() as src, target.connect() as dst:
                src.backup(dst)
            for artifact in self.ledger.artifacts.glob("*.json"):
                shutil.copyfile(artifact, target.artifacts / artifact.name)
            with target.connect() as db:
                if kind == "tamper":
                    db.execute("DROP TRIGGER events_no_update")
                    db.execute("UPDATE events SET hash=? WHERE run=? AND seq=1", ("0" * 64, run))
                else:
                    db.execute("DROP TRIGGER events_no_delete")
                    db.execute("DELETE FROM events WHERE run=? AND seq=(SELECT MAX(seq) FROM events WHERE run=?)", (run, run))
            altered = target.verify(run)
        return {"kind": kind, "run": run, "copy_verification": altered,
                "original_verification": self.ledger.verify(run), "original_unchanged": original == self.ledger.verify(run)}

    def export(self, run):
        """Export linked assessment dependencies, not just a detached verdict."""
        bundle = self.ledger.export(run)
        try:
            self.result(run)
            bundle['current_status']={'usable':True}
        except (ValueError,OSError,KeyError,TypeError):
            bundle['current_status']={'usable':False,'verdict':'INCONCLUSIVE','reason':'Evidence or evaluation context changed; historical verdict is not current.'}
        linked, pending, seen = [], [bundle], {run}
        while pending:
            current = pending.pop()
            result = current["events"][-1]["payload"] if current["events"] else {}
            if not isinstance(result,dict):
                result={}
            for key in ("source_run", "comparison_run", "selection_run"):
                reference = result.get(key)
                if reference and reference not in seen:
                    dependency = self.ledger.export(reference)
                    seen.add(reference); linked.append(dependency); pending.append(dependency)
        bundle["linked_runs"] = linked
        for item in [bundle,*linked]:
            item['graph']=(reconstruct(item['events']) if item['verification']['integrity'] else
                           {'error':'Evidence integrity failed; relationships were not reconstructed.'})
        from .evidence import verify_export
        bundle['assessment_verification']=verify_export(bundle)
        return bundle
