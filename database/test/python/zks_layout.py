"""Helpers that turn the ZKS reference machine's S7 db-layout into the
PlcDatalinkRFC1006 document shape used by `backend/src/services/couchdb_service.py`.

The ZKS YAML at docs/machines-db-layout/zks-machine-mock/db-layout.yaml is the
single source of truth for that machine. Unit tests verify the translation; the
integration suite uses the same translation to seed CouchDB.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List

import yaml


ZKS_LAYOUT_ENV = "PLC_DATALINK_ZKS_LAYOUT"
ZKS_LAYOUT_FALLBACK = Path("/app/docs/machines-db-layout/zks-machine-mock/db-layout.yaml")
ZKS_MACHINE_NAME = "zks-machine-mock"

# Mapping of the S7 type names used in the ZKS YAML to the RFC1006 tag-address
# type character understood by the backend (see README.md "PLC Address
# specification"). REAL_ARRAY is intentionally not in the table — it's expanded
# into a sequence of `R`-typed tags by `translate_field`.
_TYPE_CHAR: Dict[str, str] = {
    "BOOL": "X",
    "INT": "I",
    "DINT": "DI",
    "REAL": "R",
    "STRING": "S",
    "BYTE": "B",
    "WORD": "W",
    "DWORD": "DW",
    "DT": "DT",
}


def load_layout(path: os.PathLike | str | None = None) -> dict:
    """Load the ZKS db-layout YAML. Path defaults to $PLC_DATALINK_ZKS_LAYOUT,
    then to the bind-mount location used in dc-plc-datalink-rfc1006-test.yml."""
    if path is None:
        path = os.environ.get(ZKS_LAYOUT_ENV) or ZKS_LAYOUT_FALLBACK
    with open(path) as f:
        return yaml.safe_load(f)


def translate_field(db_number: int, field: dict) -> str:
    """Translate one ZKS field dict to an RFC1006 tag address.

    Examples:
        DB1 INT@0           -> "DB1.I0"
        DB1 DINT@4          -> "DB1.DI4"
        DB1 REAL@28         -> "DB1.R28"
        DB1 BOOL@36 bit 0   -> "DB1.X36.0"
        DB1 STRING[20]@38   -> "DB1.S38.20"
    """
    s7_type = field["type"]
    offset = field["offset"]
    if s7_type == "BOOL":
        return f"DB{db_number}.X{offset}.{field['bit']}"
    if s7_type == "STRING":
        return f"DB{db_number}.S{offset}.{field['length']}"
    try:
        char = _TYPE_CHAR[s7_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported ZKS type: {s7_type}") from exc
    return f"DB{db_number}.{char}{offset}"


def expand_array_fields(db: dict) -> List[dict]:
    """For DBs with an `array:` section (e.g. DB2 Welds), return a flat list of
    {offset, type, name, ...} dicts — one entry per element-field combination
    with element-aware names like `Weld_03.Current`."""
    array_cfg = db["array"]
    count = array_cfg["count"]
    stride = array_cfg["stride"]
    base = db["name"][:-1] if db["name"].endswith("s") else db["name"]
    width = len(str(count - 1))
    fields: List[dict] = []
    for index in range(count):
        prefix = f"{base}_{str(index).zfill(width)}"
        element_offset = index * stride
        for field in array_cfg["fields"]:
            new_field = dict(field)
            new_field["offset"] = field["offset"] + element_offset
            new_field["name"] = f"{prefix}.{field['name']}"
            fields.append(new_field)
    return fields


def iter_tags(layout: dict) -> Iterable[dict]:
    """Yield every PLC tag (name + RFC1006 address) implied by the layout.
    REAL_ARRAY is exploded into N `R`-typed tags addressed at +4 offsets each."""
    for db in layout["dbs"]:
        db_number = db["number"]
        if "fields" in db:
            sources = list(db["fields"])
        elif "array" in db:
            sources = expand_array_fields(db)
        else:
            raise ValueError(f"DB{db_number} has neither `fields` nor `array`")

        for field in sources:
            if field["type"] == "REAL_ARRAY":
                for i in range(field["count"]):
                    yield {
                        "tagName": f"{field['name']}_{i:02d}",
                        "tagAddress": f"DB{db_number}.R{field['offset'] + i * 4}",
                    }
                continue
            yield {
                "tagName": field["name"],
                "tagAddress": translate_field(db_number, field),
            }


def build_machine_doc(layout: dict, *, mqtt_ip: str = "192.168.4.172", mqtt_port: int = 1883) -> dict:
    """Build a full PlcDatalinkRFC1006 document for the ZKS reference machine.

    Matches the shape produced by
    `backend/src/plc_datalink_rfc1006_model.PlcDatalinkRFC1006Model.to_json_dict`
    (see backend/test/scripts/conftest.py:SAMPLE_CONFIG_DICT for the canonical
    form)."""
    server = layout["server"]
    tags = list(iter_tags(layout))
    return {
        "agent": {
            "flushInterval": "1s",
            "hostname": "PLC Datalink RFC1006",
            "logTimezone": "local",
            "quiet": False,
            "roundInterval": True,
        },
        "machineData": {
            "machineName": ZKS_MACHINE_NAME,
            "machineState": "OFF",
            "pduSize": 480,
            "plcIp": server["ip"],
            "plcPort": server["tcp_port"],
            "plcRack": server["rack"],
            "plcSlot": server["slot"],
            "requestInterval": 1,
            "requestS7commTimeout": "10s",
        },
        "mqttData": {
            "mqttDataFormat": "json",
            "mqttIp": mqtt_ip,
            "mqttJsonTimestampUnits": "1ms",
            "mqttLayout": "non-batch",
            "mqttPort": mqtt_port,
            "mqttTopic": f"on/ot/{ZKS_MACHINE_NAME}",
        },
        "plcTagData": tags,
    }
