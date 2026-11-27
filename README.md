# Doorstep

Offline-first address registry and emergency dispatch for un-addressed structures. College-campus pilot.
Start with [the design](docs/specs/2026-11-27-doorstep-design.md); `CLAUDE.md` lists the rules that must never break.

## Layout

| Path | What | Owner | Language |
|---|---|---|---|
| `api/openapi.yaml` | Client ↔ core API contract (source of truth) | B writes, A reviews | OpenAPI 3.1 |
| `api/vault.yaml` | Core API ↔ vault contract (internal only) | B | OpenAPI 3.1 |
| `apps/mobile` | Android app: mapper + resident modes | A | TS, React Native + Expo |
| `apps/console` | Web console + public pages | A | TS, React + MapLibre |
| `services/api` | Core API + graph worker | B | Python, FastAPI, PostGIS |
| `services/vault` | Consent vault (own DB, own credentials) | B | Python, FastAPI |
| `pipelines/` | Bootstrap import, synthetic traces, graph evaluation, imagery | B (A2 ground truth: A) | Python |
| `fixtures/` | Shared code vectors and seed data (both sides read these) | both | JSON + generator |
| `docs/specs/` | Design, edge-case catalogue, work split | team | |
| `docs/plans/` | Implementation plans for Person A and Person B | | |
| `docs/manual-tests/` | Scripts for edge cases marked *Manual* | owner of the case | |

## Conventions

- **Contract first.** Change `api/openapi.yaml` in its own commit before the code that uses it; tell the other
  person; A regenerates client types (`apps/*/src/api/types.ts`, generated, never hand-edited).
- **Tests are named after edge-case IDs**: `test_SY03_replayed_op_applies_once` (Python),
  `it('DS-01 second SOS tap shows already sent')` (TS). Operations list their cases under `x-edge-cases`.
- **Branches**: `a/<workstream>-<topic>` and `b/<workstream>-<topic>` (e.g. `b/B2-sync-push`). Small PRs; the
  other person reviews anything touching `api/`, `fixtures/` or `docs/specs/`.
- **No personal data** anywhere outside `services/vault` and `fixtures/seed/vault.json`. Use the seed personas.
- **Secrets** live in `.env` (git-ignored). `.env.example` lists every variable without values.

## Commands

```
python fixtures/build_fixtures.py --check    # shared fixtures are current and self-consistent
npx @redocly/cli lint api/openapi.yaml api/vault.yaml   # contract lint
```

Run, test and reset commands for each package are added here as each package is created (B1, A3, A8).
