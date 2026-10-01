from pathlib import Path
from html.parser import HTMLParser
import json

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/"docs"
CASE=DOCS/"tutorials"/"case-studies"
case_pages=sorted(CASE.glob("*.html"))
pages=case_pages+[DOCS/"tutorials"/"index.html",DOCS/"tutorials"/"external-contribution-lineage.html"]
forbidden=["ChatGPT","assistant prompts","chat transcript","E:\\ENTITY_ACTIVE"]
for page in pages:
    text=page.read_text(encoding="utf-8-sig")
    bad=[term for term in forbidden if term in text]
    if bad: raise SystemExit(f"FORBIDDEN_PUBLIC_META {page}: {bad}")
    if "\ufffd" in text: raise SystemExit(f"REPLACEMENT_CHAR {page}")
for page in case_pages:
    if page.name=="index.html": continue
    text=page.read_text(encoding="utf-8-sig")
    for required in ["<video", ".webm", ".mp4", "transcripts/"]:
        if required not in text: raise SystemExit(f"CASE_STUDY_MEDIA_MISSING {page}: {required}")

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]; self.sources=[]
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if tag=="a" and data.get("href"): self.hrefs.append(data["href"])
        if tag=="source" and data.get("src"): self.sources.append(data["src"])
for page in pages:
    parser=Links(); parser.feed(page.read_text(encoding="utf-8-sig"))
    for href in parser.hrefs+parser.sources:
        clean=href.split("#",1)[0].split("?",1)[0]
        if not clean or clean.startswith(("http://","https://","mailto:","javascript:")): continue
        target=(page.parent/clean).resolve()
        if clean.endswith("/"): target=target/"index.html"
        if not target.exists(): raise SystemExit(f"BROKEN_LINK {page}: {href} -> {target}")
search=json.loads((DOCS/"search-index.json").read_text(encoding="utf-8-sig"))
search_urls={row.get("url") for row in search}
expected=["tutorials/case-studies/"]+[f"tutorials/case-studies/{p.name}" for p in case_pages if p.name!="index.html"]
for url in expected:
    if url not in search_urls: raise SystemExit(f"SEARCH_MISSING {url}")
    for sitemap in ["sitemap.xml","sitemap-site.xml"]:
        if url not in (DOCS/sitemap).read_text(encoding="utf-8-sig"): raise SystemExit(f"SITEMAP_MISSING {sitemap}: {url}")
manifest=json.loads((ROOT/"PORTAL_MANIFEST.json").read_text(encoding="utf-8-sig"))
assert manifest["canonical_navigation"]["engineering_case_studies"]=="docs/tutorials/case-studies/index.html"
for p in case_pages:
    if p.name!="index.html": assert f"docs/tutorials/case-studies/{p.name}" in manifest["case_study_tutorials"]
print({"case_studies":"PASS","public_sanitization":"PASS","media":"PASS","links":"PASS","search":"PASS","sitemaps":"PASS","manifest":"PASS"})
