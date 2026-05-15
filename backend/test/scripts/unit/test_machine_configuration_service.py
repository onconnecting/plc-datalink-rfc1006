"""Tests for the Telegraf config renderer.

The renderer (`MachineConfigurationService._write_configuration_content`)
must produce byte-for-byte the same output on every run for a given input.
A committed snapshot under `snapshots/sample_machine.conf` is the ground
truth — refresh it intentionally with `UPDATE_SNAPSHOT=1 pytest` when the
rendering logic changes.
"""
from __future__ import annotations

import io
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.services.machine_configuration_service import MachineConfigurationService


SNAPSHOT_DIR = Path(__file__).parent / 'snapshots'
SNAPSHOT_PATH = SNAPSHOT_DIR / 'sample_machine.conf'
# Fixed value so the snapshot does not include a temp-dir path.
TELEGRAF_CONFIG_FOLDER = '/etc/telegraf/telegraf.d'
UPDATE_SNAPSHOT = os.environ.get('UPDATE_SNAPSHOT') == '1'


def _render(sample_config_dict: dict) -> str:
    couchdb_service = MagicMock()
    couchdb_service.get_doc.return_value = sample_config_dict
    service = MachineConfigurationService(
        TELEGRAF_CONFIG_FOLDER,
        machine_name=sample_config_dict['machineData']['machineName'],
        couchdb_service=couchdb_service,
    )
    buf = io.StringIO()
    service._write_configuration_content(buf)
    return buf.getvalue()


def test_renderer_output_matches_snapshot(sample_config_dict):
    rendered = _render(sample_config_dict)
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    if UPDATE_SNAPSHOT or not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.write_text(rendered)
        if not UPDATE_SNAPSHOT:
            pytest.skip(
                f'snapshot generated at {SNAPSHOT_PATH} — commit it and re-run; '
                f'no actual comparison happened'
            )
    expected = SNAPSHOT_PATH.read_text()
    assert rendered == expected, (
        'Telegraf config renderer drifted from snapshot. '
        'Inspect the diff; if the change is intentional, run UPDATE_SNAPSHOT=1 pytest.'
    )


def test_renderer_includes_all_static_defaults(sample_config_dict):
    rendered = _render(sample_config_dict)
    assert 'flush_interval = "1s"' in rendered
    assert 'log_with_timezone = "local"' in rendered
    assert 'round_interval = true' in rendered
    assert 'data_format = "json"' in rendered
    assert 'layout = "non-batch"' in rendered
    assert 'json_timestamp_units = "1ms"' in rendered


def test_renderer_renders_every_tag(sample_config_dict):
    rendered = _render(sample_config_dict)
    for tag in sample_config_dict['plcTagData']:
        expected_field = (
            f'name="{sample_config_dict["machineData"]["machineName"]}.'
            f'{tag["tagName"]}", address="{tag["tagAddress"]}"'
        )
        assert expected_field in rendered, f'missing tag rendering for {tag}'


def test_renderer_quotes_server_with_port(sample_config_dict):
    rendered = _render(sample_config_dict)
    assert 'server = "192.168.4.100:102"' in rendered


def test_remove_log_file_silent_when_missing(tmp_path):
    service = MachineConfigurationService(
        str(tmp_path), machine_name='nope', couchdb_service=None
    )
    # No FileNotFoundError should escape.
    service.remove_log_file()


def test_remove_log_file_deletes_existing(tmp_path):
    log = tmp_path / 'machine.log'
    log.write_text('hello')
    service = MachineConfigurationService(
        str(tmp_path), machine_name='machine', couchdb_service=None
    )
    service.remove_log_file()
    assert not log.exists()


def test_remove_configuration_file_swallows_missing_files(tmp_path, mocker):
    """The method should not raise when files are absent; subprocess.run is
    only invoked once both files were successfully unlinked."""
    mock_run = mocker.patch.object(subprocess, 'run')
    service = MachineConfigurationService(
        str(tmp_path), machine_name='nope', couchdb_service=None
    )
    service.remove_configuration_file()  # nothing to remove → no raise
    mock_run.assert_not_called()
