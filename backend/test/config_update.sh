#!/bin/bash

curl -X PUT \
  http://127.0.0.1:5000/config/update \
  -H 'Content-Type: application/json' \
  -d '{
    "agent": {
        "flushInterval": "1s",
        "hostname": "PLC Datalink RFC1006",
        "logTimezone": "local",
        "quiet": false,
        "roundInterval": true
    },
    "machineData": {
        "machineName": "devBoard4711",
        "machineState": "OFF",
        "pduSize": 10,
        "plcIp": "192.168.4.100",
        "plcPort": 102,
        "plcRack": 0,
        "plcSlot": 1,
        "requestInterval": 1,
        "requestS7commTimeout": "10s"
    },
    "mqttData": {
        "mqttDataFormat": "json",
        "mqttIp": "192.168.4.172",
        "mqttJsonTimestampUnits": "1ms",
        "mqttLayout": "non-batch",
        "mqttPort": 1883,
        "mqttTopic": "on/ot/devBoard"
    },
    "plcTagData": [
        {
            "tagAddress": "DB9.X1732.1",
            "tagName": "lightBarrier"
        },
        {
            "tagAddress": "DB9.X1732.2",
            "tagName": "lightBarrier2"
        }
    ]
}'
