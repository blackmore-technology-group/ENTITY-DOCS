#!/usr/bin/env python3
"""Generate the public Blackmore Technology GitHub footprint NEWS ledger.

This is deliberately an engineering/activity ledger, not a marketing feed.
It only publishes public GitHub state. Private repositories are filtered out
before any output is written.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ACCOUNT = os.environ.get("BTG_GITHUB_ACCOUNT", "blackmore-technology-group")
ROOT = pathlib.Path(__file__).resolve().parents[1]
NEWS_DIR = ROOT / "docs" / "news"
OUT_JSON = NEWS_DIR / "activity.json"
OUT_FEED = ROOT / "docs" / "feed.xml"
OUT_NEWS_FEED = NEWS_DIR / "feed.xml"
CONTRIB = ROOT / "docs" / "evidence" / "contributions.json"
BASE_SITE = "https://blackmore-technology-group.github.io/ENTITY-DOCS"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
NOW = dt.datetime.now(dt.timezone.utc)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "BTG-ENTITY-DOCS-news-sync/1.0",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def iso(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("+00:00", "Z")


def api(path_or_url: str, params: dict[str, Any] | None = None) -> Any:
    if path_or_url.startswith("https://"):
        url = path_or_url
    else:
        url = "https://api.github.com" + path_or_url
    if params:
        query = urllib.parse.urlencode(params)
        url += ("&" if "?" in url else "?") + query
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"GitHub API {exc.code} for {url}: {body}") from exc


def repo_from_api_url(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"/repos/([^/]+/[^/]+)", url)
    return m.group(1) if m else None


def load_contributions() -> list[dict[str, Any]]:
    if not CONTRIB.exists():
        return []
    try:
        data = json.loads(CONTRIB.read_text(encoding="utf-8-sig"))
        rows = data.get("contributions", [])
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        print(f"WARN: contribution ledger unavailable: {exc}", file=sys.stderr)
        return []


def contribution_index(rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        repo = str(row.get("repository") or "").lower()
        prn = ((row.get("upstream") or {}).get("pull_request_number"))
        if repo and isinstance(prn, int):
            out[(repo, prn)] = row
    return out


def collect_repositories() -> list[dict[str, Any]]:
    repos = api(f"/users/{ACCOUNT}/repos", {"per_page": 100, "type": "owner", "sort": "updated"})
    if not isinstance(repos, list):
        raise RuntimeError("GitHub repositories response was not a list")
    public = []
    for r in repos:
        if r.get("private") or r.get("visibility") not in (None, "public"):
            continue
        row = {
            "name": r.get("name"),
            "full_name": r.get("full_name"),
            "url": r.get("html_url"),
            "description": r.get("description"),
            "fork": bool(r.get("fork")),
            "upstream": None,
            "archived": bool(r.get("archived")),
            "default_branch": r.get("default_branch"),
            "language": r.get("language"),
            "created_at": iso(r.get("created_at")),
            "updated_at": iso(r.get("updated_at")),
            "pushed_at": iso(r.get("pushed_at")),
        }
        if row["fork"] and row["full_name"]:
            try:
                detail = api(f"/repos/{row['full_name']}")
                parent = detail.get("parent") or {}
                row["upstream"] = parent.get("full_name")
            except Exception as exc:
                print(f"WARN: fork parent lookup failed for {row['full_name']}: {exc}", file=sys.stderr)
        public.append(row)
    return public


def collect_releases(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for repo in repos:
        full = repo.get("full_name")
        if not full:
            continue
        try:
            releases = api(f"/repos/{full}/releases", {"per_page": 10})
        except Exception as exc:
            print(f"WARN: release lookup failed for {full}: {exc}", file=sys.stderr)
            continue
        if not isinstance(releases, list):
            continue
        for rel in releases:
            when = rel.get("published_at") or rel.get("created_at")
            items.append({
                "id": f"release:{full}:{rel.get('id')}",
                "type": "RELEASE",
                "occurred_at": iso(when),
                "title": f"{full} released {rel.get('tag_name') or rel.get('name') or 'release'}",
                "summary": (rel.get("name") or rel.get("tag_name") or "GitHub release").strip(),
                "repository": full,
                "url": rel.get("html_url"),
                "status": "PUBLISHED",
                "source": "GITHUB_RELEASE",
                "entity_ingested": False,
                "entity_state": None,
            })
    return items


def collect_events() -> list[dict[str, Any]]:
    events = api(f"/users/{ACCOUNT}/events/public", {"per_page": 100})
    if not isinstance(events, list):
        return []
    items: list[dict[str, Any]] = []
    for ev in events:
        et = ev.get("type")
        repo = ((ev.get("repo") or {}).get("name"))
        payload = ev.get("payload") or {}
        when = iso(ev.get("created_at"))
        eid = ev.get("id")
        if et == "PushEvent":
            commits = payload.get("commits") or []
            for c in commits:
                sha = c.get("sha")
                msg = (c.get("message") or "commit").splitlines()[0]
                if not repo or not sha:
                    continue
                items.append({
                    "id": f"commit:{repo}:{sha}",
                    "type": "COMMIT",
                    "occurred_at": when,
                    "title": f"{repo}: {msg}",
                    "summary": f"Public commit {sha[:12]}",
                    "repository": repo,
                    "url": f"https://github.com/{repo}/commit/{sha}",
                    "status": "PUSHED",
                    "source": "GITHUB_PUBLIC_EVENT",
                    "entity_ingested": False,
                    "entity_state": None,
                })
        elif et == "ForkEvent":
            forkee = payload.get("forkee") or {}
            full = forkee.get("full_name")
            items.append({
                "id": f"fork:{eid}",
                "type": "FORK",
                "occurred_at": when,
                "title": f"Fork created: {full or repo}",
                "summary": f"Fork lineage from {repo}" if repo else "Public GitHub fork created",
                "repository": full,
                "upstream": repo,
                "url": forkee.get("html_url") or (f"https://github.com/{full}" if full else None),
                "status": "PUBLIC_FORK",
                "source": "GITHUB_PUBLIC_EVENT",
                "entity_ingested": False,
                "entity_state": None,
            })
        elif et == "CreateEvent":
            ref_type = payload.get("ref_type") or "repository"
            ref = payload.get("ref")
            label = f"{ref_type} {ref}" if ref else ref_type
            items.append({
                "id": f"create:{eid}",
                "type": "REPOSITORY_EVENT",
                "occurred_at": when,
                "title": f"{repo}: created {label}",
                "summary": "Public GitHub creation event",
                "repository": repo,
                "url": f"https://github.com/{repo}" if repo else None,
                "status": "CREATED",
                "source": "GITHUB_PUBLIC_EVENT",
                "entity_ingested": False,
                "entity_state": None,
            })
        elif et == "ReleaseEvent":
            rel = payload.get("release") or {}
            items.append({
                "id": f"release-event:{eid}",
                "type": "RELEASE",
                "occurred_at": when,
                "title": f"{repo}: release {rel.get('tag_name') or rel.get('name') or ''}".strip(),
                "summary": rel.get("name") or "Public GitHub release event",
                "repository": repo,
                "url": rel.get("html_url") or (f"https://github.com/{repo}/releases" if repo else None),
                "status": "PUBLISHED",
                "source": "GITHUB_PUBLIC_EVENT",
                "entity_ingested": False,
                "entity_state": None,
            })
        elif et == "PullRequestEvent":
            pr = payload.get("pull_request") or {}
            items.append({
                "id": f"pr-event:{pr.get('html_url') or eid}",
                "type": "PULL_REQUEST",
                "occurred_at": when,
                "title": f"{repo} PR #{pr.get('number')}: {pr.get('title') or ''}".strip(),
                "summary": f"GitHub PR event: {payload.get('action') or 'updated'}",
                "repository": repo,
                "url": pr.get("html_url"),
                "status": "MERGED" if pr.get("merged") else str(pr.get("state") or payload.get("action") or "UNKNOWN").upper(),
                "source": "GITHUB_PUBLIC_EVENT",
                "entity_ingested": False,
                "entity_state": None,
            })
    return items


def collect_external_prs(cidx: dict[tuple[str, int], dict[str, Any]]) -> list[dict[str, Any]]:
    q = f"type:pr author:{ACCOUNT}"
    search = api("/search/issues", {"q": q, "sort": "updated", "order": "desc", "per_page": 100})
    rows = search.get("items", []) if isinstance(search, dict) else []
    items: list[dict[str, Any]] = []
    for row in rows:
        repo = repo_from_api_url(row.get("repository_url"))
        if not repo or repo.lower().startswith(ACCOUNT.lower() + "/"):
            continue
        prn = row.get("number")
        if not isinstance(prn, int):
            continue
        merged = None
        merged_at = None
        head_sha = None
        try:
            detail = api(row.get("pull_request", {}).get("url") or f"/repos/{repo}/pulls/{prn}")
            merged = bool(detail.get("merged"))
            merged_at = detail.get("merged_at")
            head_sha = ((detail.get("head") or {}).get("sha"))
        except Exception as exc:
            print(f"WARN: PR detail lookup failed for {repo}#{prn}: {exc}", file=sys.stderr)
        evidence = cidx.get((repo.lower(), prn))
        state = "UPSTREAM_MERGED" if merged else ("UPSTREAM_OPEN" if row.get("state") == "open" else "UPSTREAM_CLOSED_UNMERGED")
        items.append({
            "id": f"external-pr:{repo}:{prn}",
            "type": "EXTERNAL_FIX",
            "occurred_at": iso(merged_at or row.get("updated_at") or row.get("created_at")),
            "title": f"{repo} PR #{prn}: {row.get('title') or ''}",
            "summary": "BTG-authored upstream pull request" + ("; ENTITY evidence recorded" if evidence else ""),
            "repository": repo,
            "url": row.get("html_url"),
            "status": state,
            "source": "GITHUB_PR_SEARCH",
            "head_sha": head_sha,
            "entity_ingested": bool(evidence),
            "entity_state": evidence.get("entity_evidence_state") if evidence else None,
            "entity_record_url": ((evidence or {}).get("source") or {}).get("record_url") if evidence else None,
        })
    return items


def contribution_items(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for row in rows:
        upstream = row.get("upstream") or {}
        issue = row.get("issue") or {}
        source = row.get("source") or {}
        repo = row.get("repository")
        prn = upstream.get("pull_request_number")
        when = upstream.get("merged_at") or row.get("captured_at_utc")
        econ = row.get("economic") or {}
        items.append({
            "id": f"entity-evidence:{row.get('record_id')}",
            "type": "ENTITY_EVIDENCE",
            "occurred_at": iso(when),
            "title": f"ENTITY recorded {repo} PR #{prn or '?'} as {row.get('entity_evidence_state') or 'evidence'}",
            "summary": f"{row.get('contribution_class') or 'CONTRIBUTION'}; payment_settled={str(bool(econ.get('payment_settled'))).lower()}; realized_cash={econ.get('realized_cash', 0)} {econ.get('currency', '')}".strip(),
            "repository": repo,
            "url": source.get("record_url") or upstream.get("pull_request") or issue.get("url"),
            "status": row.get("entity_evidence_state"),
            "source": "ENTITY_EVIDENCE",
            "entity_ingested": True,
            "entity_state": row.get("entity_evidence_state"),
            "entity_atomic_root": source.get("entity_atomic_root"),
            "sealed_receipt_sha256": source.get("sealed_receipt_sha256"),
            "exact_reconstruction_verified": source.get("exact_reconstruction_verified"),
        })
    return items


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {"ENTITY_EVIDENCE": 5, "GITHUB_PR_SEARCH": 4, "GITHUB_RELEASE": 3, "GITHUB_PUBLIC_EVENT": 1}
    by_id: dict[str, dict[str, Any]] = {}
    by_url: dict[str, dict[str, Any]] = {}
    for item in items:
        ident = item.get("id") or ""
        url = item.get("url") or ""
        if ident in by_id:
            old = by_id[ident]
            if priority.get(item.get("source"), 0) > priority.get(old.get("source"), 0):
                by_id[ident] = item
            continue
        if url and url in by_url and item.get("type") in {"PULL_REQUEST", "EXTERNAL_FIX", "RELEASE"}:
            old = by_url[url]
            if priority.get(item.get("source"), 0) > priority.get(old.get("source"), 0):
                old.update(item)
            continue
        by_id[ident] = item
        if url:
            by_url[url] = item
    rows = list(by_id.values())
    rows.sort(key=lambda x: x.get("occurred_at") or "", reverse=True)
    return rows[:500]


def atom_feed(items: list[dict[str, Any]]) -> str:
    selected = [i for i in items if i.get("occurred_at") and i.get("url")][:100]
    updated = selected[0]["occurred_at"] if selected else NOW.isoformat().replace("+00:00", "Z")
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        '  <title>Blackmore Technology GitHub Footprint NEWS</title>',
        '  <subtitle>Factual public GitHub activity ledger: repositories, forks, releases, fixes, upstream contributions and ENTITY-ingested evidence.</subtitle>',
        f'  <link href="{BASE_SITE}/feed.xml" rel="self" type="application/atom+xml"/>',
        f'  <link href="{BASE_SITE}/news/" rel="alternate" type="text/html"/>',
        f'  <id>{BASE_SITE}/news/</id>',
        f'  <updated>{html.escape(updated)}</updated>',
        '  <author><name>Blackmore Technology Group Limited</name></author>',
    ]
    for item in selected:
        title = html.escape(str(item.get("title") or item.get("type") or "GitHub activity"))
        url = html.escape(str(item.get("url")))
        iid = html.escape(str(item.get("id") or url))
        summary = html.escape(str(item.get("summary") or ""))
        when = html.escape(str(item.get("occurred_at")))
        out += [
            "  <entry>",
            f"    <title>{title}</title>",
            f"    <link href=\"{url}\"/>",
            f"    <id>urn:btg-github-news:{iid}</id>",
            f"    <updated>{when}</updated>",
            f"    <summary>{summary}</summary>",
            "  </entry>",
        ]
    out.append("</feed>")
    return "\n".join(out) + "\n"


def main() -> int:
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    contributions = load_contributions()
    cidx = contribution_index(contributions)
    repos = collect_repositories()
    if not repos:
        raise RuntimeError("Refusing to publish an empty repository footprint")
    releases = collect_releases(repos)
    events = collect_events()
    external_prs = collect_external_prs(cidx)
    entity_rows = contribution_items(contributions)
    items = dedupe(releases + events + external_prs + entity_rows)
    forks = [r for r in repos if r.get("fork")]
    originals = [r for r in repos if not r.get("fork")]
    payload = {
        "schema": "btg-github-footprint-news-v1",
        "generated_at_utc": NOW.isoformat().replace("+00:00", "Z"),
        "account": ACCOUNT,
        "scope": "PUBLIC_GITHUB_FOOTPRINT_ONLY",
        "privacy_boundary": "Private repositories and private activity are excluded from public output.",
        "editorial_boundary": "Engineering/activity ledger, not marketing copy. Source state controls status.",
        "stats": {
            "public_repositories": len(repos),
            "original_public_repositories": len(originals),
            "public_forks": len(forks),
            "release_records": len(releases),
            "recent_external_prs": len(external_prs),
            "entity_evidence_records": len(contributions),
            "activity_items": len(items),
        },
        "repositories": sorted(repos, key=lambda r: ((r.get("pushed_at") or ""), r.get("full_name") or ""), reverse=True),
        "items": items,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    feed = atom_feed(items)
    OUT_FEED.write_text(feed, encoding="utf-8")
    OUT_NEWS_FEED.write_text(feed, encoding="utf-8")
    print(json.dumps(payload["stats"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
