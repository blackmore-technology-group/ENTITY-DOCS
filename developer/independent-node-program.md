# ENTITY Independent Node Program

The **ENTITY Independent Node Program (INP)** is the public interoperability campaign for testing ENTITY-related object transport and lineage across independently operated devices.

## Purpose

The first campaign asks a narrower, falsifiable question than "does ENTITY work everywhere?":

> Can independently operated test nodes exchange the same object, preserve its origin hash across hops, append rather than rewrite lineage, reject object/hash tampering, and retain local evidence across restart and offline handoff?

The reference harness is intentionally small and standard-library-only so participants can inspect the entire transport surface before running it.

## Participate

Source and installation instructions:

https://github.com/blackmore-technology-group/ENTITY/tree/main/independent-node

Campaign specification:

https://github.com/blackmore-technology-group/ENTITY/blob/main/independent-node/TEST_CAMPAIGN.md

Privacy and safety:

https://github.com/blackmore-technology-group/ENTITY/blob/main/independent-node/PRIVACY.md

## Evidence levels

| Classification | Meaning |
| --- | --- |
| `BTG_CONTROLLED` | BTG controls every endpoint in the test |
| `EXTERNAL_REPRODUCTION` | an unrelated operator reproduces a published test, but multi-party independence is not established |
| `INDEPENDENT_MULTI_OPERATOR` | different unrelated operators control different endpoints in the exchange |

A PASS records the bounded behavior tested. It is not automatically a claim of full ENTITY conformance, legal ownership, external-world truth, economic value, payment, certification, or endorsement.

## Test sequence

INP-01 initialization/persistence → INP-02 two-device exchange → INP-03 three-device lineage → INP-04 tamper rejection → INP-05 restart/recovery → INP-06 offline handoff → INP-07 cross-platform exchange.

## What a useful failure looks like

Participants are encouraged to report the first reproducible mismatch: installation failure, byte/hash disagreement, lineage rewrite, tamper acceptance, restart loss, platform-specific behavior, or ambiguous instructions.

Negative results are engineering evidence and should not be hidden.

## Data economy relationship

An INP receipt can be ingested as evidence of a test contribution. The receipt can identify the test event, participating pseudonymous nodes, hashes, lineage depth and result. Recording a contribution does not itself assign ownership or monetary value. Any economic entitlement must be separately defined and evidenced.
