# Entrepreneurship Professor

Bert's personal-brand workspace for content, story research, audience insights,
partnerships, and a reusable teaching/story library. BOS coordinates Codex and
Claude through the existing private control plane.

## Run locally

Use Python 3 and Node.js. No dependency installation or build is required.

```sh
python3 tools/serve_ep.py --port 8000
```

The server serves only `dist` and binds loopback. The Audience page reads live
GoHighLevel accounts and checks analytics availability through server-side
adapters. Credentials remain in secure environment bindings. Existing sample
audience metrics and actions are labeled as previews.

Configure `GHL_ACCESS_TOKEN` securely and set
`GHL_LOCATION_ID=2cCtht46QwERbvs3uITM`. Account inventory requires
`socialplanner/account.readonly`; analytics additionally requires
`socialplanner/statistics.readonly`. The provider's statistics POST retrieves
data; it does not publish content. A denied analytics request does not invalidate
a successful account inventory. LinkedIn personal profiles are not supported by
GHL's aggregated analytics.

```sh
python3 tools/check_ghl_accounts.py
python3 tools/check_ghl_statistics.py
python3 -B -m unittest discover -s tests -v
for file in dist/*.js; do node --check "$file" || exit; done
git diff --check
```

Tests use synthetic credentials and responses. The optional BOS integration test
requires a read-only checkout of `Bert-bos/bos-workforce-orchestrator`; point
`BOS_REFERENCE_DIR` to it. Without that checkout, the existing-server integration
and schema comparison are reported as skipped. Live checks require the relevant
secure binding and network destination.

## Collaboration

Read [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md), and the
[collaboration setup](docs/COLLABORATION-SETUP.md). `tools/bos_handoff.py` returns
a supplied Worker Result to an existing, currently assigned BOS job. It does not
create jobs or approve releases. Live return requires `BOS_WORKER_KEY`, the
approved BOS origin, and current task/job/attempt identifiers.

See the [implementation evidence](docs/LIVE-INTEGRATION-IMPLEMENTATION.md) and
[CC completion instructions](docs/CC-INTEGRATION-COMPLETION.md). This server is
for local development; production remains behind the existing authenticated BOS
service and its deployment process.
