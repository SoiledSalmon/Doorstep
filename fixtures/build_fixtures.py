"""Builds the shared fixtures (S0.3 code vectors, S0.4 seed data) and self-checks them.

Run:  python fixtures/build_fixtures.py          (rewrites the JSON files)
      python fixtures/build_fixtures.py --check  (fails if committed JSON is stale)

The JSON outputs are committed so TypeScript code never needs Python to read them.
This file is the reference definition of the code check character: both the
console (TS) and the API (Python) must pass fixtures/codes/vectors.json.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32: no I, L, O, U
N = len(ALPHABET)
VAL = {c: i for i, c in enumerate(ALPHABET)}

PHONETIC = {
    **dict(zip("0123456789", ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"])),
    "A": "Alfa", "B": "Bravo", "C": "Charlie", "D": "Delta", "E": "Echo", "F": "Foxtrot", "G": "Golf",
    "H": "Hotel", "J": "Juliett", "K": "Kilo", "M": "Mike", "N": "November", "P": "Papa", "Q": "Quebec",
    "R": "Romeo", "S": "Sierra", "T": "Tango", "V": "Victor", "W": "Whiskey", "X": "X-ray", "Y": "Yankee",
    "Z": "Zulu",
}


# ---------- code algorithm (reference) ----------

def check_char(payload: str) -> str:
    """Luhn mod 32 over prefix+body (6 chars)."""
    factor, total = 2, 0
    for ch in reversed(payload):
        addend = factor * VAL[ch]
        factor = 1 if factor == 2 else 2
        total += addend // N + addend % N
    return ALPHABET[(N - total % N) % N]


def is_valid_compact(compact: str) -> bool:
    factor, total = 1, 0
    for ch in reversed(compact):
        addend = factor * VAL[ch]
        factor = 1 if factor == 2 else 2
        total += addend // N + addend % N
    return total % N == 0


def normalise(raw: str):
    """Returns (canonical_code, unit_or_None) or (None, error_code)."""
    code_part, _, unit_part = raw.partition("/")
    s = "".join(ch for ch in code_part.upper() if ch not in " -\t")
    s = s.replace("O", "0").replace("I", "1").replace("L", "1")
    if len(s) != 7 or any(ch not in VAL for ch in s):
        return None, "CODE_FORMAT_INVALID"
    unit = None
    if unit_part.strip():
        u = unit_part.strip()
        if not u.isdigit() or not 1 <= int(u) <= 999:
            return None, "CODE_FORMAT_INVALID"
        unit = int(u)
    if not is_valid_compact(s):
        return None, "CODE_CHECKSUM_INVALID"
    return f"{s[:2]}-{s[2:6]}-{s[6]}", unit


def spoken(code: str, unit=None) -> str:
    groups = code.split("-")
    out = ", ".join(" ".join(PHONETIC[c] for c in g) for g in groups)
    if unit is not None:
        out += ", unit " + " ".join(PHONETIC[c] for c in str(unit))
    return out


def make_code(prefix: str, rng: random.Random) -> str:
    body = "".join(rng.choice(ALPHABET) for _ in range(4))
    return f"{prefix}-{body}-{check_char(prefix + body)}"


# ---------- vectors ----------

def build_vectors():
    rng = random.Random(20261127)
    valid = [make_code("RV", rng) for _ in range(12)] + [make_code("ZQ", rng) for _ in range(4)]
    base = valid[0]
    compact = base.replace("-", "")

    normalise_cases = [
        {"input": base, "code": base, "unit": None},
        {"input": compact.lower(), "code": base, "unit": None},
        {"input": " ".join([compact[:2], compact[2:6], compact[6]]).lower(), "code": base, "unit": None},
        {"input": f"{base} / 2", "code": base, "unit": 2},
        {"input": f"{compact}/12", "code": base, "unit": 12},
    ]
    # O/0 and I/L/1 confusion: find valid codes containing 0 or 1 and type the look-alike letter.
    for code in valid:
        if "0" in code[3:]:
            normalise_cases.append({"input": code.replace("0", "O"), "code": code, "unit": None})
            normalise_cases.append({"input": code.replace("0", "o"), "code": code, "unit": None})
            break
    for code in valid:
        if "1" in code[3:]:
            normalise_cases.append({"input": code.replace("1", "l"), "code": code, "unit": None})
            normalise_cases.append({"input": code.replace("1", "I"), "code": code, "unit": None})
            break

    invalid_cases = [
        {"input": "", "error": "CODE_FORMAT_INVALID"},
        {"input": compact[:6], "error": "CODE_FORMAT_INVALID"},
        {"input": compact + "0", "error": "CODE_FORMAT_INVALID"},
        {"input": compact[:3] + "U" + compact[4:], "error": "CODE_FORMAT_INVALID"},
        {"input": compact[:3] + "*" + compact[4:], "error": "CODE_FORMAT_INVALID"},
        {"input": f"{base} / 0", "error": "CODE_FORMAT_INVALID"},
        {"input": f"{base} / A", "error": "CODE_FORMAT_INVALID"},
    ]
    # single-character typo in each position
    for i in range(7):
        c = compact[i]
        typo = ALPHABET[(VAL[c] + 1) % N]
        invalid_cases.append({"input": compact[:i] + typo + compact[i + 1:], "error": "CODE_CHECKSUM_INVALID"})
    # adjacent transposition in the body (where chars differ and Luhn catches it)
    for i in range(2, 5):
        if compact[i] != compact[i + 1]:
            t = compact[:i] + compact[i + 1] + compact[i] + compact[i + 2:]
            if not is_valid_compact(t):
                invalid_cases.append({"input": t, "error": "CODE_CHECKSUM_INVALID"})

    return {
        "description": "Structure code test vectors. Both console (TS) and API (Python) must pass every case.",
        "format": "ZZ-XXXX-C: 2-char zone prefix + 4-char body (Crockford base32) + 1 check char",
        "alphabet": ALPHABET,
        "checkAlgorithm": "Luhn mod 32 over the 6 chars prefix+body, using each char's index in alphabet",
        "normalisation": "uppercase; strip spaces, tabs and dashes; O->0, I->1, L->1; optional '/ <unit 1-999>' suffix",
        "valid": [{"code": c, "spoken": spoken(c)} for c in valid],
        "normalise": normalise_cases,
        "invalid": invalid_cases,
        "spokenWithUnit": [{"code": base, "unit": 2, "spoken": spoken(base, 2)}],
        "phonetic": PHONETIC,
    }


def self_check(v):
    for item in v["valid"]:
        assert normalise(item["code"]) == (item["code"], None), item
        compact = item["code"].replace("-", "")
        for i in range(7):  # every single substitution must fail
            for c in ALPHABET:
                if c != compact[i]:
                    assert not is_valid_compact(compact[:i] + c + compact[i + 1:]), (item, i, c)
    for case in v["normalise"]:
        assert normalise(case["input"]) == (case["code"], case["unit"]), case
    for case in v["invalid"]:
        assert normalise(case["input"]) == (None, case["error"]), case
    assert len(set(x["code"] for x in v["valid"])) == len(v["valid"])


# ---------- seed ----------

def uid(n: int) -> str:
    return f"00000000-0000-4000-8000-{n:012d}"


# shortcut: placeholder square (~16 acres) near 12.97N 77.59E; replace with the real campus boundary in A1/A2.
LAT0, LON0 = 12.9700, 77.5900
DLAT, DLON = 0.00229, 0.00235


def pt(fx, fy):
    """fx, fy in 0..1 across the zone square -> [lon, lat]."""
    return [round(LON0 + fx * DLON, 7), round(LAT0 + fy * DLAT, 7)]


def box(fx, fy, w=0.08, h=0.06):
    return {"type": "Polygon", "coordinates": [[pt(fx, fy), pt(fx + w, fy), pt(fx + w, fy + h), pt(fx, fy + h), pt(fx, fy)]]}


def point(fx, fy):
    return {"type": "Point", "coordinates": pt(fx, fy)}


def build_seed(vectors):
    codes = iter([x["code"] for x in vectors["valid"] if x["code"].startswith("RV")])
    zone_id = uid(1)
    zone = {"id": zone_id, "name": "Pilot campus zone (placeholder geometry)", "codePrefix": "RV",
            "boundary": box(0, 0, 1, 1)}
    access_points = [
        {"id": uid(11), "zoneId": zone_id, "label": "Main gate", "kind": "gate", "location": point(0.5, 0.0)},
        {"id": uid(12), "zoneId": zone_id, "label": "East gate", "kind": "gate", "location": point(1.0, 0.5)},
        {"id": uid(13), "zoneId": zone_id, "label": "Library drop-off", "kind": "drop_off", "location": point(0.3, 0.45)},
    ]
    accounts = [
        {"id": uid(21), "username": "admin", "role": "admin"},
        {"id": uid(22), "username": "reviewer-1", "role": "reviewer"},
        {"id": uid(23), "username": "dispatcher-1", "role": "dispatcher"},
        {"id": uid(24), "username": "dispatcher-2", "role": "dispatcher"},
        {"id": uid(25), "username": "mapper-1", "role": "mapper"},
        {"id": uid(26), "username": "mapper-2", "role": "mapper"},
    ]
    devices = [
        {"id": uid(31), "accountId": uid(25), "label": "Mapper phone 1", "kind": "mapper"},
        {"id": uid(32), "accountId": uid(26), "label": "Mapper phone 2", "kind": "mapper"},
        {"id": uid(33), "accountId": None, "label": "Resident phone A", "kind": "resident"},
        {"id": uid(34), "accountId": None, "label": "Resident phone B", "kind": "resident"},
    ]

    def structure(n, status, fx, fy, *, code=None, source="mapper", conf=None, merged_into=None,
                  landmark=None, material="concrete", floors=2, colour="cream", created_by=uid(25)):
        return {"id": uid(n), "zoneId": zone_id, "code": code, "status": status, "footprint": box(fx, fy),
                "centroid": point(fx + 0.04, fy + 0.03), "material": material, "floors": floors, "colour": colour,
                "landmarkName": landmark, "source": source, "bootstrapConfidence": conf, "mergedInto": merged_into,
                "needsVerification": False, "lastVerified": "2026-11-20T10:00:00Z" if status == "confirmed" else None,
                "verificationMethod": "mapper_visit" if status == "confirmed" else None, "createdBy": created_by}

    s_main = structure(101, "confirmed", 0.40, 0.55, code=next(codes), landmark="Main block", floors=3)
    s_hostel = structure(102, "confirmed", 0.70, 0.70, code=next(codes), landmark="Hostel A", colour="red")
    s_noentr = structure(103, "confirmed", 0.15, 0.80, code=next(codes), landmark="Store room", floors=1)
    s_merged = structure(104, "retired", 0.41, 0.56, code=next(codes), merged_into=uid(101))
    s_demol = structure(105, "retired", 0.85, 0.20, code=next(codes), landmark="Old canteen", floors=1)
    cands = [structure(110 + i, "candidate", fx, fy, source="bootstrap", conf=c, created_by=None)
             for i, (fx, fy, c) in enumerate([(0.20, 0.20, 0.91), (0.55, 0.25, 0.74), (0.75, 0.45, 0.68)])]
    dup_a = structure(121, "pending_review", 0.60, 0.85, created_by=uid(25))
    dup_b = structure(122, "pending_review", 0.605, 0.852, created_by=uid(26))
    clear = structure(123, "pending_review", 0.10, 0.40, created_by=uid(25))
    structures = [s_main, s_hostel, s_noentr, s_merged, s_demol, *cands, dup_a, dup_b, clear]

    entrances = [
        {"id": uid(201), "structureId": uid(101), "label": "Front door", "isPrimary": True, "location": point(0.44, 0.55)},
        {"id": uid(202), "structureId": uid(101), "label": "Side door", "isPrimary": False, "location": point(0.48, 0.58)},
        {"id": uid(203), "structureId": uid(102), "label": "Hostel entry", "isPrimary": True, "location": point(0.74, 0.70)},
        # no entrance for 103 (GR-02 case)
    ]
    units = [
        {"id": uid(301), "structureId": uid(101), "number": 1, "label": "Ground floor office", "entranceId": None, "status": "active"},
        {"id": uid(302), "structureId": uid(101), "number": 2, "label": "Staff quarters", "entranceId": uid(202), "status": "active"},
        {"id": uid(303), "structureId": uid(101), "number": 3, "label": "Top floor", "entranceId": None, "status": "active"},
        {"id": uid(304), "structureId": uid(102), "number": 1, "label": "Warden room", "entranceId": None, "status": "active"},
        {"id": uid(305), "structureId": uid(102), "number": 2, "label": "Room 12", "entranceId": None, "status": "active"},
        {"id": uid(306), "structureId": uid(103), "number": 1, "label": "Store keeper", "entranceId": None, "status": "active"},
    ]
    service_records = [
        {"id": uid(401), "unitId": uid(302), "type": "water", "source": "shared_tap", "supplyHours": 6, "quality": "fair", "sharedWithCount": 4},
        {"id": uid(402), "unitId": uid(305), "type": "electricity", "source": "grid", "supplyHours": 20, "quality": "good", "sharedWithCount": 0},
        {"id": uid(403), "unitId": uid(306), "type": "sanitation", "source": "shared_toilet", "supplyHours": 24, "quality": "poor", "sharedWithCount": 10},
    ]
    retired_codes = [
        {"code": s_merged["code"], "reason": "merged", "replacementCode": s_main["code"], "retiredAt": "2026-11-21T09:00:00Z"},
        {"code": s_demol["code"], "reason": "demolished", "replacementCode": None, "retiredAt": "2026-11-22T09:00:00Z"},
    ]
    duplicate_candidates = [
        {"id": uid(501), "structureAId": uid(121), "structureBId": uid(122), "decision": None,
         "signals": [{"kind": "proximity", "value": 0.7, "unit": "m"}, {"kind": "footprint_overlap", "value": 0.82, "unit": "ratio"}]},
    ]
    resident_bindings = [
        {"id": uid(601), "deviceId": uid(33), "unitId": uid(302), "status": "active"},
        {"id": uid(602), "deviceId": uid(34), "unitId": uid(305), "status": "active"},
    ]
    registry = {
        "zones": [zone], "accessPoints": access_points, "accounts": accounts, "devices": devices,
        "structures": structures, "entrances": entrances, "units": units, "serviceRecords": service_records,
        "retiredCodes": retired_codes, "duplicateCandidates": duplicate_candidates, "residentBindings": resident_bindings,
    }

    # Vault only. Made-up personas. Phones use an invalid Indian prefix (0) so they can never ring anyone.
    names = ["Aarav Testmore", "Bhavna Quillfeather", "Chetan Zorvani", "Deepa Marrowline",
             "Esha Fennimore", "Farid Oakhollow", "Gauri Thistlewood", "Harish Embervale"]
    unit_for = [uid(301), uid(302), uid(302), uid(303), uid(304), uid(305), uid(306), None]
    scopes_for = [  # covers PV-01 (none), PV-02 (name only), full, withdrawn
        [], ["name"], ["name", "phone", "notes"], ["name", "phone"], ["name"], ["name", "phone", "notes"], [], [],
    ]
    personas, consents = [], []
    for i, name in enumerate(names):
        pid = uid(701 + i)
        personas.append({"id": pid, "name": name, "phone": f"+9100000001{i:02d}",
                         "notes": f"PERSONA TEST NOTE {i:02d}: uses a walking frame"})
        for scope in scopes_for[i]:
            consents.append({"personaId": pid, "unitRef": unit_for[i], "scope": scope, "status": "granted",
                             "method": "in_person_verbal", "capturedBy": uid(25), "capturedAt": "2026-11-20T11:00:00Z"})
    consents.append({"personaId": uid(708), "unitRef": uid(301), "scope": "name", "status": "withdrawn",
                     "method": "in_person_verbal", "capturedBy": uid(25), "capturedAt": "2026-11-19T11:00:00Z"})
    vault = {"personas": personas, "consents": consents}
    return registry, vault


def seed_self_check(registry, vault):
    blob = json.dumps(registry)
    for p in vault["personas"]:  # PV-08 in miniature: no vault field leaks into the registry seed
        for field in ("name", "phone", "notes"):
            assert p[field] not in blob, (p["id"], field)
    unit_ids = {u["id"] for u in registry["units"]}
    assert all(c["unitRef"] in unit_ids for c in vault["consents"])
    for s in registry["structures"]:
        if s["code"]:
            assert normalise(s["code"])[0] == s["code"]
        if s["status"] in ("candidate", "pending_review"):
            assert s["code"] is None, s["id"]


def main():
    vectors = build_vectors()
    self_check(vectors)
    registry, vault = build_seed(vectors)
    seed_self_check(registry, vault)
    outputs = {
        ROOT / "codes" / "vectors.json": vectors,
        ROOT / "seed" / "registry.json": registry,
        ROOT / "seed" / "vault.json": vault,
    }
    stale = []
    for path, data in outputs.items():
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if "--check" in sys.argv:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        sys.exit("stale fixtures, rerun build_fixtures.py: " + ", ".join(stale))
    print("fixtures ok")


if __name__ == "__main__":
    main()
