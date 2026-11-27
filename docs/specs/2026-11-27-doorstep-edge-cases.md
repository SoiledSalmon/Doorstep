# Doorstep — Edge-Case Catalogue

**Companion to:** [`2026-11-27-doorstep-design.md`](2026-11-27-doorstep-design.md)

Each entry is a situation and the behaviour the product **must** show. IDs are stable so tests can reference them: name each test after its ID. "Manual" marks cases that need a scripted manual test (GPS, airplane mode, physical devices); everything else needs an automated test.

---

## A. Offline capture and sync

| ID | Situation | Required behaviour |
|---|---|---|
| SY-01 | Mapper captures with no connectivity for hours | Every screen works from local storage; nothing waits on the network. *(Manual)* |
| SY-02 | Login session expires while offline | Capture continues. At next connection, the app re-authenticates (refresh, or prompt for password), then syncs. No queued data is discarded |
| SY-03 | The same operation is pushed twice (retry, flaky network) | The server applies it once and returns the same result both times |
| SY-04 | Push is interrupted mid-batch | Applied operations stay applied; the rest are retried; ordering per device is preserved |
| SY-05 | Two mappers edit the same field of a confirmed structure offline | Field-level merge per the [PRD](../PRD.md#61-structure-identity--dedup); when both changed the same field, the later server-received edit wins and the other is kept in history and flagged for review |
| SY-06 | Mapper edits a structure offline that a reviewer has since merged or retired | The edit is not applied or dropped silently; it goes to the review queue attached to the surviving or retired record, and the mapper sees "sent for review" |
| SY-07 | Mapper edits a structure offline that has since gained a code | Edit applies; the app shows the new code after pull |
| SY-08 | Device clock is wrong | Server ordering uses server receipt and per-device sequence, never device timestamps; device time is stored only as reported capture time |
| SY-09 | Logout or "clear data" with unsynced operations or photos | A blocking warning states the exact count of unsynced items and that they will be lost; the user must confirm |
| SY-10 | App uninstalled with unsynced data | Cannot be prevented; the persistent "N items not synced" indicator must make this unlikely. Documented as a known risk |
| SY-11 | Photo upload fails repeatedly | Records stay synced; photos retry with backoff; the item shows "photo pending"; no duplicate photos on retry |
| SY-12 | Device storage nearly full | Capture of photos is blocked with a clear message before writes fail; text capture continues |
| SY-13 | Pull returns a very large change set | Pull is paginated by cursor; an interrupted pull resumes from the last cursor |
| SY-14 | Revoked device tries to sync | Server rejects with a specific error; the app tells the user to contact admin and keeps local data until they decide |
| SY-15 | Server address changed (new tunnel URL) | The app detects that the server can't be reached; the mapper scans the new address QR from the console; queued data then syncs normally |
| SY-16 | Zone package is outdated (mapper offline for days) | On reconnect, pull brings it current; the app never assumes local copies of others' records are current for review decisions |

## B. Identity, dedup and codes

| ID | Situation | Required behaviour |
|---|---|---|
| ID-01 | Two mappers capture the same building offline | Both sync; one review item in the "possible duplicate" lane; no code issued until a decision |
| ID-02 | A mapper captures a building where a bootstrap candidate exists | The capture links to the candidate (confirm/adjust) instead of creating a second record, when the mapper chose it; if the mapper dropped a new pin instead, it raises a duplicate candidate |
| ID-03 | Reviewer chooses *merge* | One record survives; the other points to it; units, entrances, photos, services and history move or link to the survivor; if both had codes (shouldn't happen pre-issuance, but possible after edits), the loser's code is retired with a pointer |
| ID-04 | Reviewer chooses *distinct* | Both proceed to approval; the pair is not raised again for the same signals |
| ID-05 | Reviewer chooses *defer* | Neither gets a code; item stays in the queue, visibly deferred |
| ID-06 | Two reviewers act on the same item at once | The second sees that it was already decided; no double issuance |
| ID-07 | Units inside one building are close together | Proximity between units of the same building never raises duplicate candidates |
| ID-08 | Code generator produces a code already used or retired | Never issued; generator retries; issuance is atomic with the uniqueness check |
| ID-09 | Dispatcher types a code with a typo | Check character fails, giving "invalid code — ask the caller to repeat"; no lookup attempted |
| ID-10 | Dispatcher types `rv 7k3m x`, `RV-7K3M-X`, or with O/0, I/1 confusion | Normalised and accepted |
| ID-11 | Code is valid but retired | Lookup shows "retired" with reason and replacement (if merged), never a stale location as if current |
| ID-12 | Code valid in format but never issued | "No such code"; logged for review (possible misprint or abuse) |
| ID-13 | Structure confirmed demolished | Code retired, record archived, units' residents unbound with notice, open incidents and tasks warned |

## C. Mapping and GPS

| ID | Situation | Required behaviour |
|---|---|---|
| GP-01 | GPS accuracy worse than the acceptance threshold | The fix is stored with its accuracy but excluded from graph building; the mapper sees a live "GPS weak" indicator. *(Manual)* |
| GP-02 | GPS permission denied or location services off | Mapper mode explains why it's needed and links to settings; capture without location is blocked for pins and walks |
| GP-03 | App backgrounded or screen off during a walk | Recording continues (foreground service with notification); a gap in fixes is recorded as a gap, not interpolated. *(Manual)* |
| GP-04 | Walk recording interrupted (app killed, battery) | Fixes recorded so far are kept; the walk is marked incomplete; the mapper can resume or discard |
| GP-05 | Pin dropped outside the zone | Rejected with a message; zone boundary visible on the map |
| GP-06 | Camera permission denied | Capture proceeds without photo; the record is marked "photo missing" and a reminder task appears |
| GP-07 | Photo captures a face | Capture guidance tells mappers to photograph exteriors and doorways only; reviewers can flag a photo for removal; removal deletes the original and thumbnail |
| GP-08 | Bootstrap footprint badly wrong | Mapper can adjust vertices or reject it; rejection is recorded for the bootstrap metric |

## D. Graph and routing

| ID | Situation | Required behaviour |
|---|---|---|
| GR-01 | Target entrance farther from the network than the snap threshold | Route request returns `OUTSIDE_NETWORK` with distance; console shows the location without a route and raises a verification task for that entrance |
| GR-02 | Structure has no entrance recorded | Route goes to the nearest network point to the building centroid, labelled "approximate — no entrance mapped" |
| GR-03 | No path exists between access point and target (disconnected graph) | `NO_ROUTE`, with the nearest reachable point offered; never a straight line drawn as if walkable |
| GR-04 | Graph rebuilt while a dispatcher is viewing a route | The route stays pinned to the version it was computed on; the console offers "newer graph available — recompute" |
| GR-05 | Reviewer publishes a draft that disconnects previously routable entrances | Publishing shows the list of entrances that would become unroutable and requires explicit confirmation |
| GR-06 | No published graph yet | Routing returns a clear "no network published"; lookup still shows location |
| GR-07 | Origin access point not set or invalid | Dispatcher must choose one; the default is the nearest access point to the target |
| GR-08 | Spurious edge (e.g. through a wall) in a published graph | Reviewer removes the edge in a new version; responder "couldn't find" evidence that mentions a path problem raises a graph task |

## E. Dispatch, SOS and responders

| ID | Situation | Required behaviour |
|---|---|---|
| DS-01 | Resident taps SOS twice or the request retries | Exactly one incident (client-generated ID); the second tap shows "SOS already sent" |
| DS-02 | SOS arrives while no console is open | Incident persists; the next console to connect shows it as unacknowledged, loudly |
| DS-03 | Console's live connection drops and reconnects | Client catches up from its last event cursor; no event lost; a visible "reconnecting" state while down |
| DS-04 | SOS not acknowledged within a set time | Card escalates (repeats sound, highlights) until acknowledged |
| DS-05 | SOS with no mobile data | App opens SMS to the configured test number with code + coordinates + time; explains that it's a fallback. *(Manual)* |
| DS-06 | SOS without a GPS fix | Sent with the claimed unit only; dispatcher sees "position unavailable — using registered location" |
| DS-07 | SOS device position far from the claimed unit | Both shown; dispatcher warned "caller may not be at home" |
| DS-08 | SOS from a resident whose unit was retired | Incident still created, flagged "registered location retired" |
| DS-09 | Two dispatchers open the same incident | Either may view; the first to claim/assign holds the lock; the other sees "handled by X" and read-only controls |
| DS-10 | Lock holder disappears (closed tab, crash) | Lock expires after inactivity or can be taken over with confirmation, audited |
| DS-11 | Caller doesn't know the code | Dispatcher uses location-share link or landmark/attribute search; incident records which method located it |
| DS-12 | Location-share link opened after expiry, twice, or by someone else | Expired gives a clear message; a second submission updates the position and is marked as a resubmission; no data is shown to the opener beyond "location sent" |
| DS-13 | Caller denies browser location permission | Page explains how to allow it and offers "describe a landmark" text instead, which goes to the incident |
| DS-14 | Responder link opened after incident closed or link revoked | "This dispatch has ended"; no route or details shown |
| DS-15 | Responder link forwarded to someone else | Link still only shows that one incident; expires at close; dispatcher can revoke and reissue |
| DS-16 | Responder loses connectivity mid-route | Route stays visible from cache once loaded; outcome taps queue and send when back online, marked with the time pressed |
| DS-17 | Tunnel restarted, so old responder and location links are dead | Console shows "public address changed" and offers reissue for active incidents |
| DS-18 | Responder reports *reached*, but at a different place than expected | Their position is stored as evidence; if far from the entrance, a P2 verification task is raised |
| DS-19 | Incident cancelled (false alarm) | Status cancelled with reason; tokens revoked; no verification task |
| DS-20 | Any "call" or SMS action | Uses only the configured test number; the app refuses to run if that number is unset or equals a known emergency number |

## F. Residents and claim

| ID | Situation | Required behaviour |
|---|---|---|
| RS-01 | Claim code expired, used, or mistyped | Specific message for each; mistyped attempts rate-limited |
| RS-02 | Resident gets a new phone | Needs a new claim code from a mapper; old device binding can be revoked by the resident (from either device) or admin |
| RS-03 | Several residents claim the same unit | Allowed; each binding independent |
| RS-04 | Resident unbinds | Binding removed; consent records are unaffected unless the resident also withdraws them (the app asks) |
| RS-05 | Resident's unit gets a different number or is merged | Binding follows the surviving unit; resident sees the updated code with a notice |
| RS-06 | Text-to-speech unavailable on the device | Code still shown large with its spoken (phonetic) form written out |

## G. Consent and privacy

| ID | Situation | Required behaviour |
|---|---|---|
| PV-01 | Dispatch lookup for a unit with no consent | No occupant context shown; disclosure check still audited as "none granted" |
| PV-02 | Consent granted for name only | Dispatch sees name only; phone and notes are withheld |
| PV-03 | Consent withdrawn while an incident is open | Subsequent views no longer show the withdrawn fields; already-shown data is recorded in the audit |
| PV-04 | Vault service is down | Dispatch continues without occupant context, with a visible "identity service unavailable" notice; never blocks routing |
| PV-05 | Consent captured offline on a mapper's phone | Stored only until synced to the vault, then purged from the device; never in the registry sync stream |
| PV-06 | Lost or stolen mapper phone | Admin revokes the device; unsynced vault data on it is listed as at-risk in the audit; the document notes this residual risk |
| PV-07 | Removal request via grievance | Reviewer can archive the structure's service detail and unbind residents; the vault deletes the persona's identity on withdrawal; both audited |
| PV-08 | Error messages, logs or exports | Never include vault fields; an automated check scans registry tables and log output for persona test values |
| PV-09 | Dispatcher tries to open service history | Denied by role; the console doesn't show the option |

## H. Grievances

| ID | Situation | Required behaviour |
|---|---|---|
| GV-01 | Flood of reports from one device or account | Rate limit reached → rejected with "try later"; logged |
| GV-02 | Report location far from the structure it names | Accepted but marked "location mismatch"; weight not raised |
| GV-03 | Several independent reports on one structure | Status moves to corroborating, then confirmed when the weight threshold is met or a mapper verifies |
| GV-04 | Report with a photo but upload fails | Report text submitted; photo retries separately |
| GV-05 | Public form used with an invalid or retired code | Specific message; a retired code points to its replacement |

## I. Accounts and access

| ID | Situation | Required behaviour |
|---|---|---|
| AC-01 | Wrong password repeatedly | Throttled; admin can reset |
| AC-02 | Disabled account with an active session | Next request rejected; console signs out; app keeps local data and stops syncing |
| AC-03 | Mapper tries to approve their own structures | Not possible: mappers have no review rights; an admin who also maps can't approve their own captures |
| AC-04 | Role changed while logged in | Takes effect on the next request |

## J. Runtime and demo

| ID | Situation | Required behaviour |
|---|---|---|
| RT-01 | Laptop restarts | One command brings everything back with data intact; the new public address is shown as a QR in the console |
| RT-02 | Campus Wi-Fi down | Phones on mobile data reach the laptop through the tunnel (if the laptop has a connection, e.g. via hotspot); the documented fallback is a phone hotspot |
| RT-03 | Tunnel request cap (200 in flight) reached | Requests return a clear "server busy" error and retry; it shouldn't happen at pilot scale |
| RT-04 | Demo reset | One command restores the seeded state (zone, personas, structures, graph), without touching real campus capture unless explicitly asked |
| RT-05 | Database or vault container fails to start | Health page shows which part is down; the API reports degraded status instead of crashing |
| RT-06 | Backup | One command exports both databases and photos to a dated archive |

## K. Imagery pipeline

| ID | Situation | Required behaviour |
|---|---|---|
| IM-01 | Earth Engine quota or authentication fails | Job fails clearly; no partial tasks imported |
| IM-02 | Job run twice on the same period | No duplicate tasks |
| IM-03 | Change cell overlaps an area with an open task | Evidence is added to the existing task instead of creating a new one |
| IM-04 | Too few cloud-free Sentinel-2 scenes in a window | That window is skipped for the recent signal and the run says so; the baseline signal still runs |
| IM-05 | Seasonal change (monsoon greening, dry season) looks like built-up change | Compared windows cover the same season; the run records which windows were used |
| IM-06 | Only one of the two signals fires for a cell | Candidate created with lower rank and tagged with the signal that fired |
