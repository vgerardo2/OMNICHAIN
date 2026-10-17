# Live-model contract and remaining work

The current document-agent design uses **one model call to propose a bounded
action list and message summary**. Local code executes that list through mock
tools. The model does not receive read results in a second conversation turn.
This is the supported prototype protocol, not a closed-loop autonomous agent.
A future loop would need separately versioned turn budgets and tool-result lineage.

## Gemma reference check — 2026-10-17

Google's [Gemma API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
documents both configured Gemma 4 model IDs and the `generateContent` REST route.
The adapter uses that fixed host/route, sends a backend-only key, and accepts only
the local action schema. Its prompt/settings and source versions are included in
the approval context fingerprint. This documentation check is not a provider test.

Before live execution, confirm the account's model availability, terms, quota,
approved synthetic submission, and billing limits. Live mode stays disabled by
default. Refusals, errors, malformed output, and call-cap exhaustion are recorded
as observed failures or incomplete work; there is no silent scripted fallback.

## JEV reference check — 2026-10-17

The [TypeSafe introduction](https://docs.typesafe.ai/introduction) identifies Jev
as a structured decision model. Its [quick start](https://docs.typesafe.ai/introduction/quickstart)
documents `POST https://api.typesafe.ai/v1/systemone`, bearer authentication,
state plus typed questions, and the `jev-latest` alias. Choice answers include
probabilities and confidence; do not assume every question type returns the same fields.

No JEV request, SDK installation, credential setup, or inference integration has
been performed. The alias is not a pinned revision. The example revision in the
documentation is not proof that the same revision is available to this account.

The next JEV work is to freeze the question/response schema and labeled fixtures,
test a bounded adapter with a fake transport, and evaluate it only after explicit
provider setup and budget approval. Keep JEV judgments separate from observed
execution and deterministic outcomes. The existing [review plan](../jev-chain-review-plan.md)
remains the complete requirement set; reference verification does not mark its
seven implementation tasks complete.
