# Backend Implementation Checklist

## Before Starting
- [ ] Scope note read (`docs/features/<name>/scope.md`) if applicable
- [ ] Relevant ADRs read (`architecture/decisions/`) if applicable
- [ ] `.claude/rules/backend.md` re-read for conventions
- [ ] Existing routes / services / model inspected to avoid duplication

## Routes (`backend/src/routes.py`)
- [ ] New/changed endpoint follows existing URL conventions (`/config/...`, `/machine/...`)
- [ ] Input validation returns `400` with specific message
- [ ] CouchDB errors mapped: `404` (missing), `409` (conflict)
- [ ] Response shape consistent: `{"message": ...}` or `{"error": ...}`
- [ ] Uses `logger = logging.getLogger('application_logger')`

## Data Model (`backend/src/plc_datalink_rfc1006_model.py`)
- [ ] New fields added to the appropriate dataclass
- [ ] `from_dict` parses the new fields (with static defaults if not user-provided)
- [ ] `to_json_dict` serializes the new fields with the documented camelCase keys
- [ ] Backward compatibility verified for existing CouchDB documents (or migration documented)

## Services (`backend/src/services/`)
- [ ] `couchdb_service.py` is the only module that talks to CouchDB
- [ ] `telegraf_service.py` is the only module that talks to supervisord
- [ ] `machine_configuration_service.py` is the only module that writes Telegraf configs / log files
- [ ] No business logic leaked into `routes.py`

## Telegraf Integration (if applicable)
- [ ] `dynamic_startup_telegraf.sh` updated for new launch behavior
- [ ] `supervisord.conf` updated if process management changed
- [ ] `backend/config/example-machines/` has a representative new example (if a new PLC type was added)
- [ ] PLC address parser handles the new type (and rejects malformed addresses)

## OpenAPI Spec (`backend/openapi/plc_datalink_rfc1006_api.yml`)
- [ ] New/changed endpoint documented (path, method, params, request body, responses)
- [ ] Operation IDs are stable (no silent removal — use `deprecated: true`)
- [ ] Spec renders at `/swagger` without errors

## Tests (`backend/test/`)
- [ ] curl script added or updated under `backend/test/curl/` for new/changed endpoints (manual smoke)
- [ ] pytest tests added or updated under `backend/test/scripts/` (route, service, model, snapshot — as applicable)
- [ ] Both happy path and failure path covered

## Test Run (Container — MANDATORY)
- [ ] `docker compose -f dc-plc-datalink-rfc1006-test.yml build backend-test` succeeds
- [ ] `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm backend-test` is green
- [ ] If the Telegraf renderer was touched: snapshot regenerated with `UPDATE_SNAPSHOT=1` and committed
- [ ] Pytest summary reported in chat (`N passed, …`)

## Runtime Verification (manual)
- [ ] `docker compose -f dc-plc-datalink-rfc1006-dev.yml build plc-datalink-rfc1006-backend` succeeds
- [ ] Stack starts and backend health is OK in `docker logs`
- [ ] Endpoint exercised manually — response matches the OpenAPI spec

## Documentation
- [ ] `README.md` updated if user-visible behavior changed (UI fields, PLC address format, MQTT payload)
- [ ] CHANGELOG.md updated (when `/commit` runs)

## Dependencies
- [ ] No new package added to `requirements.txt` without explicit user approval
- [ ] If a package was added, the `backend/Dockerfile` build still succeeds
