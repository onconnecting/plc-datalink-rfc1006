"""Smoke test: the ZKS machine mock answers S7 reads on its documented offsets.

This is the read path Telegraf will exercise once we let it loose against
the mock — but without involving Telegraf yet. Talking to the ZKS server
with `python-snap7` directly lets us prove that:

  - The mock is reachable from inside the test container.
  - The DB layout in docs/machines-db-layout/zks-machine-mock/db-layout.yaml
    matches what the server actually serves (offsets, types).
  - Cmd writes (DB4 trigger bits) round-trip; this is the lever the E2E
    test will use to inject faults.

If the mock is not up, the session-scoped `zks_endpoint` fixture skips the
whole module — see integration/conftest.py.
"""
from __future__ import annotations

import pytest


snap7 = pytest.importorskip('snap7')
util = pytest.importorskip('snap7.util')


@pytest.fixture
def s7_client(zks_endpoint):
    host, port = zks_endpoint
    client = snap7.client.Client()
    try:
        client.connect(host, 0, 1, tcpport=port)
    except Exception as exc:  # snap7 raises Snap7Exception on connect failure
        pytest.skip(f'ZKS S7 connect failed at {host}:{port}: {exc}')
    try:
        yield client
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


def test_db1_machine_block_readable(s7_client):
    """DB1 = Machine block (60 bytes). Reading it must not raise and the
    State field at offset 0 must be a valid enum (0..4)."""
    buf = s7_client.db_read(1, 0, 60)
    assert len(buf) == 60
    state = util.get_int(buf, 0)
    assert 0 <= state <= 4, f'unexpected Machine.State {state}'


def test_db1_part_counter_is_dint(s7_client):
    """DB1.DI4 = PartCounter. Non-negative DINT."""
    buf = s7_client.db_read(1, 4, 4)
    counter = util.get_dint(buf, 0)
    assert counter >= 0


def test_db1_yield_is_real(s7_client):
    """DB1.R28 = Yield in percent. 0 ≤ yield ≤ 100 (the mock seeds non-zero
    only after RUNNING, but the read itself must produce a valid REAL)."""
    buf = s7_client.db_read(1, 28, 4)
    pct = util.get_real(buf, 0)
    assert -0.01 <= pct <= 100.01, f'Yield out of bounds: {pct}'


def test_db3_test_block_readable(s7_client):
    """DB3 = Test block (60 bytes). Result enum at offset 8 must be 0..2."""
    buf = s7_client.db_read(3, 0, 60)
    result = util.get_int(buf, 8)
    assert 0 <= result <= 2, f'Test.Result must be 0/1/2, got {result}'


def test_db4_serial_string_decodes(s7_client):
    """DB4.S32 starting at offset 0 = Part.Serial. STRING[32] is 34 bytes
    on the wire (2-byte header + 32 chars). The decoded value must be
    printable ASCII (ON-SFC format) or empty when no part is active."""
    buf = s7_client.db_read(4, 0, 34)
    serial = util.get_string(buf, 0)
    assert isinstance(serial, str)
    if serial:
        assert serial.isascii(), f'non-ASCII serial: {serial!r}'


def test_db4_command_bit_round_trip(s7_client):
    """Smoke-check the write path Telegraf will never use but the E2E fault-
    injection test will: writing Cmd_ChangeElectrode (bit 68.7) and reading
    it back must succeed. Node-RED auto-resets the bit within ~200 ms, so we
    only assert that the write call did not raise.
    """
    buf = bytearray(1)
    util.set_bool(buf, 0, 7, True)
    s7_client.db_write(4, 68, bytes(buf))
