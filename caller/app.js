'use strict';
// Browser holds the Gemini Live socket directly. Mic is captured at 16 kHz but
// only transmitted while the talk key is held; turn boundaries are signalled
// explicitly with activityStart/activityEnd, so the model never guesses from
// silence and can never hear itself.
const WS_BASE = 'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent';
const MIC_RATE = 16000, OUT_RATE = 24000, CHUNK = 2048;

const $ = id => document.getElementById(id);
let session = null, socket = null, micCtx = null, micStream = null, worklet = null;
let outCtx = null, playHead = 0, sources = [], live = false, talking = false, finding = null;
let selected = '';   // incident the operator chose from the queue
const transcript = [];

const setStatus = (text, cls) => { $('status').textContent = text; $('status').className = 'badge ' + (cls || ''); };

function log(role, text, partial) {
  if (!text) return;
  const last = transcript[transcript.length - 1];
  if (partial && last && last.role === role && last.partial) last.text += text;
  else transcript.push({ role, text, partial: !!partial });
  render();
}

function render() {
  const box = $('transcript');
  box.replaceChildren(...transcript.map(e => {
    const li = document.createElement('li');
    li.className = 'turn ' + e.role;
    const who = document.createElement('span');
    who.className = 'who';
    who.textContent = e.role === 'agent' ? 'Agent' : e.role === 'rep' ? 'You' : '';
    const p = document.createElement('p');
    p.textContent = e.text;
    li.append(who, p);
    return li;
  }));
  box.scrollTop = box.scrollHeight;
}

const b64encode = bytes => {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
};
const b64decode = text => {
  const bin = atob(text), out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
};

const WORKLET_SRC = `
class Capture extends AudioWorkletProcessor {
  constructor(){super();this.buf=[];this.n=0;}
  process(inputs){
    const ch=inputs[0]&&inputs[0][0];
    if(!ch)return true;
    this.buf.push(new Float32Array(ch));this.n+=ch.length;
    if(this.n>=${CHUNK}){
      const m=new Float32Array(this.n);let o=0;
      for(const b of this.buf){m.set(b,o);o+=b.length;}
      const pcm=new Int16Array(m.length);
      for(let i=0;i<m.length;i++){const s=Math.max(-1,Math.min(1,m[i]));pcm[i]=s<0?s*0x8000:s*0x7fff;}
      this.port.postMessage(pcm,[pcm.buffer]);
      this.buf=[];this.n=0;
    }
    return true;
  }
}
registerProcessor('capture',Capture);`;

function stopPlayback() {
  for (const s of sources) { try { s.stop(); } catch (_e) {} }
  sources = []; playHead = 0;
}

function play(bytes) {
  if (!outCtx) return;
  const pcm = new Int16Array(bytes.buffer, bytes.byteOffset, Math.floor(bytes.byteLength / 2));
  const buf = outCtx.createBuffer(1, pcm.length, OUT_RATE);
  const ch = buf.getChannelData(0);
  for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;
  const src = outCtx.createBufferSource();
  src.buffer = buf; src.connect(outCtx.destination);
  const now = outCtx.currentTime;
  if (playHead < now) playHead = now + 0.03;
  src.start(playHead); playHead += buf.duration;
  sources.push(src);
  src.onended = () => { sources = sources.filter(s => s !== src); };
}

const send = obj => { if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(obj)); };

function startTalking() {
  if (!live || talking) return;
  talking = true;
  send({ realtimeInput: { activityStart: {} } });
  $('talk').classList.add('hot');
  $('talk').textContent = 'Listening — release when done';
  setStatus('Listening to you', 'live');
}

function stopTalking() {
  if (!talking) return;
  talking = false;
  send({ realtimeInput: { activityEnd: {} } });
  $('talk').classList.remove('hot');
  $('talk').textContent = 'Hold to talk  (or hold Space)';
  setStatus('Agent is replying', 'live');
}

async function startMic() {
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
  micCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: MIC_RATE });
  await micCtx.audioWorklet.addModule(URL.createObjectURL(new Blob([WORKLET_SRC], { type: 'text/javascript' })));
  worklet = new AudioWorkletNode(micCtx, 'capture');
  worklet.port.onmessage = ev => {
    if (!live || !talking) return;   // push-to-talk: silence unless held
    send({ realtimeInput: { audio: { mimeType: 'audio/pcm;rate=' + MIC_RATE, data: b64encode(new Uint8Array(ev.data.buffer)) } } });
  };
  micCtx.createMediaStreamSource(micStream).connect(worklet);
}

function teardown() {
  live = false; talking = false;
  stopPlayback();
  if (worklet) { try { worklet.port.onmessage = null; worklet.disconnect(); } catch (_e) {} worklet = null; }
  if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  if (micCtx) { micCtx.close().catch(() => {}); micCtx = null; }
  if (outCtx) { outCtx.close().catch(() => {}); outCtx = null; }
  if (socket && socket.readyState <= WebSocket.OPEN) { try { socket.close(); } catch (_e) {} }
  socket = null;
  $('call').textContent = 'Start call';
  $('call').disabled = false;
  $('talk').hidden = true;
  $('talk').classList.remove('hot');
}

async function submitFinding(args) {
  finding = args;
  const dl = $('finding');
  dl.replaceChildren();
  const add = (label, value) => {
    if (!value || (Array.isArray(value) && !value.length)) return;
    const dt = document.createElement('dt'); dt.textContent = label;
    const dd = document.createElement('dd'); dd.textContent = Array.isArray(value) ? value.join(', ') : value;
    dl.append(dt, dd);
  };
  const c = args.change || {};
  add('Status', args.status);
  add('Summary', args.summary);
  add('Changed fields', c.changed_fields);
  add('Parameters', c.affected_parameters);
  add('New behaviour', c.described_behaviour);
  add('Do instead', c.suggested_action);
  add('Effective', c.effective_date);
  add('Quote', c.verbatim_quote);
  $('finding-panel').hidden = false;
  try {
    const r = await fetch('/api/finding', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ finding: args, transcript,
        incidentId: (session && session.incidentId) || '',
        carrier: (session && session.brief && session.brief.provider) || '' }) });
    const b = await r.json();
    if (!r.ok) {
      $('saved').textContent = 'Schema REJECTED this finding: ' + (b.detail || b.error);
      $('saved').className = 'note bad';
      return;
    }
    const relay = b.relay || {};
    let msg = 'Schema validated · saved to calls/' + b.saved;
    if (relay.attempted && relay.ok) msg += ' · relayed to repair lab (' + relay.context_chars + ' chars, HTTP ' + relay.status + ') — repair resuming';
    else if (relay.attempted) msg += ' · relay FAILED: ' + (relay.error || 'HTTP ' + relay.status);
    else msg += ' · no live incident, nothing relayed';
    $('saved').textContent = msg;
    $('saved').className = 'note ' + (relay.attempted && !relay.ok ? 'bad' : 'ok');
  } catch (err) {
    $('saved').textContent = 'Could not save: ' + err.message;
    $('saved').className = 'note bad';
  }
}

function handle(m) {
  if (m.setupComplete) {
    live = true;
    $('talk').hidden = false;
    setStatus('Connected', 'live');
    send({ clientContent: { turns: [{ role: 'user', parts: [{ text: '[The support line has just connected. Introduce yourself and begin.]' }] }], turnComplete: true } });
    return;
  }
  const c = m.serverContent;
  if (c) {
    if (c.interrupted) stopPlayback();
    if (c.outputTranscription && c.outputTranscription.text) log('agent', c.outputTranscription.text, true);
    if (c.inputTranscription && c.inputTranscription.text) log('rep', c.inputTranscription.text, true);
    for (const p of (c.modelTurn && c.modelTurn.parts) || []) {
      if (p.inlineData && p.inlineData.data) play(b64decode(p.inlineData.data));
      if (p.text) log('agent', p.text, true);
    }
    if (c.turnComplete) { transcript.forEach(e => { e.partial = false; }); if (live && !talking) setStatus('Your turn — hold to talk', 'live'); }
  }
  if (m.toolCall) {
    for (const fc of m.toolCall.functionCalls || []) {
      if (fc.name === 'report_finding') { submitFinding(fc.args || {}); setStatus('Finding recorded', 'done'); }
    }
    send({ toolResponse: { functionResponses: (m.toolCall.functionCalls || []).map(f => ({ id: f.id, name: f.name, response: { result: 'recorded' } })) } });
  }
}

async function call() {
  if (live) { teardown(); setStatus('Call ended', ''); return; }
  $('call').disabled = true;
  setStatus('Connecting…', '');
  transcript.length = 0; finding = null;
  $('finding-panel').hidden = true;
  render();
  try {
    // Re-read the session as the call starts: the incident may have been
    // picked up or resolved while this page sat open.
    session = await loadSession(selected);
    if (!session.hasKey) throw new Error('No Google API key configured');
    outCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: OUT_RATE });
    await outCtx.resume();
    await startMic();
  } catch (err) {
    setStatus('Mic or config failed', 'bad'); log('system', err.message); teardown(); return;
  }
  socket = new WebSocket(WS_BASE + '?key=' + encodeURIComponent(session.apiKey));
  socket.onopen = () => {
    send({ setup: session.liveSetup });
    $('call').textContent = 'End call';
    $('call').disabled = false;
  };
  socket.onmessage = async ev => {
    const raw = ev.data instanceof Blob ? await ev.data.text() : ev.data;
    let m; try { m = JSON.parse(raw); } catch (_e) { return; }
    handle(m);
  };
  socket.onerror = () => setStatus('Socket error', 'bad');
  socket.onclose = ev => {
    if (!live && !finding) setStatus('Closed: ' + (ev.reason || 'code ' + ev.code), 'bad');
    teardown();
  };
}

$('call').onclick = call;
const talk = $('talk');
talk.addEventListener('pointerdown', e => { e.preventDefault(); startTalking(); });
['pointerup', 'pointerleave', 'pointercancel'].forEach(t => talk.addEventListener(t, stopTalking));
addEventListener('keydown', e => { if (e.code === 'Space' && !e.repeat && live) { e.preventDefault(); startTalking(); } });
addEventListener('keyup', e => { if (e.code === 'Space' && live) { e.preventDefault(); stopTalking(); } });

// The lab does not notify us; the queue is read when the operator asks for it.
// Selecting a row only changes which brief the next call uses.
function renderQueue(queue, current) {
  const list = $('queue');
  const rows = queue || [];
  // Always shown: with nothing waiting, Refresh is how an operator picks up an
  // incident the lab raised after this page was opened.
  $('queue-panel').hidden = false;
  if (!rows.length) {
    const empty = document.createElement('li');
    empty.className = 'queue-why';
    empty.textContent = 'Nothing waiting. Refresh after the repair lab escalates; the rehearsal brief is loaded meanwhile.';
    list.replaceChildren(empty);
    return;
  }
  list.replaceChildren(...rows.map(item => {
    const li = document.createElement('li');
    li.className = 'queue-row' + (item.incident_id === current ? ' current' : '');
    const btn = document.createElement('button');
    btn.className = 'link';
    btn.textContent = item.provider + ' · ' + item.incident_id;
    btn.disabled = live;
    btn.onclick = () => { selected = item.incident_id; loadSession(selected).catch(() => {}); };
    const why = document.createElement('span');
    why.className = 'queue-why';
    why.textContent = [item.phone, item.reason].filter(Boolean).join(' · ');
    li.append(btn, why);
    return li;
  }));
}

function applySession(s) {
  session = s;
  const linked = s.source === 'repair-lab';
  selected = s.incidentId || '';
  $('context').textContent = s.brief.provider + ' · ' + s.brief.support_line + ' · '
    + (linked ? 'incident ' + s.incidentId : s.brief.order_id) + ' · ' + s.model;
  $('context').classList.toggle('linked', linked);
  document.title = (linked ? 'Escalation — ' + s.brief.provider : 'Escalation — call the provider');
  renderQueue(s.queue, s.incidentId);
  if (!live) {
    setStatus(s.hasKey ? (linked ? 'Ready · live incident' : 'Ready') : 'No API key', s.hasKey ? '' : 'bad');
    $('call').disabled = !s.hasKey;
  }
  return s;
}

async function loadSession(incidentId) {
  const query = incidentId ? '?incident=' + encodeURIComponent(incidentId) : '';
  const response = await fetch('/api/session' + query);
  if (!response.ok) throw new Error('Session unavailable (HTTP ' + response.status + ')');
  return applySession(await response.json());
}

$('refresh').onclick = () => loadSession(selected).catch(err => setStatus(err.message, 'bad'));
loadSession('').catch(() => setStatus('Server unreachable', 'bad'));
