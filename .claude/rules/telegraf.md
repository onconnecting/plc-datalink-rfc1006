---
paths:
  - "backend/config/**"
  - "backend/src/services/telegraf_service.py"
  - "backend/src/services/machine_configuration_service.py"
---

# Telegraf & PLC / MQTT Rules

The backend container runs **one Telegraf process per active machine**, supervised by **supervisord**. Each Telegraf reads tags from an S7 PLC over RFC1006 (port 102 by default) and publishes them to MQTT.

## Layout
```
backend/config/
├── backend-entrypoint.sh
├── dynamic_startup_telegraf.sh   # Renders & launches per-machine Telegraf config
├── supervisord.conf              # Top-level supervisord rules
├── env                           # Env vars for the backend container
└── example-machines/             # Reference Telegraf configs (one per machine)
```

## Telegraf Process Lifecycle
1. The user creates a machine config via the UI → backend writes a CouchDB doc
2. The user clicks Start → backend renders a Telegraf `.conf` file and starts a supervisord-managed process
3. The user clicks Stop → backend tells supervisord to stop that process
4. The user clicks Remove → backend removes the doc + the per-machine log file

`telegraf_service.py` is the only module that should talk to supervisord. `machine_configuration_service.py` is the only module that should write Telegraf config files.

## PLC Address Format
General pattern: `<area>.<type><address>[.extra]` (e.g. `DB2000.I2`, `DB2000.X0.0`, `DB2000.S30.13`).

Supported types (from README):

| Type | Meaning | Extra | Example |
|---|---|---|---|
| `X` | Bit | bit index in byte | `DB2000.X0.0` |
| `B` | Byte (8) | — | `DB2000.B1` |
| `C` | Character (8) | — | `DB2000.C2` |
| `W` | Word (16) | — | `DB2000.W2` |
| `DW` | Double Word (32) | — | `DB2000.DW2` |
| `I` | Integer (16) | — | `DB2000.I2` |
| `DI` | Double Integer (32) | — | `DB2000.DI2` |
| `R` | Real (IEEE 754, 32) | — | `DB2000.R2` |
| `DT` | Date-Time | — | `DB2000.DT2` |
| `S` | String | max length | `DB2000.S30.13` |

Always validate addresses on both the frontend form (client-side feedback) and the backend (authoritative).

## MQTT Output
- Default broker port: `1883` (plain) — TLS is not configured by default
- Topic hierarchy convention: `on/ot-connector/<machine>/<channel>` (see README example)
- Payload: JSON with `name`, `tags.host`, `tags.machine`, `fields.*`, `timestamp` (ms since epoch)
- `mqttDataFormat` is fixed to `json` and `mqttJsonTimestampUnits` to `1ms` in the static defaults (see `PlcDatalinkRFC1006Model.from_dict`)
- Do not change the payload shape without an ADR — downstream consumers depend on it

## Configuration Defaults (do not change without an ADR)
From `PlcDatalinkRFC1006Model.from_dict`:
- `agent.flushInterval = "1s"`
- `agent.hostname = "PLC Datalink RFC1006"`
- `agent.logTimezone = "local"`
- `agent.roundInterval = true`
- `machineData.machineState = "OFF"` (initial)
- `machineData.requestS7commTimeout = "10s"`
- `mqttData.mqttLayout = "non-batch"`

## Quality Standards
- Validate a new Telegraf config locally before exposing it to supervisord (dry-run if possible)
- Verify a new PLC address type round-trips: UI form → backend validation → CouchDB doc → Telegraf config → MQTT payload
- Document any new address type or MQTT field in `README.md` and the OpenAPI spec
