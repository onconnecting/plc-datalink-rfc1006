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
- `.editorconfig` at the repository root (UTF-8, LF, 4 spaces Python / 2 spaces YAML+TS+JSON, tabs in Makefiles).
- `.dockerignore` for `backend/`, `frontend/`, and `database/` build contexts to exclude VCS, IDE, venv, `node_modules/`, tests, and logs from images.
- `.github/PULL_REQUEST_TEMPLATE.md` covering change type, affected areas, related scope/ADR, breaking-change flag, test plan, and a checklist for CHANGELOG / docs / secrets.
- Top-level `Makefile` with targets for local stack (`build`, `up`, `down`, `restart`, `logs`, `ps`, `clean`), ACR stack (`build-acr`, `up-acr`, `down-acr`), and backend dev tooling (`lint`, `format`).
- `backend/pyproject.toml` (PEP 621) declaring project metadata, runtime deps (mirror of `requirements.txt`), a `dev` extras group (`ruff`, `pytest`), and config for Ruff and Pytest.
- `frontend/.prettierrc` with Angular-aligned defaults (single quotes, 2-space, 120 col).
- `.pre-commit-config.yaml` wiring Ruff (lint + format) for the backend, Prettier for the frontend, and standard hygiene hooks (trailing whitespace, EOF, YAML check, large-file guard, private-key detection, merge-conflict marker check).
- `.github/workflows/lint.yml` running Ruff on `backend/` and Prettier `--check` on `frontend/`.
- `.github/workflows/test.yml` doing a Python compile-check on the backend and `npm run build` on the frontend.
- `.github/dependabot.yml` for weekly `pip`, `npm`, and `github-actions` updates. (Docker ecosystem intentionally omitted — see comments in the file.)

### Changed
- `dc-plc-datalink-rfc1006-local.yml` and `dc-plc-datalink-rfc1006-acr.yml` now read CouchDB credentials via `${COUCHDB_USER:-admin}` / `${COUCHDB_PASSWORD:-password}` and inject `DATABASE_USER_NAME` / `DATABASE_SECRET_KEY` into the backend container.
- Rename `backend/src/init.py` → `backend/src/app.py`; the empty `backend/src/__init__.py` is kept. The Gunicorn target in `backend/config/supervisord.conf` is updated to `src.app:app`. See ADR-0001 for the rationale.
- Rename `backend/config/env` → `backend/config/env.example` to mark it explicitly as a template; the Dockerfile copies it to `/app/.env` at build time (unchanged runtime behavior).
- Reorganize `backend/test/`: shell-curl scripts moved into `backend/test/curl/`, the Python dev helper into `backend/test/scripts/`. No script logic changed.
- The ACR compose file references images via `${ACR_REGISTRY:-onconnecting.azurecr.io}/...:${IMAGE_TAG:-latest}`.
- `backend/config/env` no longer carries the CouchDB credentials; they are supplied by the compose `environment:` section.
- `database/test/couch-cmd.sh` and `database/test/devBoard1Rest.sh` fail fast if `COUCHDB_USER` / `COUCHDB_PASSWORD` are not exported.

### Removed
- Tracking of the `.claude/` directory and `doc/design/onconnecting-ci/` from version control via `.gitignore`.

### Fixed
- `.gitignore` now also excludes `backend/.venv/`, `__pycache__/`, `*.pyo`, `*.egg-info/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `node_modules/`, `frontend/dist/`, `.angular/`, and `*.swp` / `*.swo` swap files — previously these could have been accidentally committed.

### Notes
- The newly enabled lint workflow (Ruff for backend, Prettier for frontend) will likely fail on the first push because existing files were written before either tool was configured. Run `make format` (`ruff format` on backend) and `npx prettier --write "src/**/*.{ts,js,html,css,scss}"` inside `frontend/` once to establish a baseline.
- Pre-commit hooks only activate after `pre-commit install` is run in the working tree.
