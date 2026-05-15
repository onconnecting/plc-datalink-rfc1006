"""Tests for the supervisord / telegraf process glue.

Every subprocess call is mocked — these tests must not exec ps, pgrep, kill
or supervisorctl on the host running pytest.
"""
from __future__ import annotations

import os
import signal
import subprocess
from types import SimpleNamespace

import pytest

from src.services import telegraf_service as ts_module
from src.services.telegraf_service import TelegrafService


def _make_service(tmp_path, machine_name='m1', couchdb_service=None):
    return TelegrafService(
        str(tmp_path), machine_name=machine_name, couchdb_service=couchdb_service
    )


def test_get_active_telegraf_services_parses_ps_output(mocker, tmp_path):
    fake_ps_output = (
        'root  123  0.0 0.0 telegraf --config /etc/telegraf/telegraf.d/m1.conf --watch-config x\n'
        'root  456  0.0 0.0 telegraf --config /etc/telegraf/telegraf.d/other.conf\n'
        'root  999  0.0 0.0 something_else\n'
    )
    mocker.patch.object(
        subprocess,
        'run',
        return_value=SimpleNamespace(stdout=fake_ps_output),
    )
    service = _make_service(tmp_path)
    result = service.get_active_telegraf_services()
    assert {item['machine_name'] for item in result} == {'m1', 'other'}
    assert {item['process'] for item in result} == {'123', '456'}


def test_get_active_telegraf_services_swallows_errors(mocker, tmp_path):
    mocker.patch.object(subprocess, 'run', side_effect=RuntimeError('boom'))
    service = _make_service(tmp_path)
    assert service.get_active_telegraf_services() == []


def test_get_configured_machines_lists_conf_files(tmp_path):
    (tmp_path / 'a.conf').write_text('')
    (tmp_path / 'b.conf').write_text('')
    (tmp_path / 'a.log').write_text('')
    (tmp_path / 'random.txt').write_text('')
    service = _make_service(tmp_path)
    result = sorted(service.get_configured_machines())
    assert result == ['a.conf', 'b.conf']


def test_get_logged_machines_lists_log_files(tmp_path):
    (tmp_path / 'a.log').write_text('')
    (tmp_path / 'b.log').write_text('')
    (tmp_path / 'a.conf').write_text('')
    service = _make_service(tmp_path)
    result = sorted(service.get_logged_machines())
    assert result == ['a.log', 'b.log']


def test_get_current_telegraf_state_returns_idle_when_no_log(tmp_path):
    service = _make_service(tmp_path, machine_name='nolog')
    state = service.get_current_telegraf_state()
    assert state == {'last_update': None, 'last_disconnect': None, 'active_connection': False}


def test_get_current_telegraf_state_detects_active_connection(tmp_path):
    log_line = '2026-05-15T10:00:00 D! [inputs.s7comm]   got [1] for field "x"\n'
    (tmp_path / 'm1.log').write_text(log_line)
    service = _make_service(tmp_path, machine_name='m1')
    state = service.get_current_telegraf_state()
    assert state['active_connection'] is True
    assert state['last_update'] == '2026-05-15T10:00:00'


def test_get_current_telegraf_state_detects_disconnect(tmp_path):
    log = (
        '2026-05-15T10:00:00 D! [inputs.s7comm]   got [1] for field "x"\n'
        '2026-05-15T10:00:10 I! [agent] Stopping running outputs\n'
    )
    (tmp_path / 'm1.log').write_text(log)
    service = _make_service(tmp_path, machine_name='m1')
    state = service.get_current_telegraf_state()
    assert state['active_connection'] is False
    assert state['last_disconnect'] == '2026-05-15T10:00:10'


def test_stop_telegraf_service_terminates_existing(mocker, tmp_path):
    mocker.patch.object(
        ts_module,
        'MachineConfigurationService',
        autospec=True,
    )
    pgrep_result = SimpleNamespace(stdout='4242\n')
    mocker.patch.object(subprocess, 'run', return_value=pgrep_result)
    mock_kill = mocker.patch.object(os, 'kill')

    service = _make_service(tmp_path, machine_name='m1')
    service.stop_telegraf_service()

    mock_kill.assert_called_once_with(4242, signal.SIGTERM)


def test_stop_telegraf_service_handles_no_existing_process(mocker, tmp_path):
    mocker.patch.object(
        ts_module,
        'MachineConfigurationService',
        autospec=True,
    )
    mocker.patch.object(
        subprocess, 'run', return_value=SimpleNamespace(stdout='')
    )
    mock_kill = mocker.patch.object(os, 'kill')

    service = _make_service(tmp_path, machine_name='m1')
    service.stop_telegraf_service()

    mock_kill.assert_not_called()


def test_start_telegraf_service_writes_config_and_starts_process(mocker, tmp_path):
    mock_config_cls = mocker.patch.object(
        ts_module,
        'MachineConfigurationService',
        autospec=True,
    )
    mocker.patch.object(
        subprocess, 'run', return_value=SimpleNamespace(stdout='')
    )
    mock_popen = mocker.patch.object(
        subprocess, 'Popen', return_value=SimpleNamespace(pid=1234)
    )

    service = _make_service(tmp_path, machine_name='m1')
    service.start_telegraf_service()

    mock_config_cls.return_value.write_configuration_to_file.assert_called_once()
    mock_popen.assert_called_once_with(['/app/backend-entrypoint.sh'])
