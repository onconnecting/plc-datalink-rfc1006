# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — 2026-05-15

### Security
- Externalize CouchDB admin credentials and container registry settings via `.env` file. The compose stacks, `database/config/init-db.sh`, and the manual CouchDB test scripts under `database/test/` no longer carry hardcoded `admin:password` strings.

### Added
- `.env.example` at the repository root with `COUCHDB_USER`, `COUCHDB_PASSWORD`, `ACR_REGISTRY`, and `IMAGE_TAG` placeholders.
- `Configuration (.env)` section in `README.md` describing the `cp .env.example .env` workflow.
- `docs/features/` for scope notes (with README) and a first scope note for the repo-structure cleanup at `docs/features/project-structure-best-practices/scope.md`.
- `architecture/decisions/` for Architecture Decision Records, with a README and `ADR-0000-template.md`.
- `architecture/decisions/ADR-0001-backend-application-entrypoint.md` documenting the `init.py` → `app.py` rename and the rejected alternative (app-factory in `__init__.py`).
- `architecture/decisions/ADR-0002-python-project-metadata.md` documenting the coexistence of `pyproject.toml` and `requirements.txt`.
- `architecture/decisions/ADR-0003-frontend-ui-foundation-angular-cdk.md` selecting `@angular/cdk@19` as the UI foundation and rejecting Bootstrap, Material, PrimeNG, and Tailwind for the rewrite.
- `architecture/decisions/ADR-0004-frontend-greenfield-migration-strategy.md` selecting a greenfield parallel project (`frontend-next/`) with a single directory-swap cutover as the rewrite strategy.
- `docs/features/frontend-ci-rewrite/scope.md` with the corresponding feature scope.
- `architecture/decisions/ADR-0005-local-insecure-registry-for-dev-image-flow.md` documenting the DEV/PROD split: self-hosted insecure registry on `192.168.0.121:5000`, build-push-pull-up loop, single `dev` tag, no Makefile.
- `docs/features/dev-prod-split/scope.md` with the corresponding feature scope.
- `dc-registry-local.yml` running `registry:2` on `192.168.0.121:5000` with persistent storage in the named volume `plc-datalink-rfc1006-registry-data` and `REGISTRY_STORAGE_DELETE_ENABLED=true`.
- `dc-plc-datalink-rfc1006-dev.yml` for the DEV app stack with combined `image:` + `build:` directives pointing at `${LOCAL_REGISTRY:-192.168.0.121:5000}/plc-datalink-rfc1006-{service}:dev`.
- `.env.example` entries `LOCAL_REGISTRY=192.168.0.121:5000` and `LOCAL_REGISTRY_PORT=5000`.
- `.editorconfig` at the repository root (UTF-8, LF, 4 spaces Python / 2 spaces YAML+TS+JSON, tabs in Makefiles).
- `.dockerignore` for `backend/`, `frontend/`, and `database/` build contexts to exclude VCS, IDE, venv, `node_modules/`, tests, and logs from images.
- `.github/PULL_REQUEST_TEMPLATE.md` covering change type, affected areas, related scope/ADR, breaking-change flag, test plan, and a checklist for CHANGELOG / docs / secrets.
- `backend/pyproject.toml` (PEP 621) declaring project metadata, runtime deps (mirror of `requirements.txt`), a `dev` extras group (`ruff`, `pytest`), and config for Ruff and Pytest.
- `frontend/.prettierrc` with Angular-aligned defaults (single quotes, 2-space, 120 col).
- `.pre-commit-config.yaml` wiring Ruff (lint + format) for the backend, Prettier for the frontend, and standard hygiene hooks (trailing whitespace, EOF, YAML check, large-file guard, private-key detection, merge-conflict marker check).
- `.github/workflows/lint.yml` running Ruff on `backend/` and Prettier `--check` on `frontend/`.
- `.github/workflows/test.yml` doing a Python compile-check on the backend and `npm run build` on the frontend.
- `.github/dependabot.yml` for weekly `pip`, `npm`, and `github-actions` updates. (Docker ecosystem intentionally omitted — see comments in the file.)
- `docs/machines-db-layout/zks-machine-mock/` reference material for the external ZKS production-cell simulator — overview README and `db-layout.yaml` describing the S7 DBs (DB1 Machine, DB2 twelve welds, DB3 Test, DB4 Part + Commands) exposed by the mock on `192.168.0.180:102` alongside its OPC UA endpoint on `:4840`. Reference for `/qa` when exercising the PLC → Telegraf → MQTT data path; the mock runs in its own compose stack and is not a runtime dependency.

### Changed
- **Frontend complete rewrite** (per [ADR-0003](architecture/decisions/ADR-0003-frontend-ui-foundation-angular-cdk.md) + [ADR-0004](architecture/decisions/ADR-0004-frontend-greenfield-migration-strategy.md)): `frontend/` is now an Angular 19 LTS standalone-components project with Signals, OnPush, the new control-flow (`@if`/`@for`), typed reactive forms, `inject()` DI, and `takeUntilDestroyed`. UI primitives (`oc-button`, `oc-input`, `oc-field`, `oc-card`, `oc-status-pill`, `oc-toast` + `ToastService`, `oc-dialog` + `DialogService`) are built directly on `@angular/cdk` — no Bootstrap, Material, PrimeNG, or Tailwind. Design tokens (`src/styles/_tokens.css`) are the single colour/spacing/typography source; `stylelint` enforces no raw hex outside the token file. UI tonality is German per the onconnecting CI manual, no emojis, no exclamation chains; PLC addresses, IPs, ports, and topics render in Consolas. Routes (`/plc-states`, `/configuration-overview`, `/create-configuration`) and backend contract (relative `/config/*` and `/machine/*` paths) are preserved 1:1; the legacy `/api/*` prefix is dropped. Build budgets: 374 kB initial / 101 kB transfer. ESLint + Stylelint clean.
- Greenfield rewrite landed via the directory swap ADR-0004 prescribes: `frontend-next/` → `frontend/`, legacy `frontend/` deleted (history preserved in git). `dc-plc-datalink-rfc1006-dev.yml` requires no change — `build.context: ./frontend` keeps pointing at the same path with new content.
- `dc-plc-datalink-rfc1006-local.yml` and `dc-plc-datalink-rfc1006-acr.yml` now read CouchDB credentials via `${COUCHDB_USER:-admin}` / `${COUCHDB_PASSWORD:-password}` and inject `DATABASE_USER_NAME` / `DATABASE_SECRET_KEY` into the backend container.
- Rename `backend/src/init.py` → `backend/src/app.py`; the empty `backend/src/__init__.py` is kept. The Gunicorn target in `backend/config/supervisord.conf` is updated to `src.app:app`. See ADR-0001 for the rationale.
- Rename `backend/config/env` → `backend/config/env.example` to mark it explicitly as a template; the Dockerfile copies it to `/app/.env` at build time (unchanged runtime behavior).
- Reorganize `backend/test/`: shell-curl scripts moved into `backend/test/curl/`, the Python dev helper into `backend/test/scripts/`. No script logic changed.
- The ACR compose file references images via `${ACR_REGISTRY:-onconnecting.azurecr.io}/...:${IMAGE_TAG:-latest}`.
- `backend/config/env` no longer carries the CouchDB credentials; they are supplied by the compose `environment:` section.
- `database/test/couch-cmd.sh` and `database/test/devBoard1Rest.sh` fail fast if `COUCHDB_USER` / `COUCHDB_PASSWORD` are not exported.

### Removed
- Tracking of the `.claude/` directory and `doc/design/onconnecting-ci/` from version control via `.gitignore`.
- `dc-plc-datalink-rfc1006-local.yml` — superseded by `dc-plc-datalink-rfc1006-dev.yml`, which runs the same three services but goes through the local registry (build → push → pull → up) so the DEV loop matches the PROD pull mechanics.
- Top-level `Makefile` — the stack is bedient directly with `docker compose` calls; backend lint/format runs as `ruff check` / `ruff format` from `backend/`. README documents the new commands.

### Fixed
- `.gitignore` now also excludes `backend/.venv/`, `__pycache__/`, `*.pyo`, `*.egg-info/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `node_modules/`, `frontend/dist/`, `.angular/`, and `*.swp` / `*.swo` swap files — previously these could have been accidentally committed.
- Bump the pinned SHA256 of the InfluxData GPG key in `backend/dockerfile-plc-datalink-rfc1006-backend` to `40557e26…4d5dac` (the value currently served at `repos.influxdata.com/influxdata-archive.key`). The previous pin (`943666…7515`) no longer matched after an upstream key rotation, blocking the backend image build at step 4 of 20.

### Notes
- The newly enabled lint workflow (Ruff for backend, Prettier for frontend) will likely fail on the first push because existing files were written before either tool was configured. Run `ruff format src test` inside `backend/` and `npx prettier --write "src/**/*.{ts,js,html,css,scss}"` inside `frontend/` once to establish a baseline.
- Pre-commit hooks only activate after `pre-commit install` is run in the working tree.
- The DEV registry is **insecure** (HTTP). Every host that pushes or pulls must list `192.168.0.121:5000` under `insecure-registries` in `/etc/docker/daemon.json` and reload the daemon (`systemctl restart docker`). README contains the one-liner. Do not reuse this registry for PROD.
