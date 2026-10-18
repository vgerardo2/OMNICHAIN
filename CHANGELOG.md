---
title: "OmniChain — Public Preparation Changelog"
owner: SimpSec LLC
created: 2026-10-17
updated: 2026-10-17
version: "1.2.0"
classification: public-prototype-draft
---

# Public preparation changelog

## Remediation approval flow — 2026-10-17

- Rename the eligible control action to “Approve defense” and label the rationale field as an approval reason.
- After the human choice and exact settings are recorded, continue directly to the independent Validate phase; retain a clear continuation action for an already selected defense.

## Attack run explanation — 2026-10-17

- After an attack finishes, keep the user on the attack view and show a plain-language sequence of the untrusted instruction, observed tool requests, policy outcomes, and any approved task handoff.
- Add the same explanation above the evidence ledger, label raw JSON as technical details, and collapse it by default.
- Translate integrity verification into plain language, including names of missing required records.
- Explanations use recorded synthetic observations; mock sends are explicitly described as simulated and no real message or account data is implied.

## Parallax background update — 2026-10-17

- Matched the opening story to the workspace's drifting starfield and slowly animated teal-to-purple gradient.
- Made story panels translucent so the background remains visible during scroll transitions; respects reduced-motion settings.
- Updated the story controller to reuse the existing starfield layers. No assessment or evidence behavior changed.

## 1.1.0 — 2026-10-17

- Built local Python/SQLite Attack, matched control comparisons, human selection
  and independent validation with linked evidence and export verification.
- Connected the selected OmniChain UI to loopback APIs and captured records;
  removed illustrative static metrics from runtime rendering.
- Added explicit fixture mode and a bounded hosted Gemma adapter; live provider
  access has not been used or verified.
- Added backend/API tests and HTTP browser workflow checks; exact observed
  results and remaining work are in `docs/implementation-status.md`.
- Reviewed HutchDB source and documented auth/deployment/mutability findings.
- Preserved original plans, handoff history, visual concepts and transfer manifest.
  Owner authorized desktop build/new GitHub repo; authentication/push remains pending.

## 1.0.2 — 2026-10-17

- Added JEV attack-chain review plan with metadata, phased tasks, evidence gates, acceptance checks, notes and wiki.
- Linked the addendum from README, agent instructions and checkpoint; preserved original implementation-plan bytes and transfer manifest.
- Defined bounded semantic judgments, separate execution status, independent validation, failure modes and held-out evaluation.
- Documentation checks only: verified required sections/task IDs, local Markdown links and unchanged original plan digest. No JEV integration or runtime/model tests performed.

## 1.0.1 — 2026-10-17

- Added `prototype-overview.md` describing the entire public prototype without importing private product plans.
- Linked the overview in README, the fresh-chat prompt and AGENTS instructions; recorded the documentation addition in the checkpoint.
- Refreshed the transfer manifest for this expanded snapshot. Original implementation-plan bytes and all existing requirements remain unchanged.
- Verified local document links and final snapshot hashes; no application or model tests were performed for this documentation change.

## 1.0.0 — 2026-10-17

- Prepared an uncompressed laptop continuation folder; no application or private source migration was performed.
- Preserved the complete existing public phase plan without edits or requirement removal.
- Added one README/start prompt, compact AGENTS instructions, complete public handoff, Windows ARM setup, event readiness and current checkpoint.
- Recorded no-PC access, proposed hosted open-weight inference, separate honest replay mode, pending provider/budget/license decisions and unconfirmed event build timing.
- Added read-only diagnostics, explicit no-download virtual-environment preparation, transfer verification and per-file SHA-256 manifest.
- Added ignore rules for local secrets/environments/generated data; publication still requires per-file review.
- Validation: all three PowerShell scripts parsed; read-only diagnostics and CheckOnly setup ran under Windows PowerShell 5.1. Diagnostic Python/SQLite imports passed on the desktop, and CheckOnly did not create an environment.
- Validation: explicit setup created a fresh isolated desktop environment using bundled pip with no downloads, then checked it again without recreating it. The restricted sandbox's temporary-file access initially blocked ensurepip; the same bounded test succeeded with permitted temporary-file access. This is not an ARM laptop compatibility result.
- Validation: transfer-verifier checks passed for an intact snapshot and restored snapshot, and rejected changed bytes, a missing file, an unexpected file, path traversal and duplicate manifest paths. Compatibility fixes removed legacy PowerShell native-argument quoting and optional hashing-module assumptions.
- No application test results, live provider/model calls, laptop runtime validation or competition eligibility are implied by these preparation checks.


## GitHub publication checkpoint — 2026-10-17

This checkpoint supersedes earlier pending-login, no-remote and undecided-license notes.

- The owner created https://github.com/vgerardo2/OMNICHAIN as a public repository with an Apache 2.0 LICENSE, Python ignore rules and initial README.
- Preserved the owner's initial commit and LICENSE; combined ignore rules and retained the full prototype README.
- Pushed the prepared implementation and merge commit `2f8cb3f` to `main`; verified the same full commit ID with `git ls-remote`.
- Private product plans, credentials, runtime databases, reference media and local design snapshots remain excluded. Runtime evidence is not automatically uploaded to GitHub.
- Existing verification remains 23 passing tests and local browser workflow checks. This publication/documentation change did not rerun application tests, GitHub CI or live Gemma calls.
- Live inference remains disabled. JEV and HutchDB remain unconnected. ARM compatibility and event eligibility are not established by publication.


## Public language update — 2026-10-17

- Removed the interface design description from the README.
- Rewrote the README and prototype overview around the attack, evidence, defense review, and validation workflow.
- Preserved the original overview requirements in prototype-design-spec.md; the original implementation plan is unchanged.
- Moved optional live AI setup into docs/live-ai-setup.md and simplified visible app explanations and result labels without changing API identifiers or evaluation rules.
- Replaced preloaded sample scores with Not run until recorded results load.


## Public documentation and interface wording — 2026-10-17

The README and current overview explain the invoice attack chain, evidence, defense selection, and validation in plain language. Optional live setup is in docs/live-ai-setup.md. The original overview is preserved in prototype-design-spec.md; prior implementation checkpoints are in docs/development-status-history.md. The original implementation plan is unchanged. Public app labels have been simplified; API identifiers and evaluation rules are unchanged. JavaScript syntax and diff whitespace checks passed. Final browser verification is recorded with the publication result.


## Workflow breakdown — 2026-10-17

Added the central evaluation question and a plain-language Attack/Optimize/Validate table to the README and prototype overview. Explained that Optimize appears as Remediate in the app and that all three parts share the local SQLite evidence ledger. Current implementation status and limitations are unchanged. Documentation-only change; no application tests rerun.


## Plan QA — 2026-10-17

- Reviewed plans against backend, frontend, tests and release notes. Added docs/plan-qa.md with QA-01 through QA-12 and PT-01 through PT-18 coverage.
- Existing suite passed 23 tests in 22.519s. Isolated probes confirmed stale current validation status, missing useful-summary evaluation, and false-block unit mismatch; fixes remain pending.
- Updated continuation metadata, public status limitations and tracker links. Preserved original implementation-plan bytes. No runtime code changes or live provider requests.


## 0.3.0 — QA corrections — 2026-10-17

- Corrected stale current PASS, invoice-output evaluation, and false-block measurement units.
- Added context fingerprints, exact manifests, explicit evidence reconstruction, trial reset checks, job recovery, schema guards, capacity limits, and backups.
- Added numeric weight inputs, reduced-motion fallback, story illustrations, and recorded relationship inspection.
- Added 18 regression/API cases (41 total), a real scripted export generator, recovery guide, model-contract references, demo outline, and asset provenance inventory.
- Full expanded suite passed 41 tests in 94.584s. Live provider/JEV, ARM and full accessibility checks remain pending. Original plan and historical evidence were preserved.


## Final local release verification — 2026-10-17

- Final isolated suite: 42 tests passed in 93.805s, including malformed non-object evidence payloads.
- Clean committed checkout of `0f42875` passed its then-current 41 tests in 91.549s and verified the included export; final corruption regression is added in the follow-up commit.
- Browser workflow passed all five validation gates; comparison recovered across reload, numeric 99% was rejected and reset to 100%, and story invoice/evidence illustrations were present.
- Working app preserved older records and showed INCONCLUSIVE with a request to rerun under changed evaluation settings.
- Public maintained-document links resolved; explicit Git path/credential-pattern review found no issues. Backup/alternate-runtime/export patterns are now ignored.
- Original implementation plan SHA-256 remains d182cefede729159ac2bab2712c4e99a197bbeb084ef5b7c4a1a35d8f2efc1d9.
- Live model calls, ARM, full assistive-technology/contrast/zoom validation, full crash/near-full-disk matrix, timed rehearsal and unknown CSS attribution remain open. Previous GitHub CI at `4e00adb` succeeded; the new release CI result must be checked after push.

## Confirmed release checks — 2026-10-17

GitHub Actions verified code commit 44b68d68e589350789e8a13ac97546f6a460db0f: all four Python test jobs passed on Windows/Linux with Python 3.11/3.14. Run: https://github.com/vgerardo2/OMNICHAIN/actions/runs/39055424624. The final 42-test suite passed locally in 93.805s; the clean checkout passed its 41-test baseline and then the final added corruption case (0.572s), JavaScript syntax, and export verification. The working app at port 8765 completed a fresh version-two attack/comparison/selection/validation with PASS on all five gates. Older records remain preserved. No live provider calls occurred. This supersedes earlier pending-CI notes; ARM, complete accessibility, expanded crash/near-full-disk testing, timed rehearsal and unresolved CSS attribution remain open.
