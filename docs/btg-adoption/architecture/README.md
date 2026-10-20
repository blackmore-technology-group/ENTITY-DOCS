# System architecture

Public information edition 0.1 | 20 October 2026

# One economic architecture, separate responsibilities

BTG's proposed infrastructure joins personal contributions, research and the market without collapsing them into one unrestricted database.

| Layer | Intended responsibility | What it must not assume |
|---|---|---|
| BTG Bridge | Obtain opt-in contributions from supported, authorized sources | That app permissions confer resale rights |
| Personal FarmNode | Apply bounded private processing and approved research tasks | That every logical node is an independently isolated machine |
| NIKI / DataChips / Circuit Genomes | Investigate, assemble and test research capabilities | That a self-generated test proves independent validity |
| BTDU | Preserve authoritative inputs and reconstruct permitted knowledge views | That derived data escapes source restrictions |
| ENTITY / ADAM | Preserve provenance; check signatures, permissions and governed actions | That technical signatures confer legal ownership |
| Commercial rights market | Offer permitted licences to qualified customers | That a licence is an investment security |
| DCO investment services | Model securities issuance and legal investor entitlements | That simulation enables public trading |

## End-to-end intended flow

**Authorized source → BTG Bridge → permitted processing → evidence-qualified asset → ENTITY rights review → optional commercial publication → customer licensing or separately authorized investment instrument.**

The Bridge and farms should not write investor registers. A wallet display should not establish legal title. Public documents and non-identifying cryptographic commitments should be exported through a dedicated review process rather than a direct database connection.

## Release boundaries

- **Privacy boundary:** minimize sensitive input, protect third parties, allow data-subject requests where applicable and prohibit unauthorized public raw-data release.
- **Compute boundary:** independent isolation and resource limits are required for production multi-tenant FarmNodes; a list of logical farms alone does not prove runtime isolation.
- **Rights boundary:** an auditable provenance trail assists verification but must be backed by lawful contracts, permissions and ownership evidence.
- **Securities boundary:** primary offerings and secondary marketplace functions require their own legal assessments and approvals.

## Current status

Design architecture and local development evidence exist in BTG's October 2026 dossier. This public site does not assert that all services have been integrated, independently audited or deployed in production. The public assurance register identifies the relevant outstanding gates.
