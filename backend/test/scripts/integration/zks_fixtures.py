"""Shared ZKS-machine-mock test data.

The ZKS mock (see docs/machines-db-layout/zks-machine-mock/README.md) exposes
an S7/RFC1006 server on port 102 with four data blocks. The tag subset below
is the contract from docs/features/test-strategy/scope.md and is what every
integration test in this folder agrees to read/render.

Keep this list in sync with the table in scope.md. New tags belong here, not
in individual test files.
"""
from __future__ import annotations

import os


# Representative ZKS tag subset (one entry per S7 type the backend supports).
# Order matches scope.md so review diffs stay readable.
ZKS_TAGS: list[dict] = [
    {'tagAddress': 'DB1.I0',      'tagName': 'Machine.State'},
    {'tagAddress': 'DB1.DI4',     'tagName': 'Machine.PartCounter'},
    {'tagAddress': 'DB1.R28',     'tagName': 'Machine.Yield'},
    {'tagAddress': 'DB1.S20.20',  'tagName': 'Machine.LastError'},
    {'tagAddress': 'DB2.X0.0',    'tagName': 'Welds0.Done'},
    {'tagAddress': 'DB2.R2',      'tagName': 'Welds0.Current'},
    {'tagAddress': 'DB3.R4',      'tagName': 'Test.TotalResistance'},
    {'tagAddress': 'DB3.I8',      'tagName': 'Test.Result'},
    {'tagAddress': 'DB4.S32.32',  'tagName': 'Part.Serial'},
]


def zks_host() -> str:
    """Hostname/IP where the ZKS S7 server is reachable from the test container.

    `host.docker.internal` is mapped to the host gateway by
    dc-plc-datalink-rfc1006-test.yml (extra_hosts), so on Linux the test
    container reaches the host-bound ZKS mock through it.
    """
    return os.environ.get('ZKS_S7_HOST', 'host.docker.internal')


def zks_port() -> int:
    """TCP port of the ZKS S7 server.

    102 is the well-known RFC1006 port; the ZKS mock README documents 1102 as
    the fallback when 102 is unavailable to non-root users on the host.
    """
    return int(os.environ.get('ZKS_S7_PORT', '102'))


def zks_machine_config(machine_name: str = 'zks-mock') -> dict:
    """Return a complete machine-configuration dict targeting the ZKS mock.

    Shape matches conftest.SAMPLE_CONFIG_DICT (= what /config/create accepts).
    """
    return {
        'agent': {
            'flushInterval': '1s',
            'hostname': 'PLC Datalink RFC1006',
            'logTimezone': 'local',
            'quiet': False,
            'roundInterval': True,
        },
        'machineData': {
            'machineName': machine_name,
            'machineState': 'OFF',
            'pduSize': 480,
            'plcIp': zks_host(),
            'plcPort': zks_port(),
            'plcRack': 0,
            'plcSlot': 1,
            'requestInterval': 1,
            'requestS7commTimeout': '10s',
        },
        'mqttData': {
            'mqttDataFormat': 'json',
            'mqttIp': os.environ.get('TEST_MQTT_HOST', 'host.docker.internal'),
            'mqttJsonTimestampUnits': '1ms',
            'mqttLayout': 'non-batch',
            'mqttPort': int(os.environ.get('TEST_MQTT_PORT', '1883')),
            'mqttTopic': f'on/ot/{machine_name}',
        },
        'plcTagData': list(ZKS_TAGS),
    }
