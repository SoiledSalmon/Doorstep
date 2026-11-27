# Contributing to Doorstep

Two developers share this repo, split by language (see [the work split](docs/specs/work-split.md)):
**Person A** owns the TypeScript clients, **Person B** owns the Python services and data. Read the
[README](README.md) and [the design](docs/specs/design.md) first.

## Rules that must never break

These come from the design. Changing any of them needs team approval first.

- No personal data in the registry DB, logs, photos, exports or error messages. Identity lives only in the vault.
- Codes are issued by the server only after human review, never derived from location, never reused. Retired codes stay reserved.
- AI and heuristics never assign IDs or resolve duplicates; they only raise candidates for humans.
- Inferred data stays a candidate until a human verifies it.
- Mapper capture works fully offline. Every sync operation is idempotent.
- Never dial or text a real emergency number; use only the configured test number.
- Routing refuses rather than guesses (off-network, no route, no graph).
- Live updates use WebSockets (Quick Tunnels don't support SSE); clients reconnect and catch up by cursor, losing no event.
- Everything must run on free tiers.

## Workflow

- **Never commit to `main` directly.** Branch, open a PR, get the other person's review, merge, delete the branch.
- **Branch names:** `a/<workstream>-<topic>`, `b/<workstream>-<topic>`, or `docs/<topic>` for docs-only
  changes. Examples: `a/A3-sync-engine`, `b/B2-sync-push`.
- **Small PRs**, one task from your plan each, with its acceptance check passing. Tick the task in your plan
  in the same PR.
- **Cross-review is required** for anything touching `api/`, `fixtures/`, `docs/specs/` or `CONTRIBUTING.md`.
- Delete merged branches (GitHub does it on merge if "Automatically delete head branches" is on).

## The API contract

- [`api/openapi.yaml`](api/openapi.yaml) is the contract between clients and the core API;
  [`api/vault.yaml`](api/vault.yaml) is internal to the core API and the vault.
- **Contract first:** change the YAML in its own commit before the code that uses it, and tell the other person.
- Person A regenerates client types from it; generated files are never hand-edited.
- Prefer additions (new optional fields, new error codes) over changes; clients treat unknown error codes as
  generic failures.

## Tests

- Every edge case in [the catalogue](docs/specs/edge-cases.md) needs an automated test named after its ID:
  `test_SY03_replayed_op_applies_once` (Python), `it('DS-01 second SOS tap shows already sent')` (TypeScript).
- Cases marked *Manual* (GPS, airplane mode, devices) get a script in [`docs/manual-tests/`](docs/manual-tests/README.md).
- Use the shared fixtures. Never edit their JSON by hand: change `fixtures/build_fixtures.py` and rerun it.

## Data and secrets

- Seed data uses the made-up personas in `fixtures/seed/vault.json`. Never real people, real phone numbers or
  real photos of people.
- Personal data may appear only inside `services/vault` and `fixtures/seed/vault.json`.
- Secrets live in `.env`, which is git-ignored. Person B adds `.env.example` (every variable, no values) in B1.

## Line endings

`.gitattributes` stores text files with LF. On Windows, leave `core.autocrlf` at its default; git handles it.
