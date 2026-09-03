const $ = (id) => document.getElementById(id);
const statusNames = {idle:'آماده', starting:'در حال شروع', running:'در حال مناظره', stopping:'در حال توقف', waiting:'پایان بخش — آماده ادامه', stopped:'متوقف شد', error:'خطا'};
let source;

function setStatus(value){ $('status').textContent = statusNames[value] || value; controls(value); }
function escapeHtml(value){ const d=document.createElement('div'); d.textContent=value ?? ''; return d.innerHTML; }
function renderHealth(models={}){
  $('health').innerHTML = Object.entries(models).map(([role,m]) => `<div class="health-card ${m.ok?'ok':'bad'}"><span class="dot"></span><strong>${escapeHtml(role)}</strong><div>${escapeHtml(m.model||'')}</div><small>${escapeHtml(m.url||'')}</small>${m.error?`<div>${escapeHtml(m.error)}</div>`:''}</div>`).join('');
}
function renderList(id, values){ $(id).innerHTML=(values||[]).map(v=>`<li>${escapeHtml(v)}</li>`).join(''); }
function renderState(state={}){
  $('segment').textContent=state.segment ?? '—';
  $('round').textContent=state.round ?? '—';
  $('language-active').textContent=state.language_name || state.language || '—';
  renderList('consensus',state.consensus); renderList('disagreements',state.disagreements);
  renderList('proposals',state.proposals); renderList('risks',state.risks);
  renderList('open_questions',state.open_questions); renderList('decisions',state.decisions);
  renderList('next_focus',state.next_focus);
  if(state.archived_note_count !== undefined) $('note-status').textContent = `یادداشت‌های آرشیوشده: ${state.archived_note_count}`;
}
function addCard(kind,title,meta,text){ const el=document.createElement('article'); el.className=`card ${kind}`; el.innerHTML=`<h3>${escapeHtml(title)}</h3><small>${escapeHtml(meta)}</small><pre>${escapeHtml(text)}</pre>`; $('debate').appendChild(el); el.scrollIntoView({behavior:'smooth',block:'nearest'}); }
function log(text){ $('log').textContent += `${text}\n`; }
function controls(status){
  const running=['starting','running','stopping'].includes(status);
  $('start').disabled=running;
  $('stop').disabled=!['starting','running'].includes(status);
  $('continue').disabled=status!=='waiting';
  $('export').disabled=!(status==='waiting' || status==='stopped' || status==='error');
  $('send-note').disabled=!['starting','running'].includes(status);
  $('question').disabled=running;
  $('language').disabled=running;
  $('rounds').disabled=running;
  $('max_tokens').disabled=running;
}
function handle(event){
  const d=event.data; if(!d) return; const e=JSON.parse(d);
  if(e.type==='health') renderHealth(e.models);
  if(e.type==='question'){
    $('debate').innerHTML=''; $('summary').textContent='';
    $('round-total').textContent=e.rounds; $('token-total').textContent=e.max_tokens;
    $('language-active').textContent=e.language_name || e.language || '—';
    log(`موضوع: ${e.question}`); log(`زبان مناظره: ${e.language_name}`);
  }
  if(e.type==='segment_start'){
    setStatus('running'); $('round-total').textContent=e.rounds; $('token-total').textContent=e.max_tokens;
    $('language-active').textContent=e.language_name || e.language || '—';
    renderState({segment:e.segment,round:0,language_name:e.language_name}); log(`Segment ${e.segment} شروع شد — ${e.rounds} راند — سقف ${e.max_tokens} توکن — زبان: ${e.language_name}`);
  }
  if(e.type==='round_start'){ renderState({segment:e.segment,round:e.round}); log(`Round ${e.round}`); }
  if(e.type==='moderator_mission') addCard('moderator','Moderator — Mission',`Round ${e.round}${e.user_note_consumed?' — یادداشت انسانی خوانده شد و آرشیو شد':''}`,e.text);
  if(e.type==='agent_response') addCard(e.agent==='Agent 1'?'agent1':'agent2',e.agent,`Round ${e.round}${e.truncated?' — پاسخ به سقف توکن رسید':''}`,e.text);
  if(e.type==='moderator_update') addCard('moderator','Moderator — Evaluation',`Round ${e.round}`,e.text), renderState(e.state);
  if(e.type==='moderator_summary'){ $('summary').textContent=e.text; }
  if(e.type==='segment_complete'){ setStatus('waiting'); $('summary').textContent=e.summary; renderState(e.state); log(`Segment ${e.segment} کامل شد. Continue یا ذخیره Word.`); }
  if(e.type==='compacted'){ renderState(e.state); setStatus('starting'); log(e.message); }
  if(e.type==='note_queued'){ $('note').value=''; $('note-status').textContent=`${e.pending} یادداشت در صف Moderator است.`; log(e.message); }
  if(e.type==='stopping') log(e.message);
  if(e.type==='stopped'){ setStatus('stopped'); log(e.reason); }
  if(e.type==='error'){ setStatus('error'); log(`ERROR: ${e.message}`); }
}
function connect(){ source=new EventSource('/stream'); source.onmessage=handle; source.onerror=()=>{}; }
async function post(url,body){ const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); const data=await r.json(); if(!r.ok) throw new Error(data.error||`HTTP ${r.status}`); return data; }
$('start').onclick=async()=>{ try{ await post('/api/start',{question:$('question').value,language:$('language').value,rounds:Number($('rounds').value),max_tokens:Number($('max_tokens').value)}); }catch(e){ setStatus('error'); log(e.message); } };
$('stop').onclick=async()=>{ try{ await post('/api/stop',{}); setStatus('stopping'); }catch(e){log(e.message);} };
$('continue').onclick=async()=>{ try{ await post('/api/continue',{}); }catch(e){log(e.message);} };
$('send-note').onclick=async()=>{ try{ await post('/api/note',{note:$('note').value}); }catch(e){log(e.message);} };
$('note').addEventListener('keydown',(e)=>{ if((e.ctrlKey||e.metaKey)&&e.key==='Enter') $('send-note').click(); });
$('export').onclick=()=>{ window.location.href='/api/export/docx'; };
async function init(){
  connect();
  try{ const r=await fetch('/api/health'); const d=await r.json(); renderHealth(d.models); }catch(e){log('Health check failed: '+e.message);}
  try{ const r=await fetch('/api/status'); const d=await r.json(); setStatus(d.status); $('rounds').value=d.rounds ?? 10; $('max_tokens').value=d.max_tokens ?? 1200; $('language').value=d.language_mode ?? 'auto'; $('round-total').textContent=d.rounds ?? 10; $('token-total').textContent=d.max_tokens ?? 1200; renderState(d.state); if(d.summary) $('summary').textContent=d.summary; if(d.error) log(d.error); }catch(e){}
}
init();
