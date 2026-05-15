"""Fixtures and reachability gates for integration tests.

The unit suite under ../unit/ runs against in-process mocks and has no
external dependencies. This integration suite reaches outside the test
process:

  - The ZKS machine mock (S7/RFC1006 server, see docs/machines-db-layout/
    zks-machine-mock/README.md) for the snap7-based tests.
  - A throw-away CouchDB container started via `testcontainers` for the
    database round-trip tests.
  - A live backend + CouchDB + Mosquitto stack started via
    dc-plc-datalink-rfc1006-e2e.yml for the full E2E test.

Each fixture below probes its dependency at session start and skips the
dependent tests cleanly if the dependency is not available. That keeps
the suite runnable on a developer machine where the ZKS mock or the E2E
stack are not up.
"""
from __future__ import annotations

import os
import socket
import time

import pytest

from .zks_fixtures import zks_host, zks_port, zks_machine_config


# All tests in this directory are integration tests. The marker lets the
# unit suite run in isolation via `pytest -m "not integration"`.
def pytest_collection_modifyitems(config, items):
    integration_mark = pytest.mark.integration
    for item in items:
        if 'integration' in str(item.fspath):
            item.add_marker(integration_mark)


# ─── ZKS S7 mock reachability ──────────────────────────────────────────


def _tcp_reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope='session')
def zks_endpoint() -> tuple[str, int]:
    host, port = zks_host(), zks_port()
    if not _tcp_reachable(host, port):
        pytest.skip(
            f'ZKS machine mock not reachable at {host}:{port}. '
            f'Start it (see docs/machines-db-layout/zks-machine-mock/README.md) '
            f'or set ZKS_S7_HOST / ZKS_S7_PORT.'
        )
    return host, port


@pytest.fixture
def zks_config() -> dict:
    return zks_machine_config()


# ─── CouchDB via testcontainers ────────────────────────────────────────


@pytest.fixture(scope='session')
def couchdb_container():
    """Spawn a real CouchDB:3 container per test session.

    testcontainers v4 dropped the community-contributed `couchdb` submodule,
    so we use the generic `DockerContainer` directly — same effect, fewer
    moving parts. Skips the dependent tests if the docker socket is not
    available or the image cannot be pulled.
    """
    try:
        from testcontainers.core.container import DockerContainer
        from testcontainers.core.wait_strategies import LogMessageWaitStrategy
    except ImportError:  # pragma: no cover - guarded by Dockerfile.test
        pytest.skip('testcontainers not installed')

    try:
        container = (
            DockerContainer('couchdb:3')
            .with_env('COUCHDB_USER', 'admin')
            .with_env('COUCHDB_PASSWORD', 'admin')
            .with_exposed_ports(5984)
            .waiting_for(
                LogMessageWaitStrategy('Apache CouchDB has started').with_startup_timeout(60)
            )
        )
        container.start()
    except Exception as exc:
        pytest.skip(f'cannot start CouchDB testcontainer: {exc}')

    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def couchdb_service(couchdb_container):
    """Function-scoped service bound to a fresh database per test."""
    import uuid

    import requests

    from src.services.couchdb_service import CouchDBService

    host = couchdb_container.get_container_host_ip()
    port = couchdb_container.get_exposed_port(5984)
    base_url = f'http://{host}:{port}'
    db_name = f'datalink_{uuid.uuid4().hex[:8]}'
    user, pwd = 'admin', 'admin'

    requests.put(f'{base_url}/{db_name}', auth=(user, pwd)).raise_for_status()
    try:
        yield CouchDBService(base_url, user, pwd, db_name)
    finally:
        requests.delete(f'{base_url}/{db_name}', auth=(user, pwd))


# ─── E2E stack (dc-plc-datalink-rfc1006-e2e.yml) ───────────────────────


@pytest.fixture(scope='session')
def backend_url() -> str:
    """Base URL of the live backend in the E2E stack.

    Skips the dependent test when E2E_BACKEND_URL is unset (developer
    running `pytest -q` outside the E2E compose) or when the backend
    does not become reachable within ~90 s (supervisord/gunicorn
    `startsecs=30` plus pull/start overhead).
    """
    import requests  # local import — keeps unit tests cold-import clean

    url = os.environ.get('E2E_BACKEND_URL')
    if not url:
        pytest.skip(
            'E2E_BACKEND_URL not set — this test only runs inside '
            'dc-plc-datalink-rfc1006-e2e.yml (backend-e2e-runner)'
        )

    deadline = time.time() + 120
    last_err: str | None = None
    while time.time() < deadline:
        try:
            r = requests.get(f'{url}/machine/online', timeout=3)
            # 200 = machines listed, 404 = empty list — both prove Flask is up.
            if r.status_code in (200, 404):
                return url
            last_err = f'HTTP {r.status_code}'
        except requests.exceptions.RequestException as exc:
            last_err = str(exc)
        time.sleep(2)
    pytest.skip(f'backend not reachable at {url} within 120 s: {last_err}')


@pytest.fixture(scope='session')
def mqtt_endpoint() -> tuple[str, int]:
    """Hostname/port of the live Mosquitto broker in the E2E stack."""
    host = os.environ.get('E2E_MQTT_HOST')
    port = int(os.environ.get('E2E_MQTT_PORT', '1883'))
    if not host:
        pytest.skip('E2E_MQTT_HOST not set — run inside the E2E compose')
    if not _tcp_reachable(host, port, timeout=10.0):
        pytest.skip(f'mosquitto not reachable at {host}:{port}')
    return host, port
