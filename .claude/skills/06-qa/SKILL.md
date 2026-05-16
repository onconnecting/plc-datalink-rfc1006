---
name: qa
description: Validate PLC Datalink RFC1006 changes end-to-end — API via curl, UI in a browser, container logs, and the PLC→Telegraf→MQTT data path. Find and document issues; do not fix them in this skill.
argument-hint: "feature name or component to validate"
user-invocable: true
---

# QA Engineer

## Role
You validate implementation against the scope's acceptance criteria, exercise the REST API, the Angular UI, and (where possible) the PLC→Telegraf→MQTT data path. You document findings; you never fix bugs in this skill.

## Before Starting
1. Read the scope note: `docs/features/<feature-name>/scope.md` (if it exists)
2. Read related ADRs: `ls architecture/decisions/`
3. Check what changed: `git log --oneline -5` and `git diff master...HEAD`
4. Check prior QA evidence: `ls qa/evidence/ 2>/dev/null`
5. Ensure the local stack is up: `docker ps | grep plc-datalink-rfc1006`

If the stack isn't up:
- `docker-compose -f dc-plc-datalink-rfc1006-local.yml up -d`
- Wait ~20 seconds for the stack to settle

## Workflow

### 1. Re-read Acceptance Criteria
List every acceptance criterion from the scope note. Each will be marked **PASS** or **FAIL** in the evidence.

### 2. Validate the REST API
Use the curl scripts in `backend/test/` as a starting point. For each changed or new endpoint:

- **Happy path:** valid request → expected 2xx, expected response shape
- **Missing required field:** → `400` with a useful error message
- **Resource not found:** → `404`
- **Conflict** (e.g. duplicate machine name, machine currently running): → `409`
- **OpenAPI alignment:** response matches `backend/openapi/plc_datalink_rfc1006_api.yml`

For configuration endpoints, verify the CouchDB document was created/updated correctly:
- `curl -u admin:password http://localhost:5984/<db>/<machineName>` (dev only — port 5984 is mapped in the local compose stack)

### 3. Validate the Angular UI
Open `http://localhost` in a Chromium-based browser (matches the README Prerequisites).

- **Create Configuration** screen: enter a valid config and submit → it appears in Configuration Overview
- **Configuration Overview** screen: Start, Edit, Remove buttons behave per README (Remove fails with a clear message if the machine is running)
- **PLC States** screen: Start a configured machine → state moves to `Connected`; Stop → `Disconnected`
- **Validation:** invalid IPv4, invalid port, invalid PLC address, missing required fields → friendly error
- **Devtools console:** no runtime errors

### 4. Run the ZKS Integration Test (mandatory when scope touches PLC / MQTT / Telegraf / schema)
The canonical end-to-end check lives in [`backend/test/scripts/integration/test_e2e_zks_mqtt.py`](../../../backend/test/scripts/integration/test_e2e_zks_mqtt.py) and runs against the [ZKS Machine Mock](../../../docs/machines-db-layout/zks-machine-mock/README.md) (external Docker stack) via [`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml). Per [docs/features/test-strategy/scope.md](../../../docs/features/test-strategy/scope.md), Section 5, this is mandatory whenever the closed-out scope touches the backend, the schema, the PLC address parser, the Telegraf rendering, or the MQTT payload.

**Preconditions:**
1. ZKS Machine Mock running on the host (from its own repo: `make up`); verify `nc -zv localhost 102` succeeds
2. No leftover containers / images from a previous test or e2e run (cleanup procedure in [/03-backend SKILL.md §8a cleanup](../03-backend/SKILL.md))

**Run:**
```bash
docker compose -f dc-plc-datalink-rfc1006-e2e.yml build
docker compose -f dc-plc-datalink-rfc1006-e2e.yml run --rm backend-e2e-runner
```

**Assertions to confirm in the test output** (per scope acceptance criteria):
- MQTT messages per defined tag within ≤ 15 s
- `Cmd_Start` makes `PartCounter` (DB1 DINT@4) increment via MQTT
- `ERR_WELD_CURRENT_LOW` injection shows effect in MQTT stream within ≤ 30 s
- `ERR_ROBOT_FAULT` switches `Machine.State` (DB1 INT@0) to `3` (ERROR)
- ZKS-Mock unreachable → `pytest.skip(...)`, not a fail
- Cleanup is idempotent on success AND failure

**Mandatory cleanup** after the run — follow the E2E cleanup procedure in [/03-backend SKILL.md §8a](../03-backend/SKILL.md). Nothing test-related stays on the host.

If the scope is purely UI cosmetic and doesn't touch the PLC path: this test is **optional**, but document in the evidence why it was skipped.

### 5. Check Container Health
- `docker ps` — all three containers `running`
- `docker logs plc-datalink-rfc1006-backend` — no unhandled exceptions
- `docker logs plc-datalink-rfc1006-database` — no auth or compaction errors
- `docker logs plc-datalink-rfc1006-frontend` — no nginx upstream errors
- For each started machine, supervisord shows a Telegraf process running: exec into the backend container if needed (`docker exec -it plc-datalink-rfc1006-backend supervisorctl status`)

### 6. Security Audit (lightweight)
Think like an attacker:
- Are any credentials hardcoded in commits? (CouchDB admin pw, ACR creds, MQTT creds)
- Is the backend validating `machine_name` to prevent path traversal into `/etc/telegraf`?
- Are any new published ports introduced that shouldn't be exposed?
- Does the OpenAPI spec leak sensitive details?
- Did any frontend dependency bump add suspicious packages? (`git diff frontend/package.json frontend/package-lock.json`)

### 7. Regression Check
- Existing endpoints in `backend/test/` still pass
- Existing UI flows (create / edit / remove / start / stop) still work
- Existing example Telegraf configs still load (`backend/config/example-machines/`)
- Existing CouchDB documents still parse via `PlcDatalinkRFC1006Model.from_dict`

### 8. Document Results
Create `qa/evidence/<feature-name>-qa-<YYYY-MM-DD>.md` from [test-template.md](test-template.md).

Each finding: severity, component, steps to reproduce, expected vs. actual.

### 9. Present Results
Summarize for the user:
- Acceptance criteria: **X / Y passed**
- Issues found by severity (Critical / High / Medium / Low)
- Coverage gaps (e.g. "MQTT data path not exercised — no broker available")
- **Production-ready: YES / NO**

Ask: "Which issues should be fixed before release?"

## Issue Severity Levels
- **Critical:** Security vulnerability, data loss, complete API or UI failure, container won't start
- **High:** Core flow broken (cannot create machine, cannot start data collection), regression on existing endpoint
- **Medium:** Validation gap, misleading error message, UI cosmetic issue that blocks usage
- **Low:** Typos, minor UI polish, docs gaps

## Important
- NEVER fix bugs in this skill — only find, document, and prioritize
- Test both happy and failure paths for every changed component
- Document every finding, even minor ones

## Production-Ready Decision
- **READY:** No Critical or High issues remaining
- **NOT READY:** Critical or High issues exist — must be resolved first

## Handoff
If READY:
> "QA passed. Next step: Run `/deploy` to build / push images and deploy."

If NOT READY:
> "Found [N] issues ([severity breakdown]). Fix these (run `/backend`, `/frontend`, or `/database` as needed), then run `/qa` again."

## Suggested Git Commit
```
test(qa): add QA evidence for <feature-name>
```
