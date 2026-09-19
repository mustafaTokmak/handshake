// Headless check: can this key reach a Live model, and does our exact setup
// message get accepted? Run: node smoke.mjs [model]
import { readFileSync } from 'node:fs';

const NAMES = ['GOOGLE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_GENAI_API_KEY', 'GOOGLE_API'];
function key() {
  for (const n of NAMES) if (process.env[n]) return process.env[n].trim();
  for (const p of ['.env', '../.env']) {
    try {
      const t = readFileSync(p, 'utf8');
      for (const n of NAMES) {
        const m = t.match(new RegExp('^' + n + "\\s*=\\s*['\"]?([^'\"\\s]+)", 'm'));
        if (m) return m[1];
      }
    } catch {}
  }
  return '';
}

const API = key();
if (!API) { console.error('No API key found (env or caller/.env)'); process.exit(1); }

const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${API}&pageSize=200`);
if (!res.ok) { console.error('ListModels failed:', res.status, (await res.text()).slice(0, 300)); process.exit(1); }
const { models = [] } = await res.json();
const live = models
  .filter(m => (m.supportedGenerationMethods || m.supportedActions || []).some(a => /bidi/i.test(a)))
  .map(m => m.name.replace('models/', ''));
console.log('Live-capable models for this key:');
live.forEach(m => console.log('  -', m));
if (!live.length) { console.error('\nNo bidi-capable models. This key cannot use Live.'); process.exit(1); }

const want = process.argv[2] || (live.find(m => /3\.8-live/.test(m)) || live.find(m => /native-audio/.test(m)) || live[0]);
console.log('\nTesting setup handshake with:', want);

const session = await fetch('http://127.0.0.1:8770/api/session').then(r => r.json()).catch(() => null);

const ws = new WebSocket(`wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${API}`);
const done = setTimeout(() => { console.error('TIMEOUT: no setupComplete in 20s'); process.exit(1); }, 20000);

ws.onopen = () => {
  const setup = session ? { ...session.liveSetup, model: 'models/' + want }
                        : { model: 'models/' + want, generationConfig: { responseModalities: ['AUDIO'] } };
  console.log('manual activity detection:',
    setup.realtimeInputConfig?.automaticActivityDetection?.disabled === true ? 'ON (push-to-talk)' : 'off');
  ws.send(JSON.stringify({ setup }));
};
ws.onmessage = async e => {
  const raw = e.data instanceof Blob ? await e.data.text() : e.data;
  let m; try { m = JSON.parse(raw); } catch { return; }
  if (m.setupComplete) {
    clearTimeout(done);
    console.log('\nSETUP ACCEPTED — the socket, model, tools and transcription config all work.');
    console.log('Put this in caller/server.py DEFAULT_MODEL if it differs:', want);
    ws.close(); process.exit(0);
  }
  if (m.error || m.goAway) { clearTimeout(done); console.error('Server said:', JSON.stringify(m).slice(0, 400)); process.exit(1); }
};
ws.onerror = () => {};
ws.onclose = e => { clearTimeout(done); if (e.code !== 1000) { console.error(`Closed ${e.code}: ${e.reason || '(no reason)'}`); process.exit(1); } };
