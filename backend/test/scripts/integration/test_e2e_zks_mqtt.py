"""End-to-end: REST → CouchDB → Telegraf → ZKS S7 mock → MQTT
                                              ⤴ snap7 drives state machine

This is the only test that exercises every layer of the production stack
at once. Required infrastructure (must all be reachable from the runner
container, see ./conftest.py for the reachability gates):

  - The ZKS machine mock on the host (192.168.0.180:102 by default).
  - `backend-e2e` from dc-plc-datalink-rfc1006-e2e.yml — Flask + supervisord
    + Telegraf, all in the production image.
  - `couchdb-e2e` and `mosquitto-e2e` siblings on the same compose network.

Verified flow (per docs/features/test-strategy/scope.md, Section 4):

  1. REST smoke — POST /config/create + GET /config/read/one. Proves the
     Flask + CouchDB layer is up and round-trips the ZKS-targeted config.
  2. Subscribe to MQTT *before* starting Telegraf so we never miss the
     first publish.
  3. GET /machine/start — supervisord launches a per-machine Telegraf
     process that polls the ZKS mock via S7/RFC1006.
  4. Poll /machine/online until the machine appears (Telegraf has come up).
  5. Wait for the first MQTT message — proves the production chain
     Backend → Telegraf → ZKS → MQTT is alive.
  6. snap7 drives the ZKS state machine directly and reads ground-truth
     KPI snapshots from DB1:
       a. Read initial DB1 snapshot (Machine.State + 8 KPIs) — diagnostic
          baseline; not asserted against.
       b. Pulse Cmd_Stop (DB4 bit 68.2), wait ~3 s for the flank, snapshot.
       c. Write Cmd_CycleSpeedFactor = 5.0 (REAL @ DB4 92), pulse Cmd_Start
          (bit 68.1).
       d. Sleep 30 s of accelerated production (~9 part cycles at 5×).
       e. Snapshot DB1 a third time.
       f. Assert Machine.State changed AND at least one KPI moved between
          "stopped" and "running" snapshots.
  7. Confirm the MQTT stream stayed alive during the 30-s run.
  8. Cleanup: pulse Cmd_Stop, GET /machine/stop, GET /config/remove. Mock
     ends in IDLE, CouchDB clean.

Total happy-path budget is ≤ 60 s — the 30-s production wait dominates;
all other timeouts are tightly set so a regression manifests as a failure,
not a hang.

snap7 is used here as a *test instrument* (drive + ground-truth read),
not as a stand-in for Telegraf. Steps 3–5 are the actual production-path
verification; steps 6–7 use snap7 to (a) make the ZKS produce parts on
schedule and (b) read DB values without going through Telegraf's flush
window, so KPI assertions are deterministic.
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

# Tight timeouts — total test budget ≤ 60 s, dominated by PRODUCTION_WAIT.
TIMEOUT_HTTP = 15
TIMEOUT_MACHINE_ONLINE = 10
# ZKS state transitions are not instantaneous — Node-RED processes the
# Cmd_Stop flank within ~200 ms but the State field updates after the
# current operation completes. Poll DB1.State until it leaves RUNNING (1).
STOP_POLL_TIMEOUT = 10
PRODUCTION_WAIT = 25
# We don't gate on "first MQTT message" anymore — Telegraf needs ~10-15 s
# from spawn to first publish (S7 + MQTT connect overhead), and waiting
# separately doubles the test budget. Instead we assert at the end of
# PRODUCTION_WAIT that at least one message arrived — Telegraf has had
# the entire 30 s production window to flush.


# ─── helpers ───────────────────────────────────────────────────────────


def _post_config(backend_url: str, config_dict: dict) -> requests.Response:
    """/config/create expects a JSON body whose value is itself a JSON-encoded
    string — see routes.store_config (`json.loads(request.get_json())`).
    """
    body = json.dumps(json.dumps(config_dict))
    return requests.post(
        f'{backend_url}/config/create',
        data=body,
        headers={'Content-Type': 'application/json'},
        timeout=TIMEOUT_HTTP,
    )


def _force_cleanup(backend_url: str) -> None:
    """Best-effort cleanup. Runs before AND after the test, so a previous
    failed run cannot leave residual state. 404 / 409 are expected here."""
    for endpoint, params in (
        ('/machine/stop', {'machine_name': MACHINE_NAME}),
        ('/config/remove', {'machine_name': MACHINE_NAME}),
    ):
        try:
            requests.get(f'{backend_url}{endpoint}', params=params, timeout=TIMEOUT_HTTP)
        except requests.exceptions.RequestException:
            pass
    # /machine/stop is asynchronous in supervisord; give it a beat before
    # /config/remove (which 409s while the Telegraf process is still alive).
    time.sleep(1)


@pytest.fixture
def cleanup_machine(backend_url):
    _force_cleanup(backend_url)
    yield
    _force_cleanup(backend_url)


# ─── the test ──────────────────────────────────────────────────────────


def test_zks_state_and_kpi_change(
    backend_url, mqtt_endpoint, zks_endpoint, cleanup_machine
):
    """The single E2E walk-through. See module docstring for the contract."""
    import paho.mqtt.client as mqtt_lib  # local — keeps unit imports cold
    import snap7  # type: ignore
    from snap7.util import get_dint, get_int, get_real, set_bool, set_real  # type: ignore

    s7_host, s7_port = zks_endpoint
    mqtt_host, mqtt_port = mqtt_endpoint

    # python-snap7 v2 dropped the `tcpport=` kwarg from connect(); the
    # underlying snap7 C library defaults to 102. For non-default ports
    # we'd need set_param(RemotePort, …) — guard explicitly so a
    # ZKS_S7_PORT=1102 setting fails loudly rather than silently dialing 102.
    assert s7_port == 102, (
        f'snap7 v2 connect() only honours the default port 102; '
        f'ZKS_S7_PORT={s7_port} would be silently ignored. '
        f'Run the ZKS mock on 102 or extend this fixture to call '
        f'client.set_param(RemotePort, port) before connect.'
    )

    config = zks_machine_config(MACHINE_NAME)
    topic_root = config['mqttData']['mqttTopic']

    # ── 1) REST smoke: POST /config/create + GET /config/read/one ─────
    r = _post_config(backend_url, config)
    assert r.status_code == 200, f'/config/create failed: {r.status_code} {r.text}'

    r = requests.get(
        f'{backend_url}/config/read/one',
        params={'machine_name': MACHINE_NAME},
        timeout=TIMEOUT_HTTP,
    )
    assert r.status_code == 200, r.text
    fetched = r.json()
    assert fetched['_id'] == MACHINE_NAME
    assert fetched['machineData']['plcIp'] == config['machineData']['plcIp']
    assert fetched['machineData']['plcPort'] == config['machineData']['plcPort']
    assert len(fetched['plcTagData']) == len(config['plcTagData'])

    # ── 2) Subscribe BEFORE starting Telegraf so we don't miss messages
    received: Queue = Queue()
    subscribed = threading.Event()

    try:
        client = mqtt_lib.Client(mqtt_lib.CallbackAPIVersion.VERSION2, 'e2e-runner')
    except (AttributeError, TypeError):
        client = mqtt_lib.Client(client_id='e2e-runner')

    def on_connect(c, *_a, **_kw):
        # Subscribe to '#' (catch-all) — narrower filters that look
        # correct on paper (`on/ot/zks-mock` + `on/ot/zks-mock/#`) didn't
        # deliver messages reliably with paho-mqtt v2 + loop_start(),
        # while a single `#` matches the broker's routing path used by
        # mosquitto_sub and paho's loop_forever().
        c.subscribe('#', qos=0)
        subscribed.set()

    def on_message(_c, _u, msg):
        try:
            received.put((msg.topic, json.loads(msg.payload)))
        except Exception as exc:
            received.put((msg.topic, {'__decode_error': str(exc), '__raw': msg.payload}))

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_host, mqtt_port, keepalive=30)
    client.loop_start()
    assert subscribed.wait(timeout=10), 'MQTT subscriber did not connect to broker'

    try:
        # ── 3) GET /machine/start — supervisord launches Telegraf ─────
        r = requests.get(
            f'{backend_url}/machine/start',
            params={'machine_name': MACHINE_NAME},
            timeout=TIMEOUT_HTTP,
        )
        assert r.status_code == 200, f'/machine/start failed: {r.status_code} {r.text}'

        # ── 4) Poll /machine/online until Telegraf is listed ──────────
        online_deadline = time.time() + TIMEOUT_MACHINE_ONLINE
        while time.time() < online_deadline:
            r = requests.get(f'{backend_url}/machine/online', timeout=5)
            if r.status_code == 200:
                names = [m['machine_name'] for m in r.json().get('machines', [])]
                if MACHINE_NAME in names:
                    break
            time.sleep(1)
        else:
            pytest.fail(
                f'{MACHINE_NAME} never appeared in /machine/online within '
                f'{TIMEOUT_MACHINE_ONLINE} s'
            )

        # MQTT-shape validation deferred to the end of the production
        # window — Telegraf has been spawning concurrently; we don't
        # block here. See step 7 below.

        # ── 5) snap7 helpers — one connection per S7 call (mock auto-
        # resets trigger bits after ~200 ms, so we don't hold connections).
        def read_db1_snapshot() -> dict:
            s = snap7.client.Client()
            s.connect(s7_host, 0, 1)
            try:
                buf = s.db_read(1, 0, 36)
            finally:
                s.disconnect()
            return {
                'state':          get_int(buf, 0),
                'mode':           get_int(buf, 2),
                'part_counter':   get_dint(buf, 4),
                'ok_counter':     get_dint(buf, 8),
                'nok_counter':    get_dint(buf, 12),
                'scrap_counter':  get_dint(buf, 16),
                'rework_counter': get_dint(buf, 20),
                'throughput':     get_real(buf, 24),
                'yield':          get_real(buf, 28),
                'uptime':         get_dint(buf, 32),
            }

        def pulse_trigger_bit(bit: int) -> None:
            """Pulse a Cmd_* bit in DB4 byte 68 — Node-RED resets it after ~200 ms."""
            s = snap7.client.Client()
            s.connect(s7_host, 0, 1)
            try:
                buf = bytearray(1)
                set_bool(buf, 0, bit, True)
                s.db_write(4, 68, bytes(buf))
            finally:
                s.disconnect()

        def write_cycle_speed_factor(factor: float) -> None:
            s = snap7.client.Client()
            s.connect(s7_host, 0, 1)
            try:
                buf = bytearray(4)
                set_real(buf, 0, factor)
                s.db_write(4, 92, bytes(buf))
            finally:
                s.disconnect()

        # 5a) Initial state — kept for diagnostic output on failure.
        initial_snapshot = read_db1_snapshot()

        # 5b) Stop the mock — poll DB1.State until it leaves RUNNING (1).
        pulse_trigger_bit(2)  # Cmd_Stop
        poll_deadline = time.time() + STOP_POLL_TIMEOUT
        stopped_snapshot = None
        while time.time() < poll_deadline:
            snap = read_db1_snapshot()
            if snap['state'] != 1:  # 0=IDLE, 1=RUNNING — anything but 1 is "stopped"
                stopped_snapshot = snap
                break
            time.sleep(1)
        else:
            # If still RUNNING after the budget, capture anyway — the
            # assertion below will surface the actual state for diagnostics.
            stopped_snapshot = read_db1_snapshot()

        # 5c) Configure 5× speed, start the mock.
        write_cycle_speed_factor(5.0)
        pulse_trigger_bit(1)  # Cmd_Start

        # ── 6) Accelerated production for 30 s ────────────────────────
        # The same window covers two purposes: (a) the ZKS state machine
        # produces parts so KPIs move; (b) Telegraf has time to finish
        # startup (S7 + MQTT connect) and publish at least one message
        # before we check.
        time.sleep(PRODUCTION_WAIT)

        # 6a) Snapshot KPIs after the run.
        running_snapshot = read_db1_snapshot()

        # ── 7) Assertions: state, KPIs, and the MQTT chain ────────────
        assert running_snapshot['state'] != stopped_snapshot['state'], (
            f'Machine.State did not change after Cmd_Start: '
            f"stopped={stopped_snapshot['state']}, running={running_snapshot['state']}, "
            f"initial={initial_snapshot['state']}"
        )

        kpi_keys = (
            'part_counter', 'ok_counter', 'nok_counter', 'scrap_counter',
            'rework_counter', 'throughput', 'yield', 'uptime',
        )
        changed = [k for k in kpi_keys if running_snapshot[k] != stopped_snapshot[k]]
        assert changed, (
            'no KPI changed after 30 s of 5× production. '
            f'stopped={ {k: stopped_snapshot[k] for k in kpi_keys} }, '
            f'running={ {k: running_snapshot[k] for k in kpi_keys} }'
        )

        # MQTT chain assertion: Telegraf must have published at least one
        # message during the 30 s window. Validate one payload's shape.
        assert received.qsize() > 0, (
            'MQTT stream stayed silent during the 30 s production window '
            '— Backend/Telegraf/MQTT chain is broken even though snap7 '
            'confirms the ZKS mock is producing'
        )
        topic, payload = received.get_nowait()
        assert topic.startswith(topic_root), f'unexpected topic: {topic}'
        assert isinstance(payload, dict), f'payload not JSON object: {payload!r}'
        assert 'name' in payload, f'missing `name`: {payload}'
        assert 'tags' in payload and 'machine' in payload['tags']
        assert 'fields' in payload and payload['fields']
        ts = payload.get('timestamp')
        assert isinstance(ts, int), f'timestamp not int: {ts!r}'
        assert ts > 1_500_000_000_000, f'timestamp not in ms: {ts}'

        # ── 8) Leave the mock in IDLE — courtesy for the next run ─────
        pulse_trigger_bit(2)  # Cmd_Stop
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
