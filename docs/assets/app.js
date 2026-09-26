const BASE=window.B||"";
const q=document.getElementById('search');
const r=document.getElementById('results');
let I=null;

function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function clean(v){return String(v??'').replaceAll('â€¦','…').replaceAll('â€”','—').replaceAll('â€“','–').replaceAll('â†’','→').replaceAll('Â·','·').replaceAll('â€¢','•').replaceAll('Â','');}

if(q){
  q.placeholder='Search documentation…';
  q.oninput=async()=>{
    const v=q.value.toLowerCase().trim();
    if(v.length<2){r.style.display='none';return;}
    try{
      if(!I){
        const res=await fetch(BASE+'search-index.json',{cache:'no-store'});
        if(!res.ok)throw new Error('search index '+res.status);
        I=await res.json();
      }
      const h=I.filter(x=>((x.title||'')+' '+(x.text||'')+' '+(x.section||'')).toLowerCase().includes(v)).slice(0,40);
      r.innerHTML=h.length?h.map(x=>'<a href="'+BASE+esc(x.url)+'"><b>'+esc(clean(x.title))+'</b><br><span>'+esc(clean(x.section||''))+'</span></a>').join(''):'<div class="search-empty">No matching documentation.</div>';
      r.style.display='block';
    }catch(e){
      r.innerHTML='<div class="search-empty">Search index unavailable. Use the section indexes or GitHub source links.</div>';
      r.style.display='block';
    }
  };
}

function repairVisibleEncoding(){
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  const nodes=[]; while(walker.nextNode())nodes.push(walker.currentNode);
  for(const n of nodes){const p=n.parentElement;if(p&&p.tagName!=='SCRIPT'&&p.tagName!=='STYLE')n.nodeValue=clean(n.nodeValue);}
}

function enhanceLegacyPage(){
  const parts=location.pathname.split('/').filter(Boolean);
  const rootAt=parts.indexOf('ENTITY-DOCS');
  const section=parts[rootAt+1]||'';
  const file=parts[rootAt+2]||'';
  const sections=new Set(['operator','developer','protocol','economy','security','domains','versions','reference']);
  const main=document.querySelector('main');
  const hb=document.querySelector('header b');
  if(hb)hb.textContent='ENTITY Documentation Portal';
  if(!main||!sections.has(section))return;
  const isIndex=!file||file==='index.html';
  if(!isIndex){
    const note=document.createElement('div');
    note.className='legacy-note';
    note.innerHTML='<strong>Generated documentation snapshot.</strong> This page is retained for historical/reference use. For the current v3.4.2 candidate and BTDU, use the <a href="'+BASE+'v342/">v3.4.2 developer preview</a>. <a href="'+BASE+section+'/">Back to '+esc(section.charAt(0).toUpperCase()+section.slice(1))+' index</a>.';
    main.insertBefore(note,main.firstChild);
  }
}

document.addEventListener('DOMContentLoaded',()=>{repairVisibleEncoding();enhanceLegacyPage();});
