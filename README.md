# Doorstep

**A living address registry and emergency dispatch system for buildings that have no address.**

In informal settlements, homes have no street address, so an ambulance or fire crew cannot find a specific
door. Past efforts (door plaques, Plus Codes, address drives) label homes once and never check again; the
labels go stale as structures change, and none of them connect to live dispatch.

Doorstep closes that loop:

1. **Stable codes.** Every physical structure gets a short, speakable code (e.g. `RV-2GK9-9 / 2` for unit 2),
   issued by the server only after a human reviews it, and never reused.
2. **Walkable routes.** Mappers' GPS walks are merged into a footpath network, so a route ends at the right
   entrance, not at the nearest road.
3. **Live dispatch.** A dispatcher turns a code, an SOS from a resident's phone, or a caller's shared location
   into a position, a route and a link the responder opens on their phone.
4. **Self-correction.** A failed dispatch, a resident's report or a satellite-imagery change raises a
   verification task; only a human visit changes the record.
5. **Privacy by design.** No personal data lives in the registry. Names, phones and medical notes sit in a
   separate consent vault and reach a dispatcher only if the resident opted in.

The pilot runs on a **college campus (~16 acres)** standing in for a settlement, but it must be a fully
working product, demonstrated live from one laptop. It uses made-up personas only, never real residents, and
never calls a real emergency number.

## Project status

| Stage | State |
|---|---|
| Design, edge cases, work split | Written; design marked *draft for team approval* |
| S0 shared foundation: API contract, code vectors, seed data, plans | Done ([PR #1](https://github.com/SoiledSalmon/Doorstep/pull/1)) |
| Product code (apps, services, pipelines) | Not started. Next: Person A starts at A0/A2, Person B at B1/B2 |

Open decisions that need the team are listed at the end of [the Person B plan](docs/plans/person-b-services.md#open-questions-for-the-team-blocking-nothing-yet).

## How it fits together

```
 Android app (mapper + resident)      Web console (admin / reviewer / dispatcher) + public pages
        │  REST, offline queue                    │  REST + WebSocket live events
        └──────────── Cloudflare Quick Tunnel ────┘
                              │
              Laptop: Docker Compose
              ├── Core API (FastAPI) ── Registry DB (PostgreSQL + PostGIS), photo store
              ├── Graph worker (build, route, evaluate)
              └── Consent vault (FastAPI) ── Vault DB (separate instance and credentials)
              Batch pipelines: building-footprint bootstrap, synthetic traces, imagery change detection
```

| Part | Who uses it | Stack | Owner |
|---|---|---|---|
| [`apps/mobile`](apps/mobile/README.md) | Mappers (offline capture), residents (code, SOS) | React Native + Expo, TypeScript, Android | Person A |
| [`apps/console`](apps/console/README.md) | Admin, reviewer, dispatcher; responders and callers via token links | React + MapLibre GL JS, TypeScript | Person A |
| [`services/api`](services/api/README.md) | All clients | FastAPI, PostgreSQL + PostGIS | Person B |
| [`services/vault`](services/vault/README.md) | Core API only | FastAPI, separate PostgreSQL | Person B |
| [`pipelines`](pipelines/README.md) | Builders / admin | Python scripts | Person B (A2 ground truth: Person A) |
| [`api`](api/openapi.yaml) | Contract between all of the above | OpenAPI 3.1 | Person B writes, Person A reviews |
| [`fixtures`](fixtures/README.md) | Tests, mocks and demo reset on both sides | JSON + Python generator | Both |

Everything runs on free tiers: no cloud hosting, no paid SMS or map tiles.

## Documentation

Read in this order:

| Doc | What it tells you |
|---|---|
| [docs/specs/design.md](docs/specs/design.md) | **Source of truth.** What to build and why: goals, flows F1–F14, codes, roles, data model, evaluation |
| [docs/specs/edge-cases.md](docs/specs/edge-cases.md) | Every edge case (101, with stable IDs like `SY-03`) and the behaviour it requires |
| [docs/specs/work-split.md](docs/specs/work-split.md) | Who owns which workstream (A1–A11, B1–B9) and where one person waits on the other |
| [docs/plans/person-a-clients.md](docs/plans/person-a-clients.md) | Person A's task list (apps, console, public pages) with acceptance checks |
| [docs/plans/person-b-services.md](docs/plans/person-b-services.md) | Person B's task list (runtime, API, vault, graph, pipelines) with acceptance checks |
| [api/openapi.yaml](api/openapi.yaml) | The API contract. Each operation lists allowed roles (`x-roles`) and edge cases (`x-edge-cases`) |
| [fixtures/README.md](fixtures/README.md) | Code format, test vectors and seed data |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branches, PRs, contract changes, test naming, the rules that must never break |
| [docs/prd.md](docs/prd.md) | The original PRD. Background only; the design wins where they differ |

## Getting started

Nothing runs yet; the first runnable pieces come from B1 (Docker Compose) and A0 (mock server). Today you can:

1. Read the design, then your own plan.
2. Check the shared fixtures (needs Python 3.11+, no packages):
   ```
   python fixtures/build_fixtures.py --check
   ```
3. Lint the contract (needs Node 20+):
   ```
   npx @redocly/cli lint api/openapi.yaml api/vault.yaml
   ```

To run the full system later you will need Docker Desktop, Node 20+, Python 3.11+, Android Studio (for the
Expo dev build) and `cloudflared`. Run, test and reset commands are added here as each package lands.

## License

[MIT](LICENSE)
