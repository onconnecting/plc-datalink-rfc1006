import copy

import pytest

from src.plc_datalink_rfc1006_model import PlcDatalinkRFC1006Model


def test_from_dict_roundtrip_is_stable(sample_config_dict):
    model = PlcDatalinkRFC1006Model.from_dict(sample_config_dict)
    once = model.to_json_dict()
    twice = PlcDatalinkRFC1006Model.from_dict(once).to_json_dict()
    assert once == twice


def test_from_dict_to_json_dict_matches_input(sample_config_dict):
    out = PlcDatalinkRFC1006Model.from_dict(sample_config_dict).to_json_dict()
    for section in ('agent', 'machineData', 'mqttData'):
        assert out[section] == sample_config_dict[section]
    assert out['plcTagData'] == sample_config_dict['plcTagData']


def test_from_dict_fills_static_agent_defaults():
    minimal = {
        'agent': {},
        'machineData': {
            'machineName': 'm1',
            'pduSize': 10,
            'plcIp': '10.0.0.1',
            'plcPort': 102,
            'plcRack': 0,
            'plcSlot': 1,
            'requestInterval': 1,
        },
        'mqttData': {
            'mqttIp': '10.0.0.2',
            'mqttPort': 1883,
            'mqttTopic': 'topic',
        },
        'plcTagData': [],
    }
    out = PlcDatalinkRFC1006Model.from_dict(minimal).to_json_dict()
    assert out['agent'] == {
        'flushInterval': '1s',
        'hostname': 'PLC Datalink RFC1006',
        'logTimezone': 'local',
        'quiet': False,
        'roundInterval': True,
    }
    assert out['machineData']['machineState'] == 'OFF'
    assert out['machineData']['requestS7commTimeout'] == '10s'
    assert out['mqttData']['mqttDataFormat'] == 'json'
    assert out['mqttData']['mqttJsonTimestampUnits'] == '1ms'
    assert out['mqttData']['mqttLayout'] == 'non-batch'


def test_from_dict_missing_required_key_raises(sample_config_dict):
    broken = copy.deepcopy(sample_config_dict)
    del broken['machineData']['machineName']
    with pytest.raises(ValueError, match='Missing required key'):
        PlcDatalinkRFC1006Model.from_dict(broken)


# All PLC address types listed in .claude/rules/telegraf.md.
PLC_ADDRESS_CASES = [
    ('DB2000.X0.0', 'Bool'),
    ('DB2000.B1', 'Byte'),
    ('DB2000.C2', 'Char'),
    ('DB2000.W4', 'Word'),
    ('DB2000.DW8', 'DWord'),
    ('DB2000.I6', 'Int'),
    ('DB2000.DI12', 'DInt'),
    ('DB2000.R16', 'Real'),
    ('DB2000.DT20', 'DateTime'),
    ('DB2000.S30.13', 'String'),
]


@pytest.mark.parametrize('address,name', PLC_ADDRESS_CASES)
def test_plc_address_types_roundtrip(sample_config_dict, address, name):
    sample_config_dict['plcTagData'] = [{'tagAddress': address, 'tagName': name}]
    out = PlcDatalinkRFC1006Model.from_dict(sample_config_dict).to_json_dict()
    assert out['plcTagData'] == [{'tagAddress': address, 'tagName': name}]
