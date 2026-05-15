"""Integration: CouchDB starts cleanly, the system + datalink databases the
production `init-db.sh` would create are present, and auth is enforced."""
from __future__ import annotations

import requests


def test_welcome_page_served(couchdb_url: str) -> None:
    r = requests.get(couchdb_url, timeout=5)
    r.raise_for_status()
    body = r.json()
    assert body.get("couchdb") == "Welcome"
    assert body.get("version", "").startswith("3."), (
        f"production is pinned to couchdb:3 — test container reported {body.get('version')}"
    )


def test_anonymous_create_db_rejected(couchdb_url: str) -> None:
    # CouchDB is in admin party only until the first admin is set; the image's
    # COUCHDB_USER/PASSWORD env vars do set one, so anonymous writes must 401.
    r = requests.put(f"{couchdb_url}/should-not-exist", timeout=5)
    assert r.status_code == 401


def test_required_databases_exist(couchdb_url: str, admin_auth) -> None:
    r = requests.get(f"{couchdb_url}/_all_dbs", auth=admin_auth, timeout=5)
    r.raise_for_status()
    dbs = set(r.json())
    for required in ("_users", "_replicator", "_global_changes", "datalink"):
        assert required in dbs, f"{required} missing — init-db.sh logic failed"


def test_admin_can_authenticate(couchdb_url: str, admin_auth) -> None:
    r = requests.get(f"{couchdb_url}/_session", auth=admin_auth, timeout=5)
    r.raise_for_status()
    body = r.json()
    assert body["userCtx"]["name"] == admin_auth[0]
    assert "_admin" in body["userCtx"]["roles"]
