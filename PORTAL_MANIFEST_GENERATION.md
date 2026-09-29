# PORTAL_MANIFEST.json regeneration procedure

`PORTAL_MANIFEST.json` is machine-facing release, capability and discovery metadata for the ENTITY documentation portal.

## Authoritative current fields

For each regeneration:

1. Resolve the current supported ENTITY release from the canonical `blackmore-technology-group/ENTITY` release record.
2. Record the release tag and the immutable release merge commit. Do not substitute the moving `main` head for the release commit.
3. Record the BTDU component version separately. For ENTITY v3.4.3, BTDU remains 3.4.2 unchanged.
4. Resolve the current default-branch head for every repository already included in `repository_heads` directly from GitHub.
5. Record the ENTITY-DOCS source commit used to perform the regeneration in `generated_from_docs_commit`.
6. Preserve the canonical system definition and the five primitives from `docs/reference/capability-map.json` rather than reducing ENTITY to sovereignty, identity or provenance alone.
7. Preserve the implemented capability surfaces: governed objects/authority/rights, information topology, evidence, venues, instruments, balances, listings, disclosures, order books, call auctions, RFQs/quotes, trades, clearing, entitlements, usage, surveillance, cancellations, revenue rules, settlement-verifier authorization, payment attestations, economic participation and market recovery.
8. Preserve the ENTITY / BTDU / ADAM / NIKI responsibility boundaries documented in the canonical capability map.
9. Preserve current global-infrastructure/adoption surfaces: privacy/access controls, retention/destruction, federated/offline topology, causal partition recovery, crypto-suite migration, passports, provider-neutral custody/connectors, standards adapters and industry implementation packages.
10. Keep bounded engineering results explicitly scoped: the controlled BTDU benchmark measured 97% lower storage requirements; the qualified destruction/cold-recovery campaign achieved 100% exact reconstruction for the tested campaign, including Memnox 865/865 tracked blobs plus archive, manifest and acceptance proof without original workspace/Git/GitHub/network.
11. Keep real-world contribution states current: accepted cases and active cases must be sourced from the public ENTITY evidence/ledger, and upstream acceptance must not be converted into payment or ownership claims.
12. Preserve `docs/tutorials/` as a first-class learning surface. At minimum retain the tutorial hub plus the canonical learning path for Entity identity/signing, BTDU ingest/reconstruction, rights-market lifecycle, provider-independent recovery and external contribution lineage.
13. Keep tutorial instructions grounded in current public interfaces. Tutorial commands/API names must be sourced from the current identity API, BTDU CLI/continuous-ingestion API, exchange adoption surface, market-recovery documentation and public evidence model rather than invented convenience commands.
14. Rebuild `docs/search-index.json` from current public navigation/discovery routes and set `curated_search_entries` to the exact number of entries in that JSON array. Runtime overlays in `docs/assets/app.js` may add canonical capability/tutorial entries before the next static rebuild; list those separately in `runtime_discovery_overlays`.
15. Validate that every search-index, tutorial and canonical capability-map URL resolves within the published portal.
16. Validate discovery routing through `docs/sitemap-site.xml`, `docs/robots.txt`, `docs/llms.txt`, `docs/assets/site.js` and `docs/assets/app.js`; Tutorials and the canonical capability map must remain reachable from both public site-shell pages and deep documentation pages.
17. Validate that the homepage, Tutorials, Technology, Economy, Developer, Evidence, Protocol, Operator, Security, Research, Partners and Reference entry points describe ENTITY consistently with the canonical capability definition.
18. Review the resulting diff through a pull request before merge when the normal repository workflow requires one.

## Canonical capability source

The primary human and machine-readable system definitions are:

- `docs/reference/capability-map.html`
- `docs/reference/capability-map.json`

These files are the documentation-level source of truth for the high-level system inventory. They do not supersede implementation source, signed records, release manifests, protocol schemas, external upstream evidence or settlement attestations for their respective claims.

The portal should consistently describe ENTITY as a **provider-independent digital authority, information, evidence, market, economic and recovery operating fabric**. Sovereignty remains an important invariant of that fabric but must not be used as a shorthand that erases the market/economic, information, evidence or recovery layers.

## Tutorial source boundary

The tutorial hub is `docs/tutorials/index.html`. Tutorials are task-oriented learning material; they do not replace the canonical API/reference pages. Where a tutorial uses a command, method, route or state name, the corresponding developer/operator/source reference remains authoritative. Tutorial examples must preserve fail-closed behavior and the same authority, rights, provenance, settlement and recovery boundaries as the implementation.

## Public evidence publication boundary

The public contribution ledger may use portable public projections rather than path-bearing local receipts. A projection is a public disclosure view, not replacement sealed evidence. It must remain anchored to the authoritative sealed receipt using the recorded receipt SHA-256 / ENTITY atomic root and preserve the actual upstream and economic state without creating new rights, payment, ownership or settlement claims.

## Generated reference inventory

The original v3.4.0 portal generator recorded:

- 599 file-reference pages;
- 1,922 symbol-reference pages;
- 2,603 total HTML pages.

The original generator is not currently present in this repository, so those values must **not** be relabeled as current counts. They are retained only under `historical_generated_reference_inventory` with the original source release/commit and an explicit historical status.

If a deterministic full-reference generator is restored, it may introduce a new current inventory section after reproducing counts from repository source state. Historical values must remain identifiable as historical rather than silently overwritten.

## Claim boundary

The manifest describes documentation/repository state. It does not alter ENTITY protocol semantics, runtime qualification, immutable release evidence, historical tags, upstream licences/ownership, external settlement evidence, or the active wall-clock qualification campaign.
