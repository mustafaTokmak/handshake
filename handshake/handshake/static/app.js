const $ = id => document.getElementById(id);
const names = {accepted: 'Accepted · response lost', not_accepted: 'Not accepted · response lost', pending: 'Still pending', unavailable: 'Status unavailable'};
let runs = [];
const make = (tag, text, className) => {const el = document.createElement(tag); el.textContent = text; if (className) el.className = className; return el;};
async function api(path, options) {const response = await fetch(path, options); const body = await response.json(); if (!response.ok) throw new Error(body.error || 'Request failed'); return body;}
function show(run) {
  const e = run.evaluation || {};
  $('count').textContent = e.shipment_count ?? '—'; $('duplicates').textContent = e.duplicate_count ?? '—'; $('calls').textContent = e.recovery_tool_calls ?? '—';
  $('duration').textContent = run.scenario_ms == null ? '—' : (run.scenario_ms / 1000).toFixed(2) + 's';
  $('startup').textContent = run.startup_ms == null ? 'Startup unavailable' : 'Startup ' + (run.startup_ms / 1000).toFixed(2) + 's';
  $('run-badge').textContent = (run.mode === 'rehearsal' ? 'Rehearsal' : 'Live · rule ' + run.condition) + ' · ' + names[run.scenario];
  $('timeline').replaceChildren();
  for (const event of run.events || []) {
    const li = make('li', '', event.result.status); const heading = make('div', '', 'event-head');
    heading.append(make('code', event.tool), make('span', event.result.status.replaceAll('_', ' '), 'event-state'), make('time', '+' + (event.elapsed_ms / 1000).toFixed(2) + 's'));
    li.append(heading, make('p', Object.entries(event.arguments).map(([k,v]) => `${k}: ${v}`).join(' · '), 'event-args'), make('p', event.result.detail, 'event-detail'));
    $('timeline').append(li);
  }
  $('verdict').textContent = run.status === 'error' ? 'Run failed' : e.passed ? (run.status === 'unresolved' ? 'Paused correctly' : 'One shipment. Verified.') : 'Evaluation failed';
  $('verdict').className = e.passed ? 'pass' : 'fail';
  $('explanation').textContent = run.outcome?.explanation || 'Execution failed: ' + (run.error || run.evaluation_error || 'No complete evidence.');
  $('shipment').replaceChildren();
  for (const [label, value] of [['Shipment',run.outcome?.shipment_id],['Tracking',run.outcome?.tracking_number],['Original request key',run.request_key],['Model tokens',run.usage ? `${run.usage.input_tokens} in / ${run.usage.output_tokens} out` : null]]) {
    if (value) $('shipment').append(make('dt',label),make('dd',value));
  }
  $('trace').hidden = true;
  if (run.trace_url) {const url = new URL(run.trace_url); if (url.protocol === 'https:') {$('trace').href = url.href; $('trace').hidden = false;}}
  $('trace-note').textContent = run.mode === 'rehearsal' ? 'Reference execution only. No model or Gateway rule was used.' : (run.trace_id ? 'Trace captured. Verify remote rule application in the Gateway Usage chart.' : 'Logfire trace unavailable. This run is not submission-ready.');
}
async function refresh() {
  runs = await api('/api/runs'); $('history').replaceChildren();
  for (const run of runs) {
    const tr = document.createElement('tr');
    for (const text of [names[run.scenario], run.mode === 'rehearsal' ? 'Rehearsal' : `Live · rule ${run.condition}`,run.status, run.evaluation?.shipment_count ?? '—', run.evaluation ? (run.evaluation.passed ? 'Pass' : 'Fail') : 'Unavailable']) tr.append(make('td',text));
    const td = make('td',''); const button = make('button','Inspect'); button.onclick = () => show(run); td.append(button); tr.append(td); $('history').append(tr);
  }
}
$('mode').onchange = () => {const live = $('mode').value === 'live'; $('condition').disabled = !live; if (!live) $('condition').value = 'off'; $('mode-note').textContent = live ? 'Uses the Modal model through Pydantic Gateway. Set the actual rule state in Logfire first. This selector records that state; it does not toggle it.' : 'Rehearsal exercises the provider and evaluator with a deterministic reference. It is not an AI or Gateway comparison.';};
$('run').onclick = async () => {
  $('run').disabled = true; $('run').textContent = 'Running…'; $('error').hidden = true; $('run-badge').textContent = 'Execution in progress';
  try {const run = await api('/api/run', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(['scenario','mode','condition','backend'].map(k => [k,$(k).value])))}); show(run); await refresh();}
  catch (error) {$('error').textContent = error.message; $('error').hidden = false; $('run-badge').textContent = 'Setup needed';}
  finally {$('run').disabled = false; $('run').textContent = 'Run scenario ↗';}
};
async function init() {try {const config = await api('/api/config'); $('connection').textContent = config.gateway_key && config.model ? 'Gateway configured' : 'Local rehearsal ready'; const policy = await api('/api/policy'); $('policy-text').textContent = policy.instruction; await refresh(); if (runs.length) show(runs[0]);} catch (error) {$('error').textContent = error.message; $('error').hidden = false;}}
init();
