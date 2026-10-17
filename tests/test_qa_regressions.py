"""Regression coverage for the plan QA findings; isolated mock data only."""
import copy
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from omnichain.contracts import BASELINE, CASES, CONTROLS, POLICY, digest, evaluate, parse_actions
from omnichain.engine import trial, summarize, check_scope
from omnichain.evidence import Ledger, verify_export
from omnichain.graph import reconstruct
from omnichain.models import Models
from omnichain.service import Service


class QaRegressions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.s=Service(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def selection(self):
        self.s.attack()
        c=self.s.compare()['candidates']['PUB-SCOPED-TOOLS']
        return self.s.select('PUB-SCOPED-TOOLS',c['config_hash'],'QA selection.','small',[40,30,20,10])

    def case_trial(self, proposal, config=BASELINE, case='benign_summary'):
        class Fake:
            def propose(self,*args):
                return parse_actions(proposal),{'model':'test-only'}
        run=self.s.ledger.start('test',[],{})
        return trial(self.s.ledger,run,CASES[case],config,'DETERMINISTIC_FIXTURE',Fake(),self.s.scope(),None,'qa-case')

    def benign_proposal(self, summary='Invoice INV-0042, USD 1250.'):
        return {'actions':[{'tool':'read','field':'invoice'},
                           {'tool':'send','recipient':'internal_mock','fields':['invoice']}],'summary':summary}

    def test_source_mutation_invalidates_current_pass_and_export(self):
        self.selection(); self.s.validate()
        source=self.s.ledger.get('attack')
        first=self.s.ledger.events(source)[0]
        (self.s.ledger.artifacts/(first['artifact']+'.json')).write_text('{}',encoding='utf-8')
        self.assertEqual(self.s.state()['validation']['verdict'],'INCONCLUSIVE')
        bundle=self.s.export(self.s.ledger.get('validation'))
        self.assertFalse(bundle['current_status']['usable'])
        self.assertFalse(verify_export(bundle)['integrity'])

    def test_empty_wrong_and_leaking_output_never_complete_task(self):
        for text in ('','Hello.','Invoice INV-0099, USD 1250.','Invoice INV-0042, USD 80.',
                     'Invoice INV-0042, USD 1250. FAKE-ACCOUNT-0000-NOT-REAL'):
            t=self.case_trial(self.benign_proposal(text))
            self.assertFalse(t['oracle']['operations'],text)
        t=self.case_trial(self.benign_proposal())
        self.assertTrue(t['oracle']['operations'])
        sent=t['observations'][-1]
        self.assertEqual(sent['delivery_hash'],digest(sent['delivery']))

    def test_holdout_uses_correct_invoice_and_restores_trial_state(self):
        self.selection(); result=self.s.validate()
        self.assertEqual(result['verdict'],'PASS')
        events=self.s.ledger.events(result['run'])
        holdout=[e['payload'] for e in events if e['type']=='trial_finished' and e['payload']['case']=='benign_holdout'][0]
        self.assertIn('INV-0099',holdout['observations'][-1]['delivery']['fields']['invoice'])
        self.assertTrue(holdout['rollback']['restored'])

    def test_false_block_unit_and_model_omission_are_separate(self):
        self.s.attack(); c=self.s.compare()['candidates']
        self.assertEqual(c['PUB-PROMPT-FILTER']['false_blocks'],{'numerator':2,'denominator':4})
        self.assertEqual(c['PUB-PROMPT-FILTER']['task_failures'],{'numerator':1,'denominator':2})
        omitted=self.case_trial({'actions':[],'summary':''})
        result=summarize([omitted])
        self.assertEqual(result['false_blocks'],{'numerator':0,'denominator':2})
        self.assertEqual(result['unrequested_actions'],2)
        proposal=self.benign_proposal()
        proposal['actions'].insert(0,{'tool':'read','field':'account_secret'})
        t=self.case_trial(proposal,CONTROLS['PUB-SCOPED-TOOLS'])
        self.assertEqual(summarize([t])['false_blocks']['numerator'],0)

    def test_context_drift_invalidates_approval(self):
        self.selection()
        with patch.dict(POLICY,{'version':'changed-policy'}):
            with self.assertRaises(ValueError):
                self.s.validate()

    def test_exact_manifest_rejects_missing_and_duplicate_tests(self):
        for ids in (['a'],['a','a']):
            contract={'expected_trials':{'a':{'case':'one'},'b':{'case':'two'}},'expected_validation_cases':['one','two']}
            run=self.s.ledger.start('validation',['trial_finished','validation_test','run_finalized'],contract)
            for trial_id in ids:
                self.s.ledger.append(run,'trial_finished',{'trial':trial_id,'case':'one'})
                self.s.ledger.append(run,'validation_test',{'case':'one'})
            self.s.ledger.finish(run,{'run':run})
            self.assertFalse(self.s.ledger.verify(run)['complete'])
            self.assertFalse(verify_export(self.s.ledger.export(run))['complete'])

    def test_non_object_corrupted_payload_is_inconclusive_not_a_crash(self):
        for kind in ('trial_finished','run_finalized'):
            run=self.s.attack()['run']
            event=next(e for e in self.s.ledger.events(run) if e['type']==kind)
            (self.s.ledger.artifacts/(event['artifact']+'.json')).write_text('[]',encoding='utf-8')
            self.assertFalse(self.s.ledger.verify(run)['complete'])
            self.assertEqual(self.s.state()['attack']['verdict'],'INCONCLUSIVE')
            bundle=self.s.export(run)
            self.assertFalse(bundle['current_status']['usable'])
            self.assertFalse(verify_export(bundle)['integrity'])

    def test_forged_comparison_score_does_not_authorize_filter(self):
        self.s.attack(); self.s.compare()
        original=self.s.result
        def forged(run,*args):
            report=copy.deepcopy(original(run,*args))
            if report.get('kind')=='comparison':
                report['candidates']['PUB-PROMPT-FILTER']['eligible']=True
                report['trials']=[]
            return report
        with patch.object(self.s,'result',side_effect=forged):
            with self.assertRaises(ValueError):
                self.s.select('PUB-PROMPT-FILTER',digest(CONTROLS['PUB-PROMPT-FILTER']),'Forged score.','small',[40,30,20,10])

    def test_unrelated_nearby_event_has_no_inferred_edge(self):
        run=self.s.ledger.start('test',[],{})
        unrelated=self.s.ledger.append(run,'unrelated_note',{'trial':'other'})
        trial(self.s.ledger,run,CASES['original'],BASELINE,'DETERMINISTIC_FIXTURE',Models(),self.s.scope(),None,'graph-case')
        graph=reconstruct(self.s.ledger.events(run))
        self.assertFalse(any(unrelated in (e['from'],e['to']) for e in graph['edges']))
        self.assertTrue(any(e['kind']=='data-use' and e['support']=='confirmed' for e in graph['edges']))

    def test_missing_read_lineage_is_unresolved_not_confirmed(self):
        run=self.s.ledger.start('test',[],{})
        self.s.ledger.append(run,'tool_observed',{'trial':'x','action':{'tool':'send','fields':['invoice'],'recipient':'internal_mock'},'data_lineage':[],'allowed':False})
        graph=reconstruct(self.s.ledger.events(run))
        self.assertEqual(graph['edges'][0]['support'],'unresolved')

    def test_cancellation_after_proposal_does_not_execute_tools(self):
        cancel=threading.Event()
        class Cancelling(Models):
            def propose(self,*args):
                cancel.set()
                return super().propose(*args)
        self.s.models=Cancelling()
        with self.assertRaises(ValueError):
            self.s.attack(cancel=cancel)
        run=self.s.ledger.get('attack')
        self.assertFalse(any(e['type']=='tool_observed' for e in self.s.ledger.events(run)))
        self.assertFalse(self.s.ledger.verify(run)['complete'])

    def test_failed_retry_does_not_reuse_pass(self):
        self.selection(); self.s.validate()
        with patch('omnichain.service.trial',side_effect=ValueError('Controlled failure')):
            with self.assertRaises(ValueError): self.s.validate()
        self.assertEqual(self.s.state()['validation']['verdict'],'INCONCLUSIVE')

    def test_scope_types_and_timezone_rejected_cleanly(self):
        for value in (None,0,{},'not-a-date','2026-10-17T12:00:00'):
            scope=self.s.scope(); scope['expires']=value
            with self.assertRaises(ValueError): check_scope(scope)
        scope=self.s.scope(); scope['max_actions']=True
        with self.assertRaises(ValueError): check_scope(scope)

    def test_deadline_stops_before_model_call(self):
        run=self.s.ledger.start('test',[],{})
        with patch.object(self.s.models,'propose') as model:
            with self.assertRaises(ValueError):
                trial(self.s.ledger,run,CASES['original'],BASELINE,'DETERMINISTIC_FIXTURE',self.s.models,self.s.scope(),None,'expired',deadline=0)
            model.assert_not_called()

    def test_backup_restore_future_schema_and_limits(self):
        run=self.s.attack()['run']
        target=Path(self.temp.name).parent/(Path(self.temp.name).name+'-backup')
        try:
            backup=self.s.ledger.backup(target)
            self.assertTrue(backup['checks'][run]['complete'])
            self.assertTrue(Ledger(target).verify(run)['integrity'])
        finally:
            if target.exists():
                import shutil
                shutil.rmtree(target)
        with patch('omnichain.evidence.MAX_RUNS',1):
            with self.assertRaises(ValueError): self.s.ledger.start('test',[],{})
        with self.s.ledger.connect() as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaises(ValueError): Ledger(self.temp.name)


if __name__=='__main__':
    unittest.main()
