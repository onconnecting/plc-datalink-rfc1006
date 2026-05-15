"""Render the Telegraf config from a real ZKS machine-config dict.

This is the integration-test counterpart to the unit-level snapshot test:
the unit test pins the sample-machine output byte-for-byte. Here we plug in
the actual ZKS tag table and verify that every tag the ZKS docs document
appears in the generated Telegraf config — i.e. the renderer covers the
whole address grammar (`X`, `B`, `W`, `I`, `DI`, `R`, `DT`, `S`) used by
the mock, not just the unit sample.

`couchdb_service` is mocked here on purpose: the renderer is a pure
function of the config dict. Network access to a real CouchDB is exercised
separately by test_couchdb_zks_roundtrip.py.
"""
from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest

from src.services.machine_configuration_service import MachineConfigurationService

from .zks_fixtures import ZKS_TAGS


TELEGRAF_CONFIG_FOLDER = '/etc/telegraf/telegraf.d'


def _render(config: dict) -> str:
    couchdb_service = MagicMock()
    couchdb_service.get_doc.return_value = config
    service = MachineConfigurationService(
        TELEGRAF_CONFIG_FOLDER,
        machine_name=config['machineData']['machineName'],
        couchdb_service=couchdb_service,
    )
    buf = io.StringIO()
    service._write_configuration_content(buf)
    return buf.getvalue()


def test_renderer_outputs_s7comm_server_pointing_at_zks(zks_config):
    rendered = _render(zks_config)
    expected_server = (
        f'server = "{zks_config["machineData"]["plcIp"]}'
        f':{zks_config["machineData"]["plcPort"]}"'
    )
    assert expected_server in rendered


def test_renderer_emits_rack_and_slot_for_zks(zks_config):
    rendered = _render(zks_config)
    assert 'rack = 0' in rendered
    assert 'slot = 1' in rendered


@pytest.mark.parametrize('tag', ZKS_TAGS, ids=lambda t: t['tagName'])
def test_renderer_emits_every_zks_tag(zks_config, tag):
    rendered = _render(zks_config)
    expected_field = (
        f'name="{zks_config["machineData"]["machineName"]}.'
        f'{tag["tagName"]}", address="{tag["tagAddress"]}"'
    )
    assert expected_field in rendered, f'tag {tag} not rendered'


def test_renderer_emits_mqtt_topic_for_zks(zks_config):
    rendered = _render(zks_config)
    assert f'topic = "{zks_config["mqttData"]["mqttTopic"]}"' in rendered
    assert 'data_format = "json"' in rendered
    assert 'layout = "non-batch"' in rendered
