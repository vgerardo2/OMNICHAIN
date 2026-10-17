---
title: "OmniChain implementation status"
owner: SimpSec LLC
updated: 2026-10-17
version: "0.3.0"
status: working-scripted-prototype-live-testing-pending
tags: [omnichain, status, testing, wiki]
---

# Current status

OmniChain runs locally as a Python web app. It follows a simulated invoice attack,
records evidence, compares three defenses, saves a person's choice, and tests
that choice separately. The source is published at
[vgerardo2/OMNICHAIN](https://github.com/vgerardo2/OMNICHAIN) under the
[Apache License 2.0](../LICENSE).

## Available features

- Scripted invoice attack and a reworded attack, plus ordinary invoice tasks.
- Simulated read and send tools with three configurable defenses.
- Comparisons that reset the mock state before each test.
- A remediation board, review notes, and selection of a defense that passed the required checks.
- Separate five-case validation of the exact selected settings.
- SQLite event history, linked hashes, referenced JSON files, and checks for missing evidence.
- Evidence export and tests of changed or missing records on isolated copies.
- A local-only API with request validation, a session token, job limits, and cancellation.
- An optional hosted Gemma adapter, disabled by default.

The browser, test runner, and evidence storage share one local process. They are
separate parts of the workflow, not independently secured services.

## Recorded checks

The latest expanded backend test run used Python 3.14 on the development PC:

```text
python -m unittest discover -s tests -q
Ran 42 tests in 93.805s
OK
```

These tests covered mock-tool rules, human selection, validation, evidence
changes and omissions, exports, API checks, cancellation, and the model adapter
using simulated provider responses. No external model request was used.

Earlier local browser checks completed attack → evidence → comparison →
selection → validation, then checked saved results after reload and a copied
evidence fault. Layout was checked at widths of 1024, 736, 360, and 320 pixels,
with no JavaScript runtime errors observed. These are recorded development
checks, not a claim that every device or browser has been tested.

## Limits and remaining work

The three confirmed defects in the [plan QA review](plan-qa.md) now have regression
fixes: current verdicts verify linked dependencies, task completion checks the
delivered summary, and false blocks count required legitimate action opportunities.
Remaining graph, recovery, accessibility, live-provider, and release checks are
tracked separately; the full original plan is not claimed complete.

- Live Gemma responses, model resistance, provider speed, and actual cost have not been measured.
- Windows ARM operation has not been tested. There is no public hosted app.
- JEV and HutchDB are not connected. The [HutchDB review](hutchdb-backend-review.md) explains why SQLite remains the evidence store.
- The small synthetic suite does not establish protection against every attack, production readiness, compliance, or event eligibility.
- A person with full control of local storage can rewrite both the evidence and its checks.
- Cancellation waits for an active provider request to finish or time out. Interrupted runs can have incomplete evidence.
- The historical transfer manifest does not describe the current working tree.

## Continue development

Use the [README](../README.md) to start the app. Review the
[implementation plan](../prototype-implementation-plan.md) for detailed
requirements and the [live AI setup guide](live-ai-setup.md) before enabling a
provider. Keep API keys, runtime records, and private material out of source control.

The [development history](development-status-history.md) preserves earlier
checkpoints, failures, fixes, and publication notes. Older pending-login and
preparation-only statements there describe earlier work.

## Changelog

### 0.2.0 — 2026-10-17

Simplified the public status page and updated repository and license information.
Preserved the earlier technical checkpoint as development history.

## Public wording verification — 2026-10-17

JavaScript syntax and current public documentation links passed checks. The browser completed the updated scripted attack, evidence review, defense comparison, human selection, and separate validation with PASS and all five checks passed. No live model request was made. Backend rules and the original implementation plan were unchanged.


## QA correction implementation — 2026-10-17

- Added dependency-aware current verdicts and versioned execution fingerprints.
- Captured mock delivery contents/digests and checked bounded invoice output.
- Separated operation-level false blocks, failed tasks, and unrequested actions.
- Checked exact trial/test manifests, actual trial reset, and restored tool behavior.
- Added explicit invocation/data-use reconstruction with unresolved missing links.
- Persisted latest job status, bounded completed-job retention, and added interrupted-job recovery.
- Added schema compatibility checks, backup/restore checks, run/storage limits, and validation deadlines.
- Added numeric weight inputs, global reduced-motion fallback, story illustrations, and relationship inspection.
- Generated a real scripted validation bundle; provider, ARM, full accessibility, and asset clearance remain unverified.

The latest 41-test run supersedes the earlier 23-test baseline. An intermediate
run correctly failed its old false-block assertion after changing the measurement
unit; the assertion was updated to the specified action-level contract. Original
plan bytes and runtime history are preserved. See plan-qa.md for remaining work.

## Confirmed release checks — 2026-10-17

GitHub Actions verified code commit 44b68d68e589350789e8a13ac97546f6a460db0f: all four Python test jobs passed on Windows/Linux with Python 3.11/3.14. Run: https://github.com/vgerardo2/OMNICHAIN/actions/runs/39055424624. The final 42-test suite passed locally in 93.805s; the clean checkout passed its 41-test baseline and then the final added corruption case (0.572s), JavaScript syntax, and export verification. The working app at port 8765 completed a fresh version-two attack/comparison/selection/validation with PASS on all five gates. Older records remain preserved. No live provider calls occurred. This supersedes earlier pending-CI notes; ARM, complete accessibility, expanded crash/near-full-disk testing, timed rehearsal and unresolved CSS attribution remain open.
