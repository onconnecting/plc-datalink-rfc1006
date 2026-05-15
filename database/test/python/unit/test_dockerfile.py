"""Unit tests for database/Dockerfile — image base pin, init wiring."""
from __future__ import annotations

import re
from pathlib import Path

import pytest


DOCKERFILE = Path("/app/database/Dockerfile")


@pytest.fixture(scope="module")
def text() -> str:
    return DOCKERFILE.read_text()


def test_pinned_to_couchdb_3_major(text: str) -> None:
    # ADR-0008 commits to running tests against the production major version.
    # That works only if the production base image stays on couchdb:3.x.
    match = re.search(r"^FROM\s+couchdb:(\S+)", text, re.MULTILINE)
    assert match, "no `FROM couchdb:` line found"
    tag = match.group(1)
    assert tag != "latest", "couchdb image must be pinned, not :latest"
    assert tag.startswith("3."), f"expected couchdb:3.x, got couchdb:{tag}"


def test_copies_init_script_into_initdb_dir(text: str) -> None:
    assert "init-db.sh" in text
    assert "/docker-entrypoint-initdb.d/" in text


def test_copies_local_ini_into_couchdb_etc(text: str) -> None:
    assert "local.ini" in text
    assert "/opt/couchdb/etc/local.ini" in text
