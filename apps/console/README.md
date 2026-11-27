# apps/console: Doorstep web console and public pages

The browser side of Doorstep. Owner: **Person A**. Status: **not started** (plan tasks A8–A11).

| Surface | Who | What it does |
|---|---|---|
| Console | Admin, reviewer, dispatcher (login) | Review queues and code issuance, graph review and publish, tasks and grievances, accounts and zones; for dispatchers, a live incident board with SOS cards, code lookup, routing, consent-permitted occupant context, responder assignment |
| Public pages | Responders, callers, the public (no login, token links) | Responder route page with *Reached* / *Couldn't find*; caller location-share page; public report form |

- **Stack:** React + MapLibre GL JS, TypeScript, same campus basemap as the app.
- **Talks to:** the core API through [`api/openapi.yaml`](../../api/openapi.yaml), plus a WebSocket live
  channel that catches up by cursor after any reconnect (no event may be lost).
- **Rules that matter most here:** dispatchers never see service history; routing refusals are shown, never
  replaced by a straight line; user-facing errors are specific, never raw codes or stack traces.
- **Edge cases owned:** DS-02–04/07–18, ID-05/06/09–12, GR-01–07, PV-01–04/09, GV-04/05, AC-02/04, RT-01 (console side).
- **Plan:** [docs/plans/person-a-clients.md](../../docs/plans/person-a-clients.md), sections A0 and A8–A11.
