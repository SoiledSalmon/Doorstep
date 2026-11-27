# services/api: Doorstep core API and graph worker

The server every client talks to. Owner: **Person B**. Status: **not started** (plan tasks B1–B7).

- **Implements:** [`api/openapi.yaml`](../../api/openapi.yaml): auth and devices, zone packages, offline sync
  (idempotent, ordered per device), photos, registry and code lookup, dedup review and code issuance, path
  graph build/publish and routing, verification tasks, grievances, incidents and SOS, responder and
  location-share tokens, live events over WebSocket, imagery import, admin.
- **Stack:** FastAPI (Python), PostgreSQL + PostGIS for the registry DB, a local volume for photos. The graph
  worker (build, snap, route, evaluate) runs beside it.
- **Runs on:** Docker Compose on one laptop, exposed through a Cloudflare Quick Tunnel whose URL changes on
  every restart.
- **Rules that matter most here:** no personal data in any table, log or error; codes issued only after human
  review and never reused; only human decisions merge identities or change ground truth; routing refuses
  rather than guesses; the API reports degraded health instead of crashing.
- **Never:** stores consent or identity (that is [`services/vault`](../vault/README.md)), or sends SMS / calls.
- **Plan:** [docs/plans/person-b-services.md](../../docs/plans/person-b-services.md), sections B1–B7.
