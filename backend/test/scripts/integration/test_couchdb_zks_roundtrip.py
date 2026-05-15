"""Persist a ZKS machine-config in a real CouchDB and read it back.

The unit-level couchdb_service tests stub the HTTP layer with
`requests-mock`. This test runs the same code path against a CouchDB:3
container started by testcontainers (see ADR-0008). The point is to catch
divergence between our mocked expectations and CouchDB's actual semantics
— `_rev` handling, conflict status codes, doc-id derivation from
machineName.
"""
from __future__ import annotations

import pytest
from requests.exceptions import HTTPError

from src.plc_datalink_rfc1006_model import PlcDatalinkRFC1006Model

from .zks_fixtures import zks_machine_config


def test_zks_config_create_read_update_delete(couchdb_service):
    config = PlcDatalinkRFC1006Model.from_dict(zks_machine_config()).to_json_dict()

    created = couchdb_service.create_doc(config)
    assert created['ok'] is True
    assert created['id'] == 'zks-mock'

    fetched = couchdb_service.get_doc('zks-mock')
    assert fetched['machineData']['plcRack'] == 0
    assert fetched['machineData']['plcSlot'] == 1
    assert len(fetched['plcTagData']) == len(config['plcTagData'])

    fetched['mqttData']['mqttTopic'] = 'on/ot/zks-mock/updated'
    updated = couchdb_service.update_doc('zks-mock', fetched)
    assert updated['rev'].startswith('2-')

    after = couchdb_service.get_doc('zks-mock')
    assert after['mqttData']['mqttTopic'] == 'on/ot/zks-mock/updated'

    deleted = couchdb_service.delete_doc('zks-mock', after['_rev'])
    assert deleted['ok'] is True

    with pytest.raises(HTTPError) as excinfo:
        couchdb_service.get_doc('zks-mock')
    assert excinfo.value.response.status_code == 404


def test_zks_config_create_conflict_returns_409(couchdb_service):
    config = PlcDatalinkRFC1006Model.from_dict(zks_machine_config()).to_json_dict()
    couchdb_service.create_doc(config)

    with pytest.raises(HTTPError) as excinfo:
        couchdb_service.create_doc(config)
    assert excinfo.value.response.status_code == 409


def test_all_docs_lists_zks_machine(couchdb_service):
    config = PlcDatalinkRFC1006Model.from_dict(zks_machine_config()).to_json_dict()
    couchdb_service.create_doc(config)

    listing = couchdb_service.get_all_docs()
    ids = [row['id'] for row in listing['rows'] if not row['id'].startswith('_design/')]
    assert 'zks-mock' in ids
