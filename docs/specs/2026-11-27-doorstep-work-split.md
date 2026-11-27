# Doorstep — Two-Person Work Split

**Companion to:** [`2026-11-27-doorstep-design.md`](2026-11-27-doorstep-design.md)

The split is **by language**, so each person stays in one toolchain:

- **Person A (TypeScript):** everything users touch: the Android app (mapper and resident modes), the web console, and the public pages. Also the campus basemap and the hand-corrected footpath ground truth.
- **Person B (Python):** everything behind the API: runtime, core API, sync, dedup and codes, graph engine and routing, dispatch backend, feedback loop, consent vault, bootstrap import, imagery pipeline.

A works against a **mock server generated from the shared API contract** until B's real endpoints land. Most of the time neither person waits for the other. The points where they do are marked **⟵ needs**.

Workstreams are listed in a sensible order. They are not a schedule. Edge-case IDs (e.g. `SY-03`) refer to the edge-case catalogue; each workstream owns the tests for the cases listed.

---

## 0. Shared foundation (both, together, first)

| ID | What | Why | Output |
|---|---|---|---|
| S0.1 | Agree the glossary and data model in design §9 | Both sides must mean the same thing by "structure", "unit", "candidate", "confirmed" | Signed-off data model |
| S0.2 | Write the API contract (OpenAPI), including the error-code list and live-event shapes with cursors | It's the line that lets both work in parallel | `api/openapi.yaml`, owned by B, reviewed by A |
| S0.3 | Define the code format test vectors (valid, invalid, normalisation cases) | Both sides validate codes (console input, server issuance) | Shared fixture file |
| S0.4 | Seed data: zone polygon, access points, 6–10 personas, sample structures | Mocks, tests and demo reset all use the same seed | Shared seed fixtures |
| S0.5 | Repo layout and conventions (one repo, apps / services / data folders, how to run each) | Two people in one repo without collisions | Repo skeleton, README |

**Everything after this depends on S0.2.** If the contract changes later, B updates it and tells A; A regenerates types.

---

## Person A — clients (TypeScript)

| ID | Workstream | Why it matters | Edge cases owned | Dependencies |
|---|---|---|---|---|
| A1 | **Campus basemap:** extract the campus area from the Protomaps build and style it for both app and console | Offline map is the base of mapper mode; the same file serves the console | — | none |
| A2 | **Ground-truth footpaths:** export OSM footways for the zone, hand-correct them in QGIS | B's graph evaluation and synthetic traces need it | — | **B needs this for B5**, so do it early |
| A3 | **App foundation:** login (online once), role-based modes, local storage, op queue, server-address setting via QR, sync status indicator, unsynced warnings | Everything in the app sits on this | SY-02, SY-09, SY-10, SY-14, SY-15 | ⟵ needs B2 sync endpoints for real integration (mock until then) |
| A4 | **Mapper capture:** zone package download, map with zone boundary, confirm/adjust/reject candidates, new buildings, entrances, units, materials, service records, photo pipeline (resize, thumbnail, separate queue) | Core of objective G1 and data for everything else | SY-01, SY-11, SY-12, GP-02, GP-05, GP-06, GP-07, GP-08, ID-02 | ⟵ needs B4 bootstrap candidates in the zone package |
| A5 | **Walk recording:** background GPS with accuracy, weak-GPS indicator, gaps, resume/discard | Feeds the path graph (G2) | GP-01, GP-03, GP-04 | none (traces sync through A3) |
| A6 | **Mapper tasks and consent:** verification task list, "still true?" checks, grievances on a resident's behalf, consent capture, claim-code display | Closes the feedback loop (G4) and the privacy flow (G5) | PV-05 | ⟵ needs B7 tasks API, B8 vault capture API, B6 claim codes |
| A7 | **Resident mode:** claim, code display + speech, SOS (online, offline SMS fallback, no-GPS), reports, consent view/withdraw, unbind | Carries the code without placards; SOS drives dispatch | DS-01, DS-05, DS-06, DS-20, RS-01–RS-06 | ⟵ needs B6 SOS ingest + claim, B8 consent view/withdraw |
| A8 | **Console shell:** login, role-based navigation, live channel with reconnect and catch-up, "reconnecting" state, public-address QR | Dispatcher reliability depends on it | DS-03, AC-02, AC-04, RT-01 (console side) | ⟵ needs B6 live event channel |
| A9 | **Reviewer screens:** clear and duplicate lanes, bulk approve, merge/distinct/defer, code issuance, retirement, code cards, task triage, grievance triage, photo removal, accounts/devices, zones/access points, graph draft review and publish, imagery candidates | Human control over identity and ground truth | ID-05, ID-06 (UI side), GR-05 | ⟵ needs B3 review API, B5 graph versions, B7 grievances, B9 imagery tasks |
| A10 | **Dispatcher screens:** SOS cards with escalation, new-call incident, code entry with check validation and normalisation, location-share link/QR, landmark/attribute search, route preview with warnings, consent-permitted context, lock/claim, assignment, responder link sharing, outcomes, timeline | Objective G3 | ID-09–ID-12, DS-02, DS-04, DS-07–DS-11, DS-17, GR-01–GR-04, GR-06, GR-07, PV-01–PV-04, PV-09 | ⟵ needs B6 incidents, B5 routing, B8 disclosure check |
| A11 | **Public pages:** responder route page (cached route, queued outcome taps), caller location-share page, public report form | The responder and the caller are the people who need the information | DS-12–DS-16, DS-18, GV-04, GV-05 | ⟵ needs B6 tokens and outcomes, B7 grievance submit |

## Person B — services and data (Python)

| ID | Workstream | Why it matters | Edge cases owned | Dependencies |
|---|---|---|---|---|
| B1 | **Runtime:** Docker Compose with registry DB, separate vault DB, photo volume, API, worker; tunnel start that publishes the current address; seed admin; demo reset; backup; health | Laptop is the only server; the demo must be resettable | RT-01, RT-03–RT-06 | none |
| B2 | **Core API base:** auth, roles, devices, accounts, audit, zones, zone package, sync push/pull with idempotency and cursors, photo upload, consistent errors | Everything else is built on it | SY-03–SY-08, SY-13, SY-16, AC-01–AC-04 | none |
| B3 | **Dedup and codes:** duplicate signals, review lanes, decisions, merge semantics, code generator with check character, retired-code registry, code card | Objective G1 | ID-01, ID-03–ID-08, ID-13, SY-06 | needs S0.3 test vectors |
| B4 | **Bootstrap import:** Open Buildings v3 footprints for the zone as candidates with confidence | Mappers confirm rather than start from nothing | — | none |
| B5 | **Graph engine:** synthetic trace generator, graph build (hybrid), versions, draft/publish, edge removal, entrance and access-point snapping, routing with refusals, evaluation harness | Objective G2 and the headline metrics | GR-01–GR-08, GP-01 (filtering) | ⟵ **needs A2 ground truth** for evaluation and synthetic traces; ⟵ needs real traces from the field campaign (J1) for real-data results |
| B6 | **Dispatch backend:** incidents and lifecycle, lock/claim/takeover, SOS ingest (idempotent), live events with cursor catch-up and escalation timing, location-share and responder tokens, outcomes, claim codes and resident bindings, test-number guard | Objective G3 | DS-01–DS-04, DS-06–DS-10, DS-12, DS-14, DS-15, DS-17–DS-20, RS-01–RS-05 | needs B5 routing for located incidents (can stub with a straight-line placeholder until then, never shown as a route) |
| B7 | **Feedback loop:** verification tasks with priorities, evidence weights, grievance state machine, corroboration, rate limits, location cross-check, failure → P1 task | Objective G4 | GV-01–GV-03, GR-08 (task side) | needs B6 outcomes |
| B8 | **Consent vault:** separate service and DB, personas, scopes, capture, view, withdraw, disclosure check with audit, removal; privacy scan of registry and logs | Objective G5 | PV-01–PV-08 | none |
| B9 | **Imagery pipeline:** zone-cell change from two signals via Earth Engine (Open Buildings Temporal baseline + recent cloud-masked Sentinel-2 composites), ranked, imported as P3 tasks with dedup against open tasks | Objective G4's slow signal; last priority | IM-01–IM-06 | needs B7 tasks; needs an Earth Engine noncommercial project registered (either person can register it) |

---

## Joint work (both)

| ID | What | Why | Dependencies |
|---|---|---|---|
| J1 | **Field campaign:** walk and capture the whole campus at building + entrance + unit level, including deliberate duplicate captures for the dedup metric | Real data for every metric and the demo | ⟵ needs A3–A5 (capture + walks), B1–B3 (sync + review), B4 (bootstrap). A6 if consent and claims are captured on the same walk |
| J2 | **Integration passes:** after each pair of matching workstreams lands, run the real flow end to end | Catches contract drift early | Pairs: A3↔B2, A4↔B4, A9↔B3, A10↔B6+B5, A6/A7↔B8, A11↔B6/B7 |
| J3 | **Evaluation runs:** run the evaluation scripts on synthetic and real data, record results | The report needs numbers | ⟵ needs B5, J1 |
| J4 | **Demo script and rehearsal:** scripted run covering all objectives, reset between runs, a failure path (responder can't find → task → fix → re-route) | Evaluators reward the live demo | ⟵ needs everything |

## Dependency summary

The places where one person can be blocked by the other:

1. **Contract (S0.2) → everything.** Do it first, together.
2. **A2 ground truth → B5 evaluation.** A should do A2 early, before app work gets deep.
3. **B2 sync → A3 real integration.** A uses mocks until then.
4. **B4 bootstrap → A4 candidate flows.** Mocks cover UI work; real data needed before J1.
5. **B3 review API → A9 review screens.**
6. **B5 graph + routing → A10 route preview, B6 located incidents.**
7. **B6 incidents, live events, tokens → A7 SOS, A8 live channel, A10, A11.**
8. **B8 vault → A6 consent capture, A7 consent view, A10 occupant context.**
9. **A3–A5 + B1–B4 → J1 field campaign → B5 real-data results → J3.**

**Load balance:** B carries more distinct pieces, while A's screens are larger. If B falls behind, the cleanest piece to move is **B9 (imagery)**. It's Python, but it's a self-contained batch script with no API surface, so A can pick it up without learning the backend. If A falls behind, **A11 public pages** are the smallest to hand across, since they share map code with A10.
