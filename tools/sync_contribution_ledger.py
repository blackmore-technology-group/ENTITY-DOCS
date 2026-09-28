#!/usr/bin/env python3
"""Build the public ENTITY contribution ledger from ENTITY evidence + live GitHub state.

The ENTITY evidence record remains the source of truth for recorded lineage/economic state.
Live GitHub data is used only for current upstream observations such as PR state,
review state, CI state and merge status. The script never upgrades ENTITY evidence
state or economic state on its own.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API = "https://api.github.com"
ENTITY_REPO = os.environ.get("ENTITY_SOURCE_REPO", "blackmore-technology-group/ENTITY")
ENTITY_REFS = [r.strip() for r in os.environ.get(
    "ENTITY_SOURCE_REFS", "main,experiment/bounty-lineage-v343"
).split(",") if r.strip()]
BOOTSTRAP = Path(os.environ.get("CONTRIBUTION_BOOTSTRAP", "tools/contribution-bootstrap.json"))
OUTPUT = Path(os.environ.get("CONTRIBUTION_OUTPUT", "docs/evidence/contributions.json"))
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
USER_AGENT = "ENTITY-DOCS-contribution-ledger/1.0"


def api(path: str, *, optional: bool = False) -> Any:
    url = path if path.startswith("http") else API + path
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        if optional:
            print(f"WARN: GitHub lookup failed: {url}: {exc}", file=sys.stderr)
            return None
        raise


def branch_tree_sha(repo: str, ref: str) -> str | None:
    q = urllib.parse.quote(ref, safe="")
    branch = api(f"/repos/{repo}/branches/{q}", optional=True)
    if not branch:
        return None
    return branch.get("commit", {}).get("commit", {}).get("tree", {}).get("sha")


def descend_tree(repo: str, tree_sha: str, path_parts: list[str]) -> str | None:
    current = tree_sha
    for part in path_parts:
        tree = api(f"/repos/{repo}/git/trees/{current}", optional=True)
        if not tree:
            return None
        match = next((x for x in tree.get("tree", []) if x.get("path") == part and x.get("type") == "tree"), None)
        if not match:
            return None
        current = match.get("sha")
    return current


def evidence_records_for_ref(ref: str) -> list[dict[str, Any]]:
    root = branch_tree_sha(ENTITY_REPO, ref)
    if not root:
        return []
    bounty_tree = descend_tree(ENTITY_REPO, root, ["evidence", "bounty"])
    if not bounty_tree:
        return []
    tree = api(f"/repos/{ENTITY_REPO}/git/trees/{bounty_tree}?recursive=1", optional=True)
    if not tree:
        return []

    records: list[dict[str, Any]] = []
    for item in tree.get("tree", []):
        path = item.get("path", "")
        if item.get("type") != "blob" or not path.endswith("/bounty_record.json"):
            continue
        blob = api(f"/repos/{ENTITY_REPO}/git/blobs/{item['sha']}", optional=True)
        if not blob or blob.get("encoding") != "base64":
            continue
        try:
            raw = base64.b64decode(blob.get("content", "")).decode("utf-8-sig")
            rec = json.loads(raw)
        except Exception as exc:
            print(f"WARN: cannot parse {path} at {ref}: {exc}", file=sys.stderr)
            continue
        rec["_source_ref"] = ref
        rec["_source_path"] = f"evidence/bounty/{path}"
        rec["_source_record_url"] = (
            f"https://github.com/{ENTITY_REPO}/blob/{ref}/evidence/bounty/{path}"
        )
        records.append(rec)
    return records


def load_bootstrap() -> list[dict[str, Any]]:
    if not BOOTSTRAP.exists():
        return []
    data = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    out = []
    for rec in data.get("contributions", []):
        out.append({
            "record_version": 0,
            "record_id": rec.get("record_id"),
            "captured_at_utc": rec.get("captured_at_utc"),
            "contribution_class": rec.get("contribution_class"),
            "contributor": {
                "human_author": rec.get("human_author", ""),
                "corporate_contributor": rec.get("corporate_contributor", ""),
            },
            "opportunity": {
                "external_repository": rec.get("external_repository"),
                "issue_number": rec.get("issue_number"),
                "advertised_or_expected_amount": rec.get("advertised_or_expected_amount", 0),
                "currency": rec.get("currency", ""),
                "evidence_state": rec.get("entity_evidence_state", "PREPARED"),
            },
            "economic": {
                "class": rec.get("contribution_class"),
                "realized_cash": rec.get("realized_cash", 0),
                "contingent_value": rec.get("contingent_value", 0),
            },
            "upstream": {
                "pull_request": rec.get("upstream_pull_request", ""),
                "commit": rec.get("upstream_commit", ""),
                "license": rec.get("license", "UNKNOWN"),
                "cla_status": rec.get("cla_status", "UNKNOWN"),
            },
            "_bootstrap_issue_title": rec.get("issue_title", ""),
            "_source_ref": "bootstrap",
            "_source_path": "tools/contribution-bootstrap.json",
            "_source_record_url": rec.get("source_record_url", ""),
            "_entity_experiment_url": rec.get("entity_experiment_url", ""),
            "_entity_harness_url": rec.get("entity_harness_url", ""),
        })
    return out


def key_for(rec: dict[str, Any]) -> tuple[str, int]:
    opp = rec.get("opportunity", {})
    return (str(opp.get("external_repository") or ""), int(opp.get("issue_number") or 0))


def choose_latest(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: dict[tuple[str, int], dict[str, Any]] = {}
    for rec in records:
        key = key_for(rec)
        if not key[0] or key[1] <= 0:
            continue
        old = chosen.get(key)
        if old is None:
            chosen[key] = rec
            continue
        new_is_entity = rec.get("_source_ref") != "bootstrap"
        old_is_entity = old.get("_source_ref") != "bootstrap"
        if new_is_entity and not old_is_entity:
            chosen[key] = rec
            continue
        if new_is_entity == old_is_entity and str(rec.get("captured_at_utc") or "") >= str(old.get("captured_at_utc") or ""):
            chosen[key] = rec
    return list(chosen.values())


def parse_pr_url(url: str) -> tuple[str, int] | None:
    m = re.match(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)(?:$|[/?#])", url or "")
    if not m:
        return None
    return m.group(1), int(m.group(2))


def discover_btq_pr(repo: str, issue_number: int) -> tuple[str, int] | None:
    timeline = api(f"/repos/{repo}/issues/{issue_number}/timeline?per_page=100", optional=True)
    if not isinstance(timeline, list):
        return None
    candidates = []
    for event in timeline:
        if event.get("event") != "cross-referenced":
            continue
        issue = event.get("source", {}).get("issue", {})
        if not issue.get("pull_request"):
            continue
        html = issue.get("html_url", "")
        parsed = parse_pr_url(html)
        if parsed:
            score = 1 if issue.get("user", {}).get("login") == "blackmore-technology-group" else 0
            candidates.append((score, parsed))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def review_state(repo: str, number: int) -> str:
    reviews = api(f"/repos/{repo}/pulls/{number}/reviews?per_page=100", optional=True)
    if not isinstance(reviews, list):
        return "UNKNOWN"
    latest: dict[str, str] = {}
    for review in reviews:
        user = review.get("user", {}).get("login") or str(review.get("id"))
        state = str(review.get("state") or "").upper()
        if state:
            latest[user] = state
    states = set(latest.values())
    if "CHANGES_REQUESTED" in states:
        return "CHANGES_REQUESTED"
    if "APPROVED" in states:
        return "APPROVED"
    if states:
        return "REVIEWED"
    return "PENDING"


def ci_state(repo: str, sha: str) -> tuple[str, dict[str, int]]:
    if not sha:
        return "UNKNOWN", {"total": 0, "success": 0, "failure": 0, "pending": 0, "skipped": 0}
    payload = api(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100", optional=True)
    runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    bad = {"failure", "cancelled", "timed_out", "action_required", "startup_failure", "stale"}
    ok = {"success", "neutral"}
    counts = {"total": len(runs), "success": 0, "failure": 0, "pending": 0, "skipped": 0}
    for run in runs:
        status = str(run.get("status") or "").lower()
        conclusion = str(run.get("conclusion") or "").lower()
        if status != "completed" or not conclusion:
            counts["pending"] += 1
        elif conclusion in bad:
            counts["failure"] += 1
        elif conclusion == "skipped":
            counts["skipped"] += 1
        elif conclusion in ok:
            counts["success"] += 1
        else:
            counts["pending"] += 1
    if counts["failure"]:
        return "FAIL", counts
    if counts["pending"]:
        return "PENDING", counts
    if counts["success"]:
        return "PASS", counts
    return "UNKNOWN", counts


def enrich(rec: dict[str, Any]) -> dict[str, Any]:
    opp = rec.get("opportunity", {})
    econ = rec.get("economic", {})
    up = rec.get("upstream", {})
    contributor = rec.get("contributor", {})
    repo = str(opp.get("external_repository") or "")
    issue_number = int(opp.get("issue_number") or 0)

    issue = api(f"/repos/{repo}/issues/{issue_number}", optional=True) or {}
    issue_title = issue.get("title") or rec.get("_bootstrap_issue_title") or f"Issue #{issue_number}"
    issue_url = issue.get("html_url") or f"https://github.com/{repo}/issues/{issue_number}"
    issue_state = str(issue.get("state") or "unknown").upper()

    pr_target = parse_pr_url(str(up.get("pull_request") or ""))
    if not pr_target:
        pr_target = discover_btq_pr(repo, issue_number)

    pr_data: dict[str, Any] = {}
    pr_repo = ""
    pr_number = 0
    pr_url = str(up.get("pull_request") or "")
    reviews = "UNKNOWN"
    checks = "UNKNOWN"
    check_counts = {"total": 0, "success": 0, "failure": 0, "pending": 0, "skipped": 0}
    technical = "ENTITY_RECORDED_ONLY"

    if pr_target:
        pr_repo, pr_number = pr_target
        pr_data = api(f"/repos/{pr_repo}/pulls/{pr_number}", optional=True) or {}
        pr_url = pr_data.get("html_url") or pr_url or f"https://github.com/{pr_repo}/pull/{pr_number}"
        reviews = review_state(pr_repo, pr_number)
        head_sha = pr_data.get("head", {}).get("sha") or str(up.get("commit") or "")
        checks, check_counts = ci_state(pr_repo, head_sha)
        if pr_data.get("merged_at"):
            technical = "UPSTREAM_ACCEPTED"
        elif str(pr_data.get("state") or "").lower() == "closed":
            technical = "CLOSED_UNMERGED"
        elif reviews == "CHANGES_REQUESTED":
            technical = "CHANGES_REQUESTED"
        elif reviews == "APPROVED" and checks == "PASS":
            technical = "REVIEW_APPROVED_CI_GREEN"
        elif reviews == "APPROVED":
            technical = "REVIEW_APPROVED"
        elif checks == "PASS":
            technical = "CI_GREEN"
        else:
            technical = "PR_OPEN"
    else:
        head_sha = str(up.get("commit") or "")

    entity_state = str(opp.get("evidence_state") or "PREPARED")
    return {
        "record_id": rec.get("record_id"),
        "record_version": rec.get("record_version"),
        "captured_at_utc": rec.get("captured_at_utc"),
        "source": {
            "kind": "ENTITY_EVIDENCE" if rec.get("_source_ref") != "bootstrap" else "BOOTSTRAP_FROM_ENTITY_PUBLIC_RECORD",
            "entity_ref": rec.get("_source_ref"),
            "path": rec.get("_source_path"),
            "record_url": rec.get("_source_record_url", ""),
            "experiment_url": rec.get("_entity_experiment_url", "https://github.com/blackmore-technology-group/ENTITY/issues/100"),
            "harness_url": rec.get("_entity_harness_url", "https://github.com/blackmore-technology-group/ENTITY/pull/102"),
        },
        "contributor": {
            "human_author": contributor.get("human_author", ""),
            "corporate_contributor": contributor.get("corporate_contributor", ""),
        },
        "repository": repo,
        "issue": {
            "number": issue_number,
            "title": issue_title,
            "url": issue_url,
            "state": issue_state,
        },
        "contribution_class": rec.get("contribution_class") or econ.get("class") or "UNKNOWN",
        "entity_evidence_state": entity_state,
        "economic": {
            "currency": opp.get("currency", ""),
            "advertised_or_expected_amount": opp.get("advertised_or_expected_amount", 0),
            "contingent_value": econ.get("contingent_value", 0),
            "realized_cash": econ.get("realized_cash", 0),
            "payment_settled": bool(econ.get("payment_settled", False)),
        },
        "rights": {
            "license": up.get("license", "UNKNOWN"),
            "cla_status_recorded": up.get("cla_status", "UNKNOWN"),
            "provenance_does_not_override_upstream_license": True,
        },
        "upstream": {
            "pull_request": pr_url,
            "pull_request_number": pr_number or None,
            "pull_request_state": str(pr_data.get("state") or "UNKNOWN").upper(),
            "merged": bool(pr_data.get("merged_at")),
            "merged_at": pr_data.get("merged_at"),
            "mergeable": pr_data.get("mergeable"),
            "head_sha": pr_data.get("head", {}).get("sha") or head_sha,
            "recorded_commit": up.get("commit", ""),
            "review_state": reviews,
            "ci_state": checks,
            "check_counts": check_counts,
            "live_technical_state": technical,
        },
    }


def main() -> int:
    records = load_bootstrap()
    entity_count = 0
    for ref in ENTITY_REFS:
        found = evidence_records_for_ref(ref)
        if found:
            print(f"INFO: found {len(found)} ENTITY evidence record(s) on {ref}")
            entity_count += len(found)
            records.extend(found)

    selected = choose_latest(records)
    enriched = [enrich(rec) for rec in selected]
    enriched.sort(key=lambda x: (str(x.get("captured_at_utc") or ""), x.get("record_id") or ""), reverse=True)

    new_core = {
        "schema_version": 1,
        "source_repository": ENTITY_REPO,
        "source_refs_checked": ENTITY_REFS,
        "entity_records_found": entity_count,
        "contributions": enriched,
    }

    old = None
    if OUTPUT.exists():
        try:
            old = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            old = None
    if old:
        old_core = dict(old)
        old_core.pop("generated_at_utc", None)
        if old_core == new_core:
            print("INFO: public contribution ledger is already current")
            return 0

    payload = dict(new_core)
    payload["generated_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"INFO: wrote {OUTPUT} with {len(enriched)} contribution(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
