document.addEventListener('DOMContentLoaded',()=>{
  const nav=document.querySelector('.site-nav');
  const linksBox=document.querySelector('.site-links');

  // Every public-facing site shell must expose the tutorials and canonical capability map.
  if(linksBox&&!linksBox.querySelector('a[data-entity-tutorials]')){
    const script=[...document.scripts].find(s=>/assets\/site\.js(?:\?|$)/.test(s.src));
    const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
    const siteRoot=new URL('../',assetBase);
    const tutorials=document.createElement('a');
    tutorials.href=new URL('tutorials/',siteRoot).href;
    tutorials.textContent='Tutorials';
    tutorials.setAttribute('data-entity-tutorials','1');
    const github=[...linksBox.querySelectorAll('a')].find(a=>a.classList.contains('nav-cta'));
    if(github)linksBox.insertBefore(tutorials,github);else linksBox.appendChild(tutorials);
  }

  if(linksBox&&!linksBox.querySelector('a[data-entity-system-map]')){
    const script=[...document.scripts].find(s=>/assets\/site\.js(?:\?|$)/.test(s.src));
    const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
    const siteRoot=new URL('../',assetBase);
    const map=document.createElement('a');
    map.href=new URL('reference/capability-map.html',siteRoot).href;
    map.textContent='System Map';
    map.setAttribute('data-entity-system-map','1');
    const github=[...linksBox.querySelectorAll('a')].find(a=>a.classList.contains('nav-cta'));
    if(github)linksBox.insertBefore(map,github);else linksBox.appendChild(map);
  }

  const links=[...document.querySelectorAll('.site-links a')];
  const path=location.pathname.replace(/\/+$/,'/');

  // The canonical About-page identity must reflect the complete current system,
  // not reduce ENTITY to sovereignty alone. This also keeps older generated HTML
  // shells aligned when the shared site runtime is newer than their static title.
  if(/\/ENTITY-DOCS\/about\/$/.test(path)||/\/about\/$/.test(path)){
    document.title='About ENTITY · Digital Authority, Information, Market, Economic & Recovery Fabric';
    let meta=document.querySelector('meta[name="description"]');
    if(!meta){meta=document.createElement('meta');meta.name='description';document.head.appendChild(meta);}
    meta.content="ENTITY is Blackmore Technology Group's Canadian-designed digital authority, governed information, rights, evidence, market, economic and recovery operating fabric.";
  }

  for(const a of links){
    try{
      const u=new URL(a.href,location.href);
      if(u.pathname!=="/"&&path.startsWith(u.pathname.replace(/\/+$/,'/')))a.setAttribute('aria-current','page');
    }catch{}
  }

  if(nav&&linksBox){
    const b=document.createElement('button');
    b.className='menu-toggle';
    b.type='button';
    b.setAttribute('aria-expanded','false');
    b.setAttribute('aria-label','Open navigation');
    b.textContent='Menu';
    const mobile=nav.querySelector('.mobile-only');
    nav.insertBefore(b,mobile||linksBox);
    b.addEventListener('click',()=>{
      const open=linksBox.classList.toggle('open');
      b.setAttribute('aria-expanded',String(open));
      b.textContent=open?'Close':'Menu';
    });
    for(const a of links)a.addEventListener('click',()=>{
      linksBox.classList.remove('open');
      b.setAttribute('aria-expanded','false');
      b.textContent='Menu';
    });
  }

  const script=[...document.scripts].find(s=>/assets\/site\.js(?:\?|$)/.test(s.src));
  const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
  if(!document.querySelector('link[rel="icon"]')){
    const icon=document.createElement('link');
    icon.rel='icon';
    icon.type='image/svg+xml';
    icon.href=new URL('btg-mark.svg',assetBase).href;
    document.head.appendChild(icon);
  }

  const legal=document.querySelector('.legal');
  if(legal&&/BTGEntity\.io|custom domain/i.test(legal.textContent)){
    legal.textContent='Apache-2.0 open-source protocol and reference implementation. Current supported runtime: ENTITY v3.4.3. BTDU component: 3.4.2 unchanged. Public site hosted on GitHub Pages at blackmore-technology-group.github.io/ENTITY-DOCS/.';
  }
  document.documentElement.style.setProperty('--btg-brand-ready','1');
});