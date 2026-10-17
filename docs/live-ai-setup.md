---
title: "OmniChain live AI setup"
owner: SimpSec LLC
updated: 2026-10-17
version: "1.0.0"
status: adapter-implemented-provider-testing-pending
tags: [omnichain, setup, gemma]
---

# Optional live AI setup

The default **Scripted demo** needs no API key. Live mode sends synthetic invoice
text to Google's hosted Gemma API so a real model can propose simulated actions.
The app still applies its own rules and records what the mock tools do.

Live requests are disabled by default. The adapter has only been tested with
simulated provider responses. No live attack result, provider speed, or cost has
been measured for this prototype.

## Before enabling it

Review Google's [Gemma API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
and [Gemma terms](https://ai.google.dev/gemma/terms). Check provider availability,
pricing, quota, and billing limits in your account. The adapter supports the
model IDs `gemma-4-26b-a4b-it` and `gemma-4-31b-it`; availability is subject to
the provider. Keep your key private and out of source code, browser code, and exports.

## Enable a bounded first request

Run these commands from the project folder in PowerShell. Enter your key only
in the local terminal prompt:

```powershell
$gemmaSecret = Read-Host 'Enter your API key locally' -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', $gemmaSecret).Password
$env:OMNICHAIN_ALLOW_LIVE = '1'
$env:OMNICHAIN_MAX_CALLS = '1'
$env:OMNICHAIN_GEMMA_MODEL = 'gemma-4-26b-a4b-it'
python -m omnichain
```

Choose **Live Gemma** in the app. Only synthetic invoice text is submitted.
The API key is sent in a request header, never in model input or recorded evidence.
Live mode does not add tools for real file access or message delivery.

The limit above permits one request during that server session. Failed requests
also count. The app does not retry automatically or replace a failed response
with a scripted result. Restarting the server resets the counter.

This request limit is not a spending limit. A full control comparison can use
16 requests and validation uses five more. With a one-request limit, later work
will stop and be reported as incomplete. Review your provider limits before
increasing it.

## Turn it off

Stop the server with Ctrl+C and close that terminal, or set
`$env:OMNICHAIN_ALLOW_LIVE = '0'` before restarting it. Environment variables apply
to the launching terminal session. The app does not load `.env` automatically;
`.env.example` is a reference for the variable names.
