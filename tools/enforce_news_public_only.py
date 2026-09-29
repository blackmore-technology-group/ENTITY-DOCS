#!/usr/bin/env python3
"""Enforce NEWS as a public-GitHub-only publication surface.

This gate deliberately performs repository visibility checks WITHOUT GitHub
authentication. Anything that is only visible to the workflow token is treated as
non-public and removed before NEWS data or feeds can be committed.

The gate also handles a repository that was public when first observed but later
became private: retained NEWS history for that repository is removed on the next
successful sync rather than preserving a stale public reference.
"""
from __future__ import annotations

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
NEWS_JSON = ROOT / "docs" / "news" / "activity.json"
ROOT_FEED = ROOT / "docs" / "feed.xml"
NEWS_FEED = ROOT / "docs" / "news" / "feed.xml"
BASE_SITE = "https://blackmore-technology-group.github.io/ENTITY-DOCS"

# Intentionally no Authorization header. This is the core privacy invariant.
PUBLIC_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "BTG-ENTITY-DOCS-public-news-privacy-gate/1.0",
    "X-GitHub-Api-Version": "2022-11-28",
}

_GITHUB_REPO_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/([^/?#\s]+)/([^/?#\s]+)",
    re.IGNORECASE,
)


def public_api(path: str) -> Any:
    req = urllib.request.Request("https://api.github.com" + path, headers=PUBLIC_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        # Rate limits, outages, authorization surprises, etc. must not become a
        # reason to publish unverified state.
        raise RuntimeError("public GitHub visibility verification unavailable") from exc
    except Exception as exc:
        raise RuntimeError("public GitHub visibility verification unavailable") from exc


def public_owned_repositories() -> set[str]:
    result: set[str] = set()
    page = 1
    while True:
        query = urllib.parse.urlencode({
            "per_page": 100,
            "page": page,
            "type": "owner",
            "sort": "updated",
        })
        rows = public_api(f"/users/{urllib.parse.quote(ACCOUNT)}/repos?{query}")
        if not isinstance(rows, list):
            raise RuntimeError("public GitHub repository inventory verification failed")
        for row in rows:
            if row.get("private"):
                continue
            if row.get("visibility") not in (None, "public"):
                continue
            full_name = str(row.get("full_name") or "").strip().lower()
            if full_name:
                result.add(full_name)
        if len(rows) < 100:
            break
        page += 1
    if not result:
        raise RuntimeError("public GitHub repository inventory unexpectedly empty")
    return result


def normalize_repo(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip().removesuffix(".git")
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", value):
        return None
    return value


def github_repo_from_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = _GITHUB_REPO_URL.match(value.strip())
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2).removesuffix('.git')}"


def iter_strings(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)
    elif isinstance(value, str):
        yield value


def visibility_checker(owned_public: set[str]):
    cache: dict[str, bool] = {}

    def is_public(repo: str | None) -> bool:
        repo = normalize_repo(repo)
        if not repo:
            return False
        key = repo.lower()
        if key in cache:
            return cache[key]
        if key.startswith(ACCOUNT.lower() + "/"):
            value = key in owned_public
            cache[key] = value
            return value
        encoded = "/".join(urllib.parse.quote(part, safe="") for part in repo.split("/", 1))
        row = public_api(f"/repos/{encoded}")
        value = bool(
            isinstance(row, dict)
            and not row.get("private")
            and row.get("visibility") in (None, "public")
        )
        cache[key] = value
        return value

    return is_public


def record_is_public(record: dict[str, Any], is_public) -> bool:
    # Repository-bearing records must identify a repository and that repository
    # must be anonymously/publicly reachable.
    repo = normalize_repo(record.get("full_name") or record.get("repository"))
    if not repo or not is_public(repo):
        return False

    upstream = normalize_repo(record.get("upstream"))
    if upstream and not is_public(upstream):
        return False

    # Any direct GitHub URL embedded in the record must also resolve to a public
    # repository. This covers PR URLs and ENTITY evidence record URLs.
    for value in iter_strings(record):
        linked_repo = github_repo_from_url(value)
        if linked_repo and not is_public(linked_repo):
            return False

    # Defensive future-schema check.
    if record.get("private") is True:
        return False
    visibility = record.get("visibility")
    if visibility not in (None, "public"):
        return False
    return True


def atom_feed(items: list[dict[str, Any]]) -> str:
    selected = [i for i in items if i.get("occurred_at") and i.get("url")][:100]
    updated = selected[0]["occurred_at"] if selected else "1970-01-01T00:00:00Z"
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        '  <title>Blackmore Technology GitHub Footprint NEWS</title>',
        '  <subtitle>Factual public GitHub activity ledger: repositories, forks, releases, fixes, upstream contributions and ENTITY-ingested evidence.</subtitle>',
        f'  <link href="{BASE_SITE}/feed.xml" rel="self" type="application/atom+xml"/>',
        f'  <link href="{BASE_SITE}/news/" rel="alternate" type="text/html"/>',
        f'  <id>{BASE_SITE}/news/</id>',
        f'  <updated>{html.escape(str(updated))}</updated>',
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
    try:
        payload = json.loads(NEWS_JSON.read_text(encoding="utf-8-sig"))
        if payload.get("scope") != "PUBLIC_GITHUB_FOOTPRINT_ONLY":
            raise RuntimeError("NEWS payload does not declare the public-only scope")

        owned_public = public_owned_repositories()
        is_public = visibility_checker(owned_public)

        repositories = payload.get("repositories", [])
        items = payload.get("items", [])
        if not isinstance(repositories, list) or not isinstance(items, list):
            raise RuntimeError("NEWS payload shape invalid")

        safe_repositories = [
            row for row in repositories
            if isinstance(row, dict) and record_is_public(row, is_public)
        ]
        safe_items = [
            row for row in items
            if isinstance(row, dict) and record_is_public(row, is_public)
        ]

        removed_repositories = len(repositories) - len(safe_repositories)
        removed_items = len(items) - len(safe_items)

        # Do not print removed names or URLs. Private identifiers must never leak
        # through Action logs merely because the guard caught them.
        payload["privacy_boundary"] = (
            "Private, internal, deleted, or otherwise non-public repositories and activity "
            "are excluded from public output by anonymous GitHub visibility verification."
        )
        payload["privacy_enforcement"] = {
            "mode": "ANONYMOUS_PUBLIC_API_FAIL_CLOSED",
            "private_repository_names_logged": False,
            "removed_repository_records": removed_repositories,
            "removed_activity_items": removed_items,
        }
        payload["repositories"] = safe_repositories
        payload["items"] = safe_items

        forks = [r for r in safe_repositories if r.get("fork")]
        originals = [r for r in safe_repositories if not r.get("fork")]
        stats = payload.setdefault("stats", {})
        stats["public_repositories"] = len(safe_repositories)
        stats["original_public_repositories"] = len(originals)
        stats["public_forks"] = len(forks)
        stats["release_records"] = sum(
            1 for row in safe_items
            if row.get("type") == "RELEASE" and row.get("source") == "GITHUB_RELEASE"
        )
        stats["recent_external_prs"] = sum(1 for row in safe_items if row.get("type") == "EXTERNAL_FIX")
        stats["entity_evidence_records"] = sum(1 for row in safe_items if row.get("type") == "ENTITY_EVIDENCE")
        stats["activity_items"] = len(safe_items)

        # Final post-sanitization assertion before any file is written.
        if any(not record_is_public(row, is_public) for row in safe_repositories):
            raise RuntimeError("repository privacy assertion failed")
        if any(not record_is_public(row, is_public) for row in safe_items):
            raise RuntimeError("activity privacy assertion failed")

        NEWS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        feed = atom_feed(safe_items)
        ROOT_FEED.write_text(feed, encoding="utf-8")
        NEWS_FEED.write_text(feed, encoding="utf-8")

        print("NEWS_PUBLIC_ONLY_PRIVACY_GATE=PASS")
        print(f"PUBLIC_REPOSITORY_RECORDS={len(safe_repositories)}")
        print(f"PUBLIC_ACTIVITY_ITEMS={len(safe_items)}")
        print(f"REMOVED_NONPUBLIC_REPOSITORY_RECORDS={removed_repositories}")
        print(f"REMOVED_NONPUBLIC_ACTIVITY_ITEMS={removed_items}")
        return 0
    except Exception:
        # Intentionally generic: do not echo a potentially private repository name,
        # URL, API path, or title into public Actions logs.
        print("NEWS_PUBLIC_ONLY_PRIVACY_GATE=FAIL", file=sys.stderr)
        print("Publication stopped because public visibility could not be proven for all retained output.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
