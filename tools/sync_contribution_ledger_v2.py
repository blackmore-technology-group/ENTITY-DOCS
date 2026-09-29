#!/usr/bin/env python3
"""ENTITY contribution-ledger compatibility layer for v3.4.3 acceptance evidence.

This module leaves the existing synchronizer intact and extends its evidence discovery
to include both sealed upstream-acceptance receipts and portable public projections
published under evidence/bounty/**.

Portable projections deliberately omit workstation-local paths and point back to the
immutable sealed receipt by SHA-256. They are public evidence views, not replacements
for the sealed receipt bytes.
"""

from __future__ import annotations

import base64
import copy
import json
import sys
from typing import Any

import sync_contribution_ledger as ledger

ACCEPTANCE_SCHEMA = "entity-v343-external-contribution-upstream-accepted-receipt-v1"
PUBLIC_PROJECTION_SCHEMA = (
    "entity-v343-external-contribution-upstream-accepted-public-projection-v1"
)
ACCEPTANCE_SCHEMAS = {ACCEPTANCE_SCHEMA, PUBLIC_PROJECTION_SCHEMA}
ACCEPTANCE_SUFFIXES = (
    "-entity-upstream-accepted-receipt.json",
    "-entity-upstream-accepted-public-projection.json",
)

STATE_RANK = {
    "PREPARED": 10,
    "ENTITY_RECORDED": 20,
    "READY_FOR_REVIEW_RECORDED": 30,
    "UPSTREAM_ACCEPTED": 40,
    "UPSTREAM_ACCEPTED_RECORDED": 50,
    "SETTLED": 60,
}


def _decode_blob(item: dict[str, Any], ref: str, path: str) -> dict[str, Any] | None:
    blob = ledger.api(
        f"/repos/{ledger.ENTITY_REPO}/git/blobs/{item['sha']}",
        optional=True,
    )
    if not blob or blob.get("encoding") != "base64":
        return None

    try:
        raw = base64.b64decode(blob.get("content", "")).decode("utf-8-sig")
        parsed = json.loads(raw)
    except Exception as exc:
        print(f"WARN: cannot parse {path} at {ref}: {exc}", file=sys.stderr)
        return None

    return parsed if isinstance(parsed, dict) else None


def _parent_receipt_sha(receipt: dict[str, Any]) -> str:
    parent = receipt.get("parent_entity_receipt")
    if isinstance(parent, dict):
        return str(parent.get("sha256") or "")

    predecessor = receipt.get("predecessor")
    if isinstance(predecessor, dict):
        return str(predecessor.get("receipt_sha256") or "")

    event = receipt.get("event")
    if isinstance(event, dict):
        return str(event.get("parent_entity_receipt_sha256") or "")

    return ""


def _normalize_acceptance_receipt(receipt: dict[str, Any]) -> dict[str, Any] | None:
    schema = str(receipt.get("schema") or "")
    if schema not in ACCEPTANCE_SCHEMAS:
        return None

    event = receipt.get("event") if isinstance(receipt.get("event"), dict) else {}
    claims = receipt.get("claims") if isinstance(receipt.get("claims"), dict) else {}
    entity = receipt.get("entity") if isinstance(receipt.get("entity"), dict) else {}
    publication = (
        receipt.get("publication")
        if isinstance(receipt.get("publication"), dict)
        else {}
    )

    repository = str(receipt.get("repository") or event.get("repository") or "")
    issue_number = int(receipt.get("issue_number") or event.get("issue_number") or 0)
    pr_number = int(
        receipt.get("pr_number")
        or receipt.get("pull_request_number")
        or event.get("pr_number")
        or event.get("pull_request_number")
        or 0
    )

    contribution_class = str(
        receipt.get("contribution_class")
        or event.get("contribution_class")
        or "UNKNOWN"
    )

    realized_cash = receipt.get("realized_cash")
    if not isinstance(realized_cash, dict):
        realized_cash = claims.get("realized_cash")
    if not isinstance(realized_cash, dict):
        realized_cash = event.get("realized_cash")
    if not isinstance(realized_cash, dict):
        realized_cash = {}

    observed_at = str(
        receipt.get("observed_at_utc")
        or event.get("observed_at_utc")
        or ""
    )
    final_head = str(
        receipt.get("final_pr_head")
        or receipt.get("final_head_sha")
        or event.get("final_pr_head")
        or event.get("final_head_sha")
        or ""
    )

    atomic_root = str(
        receipt.get("atomic_root")
        or entity.get("atomic_root")
        or ""
    )
    exact_reconstruction = receipt.get("exact_reconstruction_verified")
    if exact_reconstruction is None:
        exact_reconstruction = entity.get("exact_reconstruction_verified", False)

    sealed_schema = str(publication.get("sealed_receipt_schema") or schema)
    sealed_receipt_sha = str(publication.get("sealed_receipt_sha256") or "")

    return {
        "record_version": 1,
        "record_id": None,
        "captured_at_utc": observed_at,
        "contribution_class": contribution_class,
        "contributor": {},
        "opportunity": {
            "external_repository": repository,
            "issue_number": issue_number,
            "advertised_or_expected_amount": 0,
            "currency": str(realized_cash.get("currency") or "USD"),
            "evidence_state": "UPSTREAM_ACCEPTED_RECORDED",
        },
        "economic": {
            "class": contribution_class,
            "realized_cash": realized_cash.get("amount", 0),
            "contingent_value": 0,
            "payment_settled": bool(claims.get("payment_settled", False)),
        },
        "upstream": {
            "pull_request": (
                f"https://github.com/{repository}/pull/{pr_number}"
                if repository and pr_number
                else ""
            ),
            "commit": final_head,
            "license": "UNKNOWN",
            "cla_status": "UNKNOWN",
        },
        "_entity_receipt_schema": sealed_schema,
        "_entity_evidence_schema": schema,
        "_entity_public_projection": schema == PUBLIC_PROJECTION_SCHEMA,
        "_entity_sealed_receipt_sha256": sealed_receipt_sha,
        "_entity_atomic_root": atomic_root,
        "_entity_exact_reconstruction_verified": bool(exact_reconstruction),
        "_entity_parent_receipt_sha256": _parent_receipt_sha(receipt),
    }


def _acceptance_records_for_ref(ref: str) -> list[dict[str, Any]]:
    root = ledger.branch_tree_sha(ledger.ENTITY_REPO, ref)
    if not root:
        return []

    bounty_tree = ledger.descend_tree(
        ledger.ENTITY_REPO,
        root,
        ["evidence", "bounty"],
    )
    if not bounty_tree:
        return []

    tree = ledger.api(
        f"/repos/{ledger.ENTITY_REPO}/git/trees/{bounty_tree}?recursive=1",
        optional=True,
    )
    if not tree:
        return []

    records: list[dict[str, Any]] = []

    for item in tree.get("tree", []):
        path = str(item.get("path") or "")
        if (
            item.get("type") != "blob"
            or not any(path.endswith(suffix) for suffix in ACCEPTANCE_SUFFIXES)
        ):
            continue

        parsed = _decode_blob(item, ref, path)
        if not parsed:
            continue

        rec = _normalize_acceptance_receipt(parsed)
        if rec is None:
            print(
                f"WARN: unsupported upstream acceptance evidence schema in {path} at {ref}",
                file=sys.stderr,
            )
            continue

        rec["_source_ref"] = ref
        rec["_source_path"] = f"evidence/bounty/{path}"
        rec["_source_record_url"] = (
            f"https://github.com/{ledger.ENTITY_REPO}/blob/"
            f"{ref}/evidence/bounty/{path}"
        )
        records.append(rec)

    return records


_original_records_for_ref = ledger.evidence_records_for_ref


def evidence_records_for_ref(ref: str) -> list[dict[str, Any]]:
    records = list(_original_records_for_ref(ref))
    records.extend(_acceptance_records_for_ref(ref))
    return records


def _key_for(rec: dict[str, Any]) -> tuple[str, int]:
    opportunity = rec.get("opportunity", {})
    return (
        str(opportunity.get("external_repository") or ""),
        int(opportunity.get("issue_number") or 0),
    )


def _state(rec: dict[str, Any]) -> str:
    return str(
        rec.get("opportunity", {}).get("evidence_state") or "PREPARED"
    ).upper()


def _merge_context(
    primary: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    merged = copy.deepcopy(primary)

    if not merged.get("record_id"):
        merged["record_id"] = fallback.get("record_id")

    contributor = merged.setdefault("contributor", {})
    fallback_contributor = fallback.get("contributor", {})
    for field in ("human_author", "corporate_contributor"):
        if not contributor.get(field):
            contributor[field] = fallback_contributor.get(field, "")

    upstream = merged.setdefault("upstream", {})
    fallback_upstream = fallback.get("upstream", {})
    if str(upstream.get("license") or "UNKNOWN").upper() == "UNKNOWN":
        upstream["license"] = fallback_upstream.get("license", "UNKNOWN")

    if str(upstream.get("cla_status") or "UNKNOWN").upper() == "UNKNOWN":
        fallback_cla = str(fallback_upstream.get("cla_status") or "UNKNOWN")
        if "PENDING" not in fallback_cla.upper():
            upstream["cla_status"] = fallback_cla

    for field in (
        "_bootstrap_issue_title",
        "_entity_experiment_url",
        "_entity_harness_url",
    ):
        if not merged.get(field) and fallback.get(field):
            merged[field] = fallback.get(field)

    return merged


def choose_latest(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: dict[tuple[str, int], dict[str, Any]] = {}

    for rec in records:
        key = _key_for(rec)
        if not key[0] or key[1] <= 0:
            continue

        old = chosen.get(key)
        if old is None:
            chosen[key] = rec
            continue

        new_is_entity = rec.get("_source_ref") != "bootstrap"
        old_is_entity = old.get("_source_ref") != "bootstrap"

        if new_is_entity and not old_is_entity:
            chosen[key] = _merge_context(rec, old)
            continue

        if old_is_entity and not new_is_entity:
            chosen[key] = _merge_context(old, rec)
            continue

        new_rank = STATE_RANK.get(_state(rec), 0)
        old_rank = STATE_RANK.get(_state(old), 0)

        if new_rank > old_rank:
            chosen[key] = _merge_context(rec, old)
            continue

        if new_rank < old_rank:
            chosen[key] = _merge_context(old, rec)
            continue

        if str(rec.get("captured_at_utc") or "") >= str(
            old.get("captured_at_utc") or ""
        ):
            chosen[key] = _merge_context(rec, old)
        else:
            chosen[key] = _merge_context(old, rec)

    return list(chosen.values())


ledger.evidence_records_for_ref = evidence_records_for_ref
ledger.choose_latest = choose_latest


if __name__ == "__main__":
    raise SystemExit(ledger.main())
