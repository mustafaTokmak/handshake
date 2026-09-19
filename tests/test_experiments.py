import asyncio
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from repair_lab.coordinator import Coordinator
from repair_lab.experiments import display_run, routes
from repair_lab.models import StartRequest
from repair_lab.carriers import LEGACY_SOURCE
from repair_lab.store import Store, ModalStore


class SixExperiments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name)/'test.sqlite')
        self.coordinator = Coordinator(self.store)

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def prepare(self):
        parent = self.coordinator.new_session()
        with patch.object(self.coordinator, '_launch', side_effect=lambda rid, key, coro: coro.close()):
            self.coordinator.start_suite(StartRequest(order={'weight_kg':3.7,'distance_km':480}), parent['id'])
        return parent['id']

    def test_six_fresh_runs_use_real_routes_and_share_only_the_order(self):
        parent_id = self.prepare(); seen = []
        async def initial(rid):
            run = self.store.get_run(rid); seen.append(run)
            self.assertEqual(run['order']['weight_kg'],3.7)
            self.assertTrue(all(c['source']==LEGACY_SOURCE and not c['attempts'] for c in run['carriers'].values()))
            self.assertEqual(self.store.latest()['id'],parent_id)
            self.assertEqual(display_run(self.store,self.store.latest())['id'],rid)
            for cid in run['carriers']:
                self.store.update_carrier(rid,cid,status='restored',source='a patch')
        with patch.object(self.coordinator,'_initial',initial):
            asyncio.run(self.coordinator._run_suite(parent_id))
        self.assertEqual([(r['condition'],r['attack'],r['route']) for r in seen],[(c,a,route) for a in (False,True) for c,route in routes().items()])
        self.assertEqual(len({r['id'] for r in seen}),6)
        self.assertEqual(len(self.store.runs()),1)
        self.assertEqual(len(self.store.runs(include_children=True)),7)
        parent=self.store.latest(); self.assertEqual(parent['suite']['status'],'complete')
        self.assertTrue(all(c['summary']['quotes']==5 for c in parent['suite']['cases']))
        self.assertEqual(display_run(self.store,seen[0])['session_id'],parent_id)

    def test_interrupt_stops_the_sequence_and_cleans_the_current_child(self):
        parent_id=self.prepare(); entered=threading.Event(); cleaned=threading.Event()
        async def initial(rid):
            entered.set()
            try: await asyncio.sleep(60)
            finally:
                await asyncio.sleep(.01); cleaned.set()
        with patch.object(self.coordinator,'_initial',initial):
            self.coordinator._launch(parent_id,'all',self.coordinator._run_suite(parent_id))
            self.assertTrue(entered.wait(2))
            fresh=self.coordinator.interrupt_and_new_session()
        self.assertTrue(cleaned.is_set())
        parent=self.store.get_run(parent_id)
        self.assertEqual(parent['suite']['status'],'interrupted')
        self.assertEqual([c['status'] for c in parent['suite']['cases']],['interrupted']+['skipped']*5)
        child=self.store.get_run(parent['suite']['current_run_id'])
        self.assertTrue(all(c['status']=='interrupted' for c in child['carriers'].values()))
        self.assertEqual(self.store.latest()['id'],fresh['id'])

    def test_restart_recovers_parent_and_child(self):
        parent_id=self.prepare()
        child=self.coordinator._start(StartRequest(),ready=True,parent_id=parent_id)
        self.store.update_carrier(child['id'],'cedar',status='repairing')
        parent=self.store.get_run(parent_id);parent['suite']['cases'][0].update(status='running',run_id=child['id']);self.store.save_run(parent)
        Coordinator(self.store)
        self.assertEqual(self.store.get_run(parent_id)['suite']['status'],'interrupted')
        self.assertEqual(self.store.get_run(child['id'])['carriers']['cedar']['status'],'interrupted')

    def test_remote_latest_stays_on_parent_when_children_change(self):
        class Records(dict):
            def put(self,key,value): self[key]=value
        store=ModalStore('unused',Records())
        store.save_run({'id':'parent','created_at':'1'})
        store.save_run({'id':'child','created_at':'2','parent_id':'parent'})
        self.assertEqual(store.latest()['id'],'parent')
        self.assertEqual([r['id'] for r in store.runs()],['parent'])

    def test_contact_completion_refreshes_parent_and_restart_does_not_reopen_incident(self):
        parent_id=self.prepare()
        child=self.coordinator._start(StartRequest(),ready=True,parent_id=parent_id)
        parent=self.store.get_run(parent_id)
        parent['suite']['status']='complete'
        parent['suite']['current_run_id']=child['id']
        parent['suite']['cases'][0].update(run_id=child['id'],status='complete')
        parent['carriers']['harbor'].update(status='resuming',incident_id='INC-resolved')
        self.store.save_run(parent)
        self.store.save_incident({'id':'INC-resolved','status':'resolved'})
        self.store.update_carrier(child['id'],'harbor',status='restored',incident_id='INC-resolved')
        Coordinator(self.store)
        self.assertEqual(self.store.incident('INC-resolved')['status'],'resolved')
        self.coordinator._update_suite_case(child['id'])
        parent=self.store.get_run(parent_id)
        self.assertEqual(parent['suite']['cases'][0]['summary']['quotes'],1)
        self.assertEqual(parent['carriers']['harbor']['status'],'restored')
        self.store.update_carrier(child['id'],'harbor',status='resuming')
        self.coordinator._update_suite_case(child['id'])
        self.assertTrue(self.store.get_run(parent_id)['suite']['cases'][0]['resuming'])
        self.store.update_carrier(child['id'],'harbor',status='restored')
        self.coordinator._update_suite_case(child['id'])
        self.assertFalse(self.store.get_run(parent_id)['suite']['cases'][0]['resuming'])
