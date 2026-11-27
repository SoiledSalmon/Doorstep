# Person B plan: services and data (Python)

**Scope:** workstreams B1 to B9 from the [work split](../specs/2026-11-27-doorstep-work-split.md).
**Contract:** [`api/openapi.yaml`](../../api/openapi.yaml), [`api/vault.yaml`](../../api/vault.yaml). You own both;
change them first, then tell A.
**Fixtures:** [`fixtures/`](../../fixtures/README.md). Seed and code vectors are already defined.

Each task is small enough for one PR. "Done when" is the acceptance check; it must be an automated test
unless marked *manual*. Tests are named after edge-case IDs (`test_SY03_...`).

## Decisions already made in S0 (change only with A)

- Check character: Luhn mod 32 over prefix+body. Reference implementation and vectors in `fixtures/`.
- Client-generated UUIDs for everything capturable offline; the server never trusts device time for ordering.
- Sync push: ordered per device by `seq`; `duplicate` / `deferred` / `rejected` / `sent_for_review` results.
- Every other state-changing POST needs `Idempotency-Key`; keys are claimed with a unique constraint and kept forever.
- Consent never enters the registry or the sync stream: `POST /consents` forwards straight to the vault.
- Live events: one global `bigint` cursor sequence, events kept forever, WebSocket with ticket auth plus `GET /events`.
- Routing refusals are `422` with `OUTSIDE_NETWORK`, `NO_ROUTE`, `NO_GRAPH_PUBLISHED`, `ORIGIN_INVALID`.

## B1 Runtime

| # | Task | Done when |
|---|---|---|
| B1.1 | Install Docker Desktop (not on the laptop yet). `docker-compose.yml`: `registry-db` (PostGIS), `vault-db` (Postgres), `api`, `worker`, `vault`, `console` (static). Vault DB on an internal network only; separate credentials in `.env`. `.env.example` lists every variable | `docker compose up` from clean starts all services; `vault-db` is unreachable from the `api` container except via `vault` |
| B1.2 | Startup guard: refuse to start if `TEST_DISPATCH_NUMBER` is unset or on `fixtures/emergency-numbers.json` | `test_DS20_server_refuses_unsafe_test_number` |
| B1.3 | Migrations tool (Alembic) for both DBs; seed loader reading `fixtures/seed/*.json`; first admin seeded from `SEED_ADMIN_PASSWORD` | Fresh DB + seed gives the fixture counts; seed load is idempotent |
| B1.4 | `scripts/tunnel` starts `cloudflared` Quick Tunnel, parses the URL, records it so `GET /admin/public-address` returns it and emits `system.public_address_changed` | *manual* `docs/manual-tests/RT-01.md`: restart → new URL shown as QR |
| B1.4b | Document the phone-hotspot fallback for when campus Wi-Fi is down | *manual* `docs/manual-tests/RT-02.md`: phones on mobile data reach the laptop through the tunnel |
| B1.5 | `scripts/reset` (and `POST /admin/demo-reset`): restore seed; keep field capture unless `--include-field-capture` | `test_RT04_reset_keeps_field_capture_by_default` |
| B1.6 | `scripts/backup`: dated archive of both DB dumps + photo volume | `test_RT06_backup_contains_both_dbs_and_photos` |
| B1.7 | `GET /health` with per-component status; API stays up with DB or vault down | `test_RT05_health_degraded_when_vault_down` |
| B1.8 | Request cap: bounded concurrency returning `503 SERVER_BUSY` with `Retry-After` | `test_RT03_overload_returns_server_busy` |
| B1.9 | Add run/test/reset commands to `README.md` and `CLAUDE.md` | Commands work from a fresh clone |

## B2 Core API base

| # | Task | Done when |
|---|---|---|
| B2.1 | FastAPI skeleton; response models generated or checked against `openapi.yaml`; the single `Error` shape; exception handler that never leaks stack traces | Contract test: every route in the spec exists with the right status codes (schemathesis or equivalent) |
| B2.2 | Log scrubber: structured logs, no request bodies on consent/occupant routes | Covered later by B8.6 privacy scan |
| B2.3 | Accounts, login with throttling, refresh tokens (long-lived), logout, `/me`; role re-read from DB every request; disabled → `401 ACCOUNT_DISABLED` | `test_AC01_login_throttled`, `test_AC02_disabled_rejected_next_request`, `test_AC04_role_change_next_request`, `test_SY02_refresh_after_offline_period` |
| B2.4 | Idempotency middleware: unique-constraint claim, request hash, replay with `Idempotent-Replayed`, `422 IDEMPOTENCY_KEY_REUSED`, `409 IDEMPOTENCY_IN_FLIGHT` | Concurrency test with two parallel identical requests → one effect |
| B2.5 | Devices: register, revoke (records last pending counts in audit), `X-Device-Id` check → `403 DEVICE_REVOKED` | `test_SY14_revoked_device_rejected`, `test_PV06_revocation_audits_at_risk_counts` |
| B2.6 | Audit log table + `GET /audit`; every review, lock, disclosure and admin action writes one row | Audit rows asserted in the tests of those features |
| B2.7 | Zones, access points (inside boundary, `OUTSIDE_ZONE`), zone package with cursor | `test_GP05_pin_outside_zone_rejected`, `test_SY16_package_cursor_then_pull_is_current` |
| B2.8 | Change log: every registry write appends a row with the next cursor (same transaction) | Pull test sees every write exactly once |
| B2.9 | `POST /sync/push`: per-device seq, op dispatch per type, results per op, `sent_for_review` for merged/retired targets | `test_SY03_replayed_op_applies_once`, `test_SY04_interrupted_batch_resumes_in_order`, `test_SY06_edit_on_merged_goes_to_review`, `test_SY07_edit_on_coded_structure_applies`, `test_SY08_device_clock_ignored_for_order` |
| B2.10 | Field-level merge for `structure.update` (per-field version, later receipt wins, loser to history + `EditReview`) | `test_SY05_same_field_conflict_flagged` |
| B2.11 | `GET /sync/pull` paginated by cursor, scoped to device zones | `test_SY13_large_pull_paginates_and_resumes` |
| B2.12 | Photos: declare via `photo.attach`, `PUT` with SHA-256 check, EXIF strip, thumbnail, size limit, delete | `test_SY11_photo_retry_no_duplicate`, `test_GP07_photo_removal_deletes_both_files` |
| B2.13 | `GET /config` from env | Returns test number and thresholds |

## B3 Dedup and codes

| # | Task | Done when |
|---|---|---|
| B3.1 | Code module: generate, normalise, validate. Port `fixtures/build_fixtures.py` logic | Passes every case in `fixtures/codes/vectors.json` |
| B3.2 | Issuance: random body, insert into a codes table whose unique constraint covers issued **and** retired codes, retry on conflict | `test_ID08_collision_with_retired_retries` (force generator to collide) |
| B3.3 | Duplicate signals on sync: proximity, footprint overlap, same-candidate; never between units of one building | `test_ID01_two_offline_captures_one_review_item`, `test_ID02_new_pin_on_candidate_raises_duplicate`, `test_ID07_units_same_building_never_duplicates` |
| B3.4 | Review lanes and `GET /review/items`; `capturedByMe` | Clear vs duplicate lanes match seed |
| B3.5 | Approvals (bulk, per-item result, version check, no own captures, blocked while duplicate undecided) | `test_ID06_concurrent_approve_issues_once`, `test_AC03_cannot_approve_own_capture` |
| B3.6 | Duplicate decisions: merge (move units/entrances/photos/services/bindings, retire loser's code with pointer), distinct (suppress same signals), defer | `test_ID03_merge_moves_children_and_retires_code`, `test_ID04_distinct_not_raised_again`, `test_ID05_deferred_stays_visible_no_code`, `test_ID06_second_decision_already_decided` |
| B3.7 | Edit reviews (`/review/edits`) | Decisions apply or discard the queued edit |
| B3.8 | Code lookup + retirement + code card | `test_ID09_bad_check_char`, `test_ID10_forgiving_input`, `test_ID11_retired_shows_replacement_no_location`, `test_ID12_never_issued_logged`, `test_ID13_retire_unbinds_and_warns` |
| B3.9 | Dedup evaluation script on a labelled set (precision/recall) | `pipelines/eval_dedup.py` prints metrics on seed + deliberate duplicates |

## B4 Bootstrap import

| # | Task | Done when |
|---|---|---|
| B4.1 | Script: Open Buildings v3 footprints clipped to the zone → `candidate` structures with confidence (idempotent by source ID) | Running twice creates no duplicates; candidates appear in the zone package |
| B4.2 | Bootstrap metric: share confirmed / adjusted / rejected / missed | `pipelines/eval_bootstrap.py` reports on the seed candidates |

## B5 Graph engine (⟵ needs A2 ground truth for B5.6+)

| # | Task | Done when |
|---|---|---|
| B5.1 | Trace storage + accuracy filter (stored, excluded from builds above threshold) | `test_GP01_low_accuracy_fixes_excluded` |
| B5.2 | Graph versions table + `building → draft / failed` worker job; `GET /graph/status` with new-trace count | Build of seed traces yields a draft with metrics |
| B5.3 | Hybrid build (adaptive seeds, map-matched backbone, trace-supported bridges, unsupported-edge suppression); edges carry support and provenance | Unit tests on small synthetic layouts (T-junction, parallel alleys, noise) |
| B5.4 | Snapping of entrances and access points per version; `GET .../snaps` | `test_GR01_far_entrance_outside_network_with_distance` |
| B5.5 | Edge removal on drafts, copy-to-draft, publish with newly-unroutable confirmation | `test_GR05_publish_requires_confirming_unroutable`, `test_GR08_remove_edge_in_new_version` |
| B5.6 | Routing (A*) with refusals and pinning | `test_GR02_no_entrance_approximate`, `test_GR03_disconnected_no_route_with_nearest`, `test_GR04_route_pinned_newer_flagged`, `test_GR06_no_published_graph`, `test_GR07_default_nearest_access_point` |
| B5.7 | Synthetic trace generator from A2 ground truth (several seeds, GPS noise model) | Generator output loads as traces |
| B5.8 | Evaluation harness: edge precision/recall, spurious edges, usable-route rate, reach, components | `pipelines/eval_graph.py` prints the design §11 table for synthetic seeds |

## B6 Dispatch backend

| # | Task | Done when |
|---|---|---|
| B6.1 | Live events: append-only table with cursor; `POST /live/tickets`; WebSocket with hello/replay/ping; `GET /events`; role filtering; close codes | `test_DS03_reconnect_replays_missed_events` (no gaps, no duplicates) |
| B6.2 | Incidents: create, list, get, timeline, status machine | Invalid transitions return `409` |
| B6.3 | SOS ingest (idempotent, already-open dedupe, flags: no position, far from unit, retired location) | `test_DS01_double_sos_one_incident`, `test_DS02_sos_persists_without_console`, `test_DS06_no_gps_uses_registered`, `test_DS07_far_position_flagged`, `test_DS08_retired_unit_flagged` |
| B6.4 | Acknowledgement + escalation timer emitting `incident.escalated` | `test_DS04_unacked_sos_escalates` |
| B6.5 | Lock: claim, renew, expiry, takeover (audited), read-only for others | `test_DS09_second_dispatcher_locked_out`, `test_DS10_lock_expires_and_takeover_audited` |
| B6.6 | Locate (records method) | `test_DS11_locate_method_recorded` |
| B6.7 | Location-share tokens: create, status, submit (resubmission flag, landmark text), expiry | `test_DS12_expired_and_resubmitted_share`, `test_DS13_landmark_text_reaches_incident` |
| B6.8 | Responder assignments: token, view (route or refusal reason), revoke/reissue, outcome (queued `pressedAt`), photos | `test_DS14_closed_link_shows_ended`, `test_DS15_forwarded_link_one_incident_only`, `test_DS16_queued_outcome_keeps_pressed_time`, `test_DS18_reached_far_raises_p2` |
| B6.9 | Tunnel change marks active links stale and emits `system.public_address_changed` with affected incidents | `test_DS17_address_change_lists_active_incidents` |
| B6.10 | Cancel and close revoke tokens; cancel raises no task | `test_DS19_cancel_revokes_no_task` |
| B6.11 | Claim codes and resident bindings: create, redeem (expired/used/invalid, rate limit), unbind, peers, follow merges | `test_RS01_claim_code_errors_and_rate_limit`, `test_RS02_revoke_old_device`, `test_RS03_multiple_residents`, `test_RS04_unbind_keeps_consent`, `test_RS05_binding_follows_merge` |

## B7 Feedback loop

| # | Task | Done when |
|---|---|---|
| B7.1 | Tasks + evidence events with weights; `task.complete` sync op updates `lastVerified`/`verificationMethod` | Completing a task updates the structure; only `task.complete` changes ground truth |
| B7.2 | Failure → P1 task with evidence (dispatcher `failed`, responder `couldnt_find`); `path_problem` → graph task | `test_GR08_path_problem_raises_graph_task` + P1 assertion |
| B7.3 | Grievances: submit (resident, mapper op, public), state machine, corroboration by weight threshold, decision | `test_GV03_independent_reports_corroborate_then_confirm` |
| B7.4 | Rate limits per device/account/IP; location cross-check | `test_GV01_flood_rate_limited`, `test_GV02_far_report_marked_mismatch` |
| B7.5 | Public report: code validation, retired → replacement, photo upload token | `test_GV05_invalid_and_retired_code_messages`, `test_GV04_text_first_photo_later` |
| B7.6 | Stale-record task generator (P4) and photo-missing reminders | `test_GP06_missing_photo_raises_reminder` |

## B8 Consent vault

| # | Task | Done when |
|---|---|---|
| B8.1 | Vault service + DB + service token; capture, list, withdraw, delete identity | Vault contract tests pass; vault tables have no geometry columns |
| B8.2 | Disclosure check with audit (including "none granted") | `test_PV01_no_consent_audited_none`, `test_PV02_name_only` |
| B8.3 | Core: `/consents` forwarder (stores nothing), unit/resident consent views and withdrawals | `test_PV05_consent_never_in_registry_or_sync` |
| B8.4 | Core: occupant context per incident, `no-store`, `vault_unavailable` fallback | `test_PV03_withdrawn_hidden_on_next_view`, `test_PV04_vault_down_dispatch_continues` |
| B8.5 | Removal request actions (archive service detail, unbind, delete identity) | `test_PV07_removal_request_archives_and_audits` |
| B8.6 | Privacy scan: dump every registry table, log file and export; fail if any `fixtures/seed/vault.json` value appears | `test_PV08_no_persona_values_in_registry_logs_exports` runs in CI |

## B9 Imagery (last priority; can move to A)

| # | Task | Done when |
|---|---|---|
| B9.1 | Register Earth Engine noncommercial project; auth from a local credential file (git-ignored) | Script lists one Sentinel-2 scene for the zone |
| B9.2 | Baseline signal per cell from Open Buildings 2.5D Temporal (latest years to 2023) | Cells with presence/count deltas |
| B9.3 | Recent signal from cloud-masked Sentinel-2 composites, same season both windows, skip a window with too few scenes | `test_IM04_too_few_scenes_skips_recent`, `test_IM05_windows_same_season_recorded` |
| B9.4 | Rank (both signals above one) and import via `POST /imagery/runs` (atomic, runKey idempotent, evidence to overlapping open tasks) | `test_IM01_failed_run_imports_nothing`, `test_IM02_rerun_no_duplicates`, `test_IM03_overlap_adds_evidence`, `test_IM06_single_signal_lower_rank` |

## Order and hand-offs to A

1. B1.1–B1.3, B2.1–B2.4 first (A integrates A3 against these).
2. B2.5–B2.13 → tell A sync is real (J2 pair A3↔B2).
3. B4, then B3 (A9 needs review API).
4. B6.1 early: A8's live channel depends on it more than on incidents.
5. B5 as soon as A2 lands; B6 and B7 in parallel with B5's later tasks; B8 any time (independent).
6. B9 last.

## Open questions for the team (blocking nothing yet)

1. **Claim codes need connectivity.** The mapper's phone must be online to issue one (codes are server-issued and the
   unit must exist server-side). Acceptable, or do we pre-issue a pool per device?
2. **Revoking another device's binding** (`/residents/me/bindings/{id}/peers`) lets housemates revoke each other.
   Keep, or limit to admin/mapper?
3. **SOS dedupe by binding:** a second SOS from the same binding while one is open returns the open incident. OK?
4. **Seed zone** is a placeholder square; who supplies the real campus boundary, and which 2-letter prefix?
