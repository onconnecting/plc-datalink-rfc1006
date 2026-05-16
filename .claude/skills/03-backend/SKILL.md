---
name: backend
description: Implement Python/Flask backend changes for the PLC Datalink RFC1006 project — routes, services (CouchDB, Telegraf, MachineConfiguration), data model, OpenAPI spec, supervisord and Telegraf integration.
argument-hint: "scope note path, endpoint name, or short description"
user-invocable: true
---

# Backend Engineer (Python / Flask)

## Role
You implement backend changes for the PLC Datalink RFC1006 platform. The backend is a Flask REST API that manages machine configurations in CouchDB and orchestrates Telegraf processes (one per machine) via supervisord.

## Before Starting
1. Read the relevant scope note in `docs/features/<feature-name>/scope.md` if it exists
2. Read related ADRs in `architecture/decisions/` if relevant
3. Read [.claude/rules/backend.md](../../../.claude/rules/backend.md) for backend conventions
4. Read [.claude/rules/telegraf.md](../../../.claude/rules/telegraf.md) if the change touches Telegraf
5. Check current state:
   - `backend/src/routes.py` — existing endpoints
   - `backend/src/plc_datalink_rfc1006_model.py` — current data model
   - `backend/src/services/` — service modules
   - `backend/openapi/plc_datalink_rfc1006_api.yml` — API spec
   - `backend/requirements.txt` — current dependencies

## Workflow

### 1. Confirm the Change
Use `AskUserQuestion` only for genuinely ambiguous points. Common clarifications:
- Is this a new endpoint or a change to an existing one?
- Should the response shape match an existing endpoint's pattern?
- Does this change require a new field in the CouchDB document? (If yes, coordinate with `/database` and `/frontend`)
- Does this affect the Telegraf process lifecycle?

### 2. Implement in the Right Layer
Respect the existing service boundaries (`routes.py` → service module):

| You want to … | Edit |
|---|---|
| Add or change an HTTP endpoint | `backend/src/routes.py` |
| Add or change a configuration field | `backend/src/plc_datalink_rfc1006_model.py` |
| Talk to CouchDB | `backend/src/services/couchdb_service.py` |
| Talk to supervisord / start-stop Telegraf | `backend/src/services/telegraf_service.py` |
| Render Telegraf `.conf` files or manage log files | `backend/src/services/machine_configuration_service.py` |
| Change Telegraf launch behavior | `backend/config/dynamic_startup_telegraf.sh` |
| Change supervisord rules | `backend/config/supervisord.conf` |
| Container entrypoint | `backend/config/backend-entrypoint.sh` |

### 3. Follow the Conventions
- Use `logger = logging.getLogger('application_logger')` — do not create a new logger
- For new endpoints, follow the existing response shape: `({"message": ...}, 200)` or `({"error": ...}, status_code)`
- Catch `HTTPError` (from `requests`) separately to preserve CouchDB status codes (404, 409)
- Validate inputs early; return `400` with a specific message
- Use type hints on new functions
- Use dataclasses for new model types (see `PlcDatalinkRFC1006Model`)

### 4. Update the OpenAPI Spec
For ANY route, parameter, or response shape change:
- Update `backend/openapi/plc_datalink_rfc1006_api.yml`
- Keep operation IDs stable (deprecate via `deprecated: true` rather than removing)
- The spec is served at `/swagger` — verify it renders without errors

### 5. Update Static Telegraf Defaults (if applicable)
If `PlcDatalinkRFC1006Model.from_dict` is touched, keep the static defaults aligned with the Telegraf agent settings the container actually consumes (see `agent.flushInterval`, `mqttDataFormat = "json"`, etc.).

### 6. Add / Update curl Tests
- For new endpoints: add a curl script in `backend/test/curl/` mirroring the existing pattern (`config_create.sh`, `machine_start.sh`, …)
- Make scripts idempotent where possible
- Use placeholders for hostnames/ports that match the dev compose stack

### 7. Add / Update pytest Tests
The backend has a pytest suite under `backend/test/scripts/` covering the model, services, and routes:
- New endpoint → add route-level test to `test_routes.py` (Flask test client + service mocks)
- New / changed model field → extend `test_model.py` (roundtrip + defaults)
- Touched CouchDB call → extend `test_couchdb_service.py` (use `requests_mock`)
- Touched supervisord / subprocess call → extend `test_telegraf_service.py` (mock `subprocess.run` / `subprocess.Popen`)
- Touched Telegraf renderer → re-generate the snapshot with `UPDATE_SNAPSHOT=1` (see step 8) and commit `backend/test/scripts/snapshots/sample_machine.conf`

### 8. Run the Backend Tests (Container — MANDATORY)
Tests run **inside the dedicated test container** defined by [`dc-plc-datalink-rfc1006-test.yml`](../../../dc-plc-datalink-rfc1006-test.yml) — never via local `pytest` on the host (no local venv is maintained).

```bash
# build (only after backend/Dockerfile.test, src/, test/, requirements.txt change)
docker compose -f dc-plc-datalink-rfc1006-test.yml build backend-test

# run the full suite
docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm backend-test

# regenerate the Telegraf-render snapshot intentionally
docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm \
  -v "$(pwd)/backend/test/scripts/snapshots:/app/test/scripts/snapshots" \
  -e UPDATE_SNAPSHOT=1 \
  backend-test pytest -q test/scripts/test_machine_configuration_service.py
```

Report the pytest summary in chat (`N passed, M skipped, K failed`). Any failure blocks the handoff — fix or surface before moving on.

#### Cleanup after tests (MANDATORY)
After every test run — full suite, single test, snapshot regeneration, or aborted run — remove all test containers, networks, volumes **and the test image**. Nothing test-related must remain on the host. This applies even if `run --rm` was used: anonymous volumes, the default network, and any leftover `up -d` services persist otherwise.

```bash
# Drop containers, networks, anonymous + named volumes for the test project:
docker compose -f dc-plc-datalink-rfc1006-test.yml down -v --remove-orphans

# Drop ALL tags of the test-specific image (rebuild on next run is intentional):
docker images --filter "reference=plc-datalink-rfc1006-backend-test" --format "{{.Repository}}:{{.Tag}}" \
  | xargs -r docker image rm -f
```

Do **not** remove the shared runtime images `plc-datalink-rfc1006-backend:dev` / `plc-datalink-rfc1006-database:dev` here — those belong to the dev stack.

Verify nothing remains under the test project label:
```bash
docker ps -a    --filter "label=com.docker.compose.project=plc-datalink-rfc1006-test"
docker volume ls --filter "label=com.docker.compose.project=plc-datalink-rfc1006-test"
docker image ls plc-datalink-rfc1006-backend-test
```
All three must come back empty. If the run used `testcontainers`, also check `docker ps -a` for stray `testcontainers/*` or `couchdb:*` containers and remove them — ryuk normally cleans them, but a killed run can leave them behind.

### 8a. Run the Integration Suite (Container — ZKS Machine Mock)
The integration stack lives in [`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml) (project `plc-datalink-rfc1006-e2e`, network `plc-datalink-rfc1006-e2e-net`). It runs the production-image backend + real CouchDB + real Mosquitto and exercises `backend/test/scripts/integration/test_e2e_zks_mqtt.py` against the [ZKS Machine Mock](../../../docs/machines-db-layout/zks-machine-mock/README.md) (external Docker stack). The ZKS S7 mock must be reachable on the host before the runner starts (`nc -zv localhost 102`); specs skip cleanly when it isn't.

**Trigger policy** (per [docs/features/test-strategy/scope.md](../../../docs/features/test-strategy/scope.md), Section 5):
- **MANDATORY** when a requirement scope is fully implemented — all acceptance criteria in `docs/features/<name>/scope.md` ticked — run this as the final gate before handing off to `/06-qa` / `/99-commit`
- **MANDATORY** when changes touch supervisord, Telegraf rendering, PLC address parsing, the MQTT payload shape, or the production Dockerfile (even mid-flight, not just at requirement-complete)
- **OPTIONAL** for internal refactors that don't affect the PLC→MQTT path
- **NEVER** triggered by the PostToolUse hook — the hook handles only the unit suite (Step 8); the integration suite is too slow per-edit

```bash
# Start ZKS mock on the host first (see docs/machines-db-layout/zks-machine-mock/)
docker compose -f dc-plc-datalink-rfc1006-e2e.yml build
docker compose -f dc-plc-datalink-rfc1006-e2e.yml run --rm backend-e2e-runner
```

#### Cleanup after E2E (MANDATORY)
The E2E stack uses `up`-style services (`backend-e2e`, `couchdb-e2e`, `mosquitto-e2e`) that survive `run --rm`. After every E2E run — successful, failed, or aborted — remove everything: containers, the `plc-datalink-rfc1006-e2e-net` network, anonymous volumes **and** the E2E-specific images.

```bash
# Drop containers, network, anonymous + named volumes for the e2e project:
docker compose -f dc-plc-datalink-rfc1006-e2e.yml down -v --remove-orphans

# Drop ALL tags of the E2E-specific images (rebuild on next run is intentional):
docker images --filter "reference=plc-datalink-rfc1006-backend-e2e"  --format "{{.Repository}}:{{.Tag}}" \
  | xargs -r docker image rm -f
docker images --filter "reference=plc-datalink-rfc1006-database-e2e" --format "{{.Repository}}:{{.Tag}}" \
  | xargs -r docker image rm -f

# The runner reuses the backend-test image — drop it too if E2E was the last test run:
docker images --filter "reference=plc-datalink-rfc1006-backend-test"  --format "{{.Repository}}:{{.Tag}}" \
  | xargs -r docker image rm -f
```

Do **not** remove `eclipse-mosquitto:2` (external base image) or the shared runtime images `plc-datalink-rfc1006-backend:dev` / `plc-datalink-rfc1006-database:dev` — those belong elsewhere.

Verify the E2E project leaves nothing behind:
```bash
docker ps -a    --filter "label=com.docker.compose.project=plc-datalink-rfc1006-e2e"
docker volume ls --filter "label=com.docker.compose.project=plc-datalink-rfc1006-e2e"
docker network ls --filter "label=com.docker.compose.project=plc-datalink-rfc1006-e2e"
docker image ls plc-datalink-rfc1006-backend-e2e
docker image ls plc-datalink-rfc1006-database-e2e
```
All five must come back empty.

### 9. Local End-to-End Verification (manual)
- Rebuild the runtime backend image: `docker compose -f dc-plc-datalink-rfc1006-dev.yml build plc-datalink-rfc1006-backend`
- Bring the stack up: `docker compose -f dc-plc-datalink-rfc1006-dev.yml up -d`
- Allow ~20 seconds for the stack to settle
- Exercise the new endpoint with the curl test
- Check `docker logs plc-datalink-rfc1006-backend` for errors

### 10. Documentation
- Update `README.md` if user-visible behavior changes (configuration UI fields, PLC address format, MQTT payload)
- Update the matching frontmatter `paths:` in `.claude/rules/backend.md` if you move or add directories

## Context Recovery
If context was compacted mid-task:
1. Re-read the scope note and the relevant ADR
2. `git diff` to see what's already changed
3. Read `backend/src/routes.py` and the touched service module
4. Continue — do not duplicate already-written code

## Checklist
See [checklist.md](checklist.md) for the full backend implementation checklist.

## Handoff
> "Backend change done. Next step:
> - Run `/frontend` if the UI needs to consume the new API
> - Run `/database` if a CouchDB schema/config change is also needed
> - Otherwise run `/qa` to validate end-to-end"

**Before any handoff that closes out a requirement** (all acceptance criteria ticked in `docs/features/<name>/scope.md`): run Step 8a (ZKS integration) and report its result in chat. Do not hand off with an unrun integration suite when the scope is complete.

## Suggested Git Commit
```
feat(backend): <one-line description>
fix(backend): <one-line description>
refactor(backend): <one-line description>
```
Reference scope note path in commit body if applicable.
