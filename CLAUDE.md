# Doorstep

Offline-first address registry and emergency dispatch for un-addressed structures. College campus pilot, but it must be a fully working product.

## Read first
- **Design** (source of truth): `docs/specs/design.md`
- **Edge-case catalogue** (required behaviour per case): `docs/specs/edge-cases.md`
- **Work split** (who owns what, dependencies): `docs/specs/work-split.md`
- **PRD** (background only; the design doc wins): `docs/prd.md`
- **Plans**: `docs/plans/person-a-clients.md`, `docs/plans/person-b-services.md`
- **Contributing** (branches, PRs, test naming): `CONTRIBUTING.md`
- **Contract**: `api/openapi.yaml` (clients ↔ core API), `api/vault.yaml` (core API ↔ vault only)

## Stack
- `apps/mobile`: React Native + Expo, TypeScript, Android only (dev build, not Expo Go)
- `apps/console`: React + MapLibre GL JS, TypeScript (console + public pages)
- `services/api`: FastAPI, PostgreSQL + PostGIS
- `services/vault`: FastAPI, separate Postgres instance and credentials
- `pipelines/`: Python data scripts (bootstrap, graph evaluation, imagery)
- Runtime: Docker Compose on one laptop, Cloudflare Quick Tunnel for public HTTPS. No cloud hosting.

## Rules that must never break
- No personal data in the registry DB, logs, photos, exports or error messages. Identity lives only in the vault.
- Codes are server-issued only after human review, never derived from location, never reused. Retired codes stay reserved.
- AI and heuristics never assign IDs or resolve duplicates. They only raise candidates for humans.
- Inferred data stays a candidate until human verification.
- Mapper capture works fully offline. Every sync operation is idempotent.
- Never dial or text a real emergency number. Use only the configured test number.
- Routing refuses rather than guesses (off-network, no route, no graph).
- Live updates use WebSockets (Quick Tunnels don't support SSE). Clients reconnect and catch up by cursor; no event may be lost.
- Everything must run on free tiers.

## Working rules
- `api/openapi.yaml` is the contract between clients and services. Change it first, then regenerate client types. Never let code drift from it.
- Name tests after edge-case IDs (e.g. `test_SY03_...`). Cases marked *Manual* get a script in `docs/manual-tests/`.
- Use the made-up personas in seed data. Never real people.
- Changes that alter user-visible behaviour or a rule above need team approval. Ask first.

## Commands
- `python fixtures/build_fixtures.py --check`: shared code vectors and seed are current and self-consistent
- `npx @redocly/cli lint api/openapi.yaml api/vault.yaml`: contract lint
<!-- Add run, test and reset commands here as they are created. -->
