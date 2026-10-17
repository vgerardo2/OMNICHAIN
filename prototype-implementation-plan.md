---
title: "SimpSec OmniChain — Public Prototype Implementation Plan"
aliases:
  - OmniChain Prototype Roadmap
  - OmniChain Prototype Wiki
type: implementation-plan
project: SimpSec-OmniChain
owner: SimpSec LLC
created: 2026-10-17
updated: 2026-10-17
timezone: America/New_York
version: "1.0.0"
status: planned
implementation_status: not-started
classification: public-prototype-draft
publication_status: not-published
current_phase: PUB-00
next_task: PUB00-01
tags:
  - omnichain
  - hacktoberfest-2026
  - prototype
  - implementation-plan
  - handoff
---

# SimpSec OmniChain — Public Prototype Implementation Plan

## Purpose and current checkpoint

Build a self-contained, synthetic demonstration of adversarial AI security testing, remediation comparison, and independent validation. Work is divided into phases that can be resumed across sessions and usage limits. This plan covers the public prototype only.

| Checkpoint | Current state |
| --- | --- |
| Completed | Prototype implementation plan created |
| Current phase | PUB-00 — fixture and evaluation contract |
| Exact next task | PUB00-01 — define the synthetic authorized task, scenario, policy and expected outcomes |
| Code and tests | Not implemented; no runtime test results |
| Evidence ledger | Planned, not created |
| Runtime | Proposed Python package, SQLite, local web interface; support version to verify |
| Git / remote | Not initialized or configured by this task |
| License | Owner decision pending |
| Publication | Not performed; requires separate release review |

Before each work session, inspect actual files and the latest checkpoint. A planned outcome is not an observed test result. Update this document after each verified work unit.

## Prototype scope

The demonstration follows **scope authorization → Attack → Optimize → human selection → Validate → evidence report**. All three engines share one trusted tamper-evident ledger service. The ledger is not a fourth engine.

- **Attack:** process an inert synthetic document containing malicious instructions through a mock agent, observe attempted unauthorized reads or tool operations, and reconstruct evidence-supported stage relationships.
- **Optimize:** compare prompt filtering, destination allowlisting and scoped tool permissions against the same malicious and legitimate workflows from fresh baseline state.
- **Validate:** independently rerun the exact human-selected configuration, judge raw observations using a frozen oracle, and verify operational behavior, mandatory requirements, evidence and rollback.
- **Evidence:** record linked events and artifacts in SQLite; verify hashes, configuration identity, references, required events and run finalization.

Use fake data, mock tools and local fixtures. The mock message tool never transmits data externally. Display `SIMULATED ENVIRONMENT`. A real model and external services are not required. Do not execute fixture content as code or allow it to redefine authorization, oracle rules, ledger records or approvals.

Keep the prototype functional without private documents, private imports, personal vault paths or commercial infrastructure. Public documentation must describe the code actually built and tested.

## Build decisions to freeze

Use stable descriptive control IDs:

| ID | Control | Evaluation question |
| --- | --- | --- |
| `PUB-PROMPT-FILTER` | Deterministic, versioned filtering of documented malicious instruction patterns | Which seeded attempts are blocked, and which benign inputs or variants are affected? |
| `PUB-DESTINATION-ALLOWLIST` | Mock-tool destination policy | Are unapproved transfers denied while legitimate internal delivery works? |
| `PUB-SCOPED-TOOLS` | Task-bound read/send capability restrictions | Are unauthorized operations denied without breaking permitted work? |

Do not preassign a winner. Prompt filtering is a tested input transformation, not an AI assertion that a prompt is safe. Explicitly define whether policies also inspect protected fields and how internal delivery differs from unauthorized reads.

Proposed synthetic task: summarize a supplier invoice and deliver an approved summary to an internal mock recipient. A fake restricted field must not be read or transferred without authorization. Define at least three stages: document ingestion, instruction propagation into a requested tool action, and mock authorization/outcome. Record delegation, read attempts and send attempts as distinct observations where present. A stage may contain multiple events, and blocked paths need not execute later stages.

Proposed implementation: Python modules with standard-library SQLite, JSON, SHA-256 and unittest; one locally served HTML/CSS/JavaScript interface bound to loopback. Verify runtime support before declaring a minimum Python version. Keep package imports and runner, evaluator, validator and writer interfaces explicit. Logical separation in one process is not hardened process isolation.

## Phased implementation

Task statuses are `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE` or `DEFERRED`. Mark a task DONE only with an existing artifact and recorded verification. All implementation tasks below begin TODO. Timeboxes are estimates, not deadlines; preserve gates when splitting a phase across sessions.

### PUB-00 — Freeze the scenario and test contract

**Dependency:** none. **Suggested work unit:** one session for fixture/schema decisions.

- [ ] **PUB00-01:** Define the authorized task, synthetic assets, mock recipients, restricted fields, scope expiry, permitted operations and expected attack/benign outcomes.
- [ ] **PUB00-02:** Version the policy, baseline, original attack, attack variant, 2–4 legitimate workflows, oracle, three controls and expected-event manifest.
- [ ] **PUB00-03:** Define stable IDs, configuration/artifact hashes, resource limits, cancellation and error handling. Fix test definitions before candidate scoring.
- [ ] **PUB00-04:** Confirm local runtime/package layout and executable development commands; document actual supported versions.

**Outputs:** substantive fixtures, schemas and golden expectations. **Gate:** original attack and legitimate expectations are independently inspectable; malformed or expired scope cannot run. **Checkpoint:** fixture paths/versions, frozen expectations, next runner task.

### PUB-01 — Implement trusted evidence capture

**Dependency:** PUB-00.

- [ ] **PUB01-01:** Build the SQLite writer with atomic append, monotonic sequence, unique event IDs, correlation IDs, schema version and idempotent logical writes.
- [ ] **PUB01-02:** Define deterministic canonical serialization and genesis anchor; SHA-256 chain each event and reference exact artifact/configuration bytes by digest.
- [ ] **PUB01-03:** Implement read-only verification of event order, IDs, hashes, artifact existence/digests, required event checkpoints and finalization.
- [ ] **PUB01-04:** Keep payloads separate from small event envelopes. Append corrections as new events; prohibit application updates/deletions of prior events.

**Outputs:** ledger module, verifier, artifact storage and integrity tests. **Gate:** intact evidence verifies; changed, reordered, duplicated, substituted or missing evidence is detected. An internally valid truncated chain cannot pass completeness checks. **Checkpoint:** schema/serializer version, database/artifact paths and verifier command.

### PUB-02 — Implement Attack replay and reconstruction

**Dependency:** PUB-01.

- [ ] **PUB02-01:** Implement inert document fixtures and a deterministic mock agent/tool runner with scope and budget checks.
- [ ] **PUB02-02:** Record source provenance, requested operation, policy expectation, actual mock outcome, trust boundary and oracle verdict through the trusted writer interface.
- [ ] **PUB02-03:** Reconstruct stage links using direct invocation IDs and supported data lineage. Label inferred or unknown links; timestamps alone do not prove causality.
- [ ] **PUB02-04:** Run a vulnerable baseline, a legitimate workflow, malformed input, expired scope and unrelated-nearby-event cases.

**Outputs:** reproducible attack trace, evidence-backed finding and accessible event table. **Gate:** unauthorized attempt and actual simulated outcome are distinguished, benign activity is not falsely asserted malicious, and no outside action occurs. **Checkpoint:** run IDs, observed outcomes, fixture versions and unresolved links.

### PUB-03 — Implement Optimize experiments and metrics

**Dependency:** PUB-02.

- [ ] **PUB03-01:** Implement the three named controls as versioned configurations; keep the oracle and fixtures read-only to candidate code.
- [ ] **PUB03-02:** Reinitialize clean state for every candidate; run matched malicious and legitimate suites with exact configuration hashes.
- [ ] **PUB03-03:** Compute attack-prevention counts, legitimate task success, false blocks and matched processing latency from raw observations. Preserve failed, aborted and unknown trials.
- [ ] **PUB03-04:** Apply mandatory eligibility constraints before comparing feasible candidates. Exclude failed constraints and require review for unknowns.
- [ ] **PUB03-05:** Present raw tradeoffs and comparable Pareto alternatives. Add transparent weighted ranking only when inputs are complete and normalization is declared.

**Outputs:** three experiment packages and comparison data. **Gate:** identical frozen inputs reproduce outcome/eligibility decisions; no cross-candidate contamination; high preference score cannot rescue mandatory failure. Timing is measured separately and may vary. **Checkpoint:** candidate-to-run mapping, exact hashes, sample sizes and exclusions.

Metrics must retain numerators and denominators. Attack prevention is prevented prohibited-outcome trials divided by scored attack trials; authorized task success is successful legitimate tasks without prohibited side effects divided by scored legitimate tasks; false blocking is wrongly denied legitimate operations divided by assessed legitimate operations. Report unrun/unknown cases separately. Measure wall-clock latency against matched baseline tasks and label it measured runtime of a simulated workload. Estimated cost and maintenance need stated inputs; unknown values are not zero.

### PUB-04 — Build the comparison and configuration interface

**Dependency:** PUB-03.

- [ ] **PUB04-01:** Build the glass-style panel with readable contrast, native profile dropdown, sliders/numeric inputs, live values, total display, errors and reset.
- [ ] **PUB04-02:** Implement Small Business, Defense Contractor and Custom profiles using the table below.
- [ ] **PUB04-03:** Reject nonfinite, negative, out-of-range or non-100% weights in both UI and backend; no hidden normalization.
- [ ] **PUB04-04:** Show hard constraints, evidence drill-down, unknown measurements and simulation labels. Support keyboard access and non-color status cues.
- [ ] **PUB04-05:** Require an explicit human candidate selection and rationale bound to configuration/profile hashes before validation.

| Dimension | Small Business | Defense Contractor |
| --- | ---: | ---: |
| Security effectiveness | 40% | 50% |
| Implementation cost | 30% | 10% |
| Operational impact / continuity | 20% | 30% |
| Maintenance complexity | 10% | 10% |
| Total | 100% | 100% |

Custom values must total 100%. Reset restores the selected preset, or a documented default for Custom. Compliance/security conditions are hard eligibility gates, never sliders. The Defense Contractor preset does not establish regulatory or contractual compliance.

**Outputs:** working local interface and recorded selection. **Gate:** actual dropdown/sliders/reset work, invalid values are rejected server-side, and no eligible candidate is handled honestly. **Checkpoint:** UI command, verified interactions and selected hash or pending-selection status.

### PUB-05 — Independently Validate and test rollback

**Dependency:** PUB-04.

- [ ] **PUB05-01:** Load the selected hash and independent suite into fresh state. Recompute outcomes from trusted observations rather than optimizer claims.
- [ ] **PUB05-02:** Test original attack, variant, legitimate workflows, unauthorized action, timeout, missing evidence and modified configuration.
- [ ] **PUB05-03:** Reject forged optimizer success and missing/altered tests. Reject a tested patch that differs from the approved patch.
- [ ] **PUB05-04:** Emit separate security, operations, configuration, evidence and rollback verdicts plus an overall result.
- [ ] **PUB05-05:** Restore the mock baseline; verify its hash and behavior. Record human disposition without implying production authorization.

**Outputs:** independent validation report, negative-case evidence and rollback record. **Gate:** mandatory failure blocks PASS; insufficient evidence gives INCONCLUSIVE; a passing verdict binds to exact policy, fixtures, suite and configuration. If no candidate passes, retain that result. **Checkpoint:** suite versions, results, failures, evidence paths and reviewer status.

### PUB-06 — Integrate, document and rehearse

**Dependency:** PUB-05.

- [ ] **PUB06-01:** Run the acceptance matrix below, preserve failures, and verify the final evidence lineage from authorized scope through human disposition.
- [ ] **PUB06-02:** Test the complete path offline, cancellation/resource limits, safe rendering and interface accessibility.
- [ ] **PUB06-03:** Create one concise README with purpose, engines, supported runtime, tested installation/run/test commands, model/dependency disclosure, limitations and selected license.
- [ ] **PUB06-04:** Write only necessary architecture, security and testing notes. Produce sanitized examples from actual synthetic runs and an offline evidence export/verifier result.
- [ ] **PUB06-05:** Map observed scenario behavior to verified official STRIDE/OWASP/MITRE references where applicable; retain unsupported mappings as pending.
- [ ] **PUB06-06:** Rehearse a three-minute demo: approved task → attack evidence → three control results → human selection → independent validation → tamper/completeness checks → limitations.

**Outputs:** runnable standalone prototype, tests, useful documentation, sanitized evidence and demo script. **Gate:** clean local setup succeeds without private files or internet-dependent runtime services. Claims match tested behavior and coverage. **Checkpoint:** exact tested commands, environment, acceptance status and demo limitations.

### PUB-07 — Review the release candidate

**Dependency:** PUB-06. **Publication requires separate authorization.**

- [ ] **PUB07-01:** Resolve the public license with the owner and check actual dependency/asset license compatibility.
- [ ] **PUB07-02:** Review an explicit public-file allowlist for secrets, personal data, proprietary material, environment paths and synthetic-data provenance.
- [ ] **PUB07-03:** Inspect staged files and applicable history before any separately authorized commit; repeat standalone checks if release files change.
- [ ] **PUB07-04:** Record owner demo/release disposition and unresolved limitations. Never automatically push, create remotes or change repository visibility.

**Outputs:** reviewed release manifest and disposition. **Gate:** owner-approved license and disclosure review, functional standalone build and authorized next release action. **Checkpoint:** reviewed file set, checks, pending approvals and exact next action.

## Prototype acceptance matrix

| ID | Test | Expected outcome |
| --- | --- | --- |
| PT-01 | Synthetic malicious document against vulnerable baseline | Unauthorized attempt and simulated policy violation observable |
| PT-02 | Original attack and legitimate tasks against each of three controls | Raw results and tradeoffs recorded without invented winner |
| PT-03 | Repeated candidate replay | Clean baseline and equivalent deterministic outcomes |
| PT-04 | Malformed/expired/out-of-scope input | Rejected; no unauthorized action |
| PT-05 | Unrelated nearby events | No confirmed causal link from timing alone |
| PT-06 | Presets, Custom, invalid and nonfinite weights | Valid totals accepted; invalid profiles rejected |
| PT-07 | Failed mandatory constraint with high weighted score | Candidate ineligible |
| PT-08 | Forged optimizer PASS | Independent validator detects inconsistency |
| PT-09 | Approval hash A, tested hash B | Rejected; new review required |
| PT-10 | Legitimate regression after attack prevention | Operational failure; no overall PASS |
| PT-11 | Event/artifact mutation, reorder, duplication or substitution | Integrity verification fails |
| PT-12 | Required event/test/final marker missing | Incomplete result; never PASS |
| PT-13 | Intact finalized evidence and matching configuration | Integrity/completeness checks succeed, separately from security verdict |
| PT-14 | Mock rollback | Baseline hash and expected behavior restored |
| PT-15 | Offline end-to-end demo | No external mock-tool action or required model service |
| PT-16 | Interrupted/over-budget execution | Stops safely; partial evidence retained as INCONCLUSIVE |
| PT-17 | Attacker text attempts oracle/ledger/approval modification | Text remains data; protected authority unchanged |
| PT-18 | Public clean setup and evidence export | Runs without private paths; exported digests verify |

All tests currently **NOT RUN**. A verified ledger alone does not prove complete capture, trustworthy origins or effective security controls. Linked hashes cannot detect a privileged full rewrite without an independent trusted anchor. Describe the ledger as tamper-evident, not absolutely immutable.

## File layout and documentation rules

Create directories only when adding substantive code, tests or documentation; this layout is a target, not a scaffold already present:

```text
src/{attack,optimize,validate,evidence,shared}/
tests/{attack,optimize,validate,evidence,integration}/
docs/{architecture,security,testing}/
examples/{synthetic-attacks,remediation-options,validation-results}/
config/examples/
scripts/
.github/workflows/
pyproject.toml
.gitignore
LICENSE
README.md
prototype-implementation-plan.md
```

Use one public README. Add a workflow only with real commands. Ignore generated local output and secrets; review actual tracked files rather than relying on ignore rules. No placeholder outputs, unsupported success claims, model-generated evidence substitutes, or commercial-document copying.

## Usage-limit checkpoint and resume

Finish the smallest safe task before stopping. Save files and exact test results, update completed checkboxes and frontmatter, and fill the checkpoint below. An abrupt limit may prevent saving; the next session must inspect actual files before trusting the saved state. Interrupted runtime trials get a new run ID on rerun.

```markdown
### Session checkpoint — YYYY-MM-DD HH:mm America/New_York
- Phase / task:
- Completed artifacts and exact relative paths:
- Fixture / policy / oracle / suite / candidate versions and hashes:
- Commands run and observed results:
- Evidence paths / run IDs:
- Failed, unrun or inconclusive checks:
- Decisions and open questions:
- Active processes / incomplete work:
- Verified Git state, if applicable:
- Exact next task and completion check:
```

Copyable continuation prompt:

```text
Read prototype-implementation-plan.md in SimpSec-OmniChain. Inspect current
files and the latest checkpoint. Continue the first incomplete task in the
recorded phase; initially PUB00-01. Implement one bounded work unit, verify
its completion gate, preserve raw results, and update this plan/checkpoint.
Keep all fixtures synthetic, evaluation deterministic and validation
independent. Do not import private materials or publish without authorization.
```

## Wiki and implementation notes

- **Attack:** scoped reproduction plus evidence-supported reconstruction.
- **Optimize:** same-suite fresh-state comparison under fixed mandatory gates.
- **Validate:** independent evaluation of exact human-selected configuration.
- **Oracle:** frozen deterministic judgment of observable behavior.
- **Ledger:** ordered event records with linked hashes, artifacts and capture checks.
- **Hard constraint:** a required eligibility condition that preferences cannot override.
- **Pareto alternative:** a feasible option not dominated across all declared comparable objectives.
- **INCONCLUSIVE:** insufficient execution, evidence or coverage for a defensible verdict.
- **Framework references:** STRIDE; applicable OWASP LLM, Agentic, API and ASVS references; MITRE ATLAS and applicable ATT&CK. Verify identifiers/editions before formal mappings. No comprehensive coverage claim.
- **Scope note:** logical mock boundaries demonstrate an evaluation pipeline; they do not establish production isolation, compliance or general attack prevention.
- **Owner decisions remaining:** public license, supported runtime, frozen fixture expectations and eventual release authorization.

## Changelog

### 1.0.0 — 2026-10-17

- Created a standalone public prototype plan with metadata, three engines, SQLite evidence requirements, organization profiles and acceptance checks.
- Divided implementation into PUB-00 through PUB-07 with task IDs, dependencies, completion gates and resume checkpoints.
- Specified the three public controls: prompt filtering, destination allowlisting and scoped tool permissions.
- Added wiki notes, disclosure boundaries and usage-limit handoff instructions.
- Recorded all implementation and runtime verification as pending.
