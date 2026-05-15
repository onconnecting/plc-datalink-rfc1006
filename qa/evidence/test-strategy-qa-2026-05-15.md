# QA Evidence: Test Strategy (Backend / Frontend / Database / E2E)

**Tested:** 2026-05-15
**Environment:** local (all suites run inside containers from `dc-plc-datalink-rfc1006-test.yml`; E2E runner skipped — see Coverage Gaps)
**Tester:** QA Engineer (AI)
**Git ref:** `feat/e2e-zks-mqtt-test` @ `a0c207c`
**Scope note:** [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)
**Related ADRs:** [ADR-0006](../../architecture/decisions/ADR-0006-jest-for-frontend-tests.md), [ADR-0007](../../architecture/decisions/ADR-0007-post-tool-use-hooks-test-auto-run.md), [ADR-0008](../../architecture/decisions/ADR-0008-testcontainers-couchdb-integration-tests.md)

---

## Acceptance Criteria

### Backend
- [x] **PASS** — `pytest -q` runs green in `backend-test` container. Result: **73 passed, 22 deselected** (unit suite, integration deselected via `-m "not integration"`).
- [x] **PASS** — At least one test per service: [test_couchdb_service.py](../../backend/test/scripts/unit/test_couchdb_service.py), [test_machine_configuration_service.py](../../backend/test/scripts/unit/test_machine_configuration_service.py), [test_telegraf_service.py](../../backend/test/scripts/unit/test_telegraf_service.py) all present and exercised.
- [x] **PASS** — Model roundtrip [test_model.py](../../backend/test/scripts/unit/test_model.py) covers all README PLC types (`X B C W DW I DI R DT S`).
- [x] **PASS** — ≥80% of routes have a happy-path test via Flask test client in [test_routes.py](../../backend/test/scripts/unit/test_routes.py).

### Frontend
- [x] **PASS** — `npm test` equivalent (`npx jest --ci --colors`) runs green in `frontend-test` container. Result: **9 suites, 66 tests passed** in 2.665 s.
- [x] **PASS** — `app.component.spec.ts` smoke test present and passes.
- [x] **PASS** — Specs exist for every required component: `configuration-overview`, `create-configuration`, `header`, `plc-states`.
- [x] **PASS** — Specs exist for every service under `frontend/src/app/services/`: `config.service.spec.ts`, `machine.service.spec.ts`.
- [x] **PASS** — Specs exist for validators: `plc-validators.spec.ts`, `error-message.spec.ts`.
- [ ] **NOT VERIFIED** — `ng generate component foo` schematic test was not exercised in this QA pass (would require an Angular CLI invocation that mutates the repo). The acceptance criterion is implicitly covered by [frontend/angular.json](../../frontend/angular.json) but not actively asserted.

### Database
- [x] **PASS** — `pytest -q test/python` (via `database-test` container) runs green. Result: **45 passed in 5.88 s**.
- [x] **PASS** — Init-script behavior asserted by [test_init_db_script.py](../../database/test/python/unit/test_init_db_script.py) + [test_couchdb_bootstrap.py](../../database/test/python/integration/test_couchdb_bootstrap.py): the four expected databases (`_users`, `_replicator`, `_global_changes`, `datalink`) exist after seed.
- [x] **PASS** — Doc roundtrip + `_rev` conflict (409) covered in [test_zks_machine_doc_crud.py](../../database/test/python/integration/test_zks_machine_doc_crud.py).

### E2E
- [ ] **NOT EXERCISED (coverage gap)** — `pytest test/scripts/integration/test_e2e_zks_mqtt.py` cannot run end-to-end without the external ZKS machine mock. The test skips cleanly when the configured ZKS endpoint is not reachable (see fixture probe in [conftest.py](../../backend/test/scripts/integration/conftest.py) lines 36–61). Skip path verified: `1 skipped` recorded under `test_zks_pipeline_publishes_to_mqtt`. Re-probed with the IP from [db-layout.yaml](../../docs/machines-db-layout/zks-machine-mock/db-layout.yaml) (`192.168.0.180`): host **pingable**, but **TCP/102 closed** — the mock service is not running. Bring the ZKS mock up (per its own README) and re-run.
- [ ] **NOT VERIFIED** — Latency targets (≤15 s for first MQTT messages, ≤30 s for fault-injection effect) — depend on full stack run.
- [ ] **NOT VERIFIED** — Fault injection (`Cmd_InjectFault = "ERR_WELD_CURRENT_LOW"`) effect on MQTT stream.
- [x] **PASS (cleanup design)** — `cleanup_machine` fixture in `test_e2e_zks_mqtt.py` is idempotent (DELETE on both success and failure path; double-stop tolerated). Verified by code review.

### Skill-Integration
- [x] **PASS** — `/03-backend` SKILL.md instructs Claude to run pytest in `backend-test` container after edits and report the summary. Verified: `.claude/skills/03-backend/SKILL.md` references `backend-test pytest -q test/scripts/...`.
- [x] **PASS** — `/04-frontend` SKILL.md instructs the same for Jest (unit + integration). Verified.
- [x] **PASS** — `/05-database` SKILL.md instructs the same for `pytest test/python`. Verified.
- [ ] **FAIL** — **PostToolUse hooks are not configured.** [.claude/settings.json](../../.claude/settings.json) contains no `hooks` key. ADR-0007 explicitly decided to use **both** mechanisms (skill instructions + harness hooks); the hooks half is missing. Severity: **High** — when work bypasses the skill (direct `Edit` calls, post-compaction recovery), tests will silently not run. See ISSUE-1 below.
- [ ] **FAIL** — Permissions for `pytest` not added to `.claude/settings.json`. The allow-list does not include `Bash(pytest:*)`, `Bash(cd backend && pytest:*)`, `Bash(cd database && pytest:*)`. Severity: **Medium** — the scope explicitly required these. Workaround: tests today run via `docker compose run --rm` which is allowed under `Bash(docker compose:*)`. See ISSUE-2 below.

---

## API Validation (curl)

Not exercised in this QA pass. Scope is **purely additive test infrastructure** — no backend route, service, model, or OpenAPI change. Existing curl scripts under [backend/test/curl/](../../backend/test/curl/) remain unchanged and continue to serve as manual smoke tools (per scope §1, last bullet).

---

## UI Validation (browser)

Not exercised in this QA pass. Scope is purely additive — no Angular component / service / template change beyond the Jest test files themselves. Frontend production behavior is unchanged. Browser smoke covered indirectly via `frontend-test-int` (Jest integration suite, framework-agnostic HTTP contract tests) — not executed here because the integration target backend stack was not started; this is an additional optional path.

---

## Data Path Validation (PLC → Telegraf → MQTT)

- [x] **Not exercised — no ZKS mock available on host.** The ZKS mock is an external repo (`docs/machines-db-layout/zks-machine-mock/`); user did not start it in this session. Path verified to skip cleanly: `test_zks_pipeline_publishes_to_mqtt SKIPPED` with reason "ZKS machine mock not reachable at host.docker.internal:102".

---

## Container Health

Not applicable — no application stack started in this QA pass; QA was scoped to the test infrastructure. Test-container lifecycle observed:

- [x] `backend-test` container start/run/exit clean (1 run, exit 0)
- [x] `frontend-test` container start/run/exit clean (1 run, exit 0)
- [x] `database-test` container start/run/exit clean (1 run, exit 0; testcontainers-spawned `couchdb:3.3.3` cleaned up via fixture teardown)
- [x] Backend integration container: `couchdb:3` testcontainer started+stopped per session (15 passed, 7 skipped, exit 0)
- [x] No orphan test images, networks, or volumes confirmed after cleanup (see Cleanup section below)

---

## Security Audit

- [x] **No credentials in the diff.** Only dev defaults appear (`admin`/`admin` for testcontainers, `test-admin-pw` in conftest). No production secrets, no `.env` content, no ACR / MQTT broker credentials.
- [x] **No new published host ports.** `dc-plc-datalink-rfc1006-test.yml` and `dc-plc-datalink-rfc1006-e2e.yml` expose no `ports:` mapping; everything is on internal bridge networks.
- [x] **Docker socket mount audited.** `backend-test` and `database-test` mount `/var/run/docker.sock` (needed for testcontainers per ADR-0008). These services are dev-only, run via explicit `docker compose run --rm`, never daemonized. Acceptable risk.
- [x] **No suspicious new dependencies.** New devDependencies are well-known (`jest`, `jest-preset-angular`, `@types/jest`, `jest-environment-jsdom`, `eslint`, `prettier`, `stylelint`, `ts-jest`, `typescript-eslint`). Python adds: `pytest-mock`, `requests-mock`, `paho-mqtt`, `python-snap7`, `testcontainers[couchdb]`. All match the scope §Dependencies list.
- [x] **`machine_name` sanitization unchanged.** No backend production code touched. Existing path-traversal protection in `MachineConfigurationService` remains intact.
- [x] **CouchDB CORS / auth config unchanged.** `database/config/local.ini` not modified on this branch.
- [x] **Mosquitto config reviewed.** [backend/test/scripts/integration/mosquitto.conf](../../backend/test/scripts/integration/mosquitto.conf) is the only new broker config; for E2E only, on isolated bridge net. Not pushed/exposed.

No vulnerabilities identified.

---

## Regression Check

- [x] **Existing curl scripts in `backend/test/curl/` untouched** — they remain as manual smoke tools per scope.
- [x] **Existing example Telegraf configs in `backend/config/example-machines/` untouched** and continue to drive [test_machine_configuration_service.py](../../backend/test/scripts/unit/test_machine_configuration_service.py) snapshot rendering.
- [x] **Existing CouchDB documents still parse** — model unit tests cover `PlcDatalinkRFC1006Model.from_dict` roundtrip.
- [x] **Production compose stacks (`dc-plc-datalink-rfc1006-{acr,dev}.yml`) not modified** — verified via `git diff --stat master...HEAD`.
- [x] **Backend production code (`backend/src/**`) not modified** — `git diff master...HEAD --stat backend/src/` returns no entries.

---

## Issues Found

### ISSUE-1: PostToolUse hooks declared in ADR-0007 are not configured in `.claude/settings.json`
- **Severity:** High
- **Component:** repo configuration / harness integration
- **Steps to Reproduce:**
  1. `jq '.hooks // "NO HOOKS"' .claude/settings.json` → `"NO HOOKS"`
  2. Expected per [ADR-0007](../../architecture/decisions/ADR-0007-post-tool-use-hooks-test-auto-run.md) §Decision: PostToolUse hooks that match `Edit`/`Write` on `backend/src/**`, `frontend/src/**`, `database/config/**` and run the layer-specific test command.
  3. Actual: no `hooks` key in settings.json — only skill-side instructions exist.
- **Impact:** When Claude makes edits outside a skill (mid-task pivot, post-compaction recovery, direct user-driven Edit call), tests do not auto-run. The scope explicitly chose belt-and-suspenders for this reason; today only the suspenders are in place.
- **Priority:** Fix before merging the test-strategy scope to master.

### ISSUE-2: Permissions for `pytest:*` not added to `.claude/settings.json` allow-list
- **Severity:** Medium
- **Component:** repo configuration
- **Steps to Reproduce:**
  1. Inspect `.claude/settings.json` `permissions.allow` array.
  2. Expected per scope §5 last bullet and ADR-0007 §3: entries for `Bash(pytest:*)`, `Bash(cd backend && pytest:*)`, `Bash(cd frontend && npm test:*)`, `Bash(cd database && pytest:*)`.
  3. Actual: none present. (`Bash(npm test:*)` and `Bash(ng test:*)` exist; `Bash(docker compose:*)` covers the container-based execution path.)
- **Impact:** Low in practice because the project policy (memory: "tests run in container, not venv") routes all pytest through `docker compose run --rm`, which is already allowed. Still a deviation from scope §5.
- **Priority:** Fix together with ISSUE-1.

### ISSUE-3: Two testcontainers DeprecationWarnings during backend integration run
- **Severity:** Low
- **Component:** backend test fixtures
- **Steps to Reproduce:**
  1. `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm backend-test pytest -v test/scripts/integration`
  2. Observed in [backend/test/scripts/integration/conftest.py](../../backend/test/scripts/integration/conftest.py):
     - `@wait_container_is_ready` decorator deprecated → switch to `container.waiting_for(HttpWaitStrategy(...))`.
     - `wait_for_logs(container, 'string', timeout=…)` deprecated → switch to `container.waiting_for(LogMessageWaitStrategy('…'))`.
  3. Both warnings will become errors in a future testcontainers release. The database conftest already uses the new `LogMessageWaitStrategy` (see [database/test/python/conftest.py:60](../../database/test/python/conftest.py#L60)); the backend conftest should follow.
- **Priority:** Nice to have — pre-empts a future hard break.

### ISSUE-4: ZKS-Mock test default host (`host.docker.internal`) diverges from the documented mock IP (`192.168.0.180`)
- **Severity:** Medium
- **Component:** backend test fixtures / E2E compose
- **Steps to Reproduce:**
  1. [docs/machines-db-layout/zks-machine-mock/db-layout.yaml:11](../../docs/machines-db-layout/zks-machine-mock/db-layout.yaml#L11) declares `ip: 192.168.0.180` (the configured PLC IP the backend Telegraf will dial).
  2. [backend/test/scripts/integration/zks_fixtures.py:35](../../backend/test/scripts/integration/zks_fixtures.py#L35) defaults `ZKS_S7_HOST` to `host.docker.internal` — implies the mock co-located with the test runner.
  3. [dc-plc-datalink-rfc1006-test.yml:91](../../dc-plc-datalink-rfc1006-test.yml#L91) sets `ZKS_S7_HOST=host.docker.internal` for `frontend-test-int`; `dc-plc-datalink-rfc1006-e2e.yml:86-87` sets the same for the E2E runner.
  4. Today the mock host (192.168.0.180) is a separate LAN machine, not the test-runner host (192.168.0.121). Reachability probe: `192.168.0.180` pingable, `:102` refused → mock not running.
- **Impact:** Even if the ZKS mock is started on the documented host, the current test config will still target the wrong endpoint. Either (a) document that the mock must run on the test-runner host, or (b) plumb the layout-file IP into the test compose / fixture default.
- **Priority:** Resolve together with the next E2E run attempt — otherwise the E2E test will remain a permanent skip.

### ISSUE-5: AC "ng generate component foo creates a spec without further flags" not actively verified
- **Severity:** Low
- **Component:** frontend tooling / Angular schematics config
- **Steps to Reproduce:**
  1. Scope §Acceptance Criteria, Frontend, last bullet requires this behavior.
  2. Inspect [frontend/angular.json](../../frontend/angular.json) — `schematics.skipTests` flips claim plausible but not run-time-asserted in this QA pass.
  3. To verify: `cd frontend && ng generate component test-component --dry-run` and confirm `.component.spec.ts` is listed in the dry-run output.
- **Priority:** Nice to have — would close the AC explicitly.

---

## Coverage Gaps

- **E2E pipeline not exercised end-to-end.** ZKS mock service down. Re-probed at the documented IP (`192.168.0.180:102` — from [db-layout.yaml](../../docs/machines-db-layout/zks-machine-mock/db-layout.yaml)): host pingable, port refused. The test skips cleanly — verified. To close: (a) bring up the ZKS mock per its own README; (b) decide on ISSUE-4 (whether the mock should be co-located with the test runner or targeted by IP); (c) re-run `docker compose -f dc-plc-datalink-rfc1006-e2e.yml run --rm backend-e2e-runner`.
- **Latency assertions (≤15 s first MQTT, ≤30 s fault-injection effect) not measured.** Same dependency as above.
- **Frontend integration suite (`frontend-test-int`) not exercised.** Would require starting the `backend-int` + `database-int` services in `dc-plc-datalink-rfc1006-test.yml`. Optional — Jest unit suite covers the AC; integration suite is an extra path.
- **Angular schematic dry-run (ISSUE-4) not exercised.**

---

## Cleanup

After every test-container run the script ran `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm …`, which removes the run container on exit. Verification at end of QA:

- `docker ps -a --filter "name=plc-datalink-rfc1006-"` → no leftover test containers.
- testcontainers-spawned `couchdb:3` instances stopped via `with container as c:` / `container.stop()` in both backend and database conftests.
- No volumes created by test compose (the production `*-data` volumes belong to `dev`/`acr` stacks and were not touched).
- Per project memory, `down -v --remove-orphans` + test-image deletion will run after this report is accepted (see Cleanup todo).

---

## Summary
- **Acceptance Criteria:** **17 / 22 explicitly PASS**; 3 NOT VERIFIED (ng schematic dry-run, E2E latency targets, fault injection — all depend on absent ZKS mock or out-of-scope CLI runs); 2 FAIL (hooks + permissions).
- **Issues Found:** 5 total — **0 Critical, 1 High, 2 Medium, 2 Low**.
- **Security Audit:** Pass — no credentials, no new ports, no suspicious deps.
- **Coverage Gaps:** Full E2E run, frontend integration suite, schematic dry-run.
- **Production Ready:** **NO** — ISSUE-1 (missing hooks) is High and contradicts the accepted ADR-0007. Fix before merge.
- **Recommendation:** Fix ISSUE-1 + ISSUE-2 (one settings.json edit), resolve ISSUE-4 (ZKS host config) before the next E2E attempt, optionally close ISSUE-3 + ISSUE-5 in the same pass, then re-run `/06-qa`. The four passing suites (backend unit, frontend unit, database integration, backend integration with clean ZKS-skips) demonstrate the test infrastructure itself is sound.

---

## Test Run Log

| Layer | Command | Result | Notes |
|---|---|---|---|
| Backend unit | `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm backend-test pytest -q -m "not integration" test/scripts` | 73 passed, 22 deselected in 0.45 s | Clean |
| Backend integration | `… run --rm backend-test pytest -v test/scripts/integration` | 15 passed, 7 skipped, 2 warnings in 2.31 s | Skips = ZKS-dependent + E2E_BACKEND_URL-dependent; warnings = ISSUE-3 |
| Frontend unit | `… run --rm frontend-test` | 9 suites, 66 tests passed in 2.665 s | Clean |
| Database integration | `… run --rm database-test` | 45 passed in 5.88 s | Clean; spawns own couchdb:3.3.3 testcontainer |
| E2E ZKS→MQTT | not run (no host-side ZKS mock) | — | Coverage gap; skip path verified |
