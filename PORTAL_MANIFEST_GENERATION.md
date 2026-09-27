# PORTAL_MANIFEST.json regeneration procedure

`PORTAL_MANIFEST.json` is machine-facing release/discovery metadata for the ENTITY documentation portal.

## Authoritative current fields

For each regeneration:

1. Resolve the current supported ENTITY release from the canonical `blackmore-technology-group/ENTITY` release record.
2. Record the release tag and the immutable release merge commit. Do not substitute the moving `main` head for the release commit.
3. Record the BTDU component version separately. For ENTITY v3.4.3, BTDU remains 3.4.2 unchanged.
4. Resolve the current default-branch head for every repository already included in `repository_heads` directly from GitHub.
5. Record the ENTITY-DOCS source commit used to perform the regeneration in `generated_from_docs_commit`.
6. Rebuild `docs/search-index.json` from current public navigation/discovery routes and set `curated_search_entries` to the exact number of entries in that JSON array.
7. Validate that every search-index URL resolves within the published portal.
8. Review the resulting diff through a pull request before merge.

## Generated reference inventory

The original v3.4.0 portal generator recorded:

- 599 file-reference pages;
- 1,922 symbol-reference pages;
- 2,603 total HTML pages.

The original generator is not currently present in this repository, so those values must **not** be relabeled as current counts. They are retained only under `historical_generated_reference_inventory` with the original source release/commit and an explicit historical status.

If a deterministic full-reference generator is restored, it may introduce a new current inventory section after reproducing counts from repository source state. Historical values must remain identifiable as historical rather than silently overwritten.

## Claim boundary

The manifest describes documentation/repository state. It does not alter ENTITY protocol semantics, runtime qualification, immutable release evidence, historical tags, or the active wall-clock qualification campaign.
