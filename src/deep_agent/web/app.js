'use strict';
const byId = id => document.getElementById(id);
let sessionId = null, controller = null, busy = false;
function setBusy(value) {
  busy = value;
  byId('send').disabled = value;
  byId('new').disabled = value;
  byId('reset').disabled = value;
  for (const button of byId('sessions').querySelectorAll('button')) button.disabled = value;
}
async function api(path, options = {}) {
  const response = await fetch(path, {credentials: 'same-origin', ...options});
  if (!response.ok) throw new Error(response.status === 429 ? 'The run queue is full. Please wait.' : response.status === 401 ? 'Sign in again to continue.' : 'Request failed. Previous evidence remains available.');
  return response;
}
function node(tag, text, className) {
  const el = document.createElement(tag); if (text !== undefined) el.textContent = String(text);
  if(className) el.className = className; return el;
}
function display(event) {
  const card = node('article', undefined, 'event ' + (event.kind === 'error' ? 'error' : event.kind === 'user' ? 'user' : event.kind));
  const labels = {user:'Your request',model:'DGX model',trace:'Run trace',a2a:'A2A exchange',task:'Procurement evidence',answer:'DeepAgent brief',evidence:'Scientific evidence'};
  card.append(node('h2', labels[event.kind] || event.kind));
  if(event.observed_at) card.append(node('span', new Date(event.observed_at).toLocaleTimeString(), 'event-time'));
  if(event.kind === 'a2a') {
    card.append(node('h3', event.sender + ' → ' + event.receiver));
    if(event.phase === 'request') {
      card.append(node('p', event.question));
      card.append(node('p', 'SendMessage · ' + event.project + ' · cutoff ' + event.as_of, 'muted'));
    } else {
      card.append(node('p', 'Task ' + event.state + ' · ' + (event.elapsed_ms / 1000).toFixed(2) + 's round trip'));
      if(event.observations && event.observations.source_count !== undefined) card.append(node('p', 'Observed: investigation read + ' + event.observations.source_count + ' source reads.'));
      card.append(node('p', 'Remote task: ' + event.remote_id, 'muted'));
    }
    card.append(node('p', 'Correlation: ' + event.correlation_id, 'muted'));
  } else if(event.kind === 'task') {
    const task=event.task; let artifact;
    try {artifact=JSON.parse((task.artifacts || [])[0].text);} catch {artifact=null;}
    card.append(node('h3', (task.simulated ? 'Simulated · ' : '') + task.state));
    if(artifact && artifact.investigation) {
      card.append(node('p', artifact.project + ' · ' + artifact.item));
      const facts=node('div',undefined,'facts');
      for(const [label,value] of [['Required',artifact.investigation.required_quantity],['Ordered',artifact.investigation.ordered_quantity],['Sources',Array.isArray(artifact.sources)?artifact.sources.length:null]]) {
        const fact=node('div');fact.append(node('span',label),node('strong',value === null || value === undefined ? 'Not assessed' : value));facts.append(fact);
      }
      card.append(facts,node('p',artifact.data_boundary,'muted'));
    }
    const details=node('details');details.append(node('summary','Inspect raw evidence artifact'),node('pre',(task.artifacts || []).map(a=>a.text).join('\n\n')));card.append(details);
    const refresh=node('button','Refresh task status');
    refresh.onclick=async()=>{if(busy)return;setBusy(true);try{display({kind:'task',task:await(await api('/api/tasks/'+encodeURIComponent(task.id))).json()});}catch{byId('status').textContent='Task service unavailable; last result retained.';}finally{setBusy(false);}};
    card.append(refresh);
  } else if(event.kind === 'trace') {
    card.append(node('p',event.text),node('p','Trace ID: '+event.trace_id,'muted'));
    if(event.project) card.append(node('p','LangSmith project: '+event.project,'muted'));
  } else {
    card.append(node('pre',event.text || JSON.stringify(event.evidence,null,2)));
    if(event.elapsed_ms !== undefined) card.append(node('span',(event.elapsed_ms/1000).toFixed(2)+'s','muted'));
  }
  byId('events').append(card);
}
async function history() {
  const sessions = await (await api('/api/sessions')).json(); const nav = byId('sessions'); nav.replaceChildren();
  for (const session of sessions) {const button = document.createElement('button'); button.textContent = 'Investigation · ' + session.id.slice(0,8); button.disabled = busy; button.onclick = () => load(session.id).catch(showError); nav.append(button);}
}
async function load(id) {
  if(busy) return; setBusy(true);
  try {
  const session = await (await api('/api/sessions/' + encodeURIComponent(id))).json();
  sessionId = id; byId('events').replaceChildren(); session.events.forEach(display); byId('status').textContent = 'Saved task history loaded. Generation is not resumed.';
  } finally {setBusy(false);}
}
async function createSession() {sessionId = (await (await api('/api/sessions', {method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).json()).id; byId('events').replaceChildren(); await history();}
async function newSession() {if(busy) return; setBusy(true); try {await createSession();} finally {setBusy(false);}}
function showError() {byId('status').textContent = 'Service unavailable. No automatic retry; saved evidence remains available.';}
byId('new').onclick = () => newSession().catch(showError);
byId('procurement').onclick = () => {byId('prompt').value = 'Investigate the GPU-A discrepancy for the selected project and cutoff. Show the governing evidence and unresolved quantities. Prepare a reviewer brief.'; byId('prompt').focus();};
byId('science').onclick = () => {byId('prompt').value = 'Does the evidence establish that vitamin D reduces multiple-sclerosis risk in humans? Distinguish animal evidence, association and causal claims, and cite the supplied studies.'; byId('prompt').focus();};
byId('composer').onsubmit = async event => {
  event.preventDefault(); if(busy) return; setBusy(true);
  try {
    if(!sessionId) await createSession();
    const runSessionId = sessionId;
    controller = new AbortController(); byId('send').disabled=true; byId('stop').hidden=false;
    const prompt = byId('prompt').value; display({kind:'user',text:prompt});
    const response = await api('/api/sessions/' + runSessionId + '/run', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,project:byId('project').value,as_of:byId('cutoff').value}),signal:controller.signal});
    const reader = response.body.getReader(), decoder = new TextDecoder(); let buffer='';
    while(true) {const {value,done}=await reader.read(); if(done) break; buffer+=decoder.decode(value,{stream:true}); const lines=buffer.split('\n'); buffer=lines.pop(); for(const line of lines) if(line) {const item=JSON.parse(line); if(item.kind==='status') byId('status').textContent=item.text; else display(item);}}
    byId('status').textContent='Run ended. Inspect evidence and task state.'; await history();
  } catch(error) {byId('status').textContent=error.name==='AbortError'?'Stopped locally; remote task outcome may be unknown.':error.message;}
  finally {controller=null; setBusy(false); byId('stop').hidden=true;}
};
byId('stop').onclick=()=>controller?.abort();
byId('download').onclick=async()=>{if(!sessionId)return; try{const blob=await(await api('/api/sessions/'+sessionId+'/download')).blob();const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='evidence-brief.json';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);}catch{showError();}};
byId('reset').onclick=async()=>{if(!sessionId||busy)return;setBusy(true);try{await api('/api/sessions/'+sessionId,{method:'DELETE'});sessionId=null;byId('events').replaceChildren();await history();}catch{showError();}finally{setBusy(false);}};
(async()=>{try{const health=await(await api('/healthz')).json();byId('mode').textContent=health.simulated?'SIMULATED PROCUREMENT · LIVE LOCAL MODEL':'READ-ONLY PROCUREMENT · A2A';await history();}catch{showError();}})();

byId('trace-download').onclick = () => {if(sessionId)location.href='/api/sessions/'+encodeURIComponent(sessionId)+'/trace';};
