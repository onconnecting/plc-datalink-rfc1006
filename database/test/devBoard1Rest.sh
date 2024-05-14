#!/bin/bash

# Define the URL
URL="http://admin:password@localhost:5984/datalink"

# Make the PUT request to create the database
curl -X PUT $URL

# Wait for the database creation to complete (you can customize this timeout)
sleep 5

# Define the JSON payload 1
JSON_PAYLOAD1='{
    "_id": "devBoard1",
    "agent": {
        "roundInterval": true,
        "quiet": false,
        "flushInterval": "1s",
        "logTimezone": "local",
        "hostname": "PLC Datalink RFC1006"
    },
    "baseData": {
        "machineName": "devBoard",
        "machineState": "OFF",
        "pduSize": 10,
        "requestInterval": "1s",
        "requestS7commTimeout": "10s"
    },
    "mqttData": {
        "mqttIp": "192.168.4.172",
        "mqttPort": 1883,
        "mqttTopic": "on/ot/dev-board",
        "mqttDataFormat": "json",
        "mqttLayout": "non-batch",
        "mqttJsonTimestampUnits": "1ms"
    },
    "plcData": {
        "plcIp": "192.168.4.100",
        "plcPort": 102,
        "plcRack": 0,
        "plcSlot": 1
    },
    "plcTagData": [
        {"tagName": "lightBarrier1", "tagAddress": "DB9.X1732.1"},
        {"tagName": "lightBarrier2", "tagAddress": "DB9.X1732.2"}
    ]
}'

# Make the POST request using curl to add the document
curl -X POST $URL \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD1"

# Define the JSON payload 2
JSON_PAYLOAD2='{
    "_id": "devBoard2",
    "agent": {
        "roundInterval": true,
        "quiet": false,
        "flushInterval": "1s",
        "logTimezone": "local",
        "hostname": "PLC Datalink RFC1006"
    },
    "baseData": {
        "machineName": "devBoard",
        "machineState": "OFF",
        "pduSize": 10,
        "requestInterval": "1s",
        "requestS7commTimeout": "10s"
    },
    "mqttData": {
        "mqttIp": "192.168.4.172",
        "mqttPort": 1883,
        "mqttTopic": "on/ot/dev-board",
        "mqttDataFormat": "json",
        "mqttLayout": "non-batch",
        "mqttJsonTimestampUnits": "1ms"
    },
    "plcData": {
        "plcIp": "192.168.4.100",
        "plcPort": 102,
        "plcRack": 0,
        "plcSlot": 1
    },
    "plcTagData": [
        {"tagName": "lightBarrier1", "tagAddress": "DB9.X1732.1"},
        {"tagName": "lightBarrier2", "tagAddress": "DB9.X1732.2"}
    ]
}'

# Make the POST request using curl to add the document
curl -X POST $URL \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD2"
