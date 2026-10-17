---
title: "HutchDB — OmniChain Backend Fit Review"
owner: SimpSec LLC
created: 2026-10-17
updated: 2026-10-17
version: "1.0.0"
status: source-reviewed-not-deployed
repository: https://github.com/ExpeditedProjects/hutchdb
scope: public-prototype-backend
tags: [omnichain, backend, hutchdb, architecture, decision, wiki]
---

# Recommendation

Retain SQLite as the first prototype's authoritative evidence store. Consider HutchDB later as an optional shared remediation/read-model service behind OmniChain's backend. Do not give the document-processing model direct credentials for unrestricted Hutch mutation tools. No Hutch code has been copied, deployed, installed or connected by this review.

This is a targeted source review of files fetched from `main`, not a complete security audit or runtime verification. Main can change. Pin a repository commit and rerun checks before integrating.

## Fit for the current project

| Requirement | Reviewed capability | Assessment |
| --- | --- | --- |
| Durable task/candidate records | Postgres JSONB collections, optional schemas, queries, status changes | Useful for remediation collaboration |
| Shared agent working context | MCP collection/record operations | Useful behind a constrained server-side adapter |
| Existing OmniChain custom board | Core saves view definitions; README says the dashboard is Cloud-only | Core does not supply the visual board; keep the existing UI |
| Local portable demo | Node >=22.12 and Postgres; Docker deployment available | More setup and operational dependencies than Python + SQLite |
| Tamper-evident evidence | Ordinary mutable records and optional unique keys | Insufficient as the authoritative ledger without a separate protected design |
| Human configuration approval | General update/status operations | OmniChain must enforce actor, exact configuration digest, rationale and version rules |
| Independent validation | General storage, not the scenario oracle | Keep validation and raw-outcome evaluation in OmniChain |
| Offline operation | Possible with a working self-hosted Postgres deployment | Cloud service is not the required offline path |
| Source license | Repository LICENSE is GNU AGPL v3 | Record this before considering code reuse or a fork; keep HutchDB's AGPL obligations separate from this repository's Apache 2.0 license |

## Concrete source findings

1. **Core and Cloud are different products.** README describes a headless single-user Core. Its MCP service instruction text repeats that multi-user sharing and published dashboards live in Cloud. View types include table, kanban, calendar, gallery and timeline; a saved view definition is not a bundled board renderer.
2. **Authentication is optional by default.** `src/lib/auth/seam.ts` returns the singleton context when `HUTCH_API_KEY` is absent. When configured, a bearer token is checked with a timing-safe digest comparison. This protects entry to the Core endpoint; it is not separate reviewer, executor and approver identities.
3. **Compose needs verification before external access.** The reviewed `docker-compose.yml` maps `${HUTCH_PORT:-3000}:3000`, not a loopback-only host binding. Its explicit container environment does not include `HUTCH_API_KEY`. Setting that variable in the host shell alone does not establish that this Compose service passes it to the container. Add explicit key forwarding and a loopback binding before testing this configuration. The same file includes legacy-looking admin/session settings and a `/login` health check despite the headless Core description. Verify actual container health rather than assuming those settings are effective Core auth.
4. **Evidence can be overwritten through normal operations.** `hutch_store_records` defaults to `on_conflict: replace`. The records service reads an existing JSONB record by unique-key fields and then updates its data. Other registered tools include update, transform, delete and status changes. Soft deletion is still a visibility/capture issue for evidence reconstruction; it is not an append-only event contract.
5. **Application-level unique keys are not approval concurrency control.** In the reviewed create/upsert path, a matching record is selected and then updated. That path does not demonstrate a compare-and-swap revision gate for competing approval updates. A future integration must independently test concurrent writes and define version conflict behavior.
6. **MCP tool hints do not enforce security boundaries.** Store is marked non-destructive/idempotent even though the default conflict behavior can replace a matching record. Treat those hints as client metadata, not permission enforcement or a guarantee of harmless writes.
7. **Useful protections are present.** Source uses Zod tool inputs, collection-access service checks, bounded imports/exports and generic database errors at the MCP registration wrapper. These help, but do not establish OmniChain's scope, immutable history, completeness or independent validation requirements.

## Proposed optional integration

```text
Untrusted document → bounded Gemma proposal → local mock-tool enforcement
                                             |
                                  trusted evidence writer
                                             |
                         SQLite events + artifacts + verifier
                                             |
                              constrained projection adapter
                                             |
                         Hutch remediation records (optional)
                                             |
                             existing OmniChain Kanban UI
```

Use Hutch only for derived findings, review tasks, candidate summaries and collaboration status. Include assessment/run/event IDs, configuration digest, evidence head and projection version. Canonical evidence, expected-event manifests and approval records remain under OmniChain's trusted writer.

An adapter should allow only explicit collections and fields, reject caller-supplied collection names/queries/URLs, and omit evidence/approval/ledger mutation tools from model access. Approval requests must go through OmniChain's server with exact configuration and review identity. If a task's status changes in Hutch, append a reviewed event locally; never infer authorization from a mutable Done label.

Export only synthetic minimal records. Keep database URLs and bearer credentials server-side. Cloud hosting/account creation/data submission are separate choices; none occurred in this review.

## Verification required before adoption

- Pin a commit, reproduce dependency install/build and review lockfile/dependencies.
- Bring up an isolated Postgres/Core instance with a non-default bearer key and loopback binding.
- Test absent, wrong and correct credentials against MCP, including container environment propagation.
- Check health/readiness endpoints and whether the Compose sample matches the actual Core build.
- Verify allowed read/write operations and deny updates/deletes of canonical evidence.
- Test duplicate/upsert concurrency, retries and lost-update handling under the intended workload.
- Test projection replay, stale views, connection loss, cancellation and restoration without changing evidence.
- Record relevant source-license decisions before a fork or code reuse; hosted-service terms are separate.
- Demonstrate that a malicious document cannot update an approval, suppress a failed test or alter the source ledger through MCP.

All deployment, build, compatibility and integration checks above are NOT RUN. Repository maintenance/readme status is not independent evidence that this integration is production-ready.

## Sources and reviewed file versions

| Source | Blob SHA inspected |
| --- | --- |
| [README](https://github.com/ExpeditedProjects/hutchdb/blob/main/README.md) | `2630145102af3b341034c933eee619047d24fcc2` |
| [package.json](https://github.com/ExpeditedProjects/hutchdb/blob/main/package.json) | `8e3806c10b2ba4428c82f0a0ae8b3a2915f98668` |
| [Auth seam](https://github.com/ExpeditedProjects/hutchdb/blob/main/src/lib/auth/seam.ts) | `089580d4a4dab878e407086c42c410aaa8070d1c` |
| [MCP server](https://github.com/ExpeditedProjects/hutchdb/blob/main/src/lib/mcp/server.ts) | `6625429b205852000d838de9422d999e89ce8d21` |
| [Record service](https://github.com/ExpeditedProjects/hutchdb/blob/main/src/lib/services/records.ts) | `33b9204f348c19a066666bd94c2abfa95ee83ed5` |
| [Schema](https://github.com/ExpeditedProjects/hutchdb/blob/main/src/lib/db/schema.ts) | `d75b7012000ded507b86f4a717135951c3503bb8` |
| [Compose](https://github.com/ExpeditedProjects/hutchdb/blob/main/docker-compose.yml) | `0b4a5e3d7189dfa3ff8064c86e3e50cb673d3dca` |
| [Dockerfile](https://github.com/ExpeditedProjects/hutchdb/blob/main/Dockerfile) | `2e182e47fa2035de57e345231a9bcfee44db59ec` |
| [View types](https://github.com/ExpeditedProjects/hutchdb/blob/main/src/lib/views/types.ts) | `5380590ed62aad8166e0e262e71e7401e6f43bdf` |
| [License](https://github.com/ExpeditedProjects/hutchdb/blob/main/LICENSE) | `be3f7b28e564e7dd05eaf59d64adba1a4065ac0e` |

## Wiki and notes

- **Authoritative ledger:** trusted source for observed actions, approvals and verifiable completeness.
- **Projection:** a rebuildable view of source evidence; it may be stale or mutable without changing the original.
- **Core:** self-hosted headless MCP service; not a visual UI package.
- **Cloud:** separately operated product with additional UI/auth/sharing capabilities.
- **Decision:** SQLite core retained; Hutch integration is optional and not approved as a replacement.

## Changelog

### 1.0.0 — 2026-10-17

- Reviewed Core architecture, record mutations, authentication, deployment sample and license.
- Recommended an optional constrained projection instead of replacing canonical evidence storage.
- Recorded implementation risks, source identities and unrun integration checks.
