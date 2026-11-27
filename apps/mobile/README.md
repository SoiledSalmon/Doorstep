# apps/mobile: Doorstep Android app

One Android app with two modes. Owner: **Person A**. Status: **not started** (plan tasks A3–A7).

| Mode | Who | What it does |
|---|---|---|
| Mapper | Field mappers (staff accounts) | Works fully offline: downloads the zone, records GPS walks, confirms or adjusts bootstrap building footprints, adds entrances, units, photos and service records, captures consent, shows claim codes, completes verification tasks, syncs when a connection appears |
| Resident | Residents (made-up personas in the pilot) | Claims a unit with a one-time code, shows and speaks the unit's code, sends SOS (falls back to an SMS to the configured **test** number when offline), files reports, views and withdraws consent |

- **Stack:** React Native + Expo (dev build, not Expo Go), TypeScript, Android only, SQLite on the device,
  bundled campus basemap (PMTiles).
- **Talks to:** the core API through [`api/openapi.yaml`](../../api/openapi.yaml), with generated types. Until
  Person B's endpoints land, it runs against a mock server generated from the contract.
- **Rules that matter most here:** every capture works offline and syncs idempotently; consent goes to a
  separate queue and is purged after the vault confirms it; never call or text a real emergency number.
- **Edge cases owned:** SY-01/02/09–12/14/15, GP-01–08, ID-02, PV-05, DS-01/05/06/20, RS-01–06.
- **Plan:** [docs/plans/person-a-clients.md](../../docs/plans/person-a-clients.md), sections A0 and A3–A7.
