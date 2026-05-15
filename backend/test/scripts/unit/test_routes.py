"""HTTP-level tests for every route in src.routes.

CouchDB calls are intercepted with `requests_mock` (CouchDBService uses
requests under the hood). TelegrafService and MachineConfigurationService
are patched at the routes-module level — both are instantiated per-request
inside route handlers, so the module-level patch wraps every construction.
"""
from __future__ import annotations

import json

import pytest


COUCHDB_BASE = 'http://couchdb-test:5984/datalink'
SAMPLE_DOC_RESPONSE = {
    '_id': 'sample',
    '_rev': '1-aaa',
    'machineData': {'machineName': 'sample'},
}


# ─── /config/read/all ───────────────────────────────────────────────────


def test_read_all_config_returns_200(client, requests_mock):
    payload = {'rows': [{'id': 'sample', 'doc': SAMPLE_DOC_RESPONSE}]}
    requests_mock.get(f'{COUCHDB_BASE}/_all_docs', json=payload)
    response = client.get('/config/read/all')
    assert response.status_code == 200
    assert response.get_json() == payload


def test_read_all_config_404_when_couchdb_missing(client, requests_mock):
    requests_mock.get(f'{COUCHDB_BASE}/_all_docs', status_code=404, json={})
    response = client.get('/config/read/all')
    assert response.status_code == 404


# ─── /config/read/one ───────────────────────────────────────────────────


def test_read_one_config_returns_200(client, requests_mock):
    requests_mock.get(f'{COUCHDB_BASE}/sample', json=SAMPLE_DOC_RESPONSE)
    response = client.get('/config/read/one?machine_name=sample')
    assert response.status_code == 200
    assert response.get_json()['_id'] == 'sample'


def test_read_one_config_400_without_machine_name(client):
    response = client.get('/config/read/one')
    assert response.status_code == 400


def test_read_one_config_404_when_missing(client, requests_mock):
    requests_mock.get(f'{COUCHDB_BASE}/sample', status_code=404, json={})
    response = client.get('/config/read/one?machine_name=sample')
    assert response.status_code == 404


# ─── /config/create ─────────────────────────────────────────────────────


def test_create_config_happy_path(client, sample_config_create_body, requests_mock):
    requests_mock.put(
        f'{COUCHDB_BASE}/sample',
        json={'ok': True, 'id': 'sample', 'rev': '1-aaa'},
    )
    response = client.post(
        '/config/create',
        data=sample_config_create_body,
        content_type='application/json',
    )
    assert response.status_code == 200


def test_create_config_409_on_conflict(client, sample_config_create_body, requests_mock):
    requests_mock.put(f'{COUCHDB_BASE}/sample', status_code=409, json={})
    response = client.post(
        '/config/create',
        data=sample_config_create_body,
        content_type='application/json',
    )
    assert response.status_code == 409


def test_create_config_400_on_invalid_model(client, sample_config_dict):
    sample_config_dict['machineData'].pop('machineName')
    body = json.dumps(json.dumps(sample_config_dict))
    response = client.post(
        '/config/create',
        data=body,
        content_type='application/json',
    )
    assert response.status_code == 400


# ─── /config/update ─────────────────────────────────────────────────────


def test_update_config_happy_path(client, requests_mock):
    requests_mock.get(
        f'{COUCHDB_BASE}/sample',
        json={**SAMPLE_DOC_RESPONSE, '_rev': '1-aaa'},
    )
    requests_mock.put(
        f'{COUCHDB_BASE}/sample',
        json={'ok': True, 'id': 'sample', 'rev': '2-bbb'},
    )
    response = client.put(
        '/config/update',
        json={'machineData': {'machineName': 'sample'}},
    )
    assert response.status_code == 200


def test_update_config_400_missing_machine_data(client):
    response = client.put('/config/update', json={'foo': 'bar'})
    assert response.status_code == 400


def test_update_config_400_missing_machine_name(client):
    response = client.put('/config/update', json={'machineData': {}})
    assert response.status_code == 400


def test_update_config_404_when_missing(client, requests_mock):
    requests_mock.get(f'{COUCHDB_BASE}/sample', status_code=404, json={})
    response = client.put(
        '/config/update',
        json={'machineData': {'machineName': 'sample'}},
    )
    assert response.status_code == 404


def test_update_config_409_on_rev_conflict(client, requests_mock):
    requests_mock.get(
        f'{COUCHDB_BASE}/sample',
        json={**SAMPLE_DOC_RESPONSE, '_rev': '1-aaa'},
    )
    requests_mock.put(f'{COUCHDB_BASE}/sample', status_code=409, json={})
    response = client.put(
        '/config/update',
        json={'machineData': {'machineName': 'sample'}},
    )
    assert response.status_code == 409


# ─── /config/remove ─────────────────────────────────────────────────────


@pytest.fixture
def telegraf_class_mock(mocker):
    return mocker.patch('src.routes.TelegrafService', autospec=True)


@pytest.fixture
def machine_config_class_mock(mocker):
    return mocker.patch('src.routes.MachineConfigurationService', autospec=True)


def test_remove_config_happy_path(
    client, telegraf_class_mock, machine_config_class_mock, requests_mock
):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = []
    requests_mock.get(
        f'{COUCHDB_BASE}/sample',
        json={**SAMPLE_DOC_RESPONSE, '_rev': '1-aaa'},
    )
    requests_mock.delete(f'{COUCHDB_BASE}/sample', json={'ok': True})
    response = client.get('/config/remove?machine_name=sample')
    assert response.status_code == 200
    machine_config_class_mock.return_value.remove_log_file.assert_called_once()


def test_remove_config_400_without_machine_name(client):
    response = client.get('/config/remove')
    assert response.status_code == 400


def test_remove_config_409_when_running(
    client, telegraf_class_mock, machine_config_class_mock
):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = [
        {'machine_name': 'sample', 'process': '111'}
    ]
    response = client.get('/config/remove?machine_name=sample')
    assert response.status_code == 409


def test_remove_config_404_when_missing(
    client, telegraf_class_mock, machine_config_class_mock, requests_mock
):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = []
    requests_mock.get(f'{COUCHDB_BASE}/sample', status_code=404, json={})
    response = client.get('/config/remove?machine_name=sample')
    assert response.status_code == 404


# ─── /machine/start  /machine/stop ──────────────────────────────────────


def test_machine_start_happy_path(client, telegraf_class_mock, requests_mock):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = []
    requests_mock.get(f'{COUCHDB_BASE}/sample', json=SAMPLE_DOC_RESPONSE)
    response = client.get('/machine/start?machine_name=sample')
    assert response.status_code == 200
    telegraf_class_mock.return_value.start_telegraf_service.assert_called_once()


def test_machine_start_restarts_if_already_running(
    client, telegraf_class_mock, requests_mock
):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = [
        {'machine_name': 'sample', 'process': '111'}
    ]
    requests_mock.get(f'{COUCHDB_BASE}/sample', json=SAMPLE_DOC_RESPONSE)
    response = client.get('/machine/start?machine_name=sample')
    assert response.status_code == 200
    telegraf_class_mock.return_value.stop_telegraf_service.assert_called_once()
    telegraf_class_mock.return_value.start_telegraf_service.assert_called_once()


def test_machine_start_400_without_machine_name(client):
    response = client.get('/machine/start')
    assert response.status_code == 400


def test_machine_start_404_when_config_missing(client, telegraf_class_mock, requests_mock):
    requests_mock.get(f'{COUCHDB_BASE}/sample', status_code=404, json={})
    response = client.get('/machine/start?machine_name=sample')
    assert response.status_code == 404


def test_machine_stop_happy_path(client, telegraf_class_mock, requests_mock):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = [
        {'machine_name': 'sample', 'process': '111'}
    ]
    requests_mock.get(f'{COUCHDB_BASE}/sample', json=SAMPLE_DOC_RESPONSE)
    response = client.get('/machine/stop?machine_name=sample')
    assert response.status_code == 200
    telegraf_class_mock.return_value.stop_telegraf_service.assert_called_once()


def test_machine_stop_when_not_running(client, telegraf_class_mock, requests_mock):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = []
    requests_mock.get(f'{COUCHDB_BASE}/sample', json=SAMPLE_DOC_RESPONSE)
    response = client.get('/machine/stop?machine_name=sample')
    assert response.status_code == 200
    telegraf_class_mock.return_value.stop_telegraf_service.assert_not_called()


def test_machine_stop_400_without_machine_name(client):
    response = client.get('/machine/stop')
    assert response.status_code == 400


# ─── /machine/online ────────────────────────────────────────────────────


def test_machine_online_returns_active(client, telegraf_class_mock):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = [
        {'machine_name': 'a', 'process': '1'},
        {'machine_name': 'b', 'process': '2'},
    ]
    response = client.get('/machine/online')
    assert response.status_code == 200
    assert len(response.get_json()['machines']) == 2


def test_machine_online_404_when_none(client, telegraf_class_mock):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = []
    response = client.get('/machine/online')
    assert response.status_code == 404


# ─── /machine/state ─────────────────────────────────────────────────────


def test_machine_state_returns_state(client, telegraf_class_mock):
    telegraf_class_mock.return_value.get_current_telegraf_state.return_value = {
        'active_connection': True,
        'last_update': '2026-05-15T10:00:00',
        'last_disconnect': None,
    }
    response = client.get('/machine/state?machine_name=sample')
    assert response.status_code == 200
    assert response.get_json()['State']['active_connection'] is True


def test_machine_state_400_without_machine_name(client):
    response = client.get('/machine/state')
    assert response.status_code == 400


def test_machine_state_404_when_no_state(client, telegraf_class_mock):
    telegraf_class_mock.return_value.get_current_telegraf_state.return_value = None
    response = client.get('/machine/state?machine_name=sample')
    assert response.status_code == 404


# ─── /machine/configured  /machine/standby ──────────────────────────────


def test_machine_configured_strips_conf_suffix(client, telegraf_class_mock):
    telegraf_class_mock.return_value.get_configured_machines.return_value = [
        'a.conf',
        'b.conf',
        'noise.txt',
    ]
    response = client.get('/machine/configured')
    assert response.status_code == 200
    assert response.get_json()['machines'] == ['a', 'b']


def test_machine_standby_strips_log_suffix(client, telegraf_class_mock):
    telegraf_class_mock.return_value.get_logged_machines.return_value = [
        'a.log',
        'b.log',
        'noise.txt',
    ]
    response = client.get('/machine/standby')
    assert response.status_code == 200
    assert response.get_json()['machines'] == ['a', 'b']


# ─── /machine/remove ────────────────────────────────────────────────────


def test_machine_remove_happy_path(client, telegraf_class_mock, machine_config_class_mock):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = []
    response = client.get('/machine/remove?machine_name=sample')
    assert response.status_code == 200
    machine_config_class_mock.return_value.remove_log_file.assert_called_once()


def test_machine_remove_400_without_machine_name(client):
    response = client.get('/machine/remove')
    assert response.status_code == 400


def test_machine_remove_409_when_running(
    client, telegraf_class_mock, machine_config_class_mock
):
    telegraf_class_mock.return_value.get_active_telegraf_services.return_value = [
        {'machine_name': 'sample', 'process': '111'}
    ]
    response = client.get('/machine/remove?machine_name=sample')
    assert response.status_code == 409


# ─── /swagger + openapi spec ────────────────────────────────────────────


def test_swagger_blueprint_mounted(client):
    response = client.get('/swagger/')
    # Swagger UI returns 200; if it can't find the blueprint we'd see 404.
    assert response.status_code == 200
