# Doorstep — Product Design

**Status:** Draft for team approval
**Date:** 2026-11-27
**Companion documents:**
- [`2026-11-27-doorstep-edge-cases.md`](2026-11-27-doorstep-edge-cases.md): every edge case and its required behaviour
- [`2026-11-27-doorstep-work-split.md`](2026-11-27-doorstep-work-split.md): the two-person split and its dependencies
- [`../PRD.md`](../PRD.md): the original PRD (background only; this document wins where they differ)

This document says **what** must exist and **why**. It does not prescribe how to implement it. Where a technology is named, it is because the team decided it; everything else is left to the builder (see §13).

---

## 1. Intent

Informal settlements have no addresses, so emergency responders can't find a specific door. Earlier efforts (door plaques, Plus Codes, community address drives) label homes once and are never re-checked. As structures are demolished, rebuilt or turn out unreachable, the labels go stale, and none of them is wired into live dispatch.

**Doorstep** is a living registry of un-addressed structures. It:

1. Gives every physical structure a stable, speakable code.
2. Builds a walkable footpath network from mappers' GPS walks.
3. Lets a dispatcher turn a code (or an SOS) into a location and a walking route to the right door.
4. Corrects itself: failed dispatches, resident reports and imagery changes all trigger re-verification.
5. Keeps resident identity out of the registry. Identity lives in a separate, opt-in consent vault.

The college campus (about 16 acres) stands in for a settlement. The product must be **fully working**, not a mock-up. Every flow in §6 works end to end, and every edge case in the edge-case catalogue has defined, tested behaviour.

**Success** means a live demo, run from the laptop, covering all five objectives: map → sync → review → code → route → SOS/dispatch → responder → failure → re-verification → corrected record, with consent-gated identity throughout and imagery-driven re-survey tasks.

## 2. Goals, non-goals, anti-goals

### Goals
- **G1 Stable identity:** one stable, de-duplicated code per confirmed structure, issued by the server only after human review, never reused.
- **G2 Walkable routing:** a versioned pedestrian path graph built from merged GPS breadcrumbs, with routes that end at a structure's entrance.
- **G3 Live dispatch:** code lookup, resident SOS, caller-without-code fallbacks, a live incident board, responder hand-off by link, and outcome capture.
- **G4 Self-correction:** failed dispatches, corroborated grievances and imagery change candidates all become prioritised mapper verification tasks. Only human verification changes ground truth.
- **G5 Privacy by design:** no PII in the registry, a separate consent vault with scoped and revocable consent, role-gated service data, and every disclosure audited.
- **G6 Offline-first capture:** mappers capture everything with no connectivity; sync happens whenever a connection appears.

### Non-goals (explicitly out of scope)
- iOS builds; regional languages
- Cloud hosting: the laptop is the only server
- Real emergency numbers (112 etc.) or real telephony; SMS ingestion by the server
- Real residents' personal data: the pilot uses made-up personas only
- Integration with any municipal or NGO dispatch system
- Commissioned imagery (drones, paid satellites)
- AI in ID assignment or identity / duplicate resolution

### Anti-goals (failures even if everything "works")
- **Confidently wrong routing.** Sending a responder to the wrong door is worse than saying "can't route". When unsure, the system refuses and says why.
- **Identity leaking into the registry,** directly or through logs, photos, exports or error messages.
- **Codes that change or get reused.** A code printed or shown once must mean that structure forever, or be explicitly retired.
- **Lost SOS.** No dropped connection, restart or reconnect may silently swallow an SOS.
- **A demo that depends on luck,** for example on campus Wi-Fi being up or on an outside service other than the tunnel.

## 3. Constraints

| Constraint | Consequence |
|---|---|
| Two developers, neither specialised; two to four weeks | Two languages only (TypeScript, Python); a work split by language; mocks against a shared contract |
| Zero budget | Every dependency must be free. No paid SMS, no paid hosting, no paid map tiles |
| Android only | No iOS-specific work. Expo dev builds, distributed as an APK |
| Laptop is the server | Docker Compose; a Cloudflare Quick Tunnel for public HTTPS. The tunnel URL changes on every restart (see edge cases); max 200 in-flight requests; Quick Tunnels do **not** support Server-Sent Events, so live updates use WebSockets |
| Campus pilot | Few, large buildings, so structures are modelled as **building + entrances + units** to reach 100+ registry records |
| Phone GPS error of 5–15 m near buildings | Every GPS fix carries its accuracy; low-quality fixes are filtered; routing refuses points too far off the network |
| Must be demonstrable live | Real-time push to the console; a deterministic demo reset; seeded personas |

## 4. Approaches considered

| Decision | Options considered | Chosen | Why |
|---|---|---|---|
| Mobile framework | Flutter (previous attempt), React Native + Expo, progressive web app | **React Native + Expo (TypeScript), Android** | Team struggled with Flutter; TypeScript is shared with the web console; a web app can't do reliable background GPS or durable offline storage |
| Backend | Node + Python (previous design), all Python | **Python / FastAPI** | Graph work needs the Python geo/ML stack; one backend language for a two-person team |
| Hosting | Laptop + tunnel; free cloud (Render + Supabase); always-free VM | **Laptop + Cloudflare Quick Tunnel only** | Free cloud tiers spin down and drop live connections, which breaks SOS; a VM adds ops work and needs a credit card. Team chose to drop cloud copies entirely |
| Code carrier | Physical placard/QR, resident app | **Resident mode in the app**, with a printable card as fallback | Avoids placards; adds SOS and self-service consent. Printable card covers phone-less homes |
| Structure definition ([PRD §7.1](../PRD.md#71-structure-definition-for-partitionedshared-dwellings)) | Footprint-based, household-based, hybrid | **Hybrid: building → entrances → units** | Matches shared dwellings; gives enough records on campus |
| Bootstrap footprints | Google Open Buildings v3, Microsoft footprints, OSM, Overture | **Google Open Buildings v3**, with OSM as reference | It's what a real Indian settlement deployment would use; OSM on campus is too good to be representative |
| Path ground truth | Hand-digitised, raw OSM footways | **OSM footways, hand-corrected for the pilot zone** | Feasible for students; also seeds synthetic traces |
| Change detection | Sentinel-2 per structure; Open Buildings Temporal per zone; both per zone | **Zone-level, two real signals via Earth Engine (Community Tier): Open Buildings 2.5D Temporal as baseline + recent Sentinel-2 composites** | Sentinel-2 can't see single structures, so both are used per zone ([PRD §6.4](../PRD.md#64-imagery--re-verification-cadence)); Open Buildings Temporal ends in 2023, and the team wanted a recent signal too |
| Link delivery | Paid SMS, share sheet / QR | **Android share sheet + on-screen QR + copy link** | Zero cost |

## 5. System overview

### 5.1 Components

| # | Component | Users | Responsibility |
|---|---|---|---|
| C1 | **Doorstep app** (React Native, Android): *mapper mode* | Mappers | Offline map, walk recording, structure/entrance/unit capture, photos, services, consent capture, claim codes, verification tasks, sync |
| C1 | **Doorstep app**: *resident mode* | Residents (personas) | Claim a unit, show and speak the code, SOS, reports, view and withdraw consent |
| C2 | **Web console** (React) | Admin, reviewer, dispatcher | Review queues, code issuance, graph review/publish, accounts, zones, incident board, lookup, routing, assignment |
| C3 | **Public pages** (part of C2, no login, token-gated) | Responders, callers, phone-less residents | Responder route page; caller location-share page; public report form |
| C4 | **Core API** (FastAPI) | All clients | Auth, registry, sync, dedup, codes, tasks, grievances, incidents, live events, responder/location tokens, photos, audit |
| C5 | **Graph engine** (Python; may run as a worker beside C4) | Core API | Build versioned path graphs from breadcrumbs, snap entrances, route (A*), evaluate against ground truth |
| C6 | **Consent vault** (separate FastAPI service + separate database + separate credentials) | Core API only | Persona identity, consent scopes, disclosure decisions, disclosure audit, withdrawal |
| C7 | **Data prep & pipelines** (Python scripts) | Admin / builders | Campus basemap extract, Open Buildings bootstrap import, ground-truth footpaths, synthetic traces, imagery change detection |
| C8 | **Runtime** (Docker Compose on laptop + Quick Tunnel) | Team | Run everything, reset the demo, back up data, publish the current public address |

### 5.2 Data stores

| Store | Holds | Must never hold |
|---|---|---|
| Registry DB (PostgreSQL + PostGIS) | Zones, structures, entrances, units, footprints, services, traces, graphs, tasks, grievances, incidents, accounts, audit | Names, phone numbers, medical notes, anything personal |
| Vault DB (separate PostgreSQL instance, separate credentials) | Persona identities, consent records, disclosure audit | Locations or geometry (it refers to units only by opaque ID) |
| Photo store (local volume) | Original and thumbnail images, addressed by opaque ID | — |
| Device store (SQLite on phone) | Zone data, captured records, pending operations, pending photos | Vault data after a successful sync (see edge cases) |

### 5.3 Architecture diagram

```
          ┌─────────────── Android phone ───────────────┐
          │ Doorstep app                                 │
          │  mapper mode | resident mode                 │
          │  SQLite + op queue + photo queue             │
          │  bundled campus basemap (PMTiles)            │
          └───────┬───────────────────────┬──────────────┘
                  │ HTTPS (REST)          │ SMS intent (offline SOS → test number)
                  ▼                       ▼
   Phones / browsers ── Cloudflare Quick Tunnel ── Laptop (Docker Compose)
                                               │
        ┌──────────────────────────────────────┼─────────────────────────┐
        │                                      ▼                         │
        │  Web console + public pages ◄──WS── Core API ──► Graph engine   │
        │  (admin/reviewer/dispatcher;         │   │       (build, route, │
        │   responder/location/report)         │   │        evaluate)     │
        │                                      │   └──► Consent vault ──► Vault DB
        │                                      ▼                         │
        │                         Registry DB (PostGIS)   Photo store    │
        │  Batch: bootstrap import · imagery change detection · synth    │
        └────────────────────────────────────────────────────────────────┘
```

## 6. Core flows

Each flow names what must happen and the invariant it protects. Failure handling lives in the edge-case catalogue.

**F1 Zone setup and bootstrap.** Admin defines the pilot zone polygon and **access points**: where vehicles stop, such as gates and drop-offs, which serve as route origins. Open Buildings footprints inside the zone are imported as `candidate` structures with their confidence score. The campus basemap is extracted once and bundled into the app.
*Why:* mappers confirm or correct rather than start from zero, and the share of confirmed vs. corrected candidates is an evaluation metric.

**F2 Offline capture (mapper).** The mapper logs in online once, downloads the zone package (candidates, confirmed structures, open tasks), then works fully offline. They:
- record a GPS walk from an access point or path to the door, saving each fix's accuracy;
- confirm, adjust or reject a candidate footprint, or drop a new building;
- add **entrances** (point, label, photo) and **units** (label, door photo optional);
- record material and per-unit **service records** (type, source, supply hours, quality, shared-with count);
- optionally capture **consent** for a persona and generate a **claim code** for a resident.

Every write lands in local storage first, and an operation joins the sync queue.
*Why:* capture must never depend on the network.

**F3 Sync.** Whenever connectivity appears, the app pushes queued operations, each with a client operation ID and per-device sequence number, then pulls changes since its last cursor. Records sync before photos; photos upload from a separate queue.
*Invariant:* replaying an operation never creates a second effect.

**F4 Review and code issuance.** Newly synced buildings enter review in one of two lanes:
- **Clear:** no duplicate signals. Can be approved in bulk.
- **Possible duplicate:** proximity, footprint overlap or similar signals fired. Each needs an individual decision: *merge*, *distinct* or *defer*.

On approval, the server issues a code (§7). A merge keeps one record, points the other at it, and never issues a second code.
*Invariant:* only a human decision creates or merges an identity.

**F5 Path graph.** A reviewer triggers a build (the console shows how many new traces arrived since the last build). The graph engine builds a new graph version from accuracy-filtered breadcrumbs across all mappers (hybrid method per Phase II findings: adaptive seeds, map-matched backbone, trace-supported bridges, unsupported-edge suppression). Then:
- It snaps every entrance and access point to the graph. Anything too far off is flagged as unroutable.
- A reviewer inspects the draft (edges with their trace support) and can remove edges.
- The reviewer publishes it. Routing always uses the latest published version and records which version it used.
*Why:* a graph that humans can review and that comes in versions makes routing auditable.

**F6 Resident claim.** At a visit, the mapper's app shows a one-time claim code (QR + 6 digits, short expiry) for a specific unit. The resident enters it in resident mode, and the device becomes bound to that unit. A unit can have several residents. No phone number is required; any personal detail goes to the vault, only with consent.
*Why:* prevents anyone claiming any code, without collecting identity.

**F7 SOS.** Resident taps SOS → confirms → the app sends the unit, device GPS (if available) and a client-generated ID. The server creates exactly one incident and pushes a live **incoming SOS card** to all dispatcher consoles, which persists until acknowledged.
If the phone has no data, the app opens an SMS to the **configured test number**, pre-filled with code and coordinates. A human relays it to the console.
*Invariant:* never dials or texts a real emergency number.

**F8 Dispatch.** A dispatcher opens an incident: from an SOS card, or a manual "new call". They resolve the location by:
1. **Code entry**, with the check character validated before lookup;
2. **Caller location share**: the console generates a one-time link or QR, the caller's browser sends its position, and the console lists the nearest structures;
3. **Landmark / attribute search**: building name, colour, material, floors, near a landmark.

The console shows location, **route from the chosen access point to the primary entrance** (falling back to the building centroid with a visible warning), entrance photo, and any **consent-permitted** occupant context.
The dispatcher assigns a responder. The first assignment **locks** the incident to that dispatcher; others see it read-only. The console produces a responder link (share sheet / QR / copy).

**F9 Responder.** The link opens a phone-sized page: route map, step list, entrance photo, code, unit, and **Reached** / **Couldn't find** buttons (with optional note, photo and current position). The outcome updates the incident live.
*Why:* the person walking the alleys is the one who needs the route.

**F10 Feedback loop.** A *couldn't find* outcome, or a dispatcher marking failure, creates a **priority-1 verification task** for that structure, with the responder's evidence attached. A mapper visits, verifies or corrects, and the record's `last_verified` and `verification_method` update. A corrected entrance or path triggers a graph rebuild candidate.
*Invariant:* inference and reports raise tasks; only human verification changes ground truth.

**F11 Grievances.** Reports come from the resident app (tagged to the claimed unit), from mappers on a resident's behalf, or from the public report form (code + photo + location). They move through **received → corroborating → confirmed / rejected**. Evidence weights drive priority:

| Source | Weight |
|---|---|
| Dispatch outcome | 1.0 |
| Corroborated report | 0.7 |
| Mapper observation | 0.6 |
| Imagery candidate | 0.4 |
| Single unverified report | 0.1 |

Reports are rate-limited per device or account and cross-checked against the registered location. Removal requests come through this channel too ([§6.9 of the PRD](../PRD.md#69-service-data-privacy-posture-pilot-default)).

**F12 Consent.** Consent is captured by the mapper with the persona present: separate scopes (*name to dispatch*, *phone to dispatch*, *medical/access notes to dispatch*), each recorded with time, mapper and method. Residents can view and withdraw consent in resident mode, or ask a mapper. At dispatch, the core API asks the vault "what may dispatch see for this unit?". The vault answers per scope and audits every request and answer. **No consent means no occupant context**, which is the default.

**F13 Imagery change detection.** A batch job, run through Earth Engine (noncommercial Community Tier), produces zone-cell change candidates from two signals:
- **Baseline signal:** building presence and counts per cell across the latest available years of Open Buildings 2.5D Temporal (yearly, ends 2023).
- **Recent signal:** a built-up change measure per cell from cloud-masked Sentinel-2 composites, comparing a recent window with an earlier one. This is coarse (10 m pixels) and noisy, so it is only used to rank cells, never to say anything about a single structure.

Each candidate records which signal(s) fired. Cells passing the threshold become zone-level re-survey tasks (weight 0.4). Cells where both signals agree rank above cells where only one fires.

**F14 Retirement and archive.** Confirmed demolition, departure, or a merge retires the structure and its code. The code goes into a permanent retired list. Retired codes resolve to "retired — see replacement" (if merged) or "retired". The record is archived, not deleted.

## 7. Structure codes

- **Format:** `ZZ-XXXX-C`: a zone prefix, four Crockford base32 characters (no I, L, O, U), and one check character computed over the prefix and body.
- **Units** are addressed as code + unit number (e.g. `RV-7K3M-X / 2`). The building code alone resolves to the building with its unit list.
- **Issued:** by the server only, after review approval. Random, never derived from location or order.
- **Never reused.** Retired codes stay reserved forever.
- **Input is forgiving:** case-insensitive; ignores spaces and dashes; maps `O→0` and `I/L→1` before validation.
- **Spoken form:** characters read individually with a fixed phonetic list. Resident mode can speak it aloud.
- **Printable card:** a code card (code, spoken form, optional QR) can be generated for any unit, as the fallback for phone-less homes.

## 8. Roles and access

| Role | Surface | Can | Cannot |
|---|---|---|---|
| Admin | Console | Everything a reviewer can; create and disable accounts and devices; zones and access points; demo reset | Read vault identity directly |
| Reviewer | Console | Dedup decisions, code issuance, retirement, task triage, grievance decisions, graph review/publish, imagery candidates | Dispatch |
| Dispatcher | Console | Incidents, lookup, routing, assignment, outcomes; consent-permitted occupant context only | Service history; review decisions |
| Mapper | App | Capture and edit in assigned zone, tasks, consent capture, claim codes | Approve own structures; issue codes |
| Resident | App (claimed) | See own code; SOS; reports; own consent | See anyone else's data |
| Responder | Token link | One incident's route and outcome buttons until the link expires | Anything else |
| Public | Token / form pages | Share location for one incident; submit a rate-limited report | Read anything |

Staff accounts are invite-only, created by admin. The first admin is seeded at install. Aggregate service statistics are visible to reviewers; per-structure service history needs a reviewer or admin role.

## 9. Data model (conceptual)

Fields listed are the ones the product depends on; the builder may add more. All entities carry created/updated timestamps and the actor responsible.

- **Zone:** polygon, code prefix, name.
- **AccessPoint:** zone, point, label (gate / drop-off).
- **Structure (building):** zone, code (null until issued), footprint, centroid, status (`candidate`, `pending_review`, `confirmed`, `retired`), `needs_verification` flag, material, floors, colour, landmark name, `last_verified`, `verification_method`, source (`bootstrap` / `mapper`), bootstrap confidence, `merged_into` (nullable).
- **Entrance:** structure, point, label, is_primary, photo, routable flag, snapped graph node (per version).
- **Unit:** structure, number, label, door photo, entrance used to reach it (optional; defaults to the building's primary entrance), status. Routing to a unit ends at that entrance.
- **ServiceRecord:** unit (or structure), type, source, supply hours, quality, shared-with count, `last_verified`, `verification_method`.
- **Photo:** owner entity, kind (building / entrance / unit / evidence), original + thumbnail, capture time.
- **Trace:** mapper, device, ordered GPS fixes (position, accuracy, time), purpose (walk / evidence).
- **GraphVersion:** status (`draft` / `published` / `superseded`), input trace set, parameters, metrics; **GraphNode / GraphEdge** with support count and provenance.
- **DuplicateCandidate:** structure pair, signals with values, decision (`merge` / `distinct` / `defer`), reviewer, time.
- **RetiredCode:** code, reason, replacement (nullable), time.
- **VerificationTask:** target (structure / unit / zone cell), reason, priority (P1 dispatch failure, P2 confirmed or corroborated grievance, P3 imagery, P4 stale), evidence list, status, assignee.
- **EvidenceEvent:** target, source type, weight, payload reference.
- **Grievance:** source (resident / mapper / public), target, category, text, photo, position, device/account, status.
- **Incident:** source (SOS / call / manual), status (`new`, `claimed`, `located`, `assigned`, `reached`, `failed`, `cancelled`, `closed`), lock holder, resolved structure/unit, location shares, graph version used, timeline of events.
- **ResponderAssignment:** incident, responder name/label, token, expiry, outcome, evidence.
- **LocationShare:** incident, token, expiry, received position + accuracy.
- **Account:** role, credentials, status. **Device:** account, registration, revoked flag, last sync cursor.
- **ResidentBinding:** device, unit, created via claim code, status. **ClaimCode:** unit, code, expiry, used flag.
- **SyncOperation:** client operation ID, device, sequence, type, result.
- **AuditEntry:** actor, action, target, time, details (no PII).
- *Vault only:* **Persona** (opaque ID, name, phone, notes), **ConsentRecord** (persona, unit reference, scope, status, method, capturer, time), **DisclosureAudit** (requester, unit, scopes asked, scopes granted, time).

## 10. Interfaces (resource level)

The API contract is written as an OpenAPI document before integration work starts. Clients generate their types from it. Resource groups:

- **Auth & devices:** staff login, token refresh (works after offline periods), device register/revoke, resident claim, resident unbind.
- **Zones:** zone package download (candidates, structures, tasks, access points) for offline use.
- **Sync:** push operations (batch, idempotent), pull changes since cursor, photo upload (resumable or retry-safe), sync status.
- **Registry:** structures/entrances/units read, search (code, attributes, nearby), retirement, code card.
- **Review:** dedup lanes, decisions, bulk approve, code issuance.
- **Graph:** build trigger, versions, draft inspection, edge removal, publish, route request (origin access point, target entrance/unit, version pinned in the response).
- **Tasks & evidence:** list/assign/complete verification tasks; attach evidence.
- **Grievances:** submit (app, mapper, public form), triage, corroborate, decide.
- **Incidents:** create, SOS ingest, claim/lock/release, locate, assign, outcome, timeline.
- **Tokens:** responder link create/revoke; location-share link create; public endpoints redeemed by token.
- **Live events:** one WebSocket channel per console session; every event carries a monotonic cursor so a reconnecting client can catch up.
- **Consent (core → vault only):** capture, view by unit, withdraw, disclosure check (audited).
- **Admin:** accounts, zones, access points, demo reset, health, current public address (shown as QR for apps).

Error responses use one consistent shape with a machine-readable code, so clients can show specific messages (e.g. `CODE_CHECKSUM_INVALID`, `OUTSIDE_NETWORK`, `INCIDENT_LOCKED`).

## 11. Evaluation

Measured and reported by repeatable scripts, not by hand:

| Area | Measures |
|---|---|
| Path graph | Edge precision/recall and spurious-edge count vs. hand-corrected ground truth; usable-route rate; destination reach; connected components. On synthetic traces (several seeds) and on real campus traces |
| Dedup | Precision/recall of duplicate candidates on a labelled set, including deliberately duplicated captures |
| Bootstrap | Share of Open Buildings candidates confirmed / corrected / rejected / missed |
| Dispatch | Lookup success rate; time from incident open to located; route usability judged by the walker; responder reach rate |
| Feedback loop | Failed dispatches and grievances that produced a correction; time from failure to corrected record |
| Privacy | Automated check that no registry table, log or export contains vault fields; disclosure audit completeness |

## 12. Quality bar

- Every edge case in the catalogue has an automated test or, where that's impossible (GPS, airplane mode), a written manual test script with expected results.
- The demo has a scripted run and a one-command reset to a known seeded state.
- All user-facing errors are specific and actionable; no stack traces or raw codes reach users.
- Nothing in the registry, logs, photos or exports can identify a persona.

## 13. Left to the builder

The builder decides, within the constraints above: internal module layout, libraries (other than those named), database schema details, the exact graph algorithm parameters, dedup thresholds (tuned from campus data), token lifetimes, UI layout and styling, and test frameworks. Choices that change user-visible behaviour or the invariants in §2 and §6 need team approval.

## 14. Known limitations (to state in the report)

- The campus is a weak stand-in for a settlement: larger, fewer and better-mapped buildings.
- Imagery change is zone-level only. The Open Buildings Temporal baseline ends at 2023, and the recent Sentinel-2 signal is coarse (10 m) and affected by cloud and season, so it prioritises re-survey but never confirms a change on its own.
- Offline SOS falls back to an SMS that a human relays; the server cannot receive SMS for free.
- The system is only available while the laptop is on; the tunnel address changes on restart.
- Purpose limitation of service data is a stated principle, not a technically enforced control.
