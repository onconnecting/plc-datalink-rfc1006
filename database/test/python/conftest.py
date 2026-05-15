"""Session-scoped CouchDB testcontainer + per-test database fixture.

Implements the contract from ADR-0008:
- A real `couchdb:3` container is spawned via the host Docker socket.
- The same init logic as `database/config/init-db.sh` runs once per session,
  so tests see `_users`, `_replicator`, `_global_changes`, `datalink`.
- Each test gets a unique throwaway database, cleaned up on teardown.
- The ZKS reference layout (`docs/machines-db-layout/zks-machine-mock/`) is
  loaded and shaped into a PlcDatalinkRFC1006 document via
  [`zks_layout.py`](zks_layout.py).
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Iterator

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from zks_layout import build_machine_doc, load_layout


COUCHDB_IMAGE = "couchdb:3.3.3"  # matches database/Dockerfile pin
ADMIN_USER = "admin"
ADMIN_PASSWORD = "test-admin-pw"
HOSTNAME_OVERRIDE = os.environ.get("TESTCONTAINERS_HOST_OVERRIDE", "localhost")


def _seed_system_dbs(base_url: str) -> None:
    """Apply the same bootstrap as `database/config/init-db.sh`."""
    auth = (ADMIN_USER, ADMIN_PASSWORD)
    for db in ("_users", "_global_changes", "_replicator", "datalink"):
        r = requests.put(f"{base_url}/{db}", auth=auth, timeout=10)
        # 201 = created, 412 = already exists (idempotent re-runs).
        assert r.status_code in (201, 412), (
            f"failed to create {db}: {r.status_code} {r.text}"
        )


@pytest.fixture(scope="session")
def couchdb_url() -> Iterator[str]:
    container = (
        DockerContainer(COUCHDB_IMAGE)
        .with_env("COUCHDB_USER", ADMIN_USER)
        .with_env("COUCHDB_PASSWORD", ADMIN_PASSWORD)
        .with_exposed_ports(5984)
        .waiting_for(LogMessageWaitStrategy("Apache CouchDB has started").with_startup_timeout(60))
    )
    with container as c:
        host = c.get_container_host_ip()
        port = c.get_exposed_port(5984)
        if host in ("0.0.0.0", "127.0.0.1", "localhost") and HOSTNAME_OVERRIDE:
            host = HOSTNAME_OVERRIDE
        base = f"http://{host}:{port}"

        # CouchDB sometimes accepts TCP a moment before it answers the HTTP
        # control plane on / — poll briefly until the welcome page is served.
        deadline = time.time() + 30
        last_err = None
        while time.time() < deadline:
            try:
                if requests.get(base, timeout=2).status_code == 200:
                    break
            except requests.exceptions.RequestException as e:
                last_err = e
            time.sleep(0.5)
        else:
            raise RuntimeError(f"CouchDB did not become reachable at {base}: {last_err}")

        _seed_system_dbs(base)
        yield base


@pytest.fixture()
def admin_auth() -> tuple[str, str]:
    return (ADMIN_USER, ADMIN_PASSWORD)


@pytest.fixture()
def ephemeral_db(couchdb_url: str, admin_auth: tuple[str, str]) -> Iterator[str]:
    """A throwaway database per test, dropped on teardown.

    Yields the full URL `http://<host>:<port>/<db>` so tests can compose
    document URLs by string concat.
    """
    name = f"test-{uuid.uuid4().hex[:12]}"
    url = f"{couchdb_url}/{name}"
    r = requests.put(url, auth=admin_auth, timeout=10)
    assert r.status_code == 201, f"could not create {name}: {r.status_code} {r.text}"
    try:
        yield url
    finally:
        requests.delete(url, auth=admin_auth, timeout=10)


@pytest.fixture(scope="session")
def zks_layout() -> dict:
    return load_layout()


@pytest.fixture()
def zks_machine_doc(zks_layout: dict) -> dict:
    return build_machine_doc(zks_layout)
