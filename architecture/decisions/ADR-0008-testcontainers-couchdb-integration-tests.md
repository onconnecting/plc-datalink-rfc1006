# ADR-0008: testcontainers[couchdb] for Database Integration Tests

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)

## Context
The [`database/test/`](../../database/test/) folder today contains two manual shell scripts ([`couch-cmd.sh`](../../database/test/couch-cmd.sh), [`devBoard1Rest.sh`](../../database/test/devBoard1Rest.sh)) that fire raw curl calls against whichever CouchDB happens to be running. They have no asserts, no setup, and no cleanup. They are useful as ad-hoc tooling but cannot be the regression net the [test-strategy scope](../../docs/features/test-strategy/scope.md) calls for.

The decision the scope leaves open is **how the test process gets a CouchDB to talk to**. Three patterns are common:

1. **In-memory or HTTP mock** (e.g. `requests-mock`, `responses`). The test fakes CouchDB responses at the HTTP-client level.
2. **Externally provisioned container.** A separate `docker compose up couchdb` runs before the test session; the tests assume it exists at a known port.
3. **testcontainers fixture.** The test process itself starts and stops a CouchDB container per session via the `testcontainers` Python library; tests address it through a fixture-provided URL.

The constraint from [`.claude/rules/backend.md`](../../.claude/rules/backend.md): *"`couchdb_service.py` is the only module that talks to CouchDB."* That module uses `requests` against the HTTP API. The value of a database test is therefore in exercising that exact HTTP surface — auth, status codes, `_rev` conflicts, `_all_docs` shape — not in mocking it away.

Additional constraints:

- Docker is already a baseline requirement on every developer machine (the dev workflow per [ADR-0005](ADR-0005-local-insecure-registry-for-dev-image-flow.md) calls `docker compose` directly).
- The production image is `couchdb:3` (see [`database/Dockerfile`](../../database/Dockerfile)). Tests must run against the same major version.
- The init script [`init-db.sh`](../../database/config/init-db.sh) and config [`local.ini`](../../database/config/local.ini) are part of what we want to test, not bypass.

## Decision
Use **pytest + `testcontainers[couchdb]`** for database integration tests. The test process starts a `couchdb:3` container per session via a fixture, applies [`database/config/init-db.sh`](../../database/config/init-db.sh) against it, and tears it down at session end.

Concrete commitments:

1. New test path [`database/test/python/`](../../database/test/python/) with `test_*.py` files. `database/test/conftest.py` holds the fixtures.
2. **Session-scoped fixture** starts the CouchDB container, applies the init script, exposes admin credentials and the dynamic port to tests.
3. **Function-scoped fixture** creates a unique throwaway database per test, drops it on teardown. Tests do not share state.
4. A dev dependency `testcontainers[couchdb]>=4` is added to `backend/pyproject.toml`'s `[project.optional-dependencies] dev` group (the test suite lives under `backend/` but exercises the `database/` container, hence the dep lives there).
5. The legacy shell scripts under `database/test/*.sh` stay in place as manual tooling. They are not invoked by pytest.

## Alternatives Considered
- **Option A — In-memory / HTTP mock (`requests-mock`).**
  - Pros: zero infrastructure, fastest possible execution, no Docker dependency.
  - Cons: tests **do not exercise CouchDB**. They exercise our assumption about how CouchDB responds. The values we most need to verify — `_rev` conflict on update, the exact 401 response when admin auth is missing, `_all_docs` paging shape — are exactly the values a mock makes us re-invent. Low return on test code that becomes a second source of truth for CouchDB semantics.

- **Option B — Externally provisioned container** (`docker compose up couchdb` before `pytest`).
  - Pros: simple, transparent — the test only needs an env var with the URL. No new Python dependency.
  - Cons: state is implicit. A failed prior test can leave a database around; the next session sees stale data. Two terminals (one for compose, one for pytest) raise friction. New contributors hit "why does the test pass for you and fail for me" until they remember to start the container.

- **Option C — testcontainers[couchdb] (chosen).**
  - Pros: each test session starts from a known empty container. Cleanup is automatic. The exact CouchDB version is pinned in the fixture (no drift from whatever the contributor has on `docker images`). Future CI port is trivial — testcontainers works the same way in GitHub Actions. The Python dependency is small and stable.
  - Cons: ~3–5 s container startup added to every test session (one-time, session-scoped). Requires Docker to be running on the developer machine — already a baseline requirement, but newly enforced for testing. The `testcontainers` library has its own surface to learn (image pull, port mapping, healthcheck) — modest but real.

## Consequences

**Positive**
- Tests exercise real CouchDB HTTP behaviour: auth, conflict, paging, init-script effects. The thing we test is the thing that runs in production.
- Deterministic startup state — no "leftover from last time" failure mode.
- Same fixtures port cleanly to CI: `testcontainers` + `docker:dind` (or a CI runner with Docker socket access) and the suite runs unchanged.
- Hook in [ADR-0007](ADR-0007-post-tool-use-hooks-test-auto-run.md) can invoke this suite after edits under `database/config/**` without extra glue.

**Negative / Trade-offs**
- Session startup latency: ~3–5 s. Mitigation: session-scope the container fixture, function-scope only the per-test database (cheap).
- Adds a Python dev dependency. Pinned to `>=4` to match the current major.
- Developers without Docker cannot run the DB suite. Acceptable — the rest of the stack already requires Docker.

**Migration / Compatibility**
- No data migration. Tests are additive.
- Existing manual shell scripts under [`database/test/`](../../database/test/) remain unchanged and untouched by pytest collection (different folder, different file extension).
- No change to production CouchDB image, init script, or config.

## References
- Related ADRs: [ADR-0005](ADR-0005-local-insecure-registry-for-dev-image-flow.md) (Docker is baseline for the workflow), [ADR-0006](ADR-0006-jest-for-frontend-tests.md) (matching framework choice for the FE), [ADR-0007](ADR-0007-post-tool-use-hooks-test-auto-run.md) (auto-run hooks invoke this suite)
- Related scope: [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)
- External: [testcontainers-python docs](https://testcontainers-python.readthedocs.io/), [CouchDB module README](https://github.com/testcontainers/testcontainers-python/tree/main/modules/couchdb)

---

## Update 2026-05-15 — Implementation notes

The core decision above (pytest + testcontainers + a per-session `couchdb:3.3.3` container, with per-test ephemeral databases) is **in place and green** (45 tests, ~2.5 s). Two implementation details from the original commitments deviated during the build-out — they don't change the decision but matter for anyone reading the ADR side-by-side with the code:

1. **Dependency package: `testcontainers>=4`, not `testcontainers[couchdb]>=4`.** The `couchdb` extra was removed from `testcontainers-python` in 4.x (pip warns: `testcontainers 4.14.2 does not provide the extra 'couchdb'`). The `testcontainers.couchdb` submodule still exists, but the integration suite uses `testcontainers.core.container.DockerContainer("couchdb:3.3.3")` directly — which is both supported across all 4.x versions and aligns with how `backend-test` already spawns containers. No functional difference: same image, same lifecycle, same waiting strategy.
2. **Where the dependency lives: `database/Dockerfile.test`, not `backend/pyproject.toml`.** Once the test suite landed at `database/test/python/` and is run from the dedicated `database-test` service in [`dc-plc-datalink-rfc1006-test.yml`](../../dc-plc-datalink-rfc1006-test.yml), having the dep in `backend/` would have crossed responsibilities. The image that runs the DB suite is the image that installs its own deps. `backend/pyproject.toml` is untouched.

The `database/test/*.sh` legacy commitment (item 5) and the session/function fixture commitments (items 2–3) are implemented as originally specified.
