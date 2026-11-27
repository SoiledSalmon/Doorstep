# Person A plan: clients (TypeScript)

**Scope:** workstreams A1 to A11 from the [work split](../specs/work-split.md).
**Contract:** [`api/openapi.yaml`](../../api/openapi.yaml). Review it now; after that, B changes it and you regenerate.
**Fixtures:** [`fixtures/`](../../fixtures/README.md): code vectors, seed, emergency deny-list.

Each task is small enough for one PR. "Done when" is the acceptance check; automated (Jest / React Testing
Library / Playwright) unless marked *manual*, in which case write `docs/manual-tests/<ID>.md`. Tests are named
after edge-case IDs (`it('DS-01 ...')`).

## Shared setup (do first)

| # | Task | Done when |
|---|---|---|
| A0.1 | Typed client generated from `openapi.yaml` (`openapi-typescript` + `openapi-fetch`) into a small shared package used by both apps; `npm run gen:api` | Changing a schema and regenerating breaks the build where it's used |
| A0.2 | Mock server from the contract (Prism) seeded with `fixtures/seed/registry.json` examples; `npm run mock` | Both apps run against the mock with no backend |
| A0.3 | Shared `codes` module: normalise, validate, spoken form | Passes every case in `fixtures/codes/vectors.json` |
| A0.4 | Shared error-message map: every `ErrorCode` → specific, actionable user text; unknown codes → generic | Test asserts every enum value has a message; no raw codes or stack traces shown |
| A0.5 | Test-number guard: refuse any call/SMS if the number is empty or on `fixtures/emergency-numbers.json` | `it('DS-20 refuses unset or emergency number')` |

## A1 Campus basemap / A2 ground truth (do A2 early: B5 is blocked on it)

| # | Task | Done when |
|---|---|---|
| A1.1 | Extract the campus area from a Protomaps build into a `.pmtiles` file; one style used by app and console | File under 50 MB; renders offline in both |
| A1.2 | Replace the placeholder zone polygon in `fixtures/build_fixtures.py` with the real campus boundary (coordinate with B) | `--check` passes; seed zone matches the basemap |
| A2.1 | Export OSM footways for the zone; hand-correct in QGIS; save as GeoJSON in `pipelines/ground_truth/` | B confirms it loads in the synthetic trace generator |

## A3 App foundation

| # | Task | Done when |
|---|---|---|
| A3.1 | Expo dev build (Android), navigation, mapper/resident mode switch | APK installs and opens offline |
| A3.2 | Server address via QR (`doorstep://server?u=`), stored; unreachable server → prompt to rescan | `it('SY-15 unreachable server prompts rescan, queue intact')` |
| A3.3 | Login online once; device registration; tokens in secure storage; refresh on reconnect, password prompt on `REFRESH_EXPIRED` | `it('SY-02 expired session re-auths without losing queue')` |
| A3.4 | SQLite store: zone data, op queue (`clientOpId`, `seq`), photo queue, consent queue (separate) | Ops survive app restart; `seq` strictly increasing per device |
| A3.5 | Sync engine: push in order, handle every `SyncOpResult.status`, pull by cursor until `hasMore=false`, resume after interruption, photos after records with backoff | Integration test against mock: replay, deferred, rejected, sent_for_review |
| A3.6 | Persistent "N items not synced" indicator; blocking logout/clear-data warning with exact counts | `it('SY-09 logout warns with exact unsynced count')`; *manual* SY-10 note |
| A3.7 | `DEVICE_REVOKED` / `ACCOUNT_DISABLED` → stop syncing, keep local data, tell user to contact admin | `it('SY-14 revoked device keeps data and stops sync')` |
| A3.8 | Report pending counts via `POST /sync/status` on every sync | Counts match local queues |

## A4 Mapper capture (⟵ B4 for real candidates; mock until then)

| # | Task | Done when |
|---|---|---|
| A4.1 | Zone package download; map with zone boundary, candidates, confirmed structures | *manual* `SY-01.md`: airplane mode for a full capture session |
| A4.2 | Pins and walks blocked without location permission, with settings link | `it('GP-02 no location blocks pin and walk')` |
| A4.3 | Pin outside zone rejected locally (and server `OUTSIDE_ZONE` handled) | `it('GP-05 pin outside zone rejected')` |
| A4.4 | Candidate confirm / adjust vertices / reject (reason) | `it('GP-08 adjust and reject candidate')`; `it('ID-02 choosing a candidate confirms instead of creating')` |
| A4.5 | New building, entrances (primary flag), units, attributes, service records | Each writes locally and queues the right op type |
| A4.6 | Photo pipeline: capture guidance (exteriors only), resize, thumbnail, SHA-256, `photo.attach` then upload; "photo pending" badge | `it('SY-11 failed upload retries, no duplicate')`; `it('GP-07 guidance shown before first photo')` |
| A4.7 | Camera denied → record marked photo missing | `it('GP-06 camera denied marks photo missing')` |
| A4.8 | Low storage → block photos with message; text capture continues | `it('SY-12 low storage blocks photos only')` |

## A5 Walk recording

| # | Task | Done when |
|---|---|---|
| A5.1 | Foreground-service GPS recording with accuracy per fix; live "GPS weak" indicator | *manual* `GP-01.md`, `GP-03.md` (screen off, gap recorded not interpolated) |
| A5.2 | Fixes persisted incrementally; interrupted walk marked incomplete; resume or discard | `it('GP-04 killed walk keeps fixes and offers resume')` |
| A5.3 | Submit as `trace.submit` with gaps and start access point / end entrance | Op payload validates against the contract |

## A6 Mapper tasks and consent (⟵ B7, B8, B6.11)

| # | Task | Done when |
|---|---|---|
| A6.1 | Task list by priority, task detail with evidence, complete via `task.complete`, "still true?" checks | Completing offline syncs later |
| A6.2 | Grievance on a resident's behalf (`grievance.create`) | Op queued with photo declaration |
| A6.3 | Consent capture per scope; separate queue; purge on `201`; keep on `503` | `it('PV-05 consent purged after vault ack, never in op queue')` |
| A6.4 | Claim code display (QR + 6 digits, expiry countdown); clear message when offline | Code shown from `POST /units/{id}/claim-codes` |

## A7 Resident mode (⟵ B6.3, B6.11, B8)

| # | Task | Done when |
|---|---|---|
| A7.1 | Claim by QR or 6 digits; specific messages for expired / used / mistyped / rate-limited | `it('RS-01 claim errors are specific')` |
| A7.2 | Code display large, spoken form written out, TTS when available | `it('RS-06 no TTS still shows phonetic form')` |
| A7.3 | Multiple bindings, notices (code changed, merged, retired), unbind (asks about consent), revoke old device | `it('RS-02 ...')`, `it('RS-03 ...')`, `it('RS-04 unbind asks about consent')`, `it('RS-05 shows updated code notice')` |
| A7.4 | SOS: confirm, one `Idempotency-Key` per intent, "SOS already sent" on second tap, works without GPS | `it('DS-01 second tap shows already sent')`, `it('DS-06 SOS without GPS fix')` |
| A7.5 | Offline SOS → SMS intent to the test number with code, coordinates, time; fallback explained | *manual* `DS-05.md`; guard from A0.5 |
| A7.6 | Reports from the claimed unit; consent view and withdraw | Withdrawal reflects on next consent view |

## A8 Console shell (⟵ B6.1)

| # | Task | Done when |
|---|---|---|
| A8.1 | Vite + React app, login, role-based navigation (dispatcher never sees service history) | `it('PV-09 dispatcher has no service history option')` |
| A8.2 | Live channel: ticket → WebSocket, store last cursor, reconnect with backoff, replay, visible "reconnecting" | Playwright: kill socket mid-stream, no event lost or duplicated (DS-03) |
| A8.3 | `401 ACCOUNT_DISABLED` signs out; role change applied on next request / WS close 4403 | `it('AC-02 ...')`, `it('AC-04 ...')` |
| A8.4 | Public-address QR page; banner on `system.public_address_changed` | *manual* `RT-01.md` (console side) |

## A9 Reviewer screens (⟵ B3, B5, B7, B9)

| # | Task | Done when |
|---|---|---|
| A9.1 | Clear lane with bulk approve; per-item failures shown | Own captures show approve disabled |
| A9.2 | Duplicate lane: side-by-side map + signals; merge (choose survivor) / distinct / defer | `it('ID-05 deferred stays visible')`, `it('ID-06 already-decided message')` |
| A9.3 | Edit reviews, retirement, code card print view | Printed card shows code, spoken form, QR |
| A9.4 | Tasks and grievances triage; photo flag/removal | Removed photo no longer loads |
| A9.5 | Accounts, devices (revoke shows at-risk counts), zones, access points | Revoke dialog lists counts |
| A9.6 | Graph: new-trace count, build, draft edges with support, remove edges, publish with unroutable confirmation | `it('GR-05 publish lists newly unroutable and needs confirmation')` |
| A9.7 | Imagery runs and candidates view | Shows which signal(s) fired |

## A10 Dispatcher screens (⟵ B6, B5, B8)

| # | Task | Done when |
|---|---|---|
| A10.1 | Incident board; SOS card persists until acknowledged; escalation (sound + highlight) | `it('DS-02 unacked SOS shown loudly on connect')`, `it('DS-04 escalates until acked')` |
| A10.2 | New call; lock / read-only "handled by X" / takeover with confirmation | `it('DS-09 ...')`, `it('DS-10 ...')` |
| A10.3 | Code entry: validate check char before lookup; forgiving input; retired / not-issued messages | `it('ID-09 ...')`, `it('ID-10 ...')`, `it('ID-11 ...')`, `it('ID-12 ...')` |
| A10.4 | Location-share link/QR; landmark/attribute search; nearest structures to a shared position; method recorded | `it('DS-11 ...')` |
| A10.5 | Route preview with every refusal and warning; pinned version; "newer graph — recompute"; origin picker defaulting to nearest | `it('GR-01 ...')` through `it('GR-07 ...')` (GR-01, 02, 03, 04, 06, 07) |
| A10.6 | SOS position vs registered location, retired-location flag | `it('DS-07 ...')`, `it('DS-08 ...')` |
| A10.7 | Occupant context panel: none / granted fields / "identity service unavailable" | `it('PV-01 ...')`–`it('PV-04 ...')` |
| A10.8 | Assignment + responder link (share / QR / copy); revoke / reissue; reissue prompt after address change; outcome + timeline | `it('DS-17 address change offers reissue')` |

## A11 Public pages (⟵ B6.7, B6.8, B7.5)

| # | Task | Done when |
|---|---|---|
| A11.1 | Responder page: route map + steps + entrance photo, cached for offline; outcome buttons queue offline with press time | `it('DS-16 outcome queued offline keeps pressed time')`, `it('DS-14 ended link shows nothing')` |
| A11.2 | Responder evidence: note, tags, photo, position | `it('DS-18 reached sends position')` |
| A11.3 | Caller location-share page: "location sent" only; denied permission → landmark text | `it('DS-12 ...')`, `it('DS-13 ...')` |
| A11.4 | Public report form: code validation, retired → replacement, photo retried separately | `it('GV-04 ...')`, `it('GV-05 ...')` |
| A11.5 | Forwarded-link check: page shows only its incident | `it('DS-15 ...')` |

## Order

1. A0 (all), then **A2** (unblocks B5), then A1.
2. A3 → A4 → A5 against the mock; integrate with B2 when B says sync is real (J2 A3↔B2).
3. A8 as soon as B6.1 lands; then A10 and A11 (share map code).
4. A9 as B3/B5/B7 land; A6 and A7 when B6.11 and B8 land.
5. J1 field campaign needs A3–A5 working against the real server.

## Review asks for the contract (please answer before B starts B2)

- Do the screens you plan need any field the schemas don't have? (Additions are cheap now.)
- Error codes: does `A0.4` have enough information per code to write a specific message?
- See the open questions at the end of [person-b-services.md](person-b-services.md); several affect resident UX.
