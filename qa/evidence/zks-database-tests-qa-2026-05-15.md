# QA Evidence: Database tests (unit + ZKS-driven integration)

**Tested:** 2026-05-15
**Environment:** local (test-only compose stack)
**Tester:** QA Engineer (AI)
**Git ref:** `feat/e2e-zks-mqtt-test` @ working tree (base commit `6655b65`)
**Scope note:** [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md), section *3. Database — Integration-Tests (pytest + testcontainers)*
**Related ADR:** [ADR-0008-testcontainers-couchdb-integration-tests](../../architecture/decisions/ADR-0008-testcontainers-couchdb-integration-tests.md)

> **Scope of this QA pass.** The change under test is **purely additive test infrastructure** — `database/test/python/` plus a docs-mount in `dc-plc-datalink-rfc1006-test.yml` and a `PyYAML` dep in `database/Dockerfile.test`. No production code, no API surface, no CouchDB document schema, and no published ports were touched. The QA template's UI / data-path / route-curl sections are therefore intentionally marked **not applicable** rather than tested.

---

## Acceptance Criteria (from scope §3)

### AC-1: New path `database/test/python/` with pytest suite (`test_*.py`)
- [x] **PASS** — Tests collected at [`database/test/python/`](../../database/test/python/), grouped into `unit/` and `integration/`. `docker compose ... run --rm database-test` reports **45 passed in 2.49s**.

### AC-2: Stack is pytest + testcontainers — fresh CouchDB per session via fixture, no manual compose-up
- [x] **PASS** — [`conftest.py`](../../database/test/python/conftest.py) uses `testcontainers.core.container.DockerContainer("couchdb:3.3.3")` with a session-scoped fixture. Container is spawned through the docker socket bind-mounted by [`dc-plc-datalink-rfc1006-test.yml`](../../dc-plc-datalink-rfc1006-test.yml).
  - **Deviation from ADR-0008:** ADR-0008 named the dependency `testcontainers[couchdb]`. The `couchdb` extra **does not exist in `testcontainers` 4.x** (pip warning: `testcontainers 4.14.2 does not provide the extra 'couchdb'`). Since the conftest only needs `DockerContainer` + `wait_for_logs`, the dependency was simplified to plain `testcontainers>=4`. **No functional difference** — same image, same lifecycle. Tracked as ISSUE-1 (Low / documentation drift).

### AC-3: `conftest.py` — session fixture for the container, function fixture for fresh DB per test
- [x] **PASS**
  - `couchdb_url` is `scope="session"` — one container per pytest invocation
  - `ephemeral_db` is the default function scope — creates `test-<uuid12>`, drops it in `finally:` regardless of test outcome
  - Verified: re-running the suite yields the same `total_rows == 1` in `test_all_docs_include_docs_returns_zks`, proving leftover docs from prior tests are not visible.

### AC-4: Init script `init-db.sh` creates the expected databases
- [x] **PASS** — Integration: [`test_couchdb_bootstrap.py::test_required_databases_exist`](../../database/test/python/integration/test_couchdb_bootstrap.py) asserts all four databases (`_users`, `_replicator`, `_global_changes`, `datalink`) are present after the conftest replays the same bootstrap. Unit: [`unit/test_init_db_script.py`](../../database/test/python/unit/test_init_db_script.py) covers all four DB names parametrically against the script text.

### AC-5: Admin auth from `local.ini` works (negative test: request without auth → 401)
- [x] **PASS** — [`test_couchdb_bootstrap.py::test_anonymous_create_db_rejected`](../../database/test/python/integration/test_couchdb_bootstrap.py) — anonymous `PUT` rejected with 401. Positive case via `test_admin_can_authenticate` (`_session` reports `_admin` role).

### AC-6: Doc roundtrip (Create / Read / Update / Delete), `_rev` conflict → 409
- [x] **PASS** — Covered in [`test_zks_machine_doc_crud.py`](../../database/test/python/integration/test_zks_machine_doc_crud.py):
  - `test_zks_doc_round_trip` — full PUT → GET equality of all 128 PLC tag entries
  - `test_put_without_rev_on_existing_doc_409` — re-PUT without `_rev` → **409 conflict** (matches the exception path in `couchdb_service.CouchDBService.create_doc`)
  - `test_update_with_rev_succeeds` — PUT with `_rev` bumps the revision from `1-…` to `2-…`
  - `test_delete_with_rev` — DELETE with `?rev=` returns `{"ok": true}` and subsequent GET → 404

### AC-7: Bulk read `_all_docs` returns expected doc IDs
- [x] **PASS** — `test_all_docs_include_docs_returns_zks` — verifies the same query the backend uses (`?include_docs=true`) returns `total_rows == 1`, the row's `id` matches `machineName`, and the embedded `doc.plcTagData` length matches the input (128 tags).

### AC-8: Existing manual scripts (`couch-cmd.sh`, `devBoard1Rest.sh`) remain as manual tooling
- [x] **PASS** — Both scripts untouched in [`database/test/`](../../database/test/) (same byte content as base commit `6655b65`). pytest collection is rooted at `database/test/python/`, so `*.sh` files are never collected.

### AC-9 (user-added): Unit tests exist alongside integration tests
- [x] **PASS** — 35 unit tests across four files:
  - [`unit/test_init_db_script.py`](../../database/test/python/unit/test_init_db_script.py) — shebang, required DB names, env-var credentials, wait-loop
  - [`unit/test_local_ini.py`](../../database/test/python/unit/test_local_ini.py) — CORS posture (origins, methods, credentials, headers)
  - [`unit/test_dockerfile.py`](../../database/test/python/unit/test_dockerfile.py) — `couchdb:3.x` pin, init script + `local.ini` placement
  - [`unit/test_zks_layout.py`](../../database/test/python/unit/test_zks_layout.py) — ZKS YAML invariants + RFC1006 address translation per README spec

### AC-10 (user-added): Integration tests use the ZKS machine layout
- [x] **PASS** — Integration tests build their CouchDB document from [`docs/machines-db-layout/zks-machine-mock/db-layout.yaml`](../../docs/machines-db-layout/zks-machine-mock/db-layout.yaml) via [`zks_layout.py`](../../database/test/python/zks_layout.py). Tag counts asserted per DB (`DB1=12`, `DB2=84`, `DB3=15`, `DB4=17`, total 128) and a representative tag is spot-checked from each region (`DB1.X36.0`, `DB2.R2`, `DB3.R12`, `DB4.S0.32`).

---

## API Validation (curl)
**N/A** — no REST endpoints added or modified. Backend code is untouched.

## UI Validation (browser)
**N/A** — no frontend changes.

## Data Path Validation (PLC → Telegraf → MQTT)
**N/A for this PR.** The MQTT data path is the subject of scope §4 (E2E ZKS-Mock) and remains a coverage gap until `/03-backend` implements `backend/test/scripts/test_e2e_zks.py`. This PR is the database-layer prerequisite.

## Container Health
Test-only stack — production stack was not started for this PR.

- [x] `docker compose -f dc-plc-datalink-rfc1006-test.yml build database-test` — clean
- [x] `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm database-test` — exit 0, 45 passed
- [x] testcontainers cleanup verified: `docker ps -a --filter ancestor=couchdb:3.3.3` shows no leftover containers after the run

## Security Audit

- [x] **No credentials in new files.** The fixture admin password (`test-admin-pw`) is a runtime-generated value used only by the ephemeral testcontainer and never touches CouchDB images, env files, or `.env` defaults. Verified with `grep -rE "password|secret|token" database/test/python` — only `ADMIN_PASSWORD` / `admin_auth` test-local names match.
- [x] **No new published ports.** `dc-plc-datalink-rfc1006-test.yml` has no `ports:` keys (verified with `grep -n "ports:"`); testcontainers exposes the CouchDB port only inside the test-network and on the docker bridge — never to the host. Aligns with [`.claude/rules/security.md`](../../.claude/rules/security.md) ("Do NOT publish CouchDB (5984) outside the docker bridge network").
- [x] **No new dependencies in `backend/requirements.txt` or `frontend/package.json`.** New deps (`testcontainers>=4`, `PyYAML`) are pinned in `database/Dockerfile.test` only — they ship inside the test image, never the production database image.
- [x] **Docker socket exposure.** `database-test` mounts `/var/run/docker.sock` — same posture as `backend-test` and consistent with ADR-0008. Test stack is DEV-only and never deployed.
- [x] **ZKS docs mount is read-only** (`:ro`).

## Regression Check

- [x] No production source touched (`git diff master...HEAD -- backend/src/ frontend/src/ database/config/` → empty).
- [x] Existing backend curl scripts under [`backend/test/curl/`](../../backend/test/curl/) untouched.
- [x] Existing `database/test/*.sh` untouched.
- [x] Existing production `dc-plc-datalink-rfc1006-{dev,acr}.yml` not modified.
- [x] Existing backend Dockerfile.test and frontend Dockerfile.test not modified.

---

## Issues Found

> All three Low findings below were **resolved in a follow-up pass on 2026-05-15** after this evidence was first written. Final test run: **45 passed, 0 warnings, 2.44 s**. The original finding text is preserved verbatim; each entry has a **Resolution** line documenting the fix.

### ISSUE-1: ADR-0008 names a non-existent extra (`testcontainers[couchdb]`)
- **Severity:** Low
- **Component:** docs / architecture
- **Steps to Reproduce:**
  1. `pip install 'testcontainers[couchdb]>=4'`
  2. Expected: silent success.
  3. Actual: `WARNING: testcontainers 4.14.2 does not provide the extra 'couchdb'`. The `couchdb` module exists internally but is no longer surfaced as an installable extra in 4.x.
- **Mitigation already applied:** [`database/Dockerfile.test`](../../database/Dockerfile.test) installs plain `testcontainers>=4`. The conftest uses the generic `DockerContainer` for the same effect.
- **Priority:** Nice to have — update ADR-0008 (or the ADR's *Decision* / *Consequences* section) to reflect the actual extra-less install. **Not a release blocker.**
- **Resolution (2026-05-15):** Appended an *Update 2026-05-15 — Implementation notes* section to [ADR-0008](../../architecture/decisions/ADR-0008-testcontainers-couchdb-integration-tests.md). The original Decision is left intact (ADR best practice — the decision didn't change, only an implementation detail); the Update documents the dropped extra and the actual location of the dependency (`database/Dockerfile.test`, not `backend/pyproject.toml`).

### ISSUE-2: Scope's ZKS tag subset table uses an incorrect address format for STRING
- **Severity:** Low (docs only — not exercised by this PR)
- **Component:** docs / scope
- **Steps to Reproduce:**
  1. Open [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md), "Repräsentativer ZKS-Tag-Subset" table.
  2. Expected per [README PLC Address spec](../../README.md#plc-address-specification): `S<offset>.<max_length>` — e.g. `DB1.S38.20` for `LastError` (`offset: 38, length: 20` in the ZKS YAML).
  3. Actual in scope: `DB1.S20.20` for `Machine.LastError` and `DB4.S32.32` for `Part.Serial`. Both rows transpose / drop the actual byte offset (38 → 20; 0 → 32). The scope's own footnote even says "Adress-Syntax … insbesondere String-Format `S<max>.<len>`" — but the README defines `S<offset>.<max>`, not `S<max>.<len>`.
- **Priority:** Fix before `/03-backend` consumes that table for the E2E runner — otherwise the E2E will send `S20.20` to Telegraf and miss the actual string buffer at byte 38. **Not blocking this PR**; the PR's own helper computes addresses correctly from the YAML.
- **Resolution (2026-05-15):** `docs/features/test-strategy/scope.md` updated — `DB1.S20.20` → `DB1.S38.20`, `DB4.S32.32` → `DB4.S0.32`, and the format footnote clarified to `S<offset>.<max>` with a pointer to the README's `DB2000.S30.13` example.

### ISSUE-3: `wait_for_logs` deprecation warning surfaces in pytest output
- **Severity:** Low
- **Component:** test / fixtures
- **Steps to Reproduce:**
  1. Run `docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm database-test`.
  2. Expected: clean output.
  3. Actual: one `DeprecationWarning` per session — `testcontainers` 4.x recommends migrating string predicates to `LogMessageWaitStrategy`.
- **Mitigation:** Tests still pass. The deprecation will only break on a future `testcontainers` major bump (≥5.x).
- **Priority:** Address opportunistically (swap `wait_for_logs` → `container.waiting_for(LogMessageWaitStrategy(...))`) when the next testcontainers upgrade is on the table.
- **Resolution (2026-05-15):** [`database/test/python/conftest.py`](../../database/test/python/conftest.py) now uses `LogMessageWaitStrategy("Apache CouchDB has started").with_startup_timeout(60)` applied via the container's `.waiting_for(...)` builder. Import is `from testcontainers.core.wait_strategies import LogMessageWaitStrategy` (the deprecation message itself misdirected to `waiting_utils`; the strategy classes actually live in `wait_strategies`). Re-run confirms zero warnings.

---

## Coverage Gaps

- **Telegraf rendering of ZKS addresses not exercised.** The translation helper (`zks_layout.translate_field`) emits addresses that match the README spec, but no test runs `machine_configuration_service.render_telegraf_config(zks_doc)` to confirm the rendered `[[inputs.s7comm]]` block is valid. Belongs to `/03-backend`.
- **MQTT data path not exercised** for ZKS. Subject of scope §4 — gated on a real ZKS-Mock + Mosquitto in a new compose stack. Belongs to `/03-backend`.
- **CORS origins from `local.ini` not verified end-to-end against a real CouchDB.** Unit tests assert the parsed values; an integration test that applies `local.ini` to the testcontainer and issues a preflighted request from a non-listed origin is left as a stretch goal — low value since CouchDB's CORS implementation is library-tested upstream.

---

## Summary

- **Acceptance Criteria:** **10 / 10 passed** (8 from scope §3 + 2 user-added).
- **Issues Found:** **3 total** (0 critical, 0 high, 0 medium, 3 low — all documentation / deprecation polish).
- **Security Audit:** **Pass** — no secrets, no new published ports, dev-only docker-socket exposure consistent with sibling test services.
- **Production Ready:** **YES** — this PR adds test infrastructure; production behavior is unchanged.
- **Recommendation:** **Release** the test suite. Address the three Low issues opportunistically:
  1. Update ADR-0008 to drop the `[couchdb]` extra.
  2. Fix the STRING addresses in the scope's ZKS tag subset table (before `/03-backend` consumes it).
  3. Migrate the `wait_for_logs` call to `LogMessageWaitStrategy` the next time testcontainers is touched.
