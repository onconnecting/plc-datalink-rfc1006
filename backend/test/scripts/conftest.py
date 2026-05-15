"""Shared pytest fixtures for the backend test suite.

Tests run inside the Dockerfile.test container with WORKDIR=/app and
PYTHONPATH=/app, so `src.*` imports work directly.
"""
from __future__ import annotations

import copy
import json

import pytest
from flask import Flask
from flask_cors import CORS

from src.routes import configure_routes


# Canonical, complete sample input — matches backend/test/curl/config_create.sh
SAMPLE_CONFIG_DICT: dict = {
    'agent': {
        'flushInterval': '1s',
        'hostname': 'PLC Datalink RFC1006',
        'logTimezone': 'local',
        'quiet': False,
        'roundInterval': True,
    },
    'machineData': {
        'machineName': 'sample',
        'machineState': 'OFF',
        'pduSize': 10,
        'plcIp': '192.168.4.100',
        'plcPort': 102,
        'plcRack': 0,
        'plcSlot': 1,
        'requestInterval': 1,
        'requestS7commTimeout': '10s',
    },
    'mqttData': {
        'mqttDataFormat': 'json',
        'mqttIp': '192.168.4.172',
        'mqttJsonTimestampUnits': '1ms',
        'mqttLayout': 'non-batch',
        'mqttPort': 1883,
        'mqttTopic': 'on/ot/sample',
    },
    'plcTagData': [
        {'tagAddress': 'DB2000.X0.0', 'tagName': 'Bool_Value'},
        {'tagAddress': 'DB2000.B1', 'tagName': 'Byte_Value'},
        {'tagAddress': 'DB2000.C2', 'tagName': 'Char_Value'},
        {'tagAddress': 'DB2000.W4', 'tagName': 'Word_Value'},
        {'tagAddress': 'DB2000.I6', 'tagName': 'Int_Value'},
        {'tagAddress': 'DB2000.DW8', 'tagName': 'Dword_Value'},
        {'tagAddress': 'DB2000.DI12', 'tagName': 'Dint_Value'},
        {'tagAddress': 'DB2000.R16', 'tagName': 'Real_Value'},
        {'tagAddress': 'DB2000.DT20', 'tagName': 'DateTime_Value'},
        {'tagAddress': 'DB2000.S30.13', 'tagName': 'String_Value'},
    ],
}

TEST_DATABASE_URL = 'http://couchdb-test:5984'
TEST_DATABASE_NAME = 'datalink'
TEST_DATABASE_USER = 'admin'
TEST_DATABASE_PASSWORD = 'admin'


@pytest.fixture
def sample_config_dict() -> dict:
    return copy.deepcopy(SAMPLE_CONFIG_DICT)


@pytest.fixture
def sample_config_create_body() -> str:
    # The /config/create route does json.loads(request.get_json()) — the body
    # is a JSON-encoded string that itself contains JSON (see the comment in
    # frontend/src/app/services/config.service.ts).
    return json.dumps(json.dumps(SAMPLE_CONFIG_DICT))


@pytest.fixture
def app(tmp_path):
    flask_app = Flask(__name__)
    CORS(flask_app)
    flask_app.config.update(
        DATABASE_USER=TEST_DATABASE_USER,
        SECRET_KEY=TEST_DATABASE_PASSWORD,
        DATABASE_URL=TEST_DATABASE_URL,
        DATABASE_NAME=TEST_DATABASE_NAME,
        TELEGRAF_CONFIG_FOLDER=str(tmp_path),
        TESTING=True,
    )
    configure_routes(flask_app)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
