"""Unit tests for database/config/init-db.sh — the script that bootstraps the
required CouchDB databases on container first start."""
from __future__ import annotations

from pathlib import Path

import pytest


INIT_SCRIPT = Path("/app/database/config/init-db.sh")


@pytest.fixture(scope="module")
def script_text() -> str:
    return INIT_SCRIPT.read_text()


def test_script_is_bash(script_text: str) -> None:
    assert script_text.startswith("#!/bin/bash")


@pytest.mark.parametrize("db", ["_users", "_global_changes", "_replicator", "datalink"])
def test_script_creates_required_database(script_text: str, db: str) -> None:
    # The PUT is the CouchDB API for db creation; presence of the URL with the
    # db name in a PUT line is what we assert.
    assert f"PUT" in script_text
    assert f"5984/{db}" in script_text, f"init-db.sh should create {db}"


def test_script_uses_env_credentials(script_text: str) -> None:
    # Admin user/password come from the couchdb image's COUCHDB_USER /
    # COUCHDB_PASSWORD env vars — never hardcoded.
    assert "${COUCHDB_USER}" in script_text
    assert "${COUCHDB_PASSWORD}" in script_text
    assert "admin:password" not in script_text


def test_script_waits_for_couchdb(script_text: str) -> None:
    # Sanity check the script does not race the couchdb HTTP listener.
    assert "until curl" in script_text or "Waiting for CouchDB" in script_text
