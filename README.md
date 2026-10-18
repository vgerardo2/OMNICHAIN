# SimpSec OmniChain

**Follow an AI attack across connected tools, compare defenses, and check the results.**

OmniChain is a local AI security prototype. Its example starts with an invoice
assistant that should send a summary to an approved recipient. A malicious note
inside the invoice tries to redirect the assistant: read restricted information,
then send it to someone else.

The app records what was requested, what the tools allowed or blocked, and whether
the approved task still worked. You can inspect the evidence, test three defenses,
choose one, and run a separate check of that exact choice.

All documents, account fields, recipients, and tool actions are simulated.
The default demo uses scripted actions, so it works without an AI account or API key.

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

## Run the demo

Install Python 3.11 or newer, open a terminal in this repository, and run:

```powershell
python -m omnichain
```

Open **http://127.0.0.1:8765** in your browser. Use this exact address.
Stop the app with Ctrl+C in the terminal.

The default demo needs no additional Python packages, Node, Docker, or model download.
It has been tested on the development PC with Python 3.14. Windows ARM has not
been tested. This app is intended to run on your own computer, not as a public server.

Records stay in the local `runtime/` folder, which Git ignores. Pushing code to
GitHub does not upload your run history. Use `--port 8766` to change the port or
`--data-dir ./runtime-other` to store a separate set of records.

## How it works

1. **Attack:** choose **Scripted demo** and **Run attack**. Follow the invoice note
   into requests to read restricted data and send it to an unapproved recipient.
2. **Evidence:** inspect each recorded request, rule decision, and simulated result.
   The moving blocks open recorded events; their motion does not represent new work.
3. **Remediate:** choose **Compare controls**. Each defense is tested from a fresh
   starting point against two attack cases and two ordinary tasks.
4. **Choose a defense:** review the results and explain your choice. A defense
   must meet the required security and task checks before you can select it.
5. **Validate:** choose **Validate selection**. A separate five-case test checks
   the exact settings you selected, the evidence, and restoration of the mock state.
6. **Review or export:** inspect the result and download its evidence as JSON.
   You can also test changed or missing records on copies without changing the originals.

## The three defenses

| Defense | What it checks |
| --- | --- |
| Prompt filtering | Looks for known malicious instruction patterns in the document. |
| Approved recipients | Limits where the simulated message tool can send information. |
| Task-only permissions | Limits the information and actions available to the task. |

A blocked message can still leave an unauthorized read. A filter can miss a
reworded attack or block ordinary content. OmniChain checks both the attack and
the legitimate work, rather than treating one blocked step as success.

Task success checks the delivered summary for the expected invoice ID and USD
total, the approved recipient, and absence of prohibited actions. Results show
counts for attacks prevented, tasks completed, and required legitimate actions
blocked by mistake. A filtered ordinary document counts as blocking its required
read and send; a model omitting an action is reported separately. Cost and maintenance are not measured, so the app
does not use them to declare a best defense. Preference sliders cannot override
a failed required check.

## Reading the result

- **PASS:** all required checks passed for this test suite and selected settings.
- **FAIL:** a required check failed.
- **INCONCLUSIVE:** the run or its evidence is incomplete.

SQLite stores the event history. Linked SHA-256 hashes help detect changed
records; separate checks look for missing records and files. These checks depend
on trusted local software and storage. Someone with full control of the computer
could rewrite the records and their checks together.

A passing demo does not establish security against every attack, production
readiness, or compliance.

## Optional live AI

A hosted Gemma adapter is included, but **live requests are disabled by default**.
It has been tested with simulated provider responses, not real Gemma requests.
The scripted demo does not show how a live model will behave.

See [live AI setup](docs/live-ai-setup.md) before enabling it. A live model can
propose only the supported simulated actions; it cannot read your files or send
real messages through the demo tools.

## Tests and further reading

```powershell
python -m unittest discover -s tests -v
python -m omnichain --verify-export .\omnichain-RUN-ID.json
```

The second command checks an exported evidence file; replace the filename with
your download. Read the [prototype overview](prototype-overview.md) for the
scenario and evidence checks, or the [implementation status](docs/implementation-status.md)
for tested features and remaining work.

The [public implementation plan](prototype-implementation-plan.md) describes
planned work; it is not a list of completed features. Internal design notes,
quality reviews, and handoff materials are maintained separately from this
public repository. JEV and HutchDB are not connected.

See the [implementation status](docs/implementation-status.md) for current
verification results and known limitations.

Additional guides:

- [Local storage, limits, backups, and recovery](docs/storage-and-recovery.md).
- [Live-model contract and verified documentation](docs/live-model-contracts.md).
- [Three-minute demo outline](docs/demo-walkthrough.md).
- [Asset provenance and outstanding attribution checks](docs/asset-provenance.md).
- [Genuine scripted validation export](examples/scripted-validation.json).

Check the example with `python -m omnichain --verify-export examples/scripted-validation.json`.
It is a recorded scripted run, not a live model result. Run a new assessment when
code, test rules, runtime, or model settings change; older records remain history.

## License

This repository includes the [Apache License 2.0](LICENSE).
