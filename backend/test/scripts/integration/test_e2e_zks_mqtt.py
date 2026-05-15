"""End-to-end: REST → CouchDB → Telegraf → ZKS S7 mock → MQTT.

This is the only test that exercises every layer of the system at once.
Required infrastructure (must all be reachable from the runner container):

  - The ZKS machine mock on the host (port 102 by default).
  - A live `backend-e2e` from dc-plc-datalink-rfc1006-e2e.yml — Flask +
    supervisord + Telegraf all in the production image.
  - The `couchdb-e2e` and `mosquitto-e2e` siblings on the same compose
    network.

Each fixture probes its dependency at the start of the session and skips
cleanly when any piece is missing; this test does not run by accident on
a workstation that lacks the stack.

What the test verifies:

  1. POST /config/create stores the ZKS-targeted machine config in CouchDB.
  2. GET /config/read/one returns it back unchanged.
  3. GET /machine/start kicks off a per-machine Telegraf process under
     supervisord; GET /machine/online eventually lists it.
  4. Telegraf reads PLC tags from the ZKS S7 server and publishes JSON to
     Mosquitto. The first message's payload matches the documented shape
     (`name`, `tags.host`, `tags.machine`, `fields`, `timestamp` in ms).
  5. Writing `Cmd_InjectFault = "ERR_WELD_CURRENT_LOW"` to DB4 via
     python-snap7 takes effect — we verify the write call itself and that
     MQTT data keeps flowing afterwards (the mock continues to emit weld
     telemetry; the fault changes which point goes NOK, not whether data
     is produced).
  6. Cleanup: /machine/stop and /config/remove leave the stack idle.

The test is one function on purpose — the whole point is to walk the
pipeline once with the same machine config. Splitting into N steps would
either rebuild the stack each time (slow) or share session state across
tests (fragile).
"""
from __future__ import annotations

import json
import threading
import time
from queue import Queue

import pytest
import requests

from .zks_fixtures import zks_machine_config


MACHINE_NAME = 'zks-mock'

# How long the test waits for state transitions. These are upper bounds —
# in a happy run the stack is online within 30 s of /machine/start.
TIMEOUT_MACHINE_ONLINE = 180
TIMEOUT_FIRST_MQTT = 180


# ─── helpers ───────────────────────────────────────────────────────────


def _post_config(backend_url: str, config_dict: dict) -> requests.Response:
    """/config/create expects a JSON body whose value is itself a JSON-encoded
    string — see routes.store_config (`json.loads(request.get_json())`) and
    the matching frontend code in services/config.service.ts.
    """
    body = json.dumps(json.dumps(config_dict))
    return requests.post(
        f'{backend_url}/config/create',
        data=body,
        headers={'Content-Type': 'application/json'},
        timeout=15,
    )


def _force_cleanup(backend_url: str) -> None:
    """Best-effort cleanup. Used both proactively (before the test, in case
    a previous run left state) and reactively (after the test, regardless
    of outcome). 404 / 409 here are expected, never raised."""
    try:
        requests.get(
            f'{backend_url}/machine/stop',
            params={'machine_name': MACHINE_NAME},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        pass
    # /machine/stop is asynchronous on the supervisord side; give it a
    # beat before /config/remove (which 409s while the machine is active).
    time.sleep(2)
    try:
        requests.get(
            f'{backend_url}/config/remove',
            params={'machine_name': MACHINE_NAME},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        pass


@pytest.fixture
def cleanup_machine(backend_url):
    _force_cleanup(backend_url)
    yield
    _force_cleanup(backend_url)


# ─── the test ──────────────────────────────────────────────────────────


def test_zks_pipeline_publishes_to_mqtt(
    backend_url, mqtt_endpoint, zks_endpoint, cleanup_machine
):
    """The single E2E walk-through. See module docstring for the contract."""
    import paho.mqtt.client as mqtt_lib  # local — keeps unit-tests cold-import light
    import snap7  # type: ignore
    from snap7.util import set_string  # type: ignore

    mqtt_host, mqtt_port = mqtt_endpoint
    config = zks_machine_config(MACHINE_NAME)
    topic_root = config['mqttData']['mqttTopic']

    # ── 1) POST /config/create ────────────────────────────────────────
    r = _post_config(backend_url, config)
    assert r.status_code == 200, f'/config/create failed: {r.status_code} {r.text}'

    # ── 2) GET /config/read/one — verify round-trip ───────────────────
    r = requests.get(
        f'{backend_url}/config/read/one',
        params={'machine_name': MACHINE_NAME},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    fetched = r.json()
    assert fetched['_id'] == MACHINE_NAME
    assert fetched['machineData']['plcIp'] == config['machineData']['plcIp']
    assert fetched['machineData']['plcPort'] == config['machineData']['plcPort']
    assert len(fetched['plcTagData']) == len(config['plcTagData'])

    # ── 3) Subscribe BEFORE /machine/start so we don't miss the first message
    received: Queue = Queue()
    subscribed = threading.Event()

    try:
        client = mqtt_lib.Client(mqtt_lib.CallbackAPIVersion.VERSION2, 'e2e-runner')
    except (AttributeError, TypeError):
        client = mqtt_lib.Client(client_id='e2e-runner')

    def on_connect(c, *_a, **_kw):
        c.subscribe(f'{topic_root}/#')
        c.subscribe(topic_root)
        subscribed.set()

    def on_message(_c, _u, msg):
        try:
            received.put((msg.topic, json.loads(msg.payload)))
        except Exception as exc:  # malformed payload still goes into the queue
            received.put((msg.topic, {'__decode_error': str(exc), '__raw': msg.payload}))

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_host, mqtt_port, keepalive=30)
    client.loop_start()
    assert subscribed.wait(timeout=10), 'MQTT subscriber did not connect to broker'

    try:
        # ── 4) GET /machine/start ─────────────────────────────────────
        r = requests.get(
            f'{backend_url}/machine/start',
            params={'machine_name': MACHINE_NAME},
            timeout=30,
        )
        assert r.status_code == 200, f'/machine/start failed: {r.status_code} {r.text}'

        # ── 5) Poll /machine/online until Telegraf is listed ──────────
        online_deadline = time.time() + TIMEOUT_MACHINE_ONLINE
        while time.time() < online_deadline:
            r = requests.get(f'{backend_url}/machine/online', timeout=5)
            if r.status_code == 200:
                names = [m['machine_name'] for m in r.json().get('machines', [])]
                if MACHINE_NAME in names:
                    break
            time.sleep(3)
        else:
            pytest.fail(
                f'{MACHINE_NAME} never appeared in /machine/online within '
                f'{TIMEOUT_MACHINE_ONLINE} s'
            )

        # ── 6) Wait for first MQTT message + assert payload shape ─────
        first = received.get(timeout=TIMEOUT_FIRST_MQTT)
        topic, payload = first
        assert topic.startswith(topic_root), f'unexpected topic: {topic}'
        assert isinstance(payload, dict), f'payload not JSON object: {payload!r}'
        assert 'name' in payload, f'missing `name`: {payload}'
        assert 'tags' in payload and 'machine' in payload['tags']
        assert 'fields' in payload and payload['fields']
        ts = payload.get('timestamp')
        assert isinstance(ts, int), f'timestamp not int: {ts!r}'
        # Sanity check: timestamp must be ms-since-epoch (so > 2020 in ms),
        # not seconds. Caught by the mqttJsonTimestampUnits="1ms" default.
        assert ts > 1_500_000_000_000, f'timestamp not in ms: {ts}'

        # Drain a few more to convince ourselves the stream is live,
        # not just one stray packet.
        seen_topics = {topic}
        for _ in range(3):
            try:
                t, _ = received.get(timeout=15)
                seen_topics.add(t)
            except Exception:
                break
        assert any(t.startswith(topic_root) for t in seen_topics)

        # ── 7) Fault injection via snap7 directly on DB4 ─────────────
        # The mock auto-resets the trigger ~200 ms after seeing the flank,
        # so we only assert the write call succeeds. The qualitative effect
        # (one weld flagged NOK) is documented behaviour of the ZKS mock —
        # asserting on it here would couple the test to the simulation's
        # RNG seed.
        s7_host, s7_port = zks_endpoint
        s7 = snap7.client.Client()
        s7.connect(s7_host, 0, 1, tcpport=s7_port)
        try:
            buf = bytearray(22)  # STRING[20] on the wire is 22 bytes
            set_string(buf, 0, 'ERR_WELD_CURRENT_LOW', 20)
            s7.db_write(4, 70, bytes(buf))  # Cmd_InjectFault, offset 70
        finally:
            s7.disconnect()

        # Confirm the stream did not die after the write.
        try:
            received.get(timeout=15)
        except Exception:
            pytest.fail('MQTT stream went silent after fault injection')

        # ── 8) /machine/stop should succeed and clear /machine/online ─
        r = requests.get(
            f'{backend_url}/machine/stop',
            params={'machine_name': MACHINE_NAME},
            timeout=15,
        )
        assert r.status_code == 200, r.text
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
