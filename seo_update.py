from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape
root=Path(r'E:\ENTITY_ACTIVE\ENTITY-DOCS\docs')
base='https://blackmore-technology-group.github.io/ENTITY-DOCS/'
index=root/'index.html'
s=index.read_text(encoding='utf-8')
needle='<p>This portal is documentation, not an authority root. Exact code, signed records, manifests, schemas and qualification evidence control their respective claims.</p>'
replacement=needle+'<div class="callout"><b>Official publisher:</b> <a href="https://www.blackmoretechgroup.com/">Blackmore Technology Group Limited</a> · <a href="https://www.blackmoretechgroup.com/post/entity-v3-4-global-passport-continuous-provenance">ENTITY v3.4.0 announcement</a></div>'
if needle in s and 'entity-v3-4-global-passport-continuous-provenance' not in s:
    s=s.replace(needle,replacement)
    index.write_text(s,encoding='utf-8',newline='\n')
htmls=sorted(root.rglob('*.html'))
urls=[]
for p in htmls:
    rel=p.relative_to(root).as_posix()
    url=base if rel=='index.html' else base+quote(rel,safe='/.-_')
    urls.append(url)
sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sitemap+=f'  <url><loc>{escape(u)}</loc></url>\n'
sitemap+='</urlset>\n'
(root/'sitemap.xml').write_text(sitemap,encoding='utf-8',newline='\n')
(root/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+base+'sitemap.xml\n',encoding='utf-8',newline='\n')
print({'html_pages':len(htmls),'sitemap_urls':len(urls),'index_crosslink':True})