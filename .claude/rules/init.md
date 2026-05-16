# Project Initialization Check

> MANDATORY — run this check before starting ANY work.

## Project Overview
**PLC Datalink RFC1006** — a Telegraf-based gateway that reads data points from S7 PLCs via the RFC1006 protocol and publishes them to an MQTT broker. The system has three containers:

- **backend** — Python/Flask REST API + Telegraf processes (managed via supervisord)
- **frontend** — Angular web UI (served by nginx on port 80)
- **database** — CouchDB for persisting machine configurations

## Initialization Check
Before touching code, verify the repo state:

1. Run `ls` at the repo root — confirm `backend/`, `frontend/`, `database/` directories exist
2. Confirm the two compose files exist: `dc-plc-datalink-rfc1006-local.yml` (build from source) and `dc-plc-datalink-rfc1006-acr.yml` (pull from ACR)
3. Check `git status` — note any in-progress work before starting new changes
4. Check `architecture/decisions/` if it exists — review prior ADRs before structural changes
5. Read `README.md` for current configuration UI flow and PLC address format

**If touching backend:**
- Verify `backend/src/` layout (`routes.py`, `plc_datalink_rfc1006_model.py`, `services/`)
- Check `backend/requirements.txt` and `backend/openapi/plc_datalink_rfc1006_api.yml`

**If touching frontend:**
- Verify `frontend/src/app/` component layout (`create-configuration/`, `configuration-overview/`, `plc-states/`, `header/`, `modals/`, `services/`, `models/`)
- Check `frontend/package.json` for the Angular version

**If touching database:**
- Read `database/config/local.ini` for current CouchDB settings
- Read `database/config/init-db.sh` for DB bootstrap behavior

**If touching Telegraf or PLC communication:**
- Read `backend/config/dynamic_startup_telegraf.sh`
- Read `backend/src/services/telegraf_service.py` and a sample from `backend/config/example-machines/`

## Repository State Map
Project state lives in files, not in chat history:

| What | Where |
|---|---|
| Backend code | `backend/src/` |
| Backend services (CouchDB, Telegraf, MachineConfig) | `backend/src/services/` |
| Backend tests (curl scripts) | `backend/test/` |
| OpenAPI spec | `backend/openapi/plc_datalink_rfc1006_api.yml` |
| Telegraf example configs | `backend/config/example-machines/` |
| Telegraf startup script | `backend/config/dynamic_startup_telegraf.sh` |
| supervisord config | `backend/config/supervisord.conf` |
| Frontend Angular app | `frontend/src/app/` |
| Frontend nginx config | `frontend/config/` |
| CouchDB config | `database/config/local.ini` |
| CouchDB tests | `database/test/` |
| Container build files | `backend/Dockerfile`, `frontend/Dockerfile`, `database/Dockerfile` |
| Compose stacks | `dc-plc-datalink-rfc1006-local.yml`, `dc-plc-datalink-rfc1006-acr.yml` |
| CI/CD | `.github/workflows/` |
| README & PLC address spec | `README.md` |
| License | `LICENSE` |
| Screenshots | `images/` |

## Optional (created on demand)
The skills may create these when scoping a non-trivial feature:

- `docs/features/<feature-name>/` — feature scope notes
- `architecture/decisions/ADR-XXXX-*.md` — architecture decision records
- `CHANGELOG.md` — release notes

**If the user is asking for a quick fix or small change:** skip the optional docs and go straight to code.
**If the user is planning a structural change** (new endpoint, new container, new data type, breaking API change): scope it via `/requirements` first.
