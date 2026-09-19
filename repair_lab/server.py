import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from .carriers import CARRIERS, BY_ID, public_company, contact_context, start_carriers, doc_html, doc_record
from .coordinator import Coordinator
from .models import StartRequest, ContactReply
from .store import Store, ModalStore


def create_server(port=8780, state_dir=Path('state'), host='127.0.0.1', store=None):
    static = Path(__file__).parent/'static'
    store = store or (ModalStore(os.environ['REPAIR_STATE_DICT']) if os.getenv('REPAIR_STATE_DICT') else Store(state_dir/'repair.sqlite'))
    coordinator = Coordinator(store)
    public_url = os.getenv('REPAIR_PUBLIC_URL', '').rstrip('/')
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, mime='application/json'):
            body = json.dumps(data).encode() if mime == 'application/json' else data
            self.send_response(status); self.send_header('Content-Type', mime); self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff'); self.end_headers(); self.wfile.write(body)
        def allowed(self):
            actual_port = self.server.server_port
            hosts = {f'localhost:{actual_port}', f'127.0.0.1:{actual_port}'}
            origins = {'http://'+s for s in hosts}
            if public_url: hosts.add(urlsplit(public_url).netloc); origins.add(public_url)
            return self.headers.get('Host') in hosts and self.headers.get('Origin') in (None, *origins)
        def do_GET(self):
            if not self.allowed(): return self.send(403, {'error': 'Origin not allowed'})
            parsed = urlsplit(self.path); path = parsed.path
            if path in ('/', '/app.js', '/flow.js', '/flow.svg', '/archify.css', '/style.css'):
                name, mime = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript'), '/flow.js': ('flow.js', 'text/javascript'), '/flow.svg': ('flow.svg', 'image/svg+xml'), '/archify.css': ('archify.css', 'text/css'), '/style.css': ('style.css', 'text/css')}[path]
                return self.send(200, (static/name).read_bytes(), mime)
            if path == '/api/config': return self.send(200, {'carriers': [public_company(c) | {'documentation_url': f'/carriers/{c["id"]}/docs'} for c in CARRIERS], 'gateway_configured': bool(os.getenv('PYDANTIC_AI_GATEWAY_API_KEY')), 'route': os.getenv('REPAIR_GATEWAY_ROUTE', 'repair-lab'), 'model': os.getenv('HANDSHAKE_MODEL'), 'contact_mode': 'stub_no_call_placed', 'session_mode': 'shared'})
            parts = path.strip('/').split('/')
            if len(parts) == 3 and parts[0] == 'carriers' and parts[1] in BY_ID and parts[2] in ('docs', 'api-doc'):
                attack = parse_qs(parsed.query).get('attack', ['1'])[0] == '1'
                if parts[2] == 'api-doc': return self.send(200, doc_record(parts[1], attack))
                html = doc_html(parts[1], attack).replace('href="/api-doc?', f'href="/carriers/{parts[1]}/api-doc?')
                return self.send(200, html.encode(), 'text/html; charset=utf-8')
            if path == '/api/runs': return self.send(200, [{k:r[k] for k in ('id', 'created_at', 'condition', 'order', 'carriers')} for r in store.runs()])
            if path == '/api/latest': return self.send(200, store.latest())
            if path.startswith('/api/runs/'):
                r = store.get_run(path.rsplit('/', 1)[-1]); return self.send(200 if r else 404, r or {'error': 'Run not found'})
            if path.startswith('/api/incidents/'):
                r = store.incident(path.rsplit('/', 1)[-1]); return self.send(200 if r else 404, r or {'error': 'Incident not found'})
            return self.send(404, {'error': 'Not found'})
        def do_POST(self):
            if not self.allowed() or self.headers.get('Content-Type') != 'application/json': return self.send(403, {'error': 'Same-origin JSON requests only'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 20000: raise ValueError('Invalid payload size')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict): raise ValueError('Expected a JSON object')
                path = urlsplit(self.path).path
                parts = path.strip('/').split('/')
                if path == '/api/sessions/interrupt':
                    if data: raise ValueError('Interruption uses the default starting state')
                    return self.send(201, coordinator.interrupt_and_new_session())
                if path == '/api/sessions':
                    if data: raise ValueError('New sessions use the default starting state')
                    return self.send(201, coordinator.new_session())
                if path == '/api/runs' or (len(parts) == 4 and parts[:2] == ['api', 'sessions'] and parts[3] == 'start'):
                    return self.send(202, coordinator.start(StartRequest.model_validate(data), parts[2] if path != '/api/runs' else None))
                if len(parts) == 4 and parts[:2] == ['api', 'incidents'] and parts[3] in ('context', 'simulate-reply'):
                    incident_id = parts[2]
                    if parts[3] == 'simulate-reply':
                        incident = store.incident(incident_id)
                        if not incident or incident['carrier_id'] != 'harbor': raise ValueError('Only Harbor has a simulated contact reply')
                        reply = ContactReply(message_id=f"simulated-harbor-reply-{len(incident['messages'])+1}", source='simulated-carrier-representative', context=contact_context())
                    else:
                        token = os.getenv('CONTACT_CALLBACK_TOKEN')
                        if token and not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer '+token): return self.send(401, {'error': 'Callback authentication required'})
                        reply = ContactReply.model_validate(data)
                    return self.send(202, coordinator.callback(incident_id, reply))
                return self.send(404, {'error': 'Not found'})
            except (ValueError, TypeError) as exc: return self.send(400, {'error': str(exc)[:1200]})
        def log_message(self, *_): pass
    server = ThreadingHTTPServer((host, port), Handler)
    server.coordinator = coordinator
    return server


def serve(port=8780, state_dir=Path('state'), host='127.0.0.1'):
    server = create_server(port, state_dir, host)
    carriers = start_carriers()
    print(f'Handshake: http://{host}:{port}', flush=True)
    try: server.serve_forever()
    finally:
        server.server_close()
        for carrier in carriers: carrier.shutdown(); carrier.server_close()
