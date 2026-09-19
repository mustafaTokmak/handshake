// Full conversational loop, headless: does the agent open the call correctly,
// listen to a reply, and emit a well-formed report_finding? Everything except
// the microphone. Run: node convtest.mjs
import { readFileSync } from 'node:fs';
const NAMES = ['GOOGLE_API_KEY','GEMINI_API_KEY','GOOGLE_GENAI_API_KEY','GOOGLE_API'];
function key(){for(const n of NAMES)if(process.env[n])return process.env[n].trim();
 for(const p of ['.env','../.env']){try{const t=readFileSync(p,'utf8');
  for(const n of NAMES){const m=t.match(new RegExp('^'+n+"\\s*=\\s*['\"]?([^'\"\\s]+)",'m'));if(m)return m[1];}}catch{}}return'';}
const API=key();
const S=await fetch('http://127.0.0.1:8770/api/session').then(r=>r.json());

// What the human "support rep" says, fed in as text turns on cue.
const REPLIES = [
  "Oh yeah, sorry about that. We pushed v3 last night and renamed tracking_number to tracking_ref across the shipments object.",
  "It went out around 22:00 UTC on the eighteenth. If you send an Accept-Version: 2 header you'll keep the old field names until January.",
];

const ws=new WebSocket(`wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${API}`);
let said='', turn=0, audioChunks=0, finding=null;
const bail=setTimeout(()=>{console.error('\nTIMEOUT after 90s. Agent said:\n'+said);process.exit(1);},90000);

ws.onopen=()=>ws.send(JSON.stringify({setup:S.liveSetup}));

ws.onmessage=async e=>{
  const raw=e.data instanceof Blob?await e.data.text():e.data;
  let m;try{m=JSON.parse(raw)}catch{return}
  if(m.setupComplete){
    console.log('setup accepted; opening the line\n');
    ws.send(JSON.stringify({clientContent:{turns:[{role:'user',parts:[{text:'[The support line has just connected. Introduce yourself and begin.]'}]}],turnComplete:true}}));
    return;
  }
  const c=m.serverContent;
  if(c){
    for(const p of (c.modelTurn?.parts)||[]) if(p.inlineData?.data) audioChunks++;
    if(c.outputTranscription?.text){said+=c.outputTranscription.text;process.stdout.write(c.outputTranscription.text);}
    if(c.turnComplete){
      console.log(`\n   [turn ${turn} done · ${audioChunks} audio chunks]\n`);
      if(turn<REPLIES.length){
        console.log('REP: '+REPLIES[turn]+'\n');
        ws.send(JSON.stringify({clientContent:{turns:[{role:'user',parts:[{text:REPLIES[turn]}]}],turnComplete:true}}));
        turn++; said='';
      }
    }
  }
  if(m.toolCall){
    for(const fc of m.toolCall.functionCalls||[]){
      if(fc.name==='report_finding'){finding=fc.args;
        console.log('\n=== report_finding ===');
        console.log(JSON.stringify(fc.args,null,2));
        const r=await fetch('http://127.0.0.1:8770/api/finding',{method:'POST',
          headers:{'Content-Type':'application/json'},body:JSON.stringify({finding:fc.args,transcript:[]})});
        const b=await r.json();
        console.log('\nserver validation:',r.ok?'ACCEPTED -> '+b.saved:'REJECTED -> '+(b.detail||b.error));
        clearTimeout(bail); ws.close(); process.exit(r.ok?0:1);
      }
    }
    ws.send(JSON.stringify({toolResponse:{functionResponses:(m.toolCall.functionCalls||[]).map(f=>({id:f.id,name:f.name,response:{result:'recorded'}}))}}));
  }
};
ws.onclose=e=>{if(!finding){clearTimeout(bail);console.error(`\nclosed ${e.code}: ${e.reason||'(none)'}`);process.exit(1);}};
