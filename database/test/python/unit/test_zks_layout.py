"""Unit tests for the ZKS reference machine layout and the helper that
translates it into the PlcDatalinkRFC1006 document shape.

The ZKS spec lives at docs/machines-db-layout/zks-machine-mock/db-layout.yaml
and is the canonical machine description used by the integration suite."""
from __future__ import annotations

import pytest

from zks_layout import (
    ZKS_MACHINE_NAME,
    build_machine_doc,
    expand_array_fields,
    iter_tags,
    load_layout,
    translate_field,
)


@pytest.fixture(scope="module")
def layout() -> dict:
    return load_layout()


def test_layout_server_endpoint(layout: dict) -> None:
    assert layout["server"]["ip"] == "192.168.0.180"
    assert layout["server"]["tcp_port"] == 102
    assert layout["server"]["rack"] == 0
    assert layout["server"]["slot"] == 1


def test_layout_has_four_dbs(layout: dict) -> None:
    numbers = sorted(db["number"] for db in layout["dbs"])
    assert numbers == [1, 2, 3, 4]


def test_layout_db_names(layout: dict) -> None:
    names = {db["number"]: db["name"] for db in layout["dbs"]}
    assert names == {1: "Machine", 2: "Welds", 3: "Test", 4: "PartAndCommands"}


@pytest.mark.parametrize(
    "field, expected",
    [
        # The classic per-type cases from the README's PLC address spec.
        ({"type": "INT", "offset": 0, "name": "State"}, "DB1.I0"),
        ({"type": "DINT", "offset": 4, "name": "PartCounter"}, "DB1.DI4"),
        ({"type": "REAL", "offset": 28, "name": "Yield"}, "DB1.R28"),
        ({"type": "BOOL", "offset": 36, "bit": 0, "name": "ErrorActive"}, "DB1.X36.0"),
        ({"type": "STRING", "offset": 38, "length": 20, "name": "LastError"}, "DB1.S38.20"),
        ({"type": "STRING", "offset": 0, "length": 32, "name": "Serial"}, "DB1.S0.32"),
    ],
)
def test_translate_field_examples(field: dict, expected: str) -> None:
    assert translate_field(1, field) == expected


def test_translate_field_rejects_unknown_type() -> None:
    with pytest.raises(ValueError):
        translate_field(1, {"type": "FLOAT64", "offset": 0, "name": "x"})


def test_expand_array_db2_welds(layout: dict) -> None:
    db2 = next(db for db in layout["dbs"] if db["number"] == 2)
    expanded = expand_array_fields(db2)
    # 12 welds × 7 fields = 84 expanded rows
    assert len(expanded) == 12 * 7
    # First weld lives at offset 0; the seventh weld (index 6) lives at
    # 6 * stride (24) = 144 + 0 = 144 for its `Done` bit.
    weld_06_done = next(f for f in expanded if f["name"] == "Weld_06.Done")
    assert weld_06_done["offset"] == 144
    # `Current` of weld 06 sits at base 144 + 2 = 146
    weld_06_current = next(f for f in expanded if f["name"] == "Weld_06.Current")
    assert weld_06_current["offset"] == 146


def test_iter_tags_expands_real_array_db3(layout: dict) -> None:
    tags = list(iter_tags(layout))
    seg = [t for t in tags if t["tagName"].startswith("SegmentResistance_")]
    # DB3 SegmentResistance has count=11
    assert len(seg) == 11
    # First entry at offset 12, stride 4 (REAL = 4 bytes).
    assert seg[0]["tagAddress"] == "DB3.R12"
    assert seg[1]["tagAddress"] == "DB3.R16"
    assert seg[-1]["tagAddress"] == f"DB3.R{12 + 10 * 4}"


def test_iter_tags_total_count(layout: dict) -> None:
    tags = list(iter_tags(layout))
    db1 = 12  # State, Mode, 5×counters, Throughput, Yield, Uptime, ErrorActive, LastError
    db2 = 12 * 7  # 12 welds × 7 fields per weld
    db3 = 4 + 11  # 4 scalars + REAL_ARRAY of 11
    db4 = 9 + 8  # 9 scalars/strings + 8 packed command bits at byte 68
    assert len(tags) == db1 + db2 + db3 + db4 == 128


def test_iter_tags_unique_names(layout: dict) -> None:
    names = [t["tagName"] for t in iter_tags(layout)]
    assert len(names) == len(set(names)), "tag names must be unique within the doc"


def test_build_machine_doc_matches_backend_shape(layout: dict) -> None:
    doc = build_machine_doc(layout)
    # Shape parity with `backend/src/plc_datalink_rfc1006_model.py` and the
    # canonical SAMPLE_CONFIG_DICT in backend/test/scripts/conftest.py.
    assert set(doc.keys()) == {"agent", "machineData", "mqttData", "plcTagData"}
    assert set(doc["machineData"].keys()) == {
        "machineName",
        "machineState",
        "pduSize",
        "plcIp",
        "plcPort",
        "plcRack",
        "plcSlot",
        "requestInterval",
        "requestS7commTimeout",
    }
    assert doc["machineData"]["machineName"] == ZKS_MACHINE_NAME
    assert doc["machineData"]["plcIp"] == "192.168.0.180"
    assert doc["machineData"]["plcPort"] == 102
    assert doc["mqttData"]["mqttTopic"] == f"on/ot/{ZKS_MACHINE_NAME}"
    # PLC tags are non-empty and every entry has the two required keys.
    assert doc["plcTagData"]
    for tag in doc["plcTagData"]:
        assert set(tag.keys()) == {"tagName", "tagAddress"}
