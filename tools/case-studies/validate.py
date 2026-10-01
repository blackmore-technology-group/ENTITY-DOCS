from pathlib import Path
from html.parser import HTMLParser
import json

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/"docs"
CASE=DOCS/"tutorials"/"case-studies"
pages=[CASE/"index.html",CASE/"pycubrid-367.html",DOCS/"tutorials"/"index.html",DOCS/"tutorials"/"external-contribution-lineage.html"]

forbidden=["ChatGPT","assistant prompts","chat transcript","E:\\ENTITY_ACTIVE"]
for page in pages:
    text=page.read_text(encoding="utf-8-sig")
    bad=[term for term in forbidden if term in text]
    if bad: raise SystemExit(f"FORBIDDEN_PUBLIC_META {page}: {bad}")
for page in [CASE/"index.html",CASE/"pycubrid-367.html"]:
    if "\ufffd" in page.read_text(encoding="utf-8-sig"):
        raise SystemExit(f"REPLACEMENT_CHAR {page}")

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href: self.hrefs.append(href)
for page in pages:
    parser=Links(); parser.feed(page.read_text(encoding="utf-8-sig"))
    for href in parser.hrefs:
        clean=href.split("#",1)[0].split("?",1)[0]
        if not clean or clean.startswith(("http://","https://","mailto:","javascript:")):
            continue
        target=(page.parent/clean).resolve()
        if clean.endswith("/"): target=target/"index.html"
        if not target.exists(): raise SystemExit(f"BROKEN_LINK {page}: {href} -> {target}")

search=json.loads((DOCS/"search-index.json").read_text(encoding="utf-8-sig"))
search_urls={row.get("url") for row in search}
expected=["tutorials/case-studies/","tutorials/case-studies/pycubrid-367.html"]
for url in expected:
    if url not in search_urls: raise SystemExit(f"SEARCH_MISSING {url}")
    for sitemap in ["sitemap.xml","sitemap-site.xml"]:
        if url not in (DOCS/sitemap).read_text(encoding="utf-8-sig"):
            raise SystemExit(f"SITEMAP_MISSING {sitemap}: {url}")

manifest=json.loads((ROOT/"PORTAL_MANIFEST.json").read_text(encoding="utf-8-sig"))
assert manifest["canonical_navigation"]["engineering_case_studies"]=="docs/tutorials/case-studies/index.html"
assert "docs/tutorials/case-studies/pycubrid-367.html" in manifest["case_study_tutorials"]
print({"case_studies":"PASS","public_sanitization":"PASS","links":"PASS","search":"PASS","sitemaps":"PASS","manifest":"PASS"})
