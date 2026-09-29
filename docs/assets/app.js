const BASE=window.B||"";
const q=document.getElementById('search');
const r=document.getElementById('results');
let I=null;
const GUIDE_INDEX=[
  {title:'Technical Guides',section:'Guides',url:'guides/',text:'data provenance sovereign data rights BTDU knowledge graph vector index portable authority recovery'},
  {title:'Data Provenance Protocol',section:'Guides',url:'guides/data-provenance-protocol.html',text:'source controller rights holder evidence provenance derivation ownership truth'},
  {title:'Sovereign Data Rights Architecture',section:'Guides',url:'guides/sovereign-data-rights.html',text:'non-rival data rights instruments DCO licensing transfer settlement derivative participation'},
  {title:'BTDU vs Knowledge Graphs and Vector Indexes',section:'Guides',url:'guides/btdu-knowledge-graphs-vector-indexes.html',text:'BTDU ADAM knowledge graph embeddings vector retrieval governed topology'},
  {title:'Portable Digital Authority and Recovery',section:'Guides',url:'guides/portable-digital-authority-recovery.html',text:'sovereign export backup restore signing authority provider capture recovery'},
  {title:'Standards & Interoperability',section:'Standards',url:'standards/',text:'IETF W3C interoperability authority provenance rights recovery pre-submission working draft'},
  {title:'Provider-Neutral Authority, Provenance, Rights and Portable State',section:'Standards',url:'standards/entity-authority-provenance.html',text:'credential validity authority delegation provenance rights event value portable state recovery conformance RFCXML'},
  {title:'Standards Review Issue #69',section:'Standards',url:'https://github.com/blackmore-technology-group/ENTITY/issues/69',text:'help wanted standards review counterexamples IETF W3C overlap terminology portability evidence'},
  {title:'Clean-Room Glossary & Object Map',section:'Developer',url:'developer/clean-room-glossary.html',text:'vector authority sovereign authority alias controlled values object families protocol 1.0 onboarding clean room'},
  {title:'ENTITY v3.4.2 Language Distribution Readiness',section:'Developer',url:'developer/distribution-readiness.html',text:'Rust crates.io TypeScript npm C# NuGet Go pkg.go.dev Swift Package Index Java Maven Central package registry distribution install verifier CLI 3.4.2'},
  {title:'Strategic Partnerships',section:'Partners',url:'partners/',text:'strategic partnerships rights markets contribution economy settlement market recovery agent authority data governance research qualification'},
  {title:'Partnership Pilot Programs',section:'Partners',url:'partners/pilot-programs.html',text:'agent authority rights market contribution economy portable market recovery sovereign data rights independent BTDU qualification'},
  {title:'Independent Qualification',section:'Partners',url:'partners/independent-qualification.html',text:'independent implementation security review research benchmark standards interoperability institutional pilot external evidence'}
];
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function clean(v){return String(v??'').replaceAll('â€¦','…').replaceAll('â€”','—').replaceAll('â€“','–').replaceAll('â†’','→').replaceAll('Â·','·').replaceAll('â€¢','•').replaceAll('Â','');}
function repairVisibleEncoding(){const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);for(const n of nodes){const p=n.parentElement;if(p&&p.tagName!=='SCRIPT'&&p.tagName!=='STYLE')n.nodeValue=clean(n.nodeValue);}}
function addDiscoveryNav(){const nav=document.querySelector('.layout > nav');if(!nav)return;const links=[{key:'entity-guides',href:BASE+'guides/',text:'Technical Guides'},{key:'entity-standards',href:BASE+'standards/',text:'Standards & Interoperability'}];for(const item of links){if(nav.querySelector('a[data-'+item.key+']'))continue;const a=document.createElement('a');a.href=item.href;a.textContent=item.text;a.setAttribute('data-'+item.key,'1');const anchors=[...nav.querySelectorAll('a')];const anchor=anchors.find(x=>/Home|v3\.4\.2/.test(x.textContent));if(anchor&&anchor.nextSibling)nav.insertBefore(a,anchor.nextSibling);else nav.appendChild(a);}}
function addGlobalSiteNav(){
  const header=document.querySelector('body > header');
  if(!header||document.querySelector('.global-site-nav'))return;
  const hb=header.querySelector('b');
  if(hb&&!hb.querySelector('a.portal-home')){
    const label=clean(hb.textContent||'ENTITY Documentation Portal');
    hb.textContent='';
    const home=document.createElement('a');
    home.className='portal-home';
    home.href=BASE+'index.html';
    home.textContent=label;
    home.setAttribute('aria-label','ENTITY home');
    hb.appendChild(home);
  }
  const bar=document.createElement('div');
  bar.className='global-site-nav';
  bar.setAttribute('aria-label','ENTITY site navigation');
  const links=[
    ['Home','index.html'],
    ['Technology','technology/'],
    ['Economy','economy/'],
    ['Developers','build/'],
    ['Evidence','evidence/'],
    ['Research','research-hub/'],
    ['Partners','collaborate/'],
    ['About','about/']
  ];
  for(const [label,path] of links){const a=document.createElement('a');a.href=BASE+path;a.textContent=label;bar.appendChild(a);}
  header.insertAdjacentElement('afterend',bar);
}
if(q){q.placeholder='Search ENTITY v3.4.3 documentation…';q.oninput=async()=>{const v=q.value.toLowerCase().trim();if(v.length<2){r.style.display='none';return;}try{if(!I){const res=await fetch(BASE+'search-index.json',{cache:'no-store'});if(!res.ok)throw new Error('search index '+res.status);I=(await res.json()).concat(GUIDE_INDEX);}const h=I.filter(x=>((x.title||'')+' '+(x.text||'')+' '+(x.section||'')).toLowerCase().includes(v)).slice(0,50);r.innerHTML=h.length?h.map(x=>'<a href="'+(/^https?:/.test(x.url)?esc(x.url):BASE+esc(x.url))+'"><b>'+esc(clean(x.title))+'</b><br><span>'+esc(clean(x.section||''))+' — '+esc(clean(x.text||''))+'</span></a>').join(''):'<div class="search-empty">No matching documentation.</div>';r.style.display='block';}catch(e){const h=GUIDE_INDEX.filter(x=>((x.title||'')+' '+(x.text||'')+' '+(x.section||'')).toLowerCase().includes(v));r.innerHTML=h.length?h.map(x=>'<a href="'+(/^https?:/.test(x.url)?esc(x.url):BASE+esc(x.url))+'"><b>'+esc(clean(x.title))+'</b><br><span>'+esc(clean(x.section||''))+' — '+esc(clean(x.text||''))+'</span></a>').join(''):'<div class="search-empty">Search index unavailable. Use the manual indexes.</div>';r.style.display='block';}};}
document.addEventListener('DOMContentLoaded',()=>{repairVisibleEncoding();addGlobalSiteNav();addDiscoveryNav();const hb=document.querySelector('header b');if(hb&&hb.textContent.includes('v3.4.0')){const a=hb.querySelector('a.portal-home');if(a)a.textContent='ENTITY Documentation Portal';else hb.textContent='ENTITY Documentation Portal';}const script=[...document.scripts].find(s=>/assets\/app\.js(?:\?|$)/.test(s.src));const assetBase=script?new URL('.',script.src):new URL(BASE+'assets/',location.href);if(!document.querySelector('link[rel="icon"]')){const icon=document.createElement('link');icon.rel='icon';icon.type='image/svg+xml';icon.href=new URL('btg-mark.svg',assetBase).href;document.head.appendChild(icon);}});