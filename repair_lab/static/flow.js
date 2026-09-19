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
 function svg(tag,attrs={},text){const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
 function render(root,run,company){
  const id=company.id,data=state(run,id);if(lastCarrier!==id){selectedNode='sandbox';lastCarrier=id;}
  root.replaceChildren();
  const heading=document.createElement('div');heading.className='flow-heading';const title=document.createElement('div');
  const name=document.createElement('h3');name.textContent=company.name;const caption=document.createElement('p');caption.textContent='Follow the real repair. Select a step to inspect its evidence.';title.append(name,caption);
  const badge=document.createElement('span');badge.className='flow-live';badge.textContent=['repairing','resuming','loading'].includes(data.carrier?.status)?'LIVE · IN PROGRESS':data.carrier?.status==='waiting_contact'?'WAITING FOR CONTACT':data.carrier?.quote?'QUOTE AVAILABLE':'READY';heading.append(title,badge);root.append(heading);
  const scroller=document.createElement('div');scroller.className='flow-canvas';const chart=svg('svg',{viewBox:'0 0 740 600',role:'group','aria-label':company.name+' live repair workflow'});
  const defs=svg('defs');const pattern=svg('pattern',{id:'flow-grid',width:20,height:20,patternUnits:'userSpaceOnUse'});pattern.append(svg('circle',{cx:1,cy:1,r:.7,fill:'#cbd5e1'}));defs.append(pattern);
  const marker=svg('marker',{id:'flow-arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'});marker.append(svg('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'context-stroke'}));defs.append(marker);chart.append(defs,svg('rect',{width:740,height:600,fill:'url(#flow-grid)'}));
  const paths=[
   ['response','validation','M220 105 H270',''],['validation','docs','M460 105 H510',''],
   ['docs','gateway','M605 150 V174',''],['gateway','model','M605 224 V250',''],
   ['model','sandbox','M510 295 H460',''],['sandbox','quote','M270 295 H220',''],
   ['validation','quote','M270 105 H245 V210 H125 V250','valid'],
   ['sandbox','docs','M365 250 V184 H485 V30 H725 V105 H700','retry'],
   ['sandbox','contact','M365 340 V450','escalate'],['contact','context','M460 495 H510',''],['context','model','M605 450 V340','resume']
  ];
  for(const [from,to,d,kind]of paths){let reached=data.nodes[to].status!=='pending';if(kind==='valid')reached=data.carrier?.status==='available';if(from==='sandbox'&&to==='quote')reached=data.carrier?.status==='restored';if(kind==='retry')reached=(data.carrier?.attempts?.length||0)>1;if(kind==='resume')reached=data.nodes.context.status==='done';const active=reached&&data.nodes[to].status==='active';chart.append(svg('path',{d,class:'flow-edge'+(reached?' reached':'')+(active?' flowing':''),'marker-end':'url(#flow-arrow)'}));}
  for(const [x,y,text]of [[115,196,'Already valid'],[495,21,'Failed patch → retry'],[375,397,'5 failed patches'],[614,399,'Resume']]){const t=svg('text',{x,y,class:'flow-route-label'},text);chart.append(t);}
  for(const [id,label,x,y,w,h]of specs){const node=data.nodes[id],g=svg('g',{class:'flow-node '+node.status+(selectedNode===id?' focused':''),role:'button',tabindex:0,'aria-label':label+': '+node.detail,'data-step':id,transform:`translate(${x} ${y})`});g.append(svg('rect',{width:w,height:h,rx:10}),svg('circle',{cx:16,cy:20,r:4}),svg('text',{x:28,y:25,class:'flow-node-title'},label),svg('text',{x:16,y:h===50?42:57,class:'flow-node-detail'},node.detail));if(h!==50)g.append(svg('text',{x:16,y:76,class:'flow-node-status'},node.status==='pending'?'WAITING':node.status.toUpperCase()));const inspect=()=>{selectedNode=id;render(root,run,company);root.querySelector('.flow-proof').scrollIntoView({behavior:'smooth',block:'nearest'});};g.addEventListener('click',inspect);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect();}});chart.append(g);}
  scroller.append(chart);root.append(scroller);
  const proof=document.createElement('div');proof.className='flow-proof';const summary=document.createElement('strong');summary.textContent=specs.find(n=>n[0]===selectedNode)[1]+' · '+data.nodes[selectedNode].detail;proof.append(summary);
  const evidence=data.nodes[selectedNode].events.at(-1),pre=document.createElement('pre');pre.textContent=evidence?JSON.stringify(evidence.data,null,2):'No event recorded for this step yet.';proof.append(pre);root.append(proof);
  const legend=document.createElement('p');legend.className='flow-legend';legend.textContent='Green · completed    Blue · running    Amber · waiting    Red · failed check    Dashed arrows · active transition';root.append(legend);
 }
 return {state,render};
})();
