/* The diagram derives its state from recorded events; animation never fabricates progress. */
const RepairFlow=(()=>{
 const ns='http://www.w3.org/2000/svg';let selectedNode='sandbox',lastCarrier=null;
 const specs=[
  ['response','Carrier response',30,60,190,90],['validation','Pydantic validation',270,60,190,90],['docs','Read API docs',510,60,190,90],
  ['gateway','Gateway boundary',510,174,190,50],['model','Gemma repair',510,250,190,90],['sandbox','Modal sandbox',270,250,190,90],['quote','Verified quote',30,250,190,90],
  ['contact','Contact carrier',270,450,190,90],['context','New incident context',510,450,190,90]
 ];
 const groups={response:['quote_response'],validation:['validation_failed','quote_response'],docs:['documentation_read'],gateway:['gateway_response'],model:['investigating','inference_wait','candidate_proposed','model_exchange','repair_error'],sandbox:['sandbox_started','sandbox_finished'],quote:['quote_restored','quote_response'],contact:['contact_requested','operator_review_required'],context:['contact_context_received']};
 function state(run,carrierId){
  const carrier=run?.carriers[carrierId],events=(run?.events||[]).filter(e=>e.carrier_id===carrierId),has=k=>events.some(e=>e.kind===k),last=k=>events.filter(e=>e.kind===k).at(-1);
  const attempt=carrier?.attempts?.at(-1),busy=['repairing','resuming'].includes(carrier?.status),sandboxRunning=attempt?.status==='sandbox_running';
  const receipts=events.filter(e=>e.kind==='gateway_response'&&e.data.http_status===200),redacted=receipts.some(e=>e.data.guardrails?.includes(';redact')),optimized=receipts.some(e=>e.data.optimizations);
  const nodes=Object.fromEntries(specs.map(([id])=>[id,{status:'pending',detail:'Not reached',events:events.filter(e=>groups[id].includes(e.kind))}]));
  const set=(id,status,detail)=>Object.assign(nodes[id],{status,detail});
  if(carrier?.status==='loading')set('response','active','Requesting quote');
  if(has('quote_response'))set('response','done','HTTP '+last('quote_response').data.http_status);
  if(has('validation_failed'))set('validation','failed','Schema mismatch');
  else if(carrier?.status==='available')set('validation','done','Original schema valid');
  if(has('documentation_read'))set('docs','done',last('documentation_read').data.version+' documentation read');
  if(receipts.length)set('gateway',redacted?'protected':'done',redacted?'Injection redacted':optimized?'Optimization applied':'No redaction reported');
  if(has('candidate_proposed'))set('model','done',`${carrier.attempts.length} patches proposed`);
  if(busy&&!sandboxRunning)set('model','active',has('inference_wait')&&!receipts.length?'Starting on Modal':'Generating next patch');
  if(sandboxRunning)set('sandbox','active',`Testing patch ${attempt.number}`);
  else if(attempt?.validation)set('sandbox',attempt.validation.passed?'done':'failed',`${attempt.validation.checks.filter(c=>c.passed).length}/${attempt.validation.checks.length} checks passed`);
  if(carrier?.quote)set('quote','done',`£${(carrier.quote.amount_minor/100).toFixed(2)} · ${carrier.quote.eta_days} business days`);
  if(has('contact_requested'))set('contact',carrier?.status==='waiting_contact'?'waiting':'done',carrier?.status==='waiting_contact'?'Waiting for a person':'Incident opened');
  if(has('contact_context_received'))set('context','done','Reply received');
  if(['infrastructure_error','error','blocked','needs_review','interrupted'].includes(carrier?.status)){
   const target=sandboxRunning||attempt?.status==='interrupted'?'sandbox':'model';set(target,'failed',carrier.status.replaceAll('_',' '));
  }
  return {nodes,carrier,events,redacted,optimized};
 }
 let template=null,loading=null,lastRender=null;
 function diagram(){
  if(!loading)loading=fetch('/flow.svg').then(r=>{if(!r.ok)throw new Error('Diagram unavailable');return r.text();}).then(text=>{template=new DOMParser().parseFromString(text,'text/html').querySelector('svg');if(lastRender)render(...lastRender);}).catch(()=>{loading=null;});
 }
 function render(root,run,company){
  lastRender=[root,run,company];const data=state(run,company.id);if(lastCarrier!==company.id){selectedNode='sandbox';lastCarrier=company.id;}
  root.replaceChildren();root.className='repair-flow archify-panel';
  const header=document.createElement('div');header.className='archify-header';
  const text=document.createElement('div');const kicker=document.createElement('p');kicker.className='archify-kicker';kicker.textContent='HANDSHAKE / LIVE SYSTEM';const title=document.createElement('h3');title.textContent=company.name;const caption=document.createElement('p');caption.textContent='Every step comes from a recorded event. Select a node to inspect the evidence.';text.append(kicker,title,caption);
  const controls=document.createElement('div');controls.className='archify-controls';const status=document.createElement('span');status.className='archify-status';status.textContent=(data.carrier?.status||'ready').replaceAll('_',' ').toUpperCase();controls.append(status);header.append(text,controls);root.append(header);
  const resources=document.createElement('nav');resources.className='archify-links';resources.setAttribute('aria-label',company.name+' flow resources');
  const addLink=(label,url)=>{const a=document.createElement('a');a.textContent=label+' ↗';a.href=url;a.target='_blank';a.rel='noopener';resources.append(a);};
  addLink('Carrier API docs',company.documentation_url+`?attack=${run?.attack?1:0}`);
  addLink('Gateway rules & guardrails','https://logfire-eu.pydantic.dev/mtokmak06/-/gateway/endpoints');
  addLink('Modal dashboard','https://modal.com/apps/mtokmak06/main/deployed/handshake-live-demo');
  if(data.carrier?.trace_url)addLink('Logfire trace',data.carrier.trace_url);
  if(data.carrier?.incident_id)addLink('Contact incident','/api/incidents/'+encodeURIComponent(data.carrier.incident_id));
  root.append(resources);
  const canvas=document.createElement('div');canvas.className='archify-canvas';
  if(template){
   const chart=template.cloneNode(true);chart.setAttribute('aria-label',company.name+' live repair workflow');
   for(const node of chart.querySelectorAll('[data-node-id]')){
    const id=node.dataset.nodeId,step=data.nodes[id];if(!step)continue;
    node.classList.add('live-node',step.status);if(selectedNode===id)node.classList.add('live-selected');
    node.setAttribute('aria-label',node.dataset.nodeLabel+': '+step.detail);node.setAttribute('aria-pressed',String(selectedNode===id));
    const detail=node.querySelector('[data-detail="context"]');if(detail)detail.textContent=step.detail;const tooltip=node.querySelector('title');if(tooltip)tooltip.textContent=node.dataset.nodeLabel+': '+step.detail;
    const inspect=()=>{selectedNode=id;render(root,run,company);};node.addEventListener('click',inspect);node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();inspect();}});
   }
   for(const edge of chart.querySelectorAll('[data-edge-id]')){
    const from=edge.dataset.edgeFrom,to=edge.dataset.edgeTo;if(!from||!to)continue;
    let reached=data.nodes[to]?.status!=='pending';const edgeId=edge.dataset.edgeId;
    if(edgeId==='healthy')reached=data.carrier?.status==='available';
    if(edgeId==='passed')reached=data.carrier?.status==='restored';
    if(edgeId==='retry')reached=(data.carrier?.attempts?.length||0)>1;
    if(edgeId==='resume')reached=data.nodes.context.status==='done';
    edge.classList.add(reached?'live-reached':'live-pending');
    if(reached&&data.nodes[to]?.status==='active')edge.classList.add('live-flowing');
   }
   canvas.append(chart);
  }else{const pending=document.createElement('p');pending.textContent='Loading the live architecture…';canvas.append(pending);diagram();}
  root.append(canvas);
  const proof=document.createElement('div');proof.className='archify-proof';const summary=document.createElement('div');const label=document.createElement('p');label.className='archify-kicker';label.textContent='SELECTED STEP / '+data.nodes[selectedNode].status.toUpperCase();const heading=document.createElement('h4');heading.textContent=specs.find(n=>n[0]===selectedNode)[1];const detail=document.createElement('p');detail.textContent=data.nodes[selectedNode].detail;summary.append(label,heading,detail);const inspect=document.createElement('a');inspect.href='#details';inspect.textContent='View carrier evidence ↓';inspect.className='archify-evidence-link';summary.append(inspect);
  const evidence=data.nodes[selectedNode].events.at(-1),pre=document.createElement('pre');pre.textContent=evidence?JSON.stringify(evidence.data,null,2):'No event recorded for this step yet.';proof.append(summary,pre);root.append(proof);
 }
 return {state,render};
})();
