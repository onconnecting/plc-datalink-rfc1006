---
name: frontend
description: Implement Angular frontend changes for the PLC Datalink RFC1006 project — components, services, models, modals, and nginx config. The UI configures machines, manages configurations, and shows live PLC states.
argument-hint: "scope note path, component name, or short description"
user-invocable: true
---

# Frontend Engineer (Angular)

## Role
You implement frontend changes for the PLC Datalink RFC1006 platform. The frontend is an Angular SPA served by nginx on port 80, talking to the Flask backend over relative HTTP paths.

## Before Starting
1. Read the relevant scope note in `docs/features/<feature-name>/scope.md` if it exists
2. Read related ADRs in `architecture/decisions/` if relevant
3. Read [.claude/rules/frontend.md](../../../.claude/rules/frontend.md) for frontend conventions
4. Check current state:
   - `frontend/src/app/` — component directories (`create-configuration/`, `configuration-overview/`, `plc-states/`, `header/`, `modals/`)
   - `frontend/src/app/services/` — HTTP clients
   - `frontend/src/app/models/` — TypeScript interfaces mirroring the backend JSON
   - `frontend/package.json` — current Angular and library versions
5. If the change consumes a new backend endpoint, verify it exists in `backend/openapi/plc_datalink_rfc1006_api.yml`

## Workflow

### 1. Confirm the Change
Use `AskUserQuestion` only for genuinely ambiguous points:
- Which existing screen does this extend, or is it a new screen?
- Does an existing service / model fit, or is a new one needed?
- Are there specific validation rules (PLC address format, IPv4, port ranges)?
- Should a modal confirmation be required before destructive actions?

### 2. Implement in the Right Layer

| You want to … | Edit |
|---|---|
| Build/modify a screen | `frontend/src/app/<area>/` (`create-configuration`, `configuration-overview`, `plc-states`, `header`) |
| Reusable dialog | `frontend/src/app/modals/` |
| Call the backend | `frontend/src/app/services/` |
| Define a TypeScript shape mirroring backend JSON | `frontend/src/app/models/` |
| Register a new module-level component / service | `frontend/src/app/app.module.ts` |
| nginx routing / API proxying | `frontend/config/nginx-custom.conf` |
| nginx global config | `frontend/config/nginx-main.conf` |

### 3. Follow the Conventions
- One feature directory per top-level UI area (matches the existing tree)
- Each component directory has its own `.ts`, `.html`, `.css`
- Specs live under `frontend/test/unit/` (mocked, fast) and `frontend/test/integration/` (real HTTP) — **not** co-located next to source. See §7 below for which kind goes where
- Templates stay declarative — push state and side effects into the component class or a service
- Services use `HttpClient` and return `Observable<T>` typed against `models/`
- Use **relative URLs** for backend calls (`/config/read/all`, `/machine/start`) — nginx serves the bundle on the same origin
- Field names in TypeScript models match the backend exactly (camelCase: `machineName`, `plcIp`, `mqttTopic`, `tagAddress`, …)

### 4. Input Validation
For PLC inputs, validate on the form (client-side) and rely on the backend for authoritative checks:
- IPv4 format on `PLC IP Address` and `MQTT Server`
- Port range on `PLC Port` (default 102) and `MQTT Port` (default 1883)
- PLC address: `<area>.<type><address>[.extra]` (see README and `.claude/rules/telegraf.md`)
- Batch-request size > 0

### 5. Coordinate with Other Layers
If the change touches the backend or schema:
- Confirm the corresponding backend change exists (run `/backend` first if needed)
- If the CouchDB document shape changed, ensure existing documents still parse — coordinate with `/database`

### 6. Local Verification
- Rebuild the frontend image: `docker compose -f dc-plc-datalink-rfc1006-dev.yml build plc-datalink-rfc1006-frontend`
- Bring the stack up: `docker compose -f dc-plc-datalink-rfc1006-dev.yml up -d`
- Open `http://localhost` in a Chromium-based browser (matches the README Prerequisites)
- Exercise the changed screen end-to-end: golden path AND at least one failure path (invalid input, machine running when trying to remove, etc.)
- Check the browser devtools console for runtime errors

### 7. Run the Frontend Test Suite (mandatory after edits)
Tests run in a dedicated container, NEVER on the host. The test image bakes in Jest + dependencies; sources are mounted read-only at runtime so re-runs pick up edits without rebuilding.

Two flavours, split by purpose:

| Kind | Location | What it tests | Dependencies |
|---|---|---|---|
| **Unit** | `frontend/test/unit/**/*.spec.ts` | Components, services, validators in isolation (mocked HttpClient, mocked services) | None — pure Jest |
| **Integration** | `frontend/test/integration/**/*.int.spec.ts` | Real HTTP against the Flask backend (+ optional ZKS-Mock for live PLC) | `backend-int`, `database-int`, optionally external ZKS-Mock |

**Always required after any edit:**
```bash
# One-time / after Dockerfile.test or package.json changes:
docker compose -f dc-plc-datalink-rfc1006-test.yml build frontend-test

# Per test cycle:
docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm frontend-test
```

**Required after any change to a service, model, or anything that touches the backend contract:**
```bash
# Bring up real backend + CouchDB:
docker compose -f dc-plc-datalink-rfc1006-test.yml up -d database-int backend-int
# Wait ~20 s for backend to settle, then:
docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm frontend-test-int
```

#### Cleanup after tests (MANDATORY)
After every test run — unit, integration, or aborted — remove all test containers, networks, volumes **and the test image**. Nothing test-related must remain on the host. The unit flow uses only `run --rm`, but `up -d database-int backend-int` for integration leaves containers, a network and named volumes behind unless explicitly dropped.

```bash
# Drop containers, networks, anonymous + named volumes for the test project:
docker compose -f dc-plc-datalink-rfc1006-test.yml down -v --remove-orphans

# Drop ALL tags of the test-specific image (rebuild on next run is intentional):
docker images --filter "reference=plc-datalink-rfc1006-frontend-test" --format "{{.Repository}}:{{.Tag}}" \
  | xargs -r docker image rm -f
```

Do **not** remove the shared runtime images `plc-datalink-rfc1006-backend:dev` / `plc-datalink-rfc1006-database:dev` here — `backend-int` / `database-int` reuse the dev images and the dev stack still needs them.

Verify nothing remains under the test project label:
```bash
docker ps -a    --filter "label=com.docker.compose.project=plc-datalink-rfc1006-test"
docker volume ls --filter "label=com.docker.compose.project=plc-datalink-rfc1006-test"
docker image ls plc-datalink-rfc1006-frontend-test
```
All three must come back empty.

**Optional — full PLC path with live S7 data via ZKS-Mock:**
The ZKS reference machine ([docs/machines-db-layout/zks-machine-mock/README.md](../../../docs/machines-db-layout/zks-machine-mock/README.md)) is an external Docker stack — bring it up from its own repo with `make up`. Integration specs auto-skip the ZKS path when its S7 port is unreachable; bringing it up makes the `start against the ZKS-Mock` test actually run.

Report both Jest summaries (unit + integration: suites, tests, time) in the chat before marking the task done.

### 7a. Integration Test against ZKS — when a requirement is fully implemented
**Policy** (per [docs/features/test-strategy/scope.md](../../../docs/features/test-strategy/scope.md), Section 5): once all acceptance criteria in `docs/features/<name>/scope.md` are ticked, the full backend integration suite against the ZKS Machine Mock must run before handoff to `/06-qa` or `/99-commit`. Frontend changes alone don't exercise the PLC→MQTT path, but the integration test catches schema/contract drift that pure frontend specs miss.

Delegate to `/06-qa` for the actual run — it owns the ZKS-Mock preconditions and the cleanup procedure. Do not skip this when the scope is complete.

Where to put new specs:
- New component / service / validator with **isolated logic** → unit spec under `frontend/test/unit/`
- New service method or change to an endpoint contract → also add an integration spec under `frontend/test/integration/` named `*.int.spec.ts`
- `angular.json` has `skipTests: false`, but the generated spec goes co-located by default — move it into `frontend/test/unit/` and fix the import paths to `../../src/app/...`

### 8. Documentation
- Update `README.md` if user-visible behavior changes (new field, new button, changed UI flow)
- If a screenshot in `images/` is now stale, note it in the commit body so the user can refresh it

## Context Recovery
If context was compacted mid-task:
1. Re-read the scope note and any related ADR
2. `git diff` to see what's already changed
3. Read the touched component's `.ts`, `.html`, and the service it depends on
4. Continue — do not duplicate already-written code

## Checklist
See [checklist.md](checklist.md) for the full frontend implementation checklist.

## Handoff
> "Frontend change done. Next step:
> - Run `/qa` to validate end-to-end (UI → backend → CouchDB / Telegraf → MQTT)
> - Or run `/commit` if QA already passed"

## Suggested Git Commit
```
feat(frontend): <one-line description>
fix(frontend): <one-line description>
refactor(frontend): <one-line description>
```
