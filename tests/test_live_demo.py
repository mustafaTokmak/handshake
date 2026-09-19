import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from repair_lab.carriers import LEGACY_SOURCE
from repair_lab.models import StartRequest
from repair_lab.server import create_server
from repair_lab.store import ModalStore


class SharedDemo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(0, Path(self.tmp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.launch = patch.object(self.server.coordinator, '_launch', side_effect=lambda rid, key, coro: coro.close())
        self.launch.start()

    def tearDown(self):
        self.launch.stop(); self.server.shutdown(); self.server.server_close()
        self.server.coordinator.store.db.close(); self.tmp.cleanup()

    def request(self, method, path, data=None, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type': 'application/json'}
        if origin: headers['Origin'] = origin
        connection.request(method, path, json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse(); body = response.read(); status = response.status
        result = json.loads(body) if response.headers['Content-Type'] == 'application/json' else body.decode()
        connection.close()
        return status, result

    def test_new_session_resets_state_and_is_shared_across_clients(self):
        status, first = self.request('POST', '/api/sessions', {})
        self.assertEqual(status, 201)
        self.server.coordinator.store.update_carrier(first['id'], 'cedar', status='restored', source='old patch', quote={'amount_minor': 1})
        status, fresh = self.request('POST', '/api/sessions', {})
        self.assertEqual(status, 201); self.assertNotEqual(first['id'], fresh['id'])
        self.assertEqual(self.request('GET', '/api/latest')[1]['id'], fresh['id'])
        self.assertEqual(fresh['order']['weight_kg'], 2.4)
        self.assertEqual(fresh['events'], [])
        for carrier in fresh['carriers'].values():
            self.assertEqual(carrier['status'], 'ready'); self.assertEqual(carrier['source'], LEGACY_SOURCE)
            self.assertEqual(carrier['attempts'], []); self.assertIsNone(carrier['incident_id']); self.assertIsNone(carrier['quote'])
        self.assertEqual(len(self.request('GET', '/api/runs')[1]), 2)
        self.assertEqual(self.request('GET', '/api/runs/'+first['id'])[1]['carriers']['cedar']['source'], 'old patch')

    def test_session_starts_once_and_reset_cannot_interrupt_active_work(self):
        _, session = self.request('POST', '/api/sessions', {})
        path = '/api/sessions/'+session['id']+'/start'
        self.assertEqual(self.request('POST', path, StartRequest().model_dump())[0], 202)
        self.assertEqual(self.request('POST', path, {})[0], 400)
        self.server.coordinator.active.add((session['id'], 'all'))
        self.assertEqual(self.request('POST', '/api/sessions', {})[0], 400)
        self.assertEqual(self.request('GET', '/api/latest')[1]['id'], session['id'])

    def test_old_ready_session_cannot_replace_new_shared_session(self):
        _, first = self.request('POST', '/api/sessions', {})
        self.request('POST', '/api/sessions', {})
        self.assertEqual(self.request('POST', '/api/sessions/'+first['id']+'/start', {})[0], 400)

    def test_public_docs_and_origin_boundary(self):
        config = self.request('GET', '/api/config')[1]
        for carrier in config['carriers']:
            self.assertTrue(carrier['documentation_url'].startswith('/carriers/'))
            status, html = self.request('GET', carrier['documentation_url'])
            self.assertEqual(status, 200); self.assertIn(carrier['contact']['email'], html)
            self.assertIn('/carriers/'+carrier['id']+'/api-doc?', html)
        self.assertEqual(self.request('POST', '/api/sessions', {}, 'https://untrusted.example')[0], 403)


class RemotePersistence(unittest.TestCase):
    def test_shared_records_survive_store_recreation(self):
        class Records(dict):
            def put(self, key, value): self[key] = value
            def items(self): raise AssertionError('Live polling must not scan history')
        records = Records(); store = ModalStore('unused', records)
        store.save_run({'id':'one','created_at':'2026-09-19','events':[], 'carriers':{'cedar':{'status':'ready'}}})
        store.update_carrier('one','cedar',status='restored')
        store.event('one','cedar','quote_restored',{'amount_minor':400})
        store.save_incident({'id':'INC-one','status':'waiting'})
        restarted = ModalStore('unused', records)
        self.assertEqual(restarted.latest()['carriers']['cedar']['status'], 'restored')
        self.assertEqual(len(restarted.get_run('one')['events']), 1)
        self.assertEqual(restarted.incident('INC-one')['status'], 'waiting')


class InterruptSession(unittest.TestCase):
    def test_reset_waits_for_async_cleanup_and_preserves_old_session(self):
        import asyncio
        from repair_lab.coordinator import Coordinator
        from repair_lab.store import Store
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory)/'repair.sqlite')
            try:
                coordinator = Coordinator(store)
                old = coordinator.new_session()
                store.update_carrier(old['id'], 'cedar', status='repairing', attempts=[{'status':'sandbox_running'}])
                started = threading.Event(); closed = threading.Event()
                async def work():
                    try:
                        started.set()
                        await asyncio.Event().wait()
                    finally:
                        await asyncio.sleep(.02)
                        closed.set()
                coordinator._launch(old['id'], 'cedar', work())
                self.assertTrue(started.wait(3))
                fresh = coordinator.interrupt_and_new_session()
                self.assertTrue(closed.is_set())
                self.assertFalse(coordinator.active)
                self.assertNotEqual(fresh['id'], old['id'])
                self.assertTrue(all(c['status']=='ready' for c in fresh['carriers'].values()))
                saved = store.get_run(old['id'])
                self.assertEqual(saved['carriers']['cedar']['status'], 'interrupted')
                self.assertEqual(saved['carriers']['cedar']['attempts'][0]['status'], 'interrupted')
                self.assertEqual(saved['events'][-1]['kind'], 'repair_interrupted')
            finally: store.db.close()
