# services/vault: Doorstep consent vault

The only place personal data lives. Owner: **Person B**. Status: **not started** (plan task B8).

- **Holds:** made-up persona identities (name, phone, access notes), consent records per scope
  (*name*, *phone*, *notes* to dispatch), and an audit of every disclosure check.
- **Never holds:** locations or geometry. It knows units only by opaque ID.
- **Implements:** [`api/vault.yaml`](../../api/vault.yaml). Only the core API calls it, with a service token,
  on an internal Docker network; it is never exposed through the tunnel.
- **Stack:** FastAPI (Python), its own PostgreSQL instance with its own credentials.
- **Behaviour that matters:** no consent means no occupant context (the default); every disclosure check is
  audited, including ones that grant nothing; withdrawal takes effect on the next view; if the vault is down,
  dispatch continues without occupant context.
- **Edge cases owned:** PV-01–08.
- **Plan:** [docs/plans/person-b-services.md](../../docs/plans/person-b-services.md), section B8.
