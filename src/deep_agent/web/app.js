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
function display(event) {
  const card = document.createElement('article'); card.className = 'event ' + (event.kind === 'error' ? 'error' : event.kind === 'user' ? 'user' : '');
  const heading = document.createElement('h2'); heading.textContent = event.kind;
  const text = document.createElement('pre');
  if (event.kind === 'task') {
    const task = event.task;
    text.textContent = `${task.simulated ? 'SIMULATED SPECIALIST · ' : ''}${task.state}\nTask: ${task.id}\n` + (task.artifacts || []).map(a => a.text).join('\n\n');
    const refresh = document.createElement('button'); refresh.textContent = 'Refresh task status';
    refresh.onclick = async () => {if(busy)return;setBusy(true);try {display({kind:'task',task:await (await api('/api/tasks/' + encodeURIComponent(task.id))).json()});} catch {byId('status').textContent = 'Task service unavailable; last result retained.';}finally{setBusy(false);}};
    card.append(refresh);
  } else text.textContent = event.text || JSON.stringify(event.evidence, null, 2);
  card.prepend(heading, text); byId('events').append(card);
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
(async()=>{try{const health=await(await api('/healthz')).json();byId('mode').textContent=health.simulated?'SIMULATED PROCUREMENT · LIVE LOCAL MODEL':'PROCUREMENT INTEGRATION PENDING';await history();}catch{showError();}})();
