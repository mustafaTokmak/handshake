import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from repair_lab.carriers import CARRIERS, AGREEMENT, CANARY, LEGACY_SOURCE, contact_context, documentation, expected_quote, quote_response
from repair_lab.coordinator import Coordinator, LegacyResponse, code_hash
from repair_lab.models import Candidate, ContactReply, Order, Quote, StartRequest
from repair_lab.store import Store


class CarrierContracts(unittest.TestCase):
    def test_two_healthy_three_changed(self):
        order = Order().model_dump()
        request = dict(order_ref=order['reference'], weight_kg=order['weight_kg'], distance_km=order['distance_km'], destination_country='GB')
        healthy=[]
        for c in CARRIERS:
            status, response = quote_response(c['id'], request)
            try: LegacyResponse.model_validate(response)
            except ValidationError: continue
            self.assertEqual(status,200); healthy.append(c['id'])
        self.assertEqual(healthy,['parcelnest','meridian'])

    def test_prices_vary_with_order(self):
        for c in CARRIERS:
            self.assertNotEqual(expected_quote(c['id'],Order().model_dump())['amount_minor'], expected_quote(c['id'],Order(weight_kg=9,distance_km=811).model_dump())['amount_minor'])

    def test_contact_context_is_not_in_initial_docs(self):
        self.assertNotIn(AGREEMENT,documentation('harbor'))
        self.assertIn(AGREEMENT,contact_context())
        self.assertIn(CANARY,documentation('copper',True))
        self.assertNotIn(CANARY,documentation('copper',False))

    def test_quote_contract_rejects_coercion_and_bad_prices(self):
        for amount in (0,-1,'100',True,1.5):
            with self.assertRaises(ValidationError): Quote(amount_minor=amount,currency='GBP',eta_days=2,service='standard')

    def test_patch_identity_ignores_format_and_comments(self):
        self.assertEqual(code_hash('def f(x):\n return x'),code_hash('# another guess\ndef f(x):\n    return x\n'))


class RepairLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.tmp.name)/'test.sqlite')
        self.coordinator=Coordinator(self.store)
        self.launched=[]
        def launch(run_id,key,coro):
            self.launched.append((run_id,key)); coro.close()
        self.launch=patch.object(self.coordinator,'_launch',side_effect=launch);self.launch.start()
        self.run=self.coordinator.start(StartRequest())
        self.store.update_carrier(self.run['id'],'harbor',status='repairing',response={'error':'AGREEMENT_REQUIRED'},error='schema changed')

    def tearDown(self):
        self.launch.stop();self.store.db.close();self.tmp.cleanup()

    def test_five_distinct_failures_escalate_then_callback_resumes_once(self):
        candidates=[(Candidate(hypothesis='Try another request format',source=LEGACY_SOURCE+f'\nGUESS={i}\n'),{}) for i in range(5)]
        failure={'passed':False,'checks':[{'passed':False,'error':'Agreement required'}],'quote':None,'failure_response':None}
        with patch('repair_lab.coordinator.propose',AsyncMock(side_effect=candidates)), patch('repair_lab.coordinator.validate_patch',AsyncMock(return_value=failure)) as validator:
            asyncio.run(self.coordinator._repair(self.run['id'],'harbor',None,'initial'))
            self.assertEqual(validator.await_count,5)
        state=self.store.get_run(self.run['id'])['carriers']['harbor']
        self.assertEqual(state['status'],'waiting_contact')
        incident_id=state['incident_id']
        reply=ContactReply(message_id='reply-1',context=contact_context())
        self.assertFalse(self.coordinator.callback(incident_id,reply)['duplicate'])
        self.assertTrue(self.coordinator.callback(incident_id,reply)['duplicate'])
        self.assertEqual(len(self.launched),2)
        self.assertEqual(self.store.incident(incident_id)['status'],'resuming')

    def test_duplicate_candidates_do_not_spend_sandbox_attempts(self):
        proposal=(Candidate(hypothesis='Same patch repeated again',source=LEGACY_SOURCE),{})
        failure={'passed':False,'checks':[],'quote':None}
        with patch('repair_lab.coordinator.propose',AsyncMock(return_value=proposal)) as agent, patch('repair_lab.coordinator.validate_patch',AsyncMock(return_value=failure)) as validator:
            asyncio.run(self.coordinator._repair(self.run['id'],'harbor',None,'initial'))
            self.assertEqual(agent.await_count,10);self.assertEqual(validator.await_count,1)
        state=self.store.get_run(self.run['id'])['carriers']['harbor']
        self.assertEqual(state['status'],'waiting_contact')
        self.assertIn('before five',self.store.incident(state['incident_id'])['reason'])

    def test_sandbox_failure_never_promotes(self):
        proposal=(Candidate(hypothesis='Candidate awaiting execution',source=LEGACY_SOURCE),{})
        with patch('repair_lab.coordinator.propose',AsyncMock(return_value=proposal)), patch('repair_lab.coordinator.validate_patch',AsyncMock(side_effect=TimeoutError)):
            asyncio.run(self.coordinator._repair(self.run['id'],'harbor',None,'initial'))
        state=self.store.get_run(self.run['id'])['carriers']['harbor']
        self.assertEqual(state['status'],'infrastructure_error')
        self.assertEqual(state['attempts'][0]['status'],'interrupted')
        self.assertIsNone(state['quote'])

    def test_concurrent_new_run_is_rejected(self):
        self.coordinator.active.add(('existing','all'))
        with self.assertRaises(ValueError): self.coordinator.start(StartRequest())

    def test_failed_resumption_accepts_fresh_contact_context(self):
        self.coordinator._escalate(self.run['id'],'harbor','initial','Five failed patches',lambda *_:None)
        incident_id=self.store.get_run(self.run['id'])['carriers']['harbor']['incident_id']
        self.coordinator.callback(incident_id,ContactReply(message_id='first',context=contact_context()))
        with patch('repair_lab.coordinator.propose',AsyncMock(side_effect=TimeoutError)):
            asyncio.run(self.coordinator._repair(self.run['id'],'harbor',contact_context(),'contact-1'))
        self.assertEqual(self.store.incident(incident_id)['status'],'waiting')
        self.assertFalse(self.coordinator.callback(incident_id,ContactReply(message_id='second',context=contact_context()))['duplicate'])

    def test_restart_reopens_inflight_contact_incident(self):
        self.coordinator._escalate(self.run['id'],'harbor','initial','Five failed patches',lambda *_:None)
        incident_id=self.store.get_run(self.run['id'])['carriers']['harbor']['incident_id']
        self.coordinator.callback(incident_id,ContactReply(message_id='first',context=contact_context()))
        Coordinator(self.store)
        self.assertEqual(self.store.incident(incident_id)['status'],'waiting')
        self.assertEqual(self.store.get_run(self.run['id'])['carriers']['harbor']['status'],'waiting_contact')

    def test_busy_callback_does_not_consume_reply(self):
        self.coordinator._escalate(self.run['id'],'harbor','initial','Five failed patches',lambda *_:None)
        incident_id=self.store.get_run(self.run['id'])['carriers']['harbor']['incident_id']
        key=(self.run['id'],'harbor');self.coordinator.active.add(key)
        reply=ContactReply(message_id='retryable',context=contact_context())
        with self.assertRaises(ValueError):self.coordinator.callback(incident_id,reply)
        self.assertEqual(self.store.incident(incident_id)['messages'],[])
        self.assertEqual(self.store.incident(incident_id)['status'],'waiting')
        self.coordinator.active.remove(key)
        self.assertFalse(self.coordinator.callback(incident_id,reply)['duplicate'])


class DocumentationBoundary(unittest.TestCase):
    def test_document_is_only_in_gateway_scannable_content_channel(self):
        from repair_lab.agent import documentation_result
        from repair_lab.carriers import doc_record
        document=doc_record('copper',True)
        result=documentation_result(document,'http://127.0.0.1:8785/api-doc')
        self.assertNotIn(CANARY,json.dumps(result.return_value))
        self.assertNotIn('CARRIER-RUNTIME-DIRECTIVE',json.dumps(result.return_value))
        self.assertIn(CANARY,result.content)
        self.assertIn('offer.total_gbp',result.content)
        self.assertEqual(json.loads(result.content.split('\n',1)[1]),document)

if __name__=='__main__': unittest.main()
