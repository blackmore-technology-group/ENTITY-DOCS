document.addEventListener('DOMContentLoaded',()=>{
  const nav=document.querySelector('.site-nav');
  const linksBox=document.querySelector('.site-links');
  const script=[...document.scripts].find(s=>/assets\/site\.js(?:\?|$)/.test(s.src));
  const assetBase=script?new URL('.',script.src):new URL('assets/',location.href);
  const siteRoot=new URL('../',assetBase);
  const insertBeforeGithub=(a)=>{const github=[...linksBox.querySelectorAll('a')].find(x=>x.classList.contains('nav-cta'));if(github)linksBox.insertBefore(a,github);else linksBox.appendChild(a);};

  if(linksBox&&!linksBox.querySelector('a[data-entity-tutorials]')){
    const a=document.createElement('a');a.href=new URL('tutorials/',siteRoot).href;a.textContent='Tutorials';a.setAttribute('data-entity-tutorials','1');insertBeforeGithub(a);
  }
  if(linksBox&&!linksBox.querySelector('a[data-entity-recipes]')){
    const a=document.createElement('a');a.href=new URL('recipes/',siteRoot).href;a.textContent='Recipes';a.setAttribute('data-entity-recipes','1');insertBeforeGithub(a);
  }
  if(linksBox&&!linksBox.querySelector('a[data-entity-community]')){
    const a=document.createElement('a');a.href=new URL('community/',siteRoot).href;a.textContent='Community';a.setAttribute('data-entity-community','1');insertBeforeGithub(a);
  }
  if(linksBox&&!linksBox.querySelector('a[data-entity-news]')){
    const a=document.createElement('a');a.href=new URL('news/',siteRoot).href;a.textContent='NEWS';a.setAttribute('data-entity-news','1');insertBeforeGithub(a);
  }
  if(linksBox&&!linksBox.querySelector('a[data-entity-system-map]')){
    const a=document.createElement('a');a.href=new URL('reference/capability-map.html',siteRoot).href;a.textContent='System Map';a.setAttribute('data-entity-system-map','1');insertBeforeGithub(a);
  }

  const links=[...document.querySelectorAll('.site-links a')];
  const path=location.pathname.replace(/\/+$/,'/');
  if(/\/ENTITY-DOCS\/about\/$/.test(path)||/\/about\/$/.test(path)){
    document.title='About ENTITY · Digital Authority, Information, Market, Economic & Recovery Fabric';
    let meta=document.querySelector('meta[name="description"]');
    if(!meta){meta=document.createElement('meta');meta.name='description';document.head.appendChild(meta);}
    meta.content="ENTITY is Blackmore Technology Group's Canadian-designed digital authority, governed information, rights, evidence, market, economic and recovery operating fabric.";
  }
  for(const a of links){try{const u=new URL(a.href,location.href);if(u.pathname!=="/"&&path.startsWith(u.pathname.replace(/\/+$/,'/')))a.setAttribute('aria-current','page');}catch{}}

  if(nav&&linksBox){
    const b=document.createElement('button');b.className='menu-toggle';b.type='button';b.setAttribute('aria-expanded','false');b.setAttribute('aria-label','Open navigation');b.textContent='Menu';
    const mobile=nav.querySelector('.mobile-only');nav.insertBefore(b,mobile||linksBox);
    b.addEventListener('click',()=>{const open=linksBox.classList.toggle('open');b.setAttribute('aria-expanded',String(open));b.textContent=open?'Close':'Menu';});
    for(const a of links)a.addEventListener('click',()=>{linksBox.classList.remove('open');b.setAttribute('aria-expanded','false');b.textContent='Menu';});
  }

  if(!document.querySelector('link[rel="icon"]')){const icon=document.createElement('link');icon.rel='icon';icon.type='image/svg+xml';icon.href=new URL('btg-mark.svg',assetBase).href;document.head.appendChild(icon);}
  const legal=document.querySelector('.legal');
  if(legal&&/BTGEntity\.io|custom domain/i.test(legal.textContent))legal.textContent='Apache-2.0 open-source protocol and reference implementation. Current supported runtime: ENTITY v3.4.3. BTDU component: 3.4.2 unchanged. Public site hosted on GitHub Pages at blackmore-technology-group.github.io/ENTITY-DOCS/.';
  document.documentElement.style.setProperty('--btg-brand-ready','1');
});