"""Integration: full lifecycle of the ZKS reference machine configuration
document against a real CouchDB instance.

These tests exercise the exact HTTP surface that
[`backend/src/services/couchdb_service.py`](../../../../backend/src/services/couchdb_service.py)
uses — `PUT /<db>/<_id>` with the machineName as `_id`, `_rev` conflict on
re-PUT, `_all_docs?include_docs=true`, and `DELETE /<db>/<_id>?rev=`.
"""
from __future__ import annotations

import requests

from zks_layout import ZKS_MACHINE_NAME


# ----- Helpers ---------------------------------------------------------------


def _put_doc(db_url: str, auth, doc: dict) -> dict:
    """Replicate `CouchDBService.create_doc` — sets `_id` from machineName."""
    body = dict(doc)
    body["_id"] = body["machineData"]["machineName"]
    r = requests.put(f"{db_url}/{body['_id']}", auth=auth, json=body, timeout=10)
    r.raise_for_status()
    return r.json()


# ----- Tests -----------------------------------------------------------------


def test_zks_doc_round_trip(ephemeral_db: str, admin_auth, zks_machine_doc: dict) -> None:
    """PUT the ZKS doc, GET it back, every field survives the round trip."""
    result = _put_doc(ephemeral_db, admin_auth, zks_machine_doc)
    assert result["ok"] is True
    assert result["id"] == ZKS_MACHINE_NAME

    r = requests.get(f"{ephemeral_db}/{ZKS_MACHINE_NAME}", auth=admin_auth, timeout=10)
    r.raise_for_status()
    got = r.json()
    assert got["_id"] == ZKS_MACHINE_NAME
    assert got["_rev"].startswith("1-")
    # PLC connection settings come from the ZKS YAML.
    assert got["machineData"]["plcIp"] == "192.168.0.180"
    assert got["machineData"]["plcPort"] == 102
    assert got["machineData"]["plcRack"] == 0
    assert got["machineData"]["plcSlot"] == 1
    # Tag list (128 entries) survives unchanged.
    assert got["plcTagData"] == zks_machine_doc["plcTagData"]


def test_zks_doc_all_dbs_zoo(ephemeral_db: str, admin_auth, zks_machine_doc: dict) -> None:
    """Every DB-region in the ZKS layout is represented in the persisted tag list."""
    _put_doc(ephemeral_db, admin_auth, zks_machine_doc)
    r = requests.get(f"{ephemeral_db}/{ZKS_MACHINE_NAME}", auth=admin_auth, timeout=10)
    r.raise_for_status()
    addresses = [t["tagAddress"] for t in r.json()["plcTagData"]]
    by_db = {db: [a for a in addresses if a.startswith(f"DB{db}.")] for db in (1, 2, 3, 4)}
    assert len(by_db[1]) == 12, "DB1 (Machine) tag count drifted"
    assert len(by_db[2]) == 12 * 7, "DB2 (Welds) expansion drifted"
    assert len(by_db[3]) == 4 + 11, "DB3 (Test) tag count drifted (REAL_ARRAY?)"
    assert len(by_db[4]) == 9 + 8, "DB4 (PartAndCommands) tag count drifted"
    # Spot-check a representative address from each DB.
    assert "DB1.X36.0" in addresses  # ErrorActive BOOL
    assert "DB2.R2" in addresses  # Weld_00.Current
    assert "DB3.R12" in addresses  # SegmentResistance[0]
    assert "DB4.S0.32" in addresses  # Serial STRING[32]


def test_put_without_rev_on_existing_doc_409(
    ephemeral_db: str, admin_auth, zks_machine_doc: dict
) -> None:
    """CouchDB's optimistic concurrency: a second PUT without `_rev` must
    fail with 409 (this is the contract `CouchDBService.create_doc` leans on
    via raise_for_status)."""
    _put_doc(ephemeral_db, admin_auth, zks_machine_doc)
    r = requests.put(
        f"{ephemeral_db}/{ZKS_MACHINE_NAME}",
        auth=admin_auth,
        json={**zks_machine_doc, "_id": ZKS_MACHINE_NAME},
        timeout=10,
    )
    assert r.status_code == 409
    assert r.json().get("error") == "conflict"


def test_update_with_rev_succeeds(
    ephemeral_db: str, admin_auth, zks_machine_doc: dict
) -> None:
    """The standard backend update path: GET to read `_rev`, modify, PUT."""
    _put_doc(ephemeral_db, admin_auth, zks_machine_doc)
    got = requests.get(
        f"{ephemeral_db}/{ZKS_MACHINE_NAME}", auth=admin_auth, timeout=10
    ).json()

    updated = dict(got)
    updated["machineData"] = {**got["machineData"], "machineState": "ON"}

    r = requests.put(
        f"{ephemeral_db}/{ZKS_MACHINE_NAME}",
        auth=admin_auth,
        json=updated,
        timeout=10,
    )
    r.raise_for_status()
    rev2 = r.json()["rev"]
    assert rev2.startswith("2-")

    again = requests.get(
        f"{ephemeral_db}/{ZKS_MACHINE_NAME}", auth=admin_auth, timeout=10
    ).json()
    assert again["machineData"]["machineState"] == "ON"
    assert again["_rev"] == rev2


def test_all_docs_include_docs_returns_zks(
    ephemeral_db: str, admin_auth, zks_machine_doc: dict
) -> None:
    """`/_all_docs?include_docs=true` is what `CouchDBService.get_all_docs` calls.
    Verify the result shape and that the embedded doc carries the full config."""
    _put_doc(ephemeral_db, admin_auth, zks_machine_doc)
    r = requests.get(
        f"{ephemeral_db}/_all_docs",
        params={"include_docs": "true"},
        auth=admin_auth,
        timeout=10,
    )
    r.raise_for_status()
    body = r.json()
    assert body["total_rows"] == 1
    (row,) = body["rows"]
    assert row["id"] == ZKS_MACHINE_NAME
    assert row["doc"]["machineData"]["machineName"] == ZKS_MACHINE_NAME
    assert len(row["doc"]["plcTagData"]) == len(zks_machine_doc["plcTagData"])


def test_delete_with_rev(ephemeral_db: str, admin_auth, zks_machine_doc: dict) -> None:
    create = _put_doc(ephemeral_db, admin_auth, zks_machine_doc)
    r = requests.delete(
        f"{ephemeral_db}/{ZKS_MACHINE_NAME}",
        params={"rev": create["rev"]},
        auth=admin_auth,
        timeout=10,
    )
    r.raise_for_status()
    assert r.json()["ok"] is True

    after = requests.get(
        f"{ephemeral_db}/{ZKS_MACHINE_NAME}", auth=admin_auth, timeout=10
    )
    assert after.status_code == 404
