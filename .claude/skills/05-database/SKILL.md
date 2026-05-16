---
name: database
description: Change CouchDB configuration, init scripts, or document schema for the PLC Datalink RFC1006 project. Coordinate schema changes with the backend model and the frontend TypeScript model.
argument-hint: "scope note path, schema field, or short description"
user-invocable: true
---

# Database Engineer (CouchDB)

## Role
You change CouchDB configuration or the machine-configuration document schema. CouchDB holds one document per machine, keyed by `machineName`, with the full PLC + MQTT + Telegraf agent settings.

## Before Starting
1. Read the relevant scope note in `docs/features/<feature-name>/scope.md` if it exists
2. Read related ADRs in `architecture/decisions/` if relevant
3. Read [.claude/rules/database.md](../../../.claude/rules/database.md) for CouchDB conventions
4. Check current state:
   - `database/config/local.ini` — CouchDB tuning
   - `database/config/init-db.sh` — DB bootstrap
   - `database/config/database-entrypoint.sh` — container entry
   - `backend/src/plc_datalink_rfc1006_model.py` — current document shape
   - `backend/src/services/couchdb_service.py` — CRUD logic
   - `frontend/src/app/models/` — TypeScript interfaces

## Workflow

### 1. Confirm the Change
Use `AskUserQuestion` for ambiguous points:
- Is this a schema change (document shape) or a config change (CouchDB itself)?
- For schema: is the new field required or optional? What's the default for existing docs?
- For config: does this affect network exposure, auth, or resource limits?
- Are there existing documents that need a migration?

### 2. Implement in the Right Layer

| You want to … | Edit |
|---|---|
| Add / rename / remove a document field | `backend/src/plc_datalink_rfc1006_model.py` (and coordinate with frontend) |
| Change the bootstrap behavior (new DB, design doc) | `database/config/init-db.sh` |
| Change CouchDB tuning (heap, query timeout, log level) | `database/config/local.ini` |
| Change container entrypoint | `database/config/database-entrypoint.sh` |
| Change image base / packaging | `database/Dockerfile` |

### 3. Schema Change Coordination
**Adding an optional field** (backward-compatible):
- Update `PlcDatalinkRFC1006Model` (backend) to parse the new field with a static default
- Update the matching TypeScript interface in `frontend/src/app/models/`
- Update the OpenAPI spec
- Existing documents work without migration

**Renaming or removing a field** (breaking):
- Requires an ADR explaining the migration plan
- Write a migration script in `database/` (idempotent: read all docs, transform, update with `_rev`)
- Coordinate the backend, frontend, and migration script in a single commit (or staged commits) to minimize broken-state windows
- Document the migration in `CHANGELOG.md`

### 4. Configuration Changes
- Test `local.ini` changes by rebuilding only the database image and verifying the container starts cleanly
- Never change admin credentials in the compose files without coordinating env vars consumed by `couchdb_service.py` (see `backend/config/env`)
- Resource limit / timeout changes require an ADR

### 5. Run the Database Tests (Container — MANDATORY)
Database tests live under `database/test/python/` and run **inside the dedicated test container** defined by [`dc-plc-datalink-rfc1006-test.yml`](../../../dc-plc-datalink-rfc1006-test.yml). The `database-test` service uses `testcontainers[couchdb]` to spawn a fresh CouchDB per session via the host Docker socket — no local Python venv, no separately-run `docker compose up`.

```bash
# build (only after database/Dockerfile.test or database/test/python/ changes)
docker compose -f dc-plc-datalink-rfc1006-test.yml build database-test

# run the full suite
docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm database-test
```

Report the pytest summary in chat. The runtime smoke (next step) supplements but does not replace this test run.

#### Cleanup after tests (MANDATORY)
After every test run — full suite, single test, or aborted run — remove all test containers, networks, volumes **and the test image**. Nothing test-related must remain on the host. `run --rm` removes the test runner itself, but the default network, any anonymous volumes, and `testcontainers`-spawned CouchDB containers can persist otherwise.

```bash
# Drop containers, networks, anonymous + named volumes for the test project:
docker compose -f dc-plc-datalink-rfc1006-test.yml down -v --remove-orphans

# Drop ALL tags of the test-specific image (rebuild on next run is intentional):
docker images --filter "reference=plc-datalink-rfc1006-database-test" --format "{{.Repository}}:{{.Tag}}" \
  | xargs -r docker image rm -f
```

Do **not** remove the shared runtime image `plc-datalink-rfc1006-database:dev` here — that belongs to the dev stack.

Verify nothing remains under the test project label, and that `testcontainers` left no stragglers:
```bash
docker ps -a    --filter "label=com.docker.compose.project=plc-datalink-rfc1006-test"
docker volume ls --filter "label=com.docker.compose.project=plc-datalink-rfc1006-test"
docker image ls plc-datalink-rfc1006-database-test
docker ps -a --filter "ancestor=couchdb"   # testcontainers-spawned CouchDBs
docker ps -a --filter "name=testcontainers"
```
All five must come back empty. If a killed run left `testcontainers`-spawned containers, `docker rm -f <id>` them — ryuk normally handles cleanup but cannot recover from a SIGKILL.

### 5a. Integration Test against ZKS — when a requirement is fully implemented
**Policy** (per [docs/features/test-strategy/scope.md](../../../docs/features/test-strategy/scope.md), Section 5): once all acceptance criteria in `docs/features/<name>/scope.md` are ticked — particularly any change to the CouchDB document schema or `init-db.sh` — the full backend integration suite against the ZKS Machine Mock must run before handoff to `/06-qa` or `/99-commit`. Schema changes propagate through `PlcDatalinkRFC1006Model` → Telegraf rendering → MQTT, and the integration test is the canonical end-to-end check.

Delegate to `/06-qa` for the actual run — it owns the ZKS-Mock preconditions and the cleanup procedure. Do not skip this when the scope is complete.

### 6. Local Runtime Verification (manual)
- Rebuild: `docker compose -f dc-plc-datalink-rfc1006-dev.yml build plc-datalink-rfc1006-database`
- Bring the stack up: `docker compose -f dc-plc-datalink-rfc1006-dev.yml up -d`
- Verify the DB starts: `docker logs plc-datalink-rfc1006-database`
- Hit it from the host (dev compose exposes `5984:5984`):
  - `curl -u admin:password http://localhost:5984/` — should return CouchDB version JSON
  - `curl -u admin:password http://localhost:5984/_all_dbs` — should include the configured DB
- Use `database/test/couch-cmd.sh` and `database/test/devBoard1Rest.sh` as templates for ad-hoc verification
- Verify create/read/update/delete with the backend curl tests in `backend/test/curl/`

### 7. Run the Migration (if applicable)
- Snapshot the data volume first (`docker run --rm -v plc-datalink-rfc1006-database-data:/data -v $PWD:/backup busybox tar czf /backup/db-snapshot.tar.gz /data`)
- Run the migration script against the dev container
- Verify all documents are valid after migration
- Update or add a runbook in `runbooks/` (created by `/operations` if needed)

## Context Recovery
If context was compacted mid-task:
1. Re-read the scope note and any related ADR
2. `git diff` to see what's already changed
3. Read the current `PlcDatalinkRFC1006Model` and the migration script (if any)
4. Continue — do not duplicate already-written changes

## Checklist
- [ ] Scope note / ADR read (if applicable)
- [ ] Schema change reflected in BOTH backend model AND frontend TypeScript model
- [ ] OpenAPI spec updated for any field that appears in request/response payloads
- [ ] Migration script written and tested (if breaking change)
- [ ] Existing documents verified to load correctly after the change
- [ ] CouchDB starts cleanly with updated `local.ini` / `init-db.sh`
- [ ] backend container can still authenticate against CouchDB (env vars in sync)
- [ ] `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm database-test` is green
- [ ] Backend curl tests still pass
- [ ] `README.md` and `CHANGELOG.md` updated if user-visible

## Handoff
> "Database change done. Next step:
> - Run `/qa` to validate end-to-end
> - Run `/operations` to add or update a backup/restore runbook if the schema change affects recovery"

## Suggested Git Commit
```
feat(database): <one-line description>
feat(backend): <one-line> + corresponding model change
docs(architecture): add ADR-XXXX for breaking schema changes
```
