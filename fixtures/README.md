# Shared fixtures (S0.3, S0.4)

Used by both sides: mocks, tests and demo reset all read these files. Do not hand-edit the JSON; change
`build_fixtures.py` and rerun it.

```
python fixtures/build_fixtures.py          # regenerate
python fixtures/build_fixtures.py --check  # CI: fail if the committed JSON is stale
```

| File | What |
|---|---|
| `codes/vectors.json` | Structure-code test vectors: valid codes, normalisation inputs, invalid inputs with the expected error code, spoken forms, phonetic list |
| `seed/registry.json` | Registry seed: zone, access points, staff accounts, devices, structures in every status, entrances, units, service records, retired codes, a duplicate pair, resident bindings. **No personal data.** |
| `seed/vault.json` | Vault seed only: made-up personas and their consent records, keyed by unit ID |
| `emergency-numbers.json` | Numbers the app and API must never call or text (DS-20) |

## Code format

`ZZ-XXXX-C`: zone prefix (2 chars) + body (4 chars) + check (1 char), all from the Crockford base32 alphabet
`0123456789ABCDEFGHJKMNPQRSTVWXYZ`. The check character is **Luhn mod 32** over the 6 prefix+body chars, so
every single-character typo is caught (the script proves this for every vector) and most adjacent
transpositions are. Zone prefixes must use the same alphabet, otherwise normalisation (`O→0`, `I/L→1`) would
corrupt them.

The design's example `RV-7K3M-X` is illustrative and does **not** pass the check; use the codes in
`vectors.json` in tests and docs.

## Seed coverage

| Seed item | Edge cases it exercises |
|---|---|
| `RV` main block: 2 entrances, 3 units, unit 2 uses the side door | routing to a unit's entrance, RS-03 |
| Store room: no entrance | GR-02 |
| Retired, merged into main block | ID-11 with replacement |
| Old canteen: retired, demolished | ID-11 without replacement, ID-13 |
| 3 bootstrap candidates with confidence | ID-02, GP-08, bootstrap metric |
| Two `pending_review` captures 0.5 m apart, by different mappers | ID-01, ID-03 to ID-06 |
| One `pending_review` capture with no signals | clear lane, bulk approve |
| Two dispatchers, two mappers | DS-09, SY-05 |
| Personas with none / name-only / full / withdrawn consent | PV-01, PV-02, PV-03 |

Placeholder: the zone polygon is a ~16-acre square, not the real campus. A1/A2 replace it with the real boundary.
Staff passwords are not in the seed; the API seeds them from environment variables (see the B1 plan).
