(()=>{
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=t=>{if(!t)return'unknown time';try{return new Date(t).toLocaleString(undefined,{year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});}catch{return t}};
let DATA=null,FILTER='ALL';
const TYPES=['ALL','RELEASE','COMMIT','FORK','EXTERNAL_FIX','ENTITY_EVIDENCE','PULL_REQUEST','REPOSITORY_EVENT'];
function tag(v){return v?`<span class="tag">${esc(v)}</span>`:''}
function itemHtml(x){
  const link=x.url?`<a href="${esc(x.url)}">Open source record →</a>`:'';
  const ingest=x.entity_ingested?tag('ENTITY INGESTED'):'';
  return `<article class="news-item"><div class="row">${tag(x.type)}${tag(x.status)}${ingest}</div><h3>${esc(x.title||x.type)}</h3><p>${esc(x.summary||'')}</p><div class="news-meta"><span>${esc(fmt(x.occurred_at))}</span>${x.repository?`<span>${esc(x.repository)}</span>`:''}${x.upstream?`<span>upstream: ${esc(x.upstream)}</span>`:''}${x.entity_state?`<span>ENTITY: ${esc(x.entity_state)}</span>`:''}</div>${link?`<p>${link}</p>`:''}${x.entity_record_url&&x.entity_record_url!==x.url?`<div class="news-source"><a href="${esc(x.entity_record_url)}">ENTITY evidence record</a></div>`:''}</article>`;
}
function renderActivity(){
  const rows=(DATA.items||[]).filter(x=>FILTER==='ALL'||x.type===FILTER).slice(0,200);
  $('activity').innerHTML=rows.length?rows.map(itemHtml).join(''):'<div class="loading">No matching activity in the retained public ledger.</div>';
}
function renderFilters(){
  $('filters').innerHTML=TYPES.map(t=>`<button type="button" data-filter="${t}" aria-pressed="${t==='ALL'}">${t.replaceAll('_',' ')}</button>`).join('');
  $('filters').addEventListener('click',e=>{const b=e.target.closest('button[data-filter]');if(!b)return;FILTER=b.dataset.filter;for(const x of $('filters').querySelectorAll('button'))x.setAttribute('aria-pressed',String(x===b));renderActivity();});
}
function renderStats(){const s=DATA.stats||{};$('stats').innerHTML=[['Public repos',s.public_repositories],['Original repos',s.original_public_repositories],['Public forks',s.public_forks],['Release records',s.release_records],['Recent external PRs',s.recent_external_prs],['ENTITY evidence',s.entity_evidence_records],['Activity items',s.activity_items]].map(([k,v])=>`<div class="stat-box"><strong>${esc(v??0)}</strong><span>${esc(k)}</span></div>`).join('');$('generated').innerHTML=`<span>Snapshot: ${esc(fmt(DATA.generated_at_utc))}</span><span>${esc(DATA.scope||'')}</span><span>${esc(DATA.privacy_boundary||'')}</span>${DATA.history_retention?`<span>${esc(DATA.history_retention)}</span>`:''}`;}
function renderReleases(){const rows=(DATA.items||[]).filter(x=>x.type==='RELEASE');$('releases').innerHTML=rows.length?rows.map(itemHtml).join(''):'<div class="loading">No public GitHub release records were found.</div>';}
function renderExternal(){const rows=(DATA.items||[]).filter(x=>x.type==='EXTERNAL_FIX');$('external').innerHTML=rows.length?rows.map(itemHtml).join(''):'<div class="loading">No recent external pull requests found in the current GitHub search window.</div>';}
function renderEvidence(){const rows=(DATA.items||[]).filter(x=>x.type==='ENTITY_EVIDENCE');$('entity-evidence').innerHTML=rows.length?rows.map(itemHtml).join(''):'<div class="loading">No public ENTITY contribution-evidence records were found.</div>';}
function renderRepos(){const rows=DATA.repositories||[];$('repos').innerHTML=rows.length?rows.map(r=>`<article class="repo-card"><div class="row">${tag(r.fork?'FORK':'BTG REPOSITORY')}${r.archived?tag('ARCHIVED'):''}</div><h3><a href="${esc(r.url)}">${esc(r.full_name)}</a></h3><p>${esc(r.description||'No repository description.')}</p>${r.fork?`<p class="muted-small">Upstream: ${esc(r.upstream||'GitHub parent unavailable')}</p>`:''}<p class="muted-small">Default branch: ${esc(r.default_branch||'—')} · Language: ${esc(r.language||'—')}</p><p class="muted-small">Last push: ${esc(fmt(r.pushed_at))}</p></article>`).join(''):'<div class="loading">No public repositories found.</div>';}
async function main(){try{const res=await fetch('activity.json',{cache:'no-store'});if(!res.ok)throw new Error(`activity.json ${res.status}`);DATA=await res.json();renderStats();renderFilters();renderActivity();renderReleases();renderExternal();renderEvidence();renderRepos();}catch(err){for(const id of ['stats','activity','releases','external','entity-evidence','repos']){const el=$(id);if(el)el.innerHTML=`<div class="loading">NEWS source data is temporarily unavailable: ${esc(err.message)}</div>`;}}}
main();
})();
