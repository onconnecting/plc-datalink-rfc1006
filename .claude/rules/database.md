---
paths:
  - "database/**"
  - "backend/src/services/couchdb_service.py"
---

# Database (CouchDB) Rules

CouchDB persists one document per machine configuration. The document `_id` is the machine name (see `couchdb_service.py`). Each document holds the full PLC + MQTT + Telegraf agent settings (see `PlcDatalinkRFC1006Model.to_json_dict()`).

## Layout
```
database/
├── config/
│   ├── database-entrypoint.sh   # Container entrypoint
│   ├── init-db.sh               # Creates the configuration DB on first start
│   └── local.ini                # CouchDB tuning (queries, bind address, admin)
├── test/
│   ├── couch-cmd.sh
│   └── devBoard1Rest.sh
└── Dockerfile
```

## Document Schema
- One document per machine, `_id` = `machineName`
- Top-level keys: `agent`, `machineData`, `mqttData`, `plcTagData`
- All field names are camelCase (`machineName`, `plcIp`, `plcPort`, `plcRack`, `plcSlot`, `pduSize`, `requestInterval`, `requestS7commTimeout`, `mqttIp`, `mqttPort`, `mqttTopic`, `mqttDataFormat`, `mqttLayout`, `mqttJsonTimestampUnits`, `tagAddress`, `tagName`, …)
- `_rev` is managed by CouchDB — always pass it back on updates to avoid `409 Conflict`

## Configuration Rules
- Do not change the database name without updating `init-db.sh` AND the `DATABASE_NAME` env var consumed by `couchdb_service.py`
- Do not change CouchDB admin credentials without coordinating both compose files (`dc-plc-datalink-rfc1006-local.yml` and `dc-plc-datalink-rfc1006-acr.yml`) and the `env` file in `backend/config/`
- Tuning changes in `local.ini` (heap, query timeout, log level) require an ADR
- Never expose CouchDB on port `5984` to the public internet — it must stay on the `plc-datalink-rfc1006-network` bridge

## Schema Changes
- Adding optional fields to documents is backward-compatible — no migration needed
- Renaming or removing fields breaks existing documents — write a migration script in `database/` and document it in `CHANGELOG.md`
- Always update `PlcDatalinkRFC1006Model` (backend) AND the matching TypeScript model (frontend) in the same change

## Testing
- Use `database/test/couch-cmd.sh` and `database/test/devBoard1Rest.sh` as templates for ad-hoc verification
- After schema changes, verify create/read/update/delete with curl against the running container

## Backup / Restore
- The CouchDB data volume is `plc-datalink-rfc1006-database-data` mounted at `/opt/couchdb/data`
- Operational backup/restore procedure lives in `runbooks/` (created by `/operations` when needed)
