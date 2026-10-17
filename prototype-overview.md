---
title: "SimpSec OmniChain — Prototype overview"
owner: SimpSec LLC
created: 2026-10-17
updated: 2026-10-17
version: "2.1.0"
status: working-scripted-prototype
classification: public
tags: [omnichain, prototype, overview, wiki]
---

# What OmniChain does

OmniChain shows how an attack can move from an untrusted document into an AI
assistant's connected tools. It records the attempt, compares defenses, and lets
a person choose a defense before a separate validation run checks it.

The current prototype is a local web app with one invoice scenario. Its default
mode uses scripted proposals and simulated tools. A hosted Gemma connection is
available in code, but live requests are disabled and have not been provider-tested.

## The question OmniChain answers

**Which tested defense stops the unauthorized behavior while still letting the
approved task finish?**

The answer comes from recorded actions and rule-based checks. A model's
recommendation or a high score alone does not show that a defense worked.

## Three parts, one evidence record

| Part | What it does | What you can review |
| --- | --- | --- |
| **OmniChain Attack** | Runs the sample scenario and follows the requests made through simulated tools. | The recorded steps, allowed or blocked actions, and any finding. |
| **OmniChain Optimize** | Tests three defenses from a fresh starting point and checks whether the approved tasks still work. This is the **Remediate** area in the app. | Results for each defense, failed checks, tradeoffs, and choices eligible for human selection. |
| **OmniChain Validate** | Runs separate tests against the exact settings a person selected. | Security and task results, matching settings, evidence checks, and confirmation that the mock state was restored. |

All three parts share a local SQLite evidence ledger: a linked history of the
tests and decisions. It supports the workflow; it is not a fourth engine or a
blockchain. These parts currently run within one local application.

## Follow the invoice attack

The approved task is simple: summarize a sample invoice and send the summary to
an approved internal recipient. Restricted account information is outside the task.

The malicious invoice contains a note claiming emergency approval. It asks the
assistant to read restricted fields and send the full record to an outside recipient.
This connects several steps: document input, a changed task, a data request, and
an attempted transfer. Prompt injection is the entry point to that chain.

The app records the requested actions and the tools' decisions. An attempted
action, a blocked action, and an allowed simulated action are different outcomes.
The chain view only shows supported observations. No real account data is read
and no real message is sent.

## Review and improve the result

**Attack** runs the scenario. **Evidence** lets you inspect what happened.
After a finding, **Remediate** compares three defenses: filtering known malicious
instructions, allowing only approved recipients, and limiting tools to the task.

Each comparison starts from fresh mock state and runs the same two attacks and
two ordinary tasks. Results show whether restricted actions were prevented and
whether the approved work still finished. Blocking delivery alone does not fix
an unauthorized read.

The remediation board organizes the review. A finished board item means its
review step finished; the separate validation result says whether checks passed.
Choose an eligible defense and record why you selected it. The app saves the
exact settings and preference profile with that decision.

## Check the chosen defense

**Validate** starts again from fresh state and runs a separate five-case suite,
including an additional ordinary task. It checks raw observations rather than
accepting the comparison's score as proof.

| Check | What it asks |
| --- | --- |
| Security | Were the restricted actions prevented? |
| Task completion | Did the approved work still succeed? |
| Selected settings | Were the exact approved settings tested? |
| Evidence | Are required records and files present and consistent? |
| State restoration | Was the mock starting state restored? |

**PASS** means all required checks passed within this suite. **FAIL** means a
required check failed. **INCONCLUSIVE** means the run or evidence was incomplete.
Preference weights cannot turn a failed required check into a pass.

## Inspect the evidence

Current results also check every linked source run and the frozen evaluation context.
Changed settings or evidence require a new assessment; old records stay available
as history. Task completion checks the actual delivered invoice ID and USD total.

SQLite stores events. Each event has an ID, sequence, source, recorded action or
decision, and links to relevant earlier events and files. SHA-256 hashes act as
digital fingerprints: a change to a record or file can break verification.

The app checks missing required events separately. An unbroken chain of hashes
alone cannot prove that everything was captured. Local administrators can also
rewrite the records and their checks together; this is not an independently
secured or immutable record system.

Select a moving block to inspect a captured event. The animation illustrates
existing records and does not indicate that another test is running. Export a
JSON bundle to inspect the linked assessment records outside the app. The fault
buttons test altered or missing evidence on copies, keeping the original run intact.

## What is available today

- A local Python web app, scripted attack, and simulated read/send tools.
- Three-control comparison, human selection, and separate validation.
- Local evidence storage, integrity and completeness checks, and JSON export.
- A hosted Gemma adapter with live requests disabled by default.

The recorded backend run passed 42 tests on the development PC with Python 3.14.
Live Gemma behavior, Windows ARM operation, broader attack coverage, production
deployment, and event eligibility remain unverified. JEV and HutchDB are not connected.

## Start here

- [Run the app and try the workflow](README.md).
- [Set up optional live AI](docs/live-ai-setup.md).
- [Review implementation status and observed checks](docs/implementation-status.md).
- [Read the detailed development plan](prototype-implementation-plan.md).
- [Read the original design requirements](prototype-design-spec.md).

The original requirements are preserved for development. Planned features in
those documents are not claims about what this release already does.

## Changelog

### 2.1.0 — 2026-10-17

Added the central question, the Attack/Optimize/Validate responsibilities, and an explanation of the shared evidence ledger.

### 2.0.0 — 2026-10-17

Rewrote the public overview in plain language, updated the implementation status,
and preserved the original specification in `prototype-design-spec.md`.
