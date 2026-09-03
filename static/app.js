const $ = (id) => document.getElementById(id);
const statusNames = {idle:'آماده', starting:'در حال شروع', running:'در حال مناظره', stopping:'در حال توقف', waiting:'پایان بخش — آماده ادامه', stopped:'متوقف شد', error:'خطا'};
let source;

function setStatus(value){ $('status').textContent = statusNames[value] || value; }
function escapeHtml(value){ const d=document.createElement('div'); d.textContent=value ?? ''; return d.innerHTML; }
function renderHealth(models={}){
  $('health').innerHTML = Object.entries(models).map(([role,m]) => `<div class="health-card ${m.ok?'ok':'bad'}"><span class="dot"></span><strong>${escapeHtml(role)}</strong><div>${escapeHtml(m.model||'')}</div><small>${escapeHtml(m.url||'')}</small>${m.error?`<div>${escapeHtml(m.error)}</div>`:''}</div>`).join('');
}
function renderList(id, values){ $(id).innerHTML=(values||[]).map(v=>`<li>${escapeHtml(v)}</li>`).join(''); }
function renderState(state={}){
  $('segment').textContent=state.segment ?? '—';
  $('round').textContent=state.round ?? '—';
  renderList('consensus',state.consensus); renderList('disagreements',state.disagreements);
  renderList('proposals',state.proposals); renderList('risks',state.risks);
  renderList('open_questions',state.open_questions); renderList('decisions',state.decisions);
}
function addCard(kind,title,meta,text){ const el=document.createElement('article'); el.className=`card ${kind}`; el.innerHTML=`<h3>${escapeHtml(title)}</h3><small>${escapeHtml(meta)}</small><pre>${escapeHtml(text)}</pre>`; $('debate').appendChild(el); el.scrollIntoView({behavior:'smooth',block:'nearest'}); }
function log(text){ $('log').textContent += `${text}\n`; }
function controls(status){
  const running=['starting','running','stopping'].includes(status);
  $('start').disabled=running;
  $('stop').disabled=!['starting','running'].includes(status);
  $('continue').disabled=status!=='waiting';
  $('question').disabled=running;
}
function handle(event){
  const d=event.data; if(!d) return; const e=JSON.parse(d);
  if(e.type==='health') renderHealth(e.models);
  if(e.type==='question'){ $('debate').innerHTML=''; $('summary').textContent=''; log(`موضوع: ${e.question}`); }
  if(e.type==='segment_start'){ setStatus('running'); renderState({segment:e.segment,round:0}); log(`Segment ${e.segment} شروع شد — ${e.rounds} راند`); }
  if(e.type==='round_start'){ renderState({segment:e.segment,round:e.round}); log(`Round ${e.round}`); }
  if(e.type==='moderator_mission') addCard('moderator','Moderator — Mission',`Round ${e.round}`,e.text);
  if(e.type==='agent_response') addCard(e.agent==='Agent 1'?'agent1':'agent2',e.agent,`Round ${e.round}${e.truncated?' — پاسخ به سقف توکن رسید':''}`,e.text);
  if(e.type==='moderator_update'){ addCard('moderator','Moderator — Evaluation',`Round ${e.round}`,e.text); renderState(e.state); }
  if(e.type==='moderator_summary'){ $('summary').textContent=e.text; }
  if(e.type==='segment_complete'){ setStatus('waiting'); $('summary').textContent=e.summary; renderState(e.state); controls('waiting'); log(`Segment ${e.segment} کامل شد. Continue یا Stop.`); }
  if(e.type==='compacted'){ renderState(e.state); setStatus('starting'); log(e.message); }
  if(e.type==='stopping') log(e.message);
  if(e.type==='stopped'){ setStatus('stopped'); controls('stopped'); log(e.reason); }
  if(e.type==='error'){ setStatus('error'); controls('error'); log(`ERROR: ${e.message}`); }
}
function connect(){ source=new EventSource('/stream'); source.onmessage=handle; source.onerror=()=>log('SSE connection retrying...'); }
async function post(url,body){ const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); const data=await r.json(); if(!r.ok) throw new Error(data.error||`HTTP ${r.status}`); return data; }
$('start').onclick=async()=>{ try{ await post('/api/start',{question:$('question').value}); controls('running'); }catch(e){ setStatus('error'); log(e.message); } };
$('stop').onclick=async()=>{ try{ await post('/api/stop',{}); controls('stopping'); }catch(e){log(e.message);} };
$('continue').onclick=async()=>{ try{ await post('/api/continue',{}); controls('running'); }catch(e){log(e.message);} };
async function init(){ connect(); try{ const r=await fetch('/api/health'); const d=await r.json(); renderHealth(d.models); }catch(e){log('Health check failed: '+e.message);} try{ const r=await fetch('/api/status'); const d=await r.json(); setStatus(d.status); renderState(d.state); if(d.summary) $('summary').textContent=d.summary; if(d.error) log(d.error); controls(d.status); }catch(e){} }
init();
