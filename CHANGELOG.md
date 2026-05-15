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
- `.editorconfig` at the repository root (UTF-8, LF, 4 spaces Python / 2 spaces YAML+TS+JSON, tabs in Makefiles).
- `.dockerignore` for `backend/`, `frontend/`, and `database/` build contexts to exclude VCS, IDE, venv, `node_modules/`, tests, and logs from images.
- `.github/PULL_REQUEST_TEMPLATE.md` covering change type, affected areas, related scope/ADR, breaking-change flag, test plan, and a checklist for CHANGELOG / docs / secrets.

### Changed
- `dc-plc-datalink-rfc1006-local.yml` and `dc-plc-datalink-rfc1006-acr.yml` now read CouchDB credentials via `${COUCHDB_USER:-admin}` / `${COUCHDB_PASSWORD:-password}` and inject `DATABASE_USER_NAME` / `DATABASE_SECRET_KEY` into the backend container.
- The ACR compose file references images via `${ACR_REGISTRY:-onconnecting.azurecr.io}/...:${IMAGE_TAG:-latest}`.
- `backend/config/env` no longer carries the CouchDB credentials; they are supplied by the compose `environment:` section.
- `database/test/couch-cmd.sh` and `database/test/devBoard1Rest.sh` fail fast if `COUCHDB_USER` / `COUCHDB_PASSWORD` are not exported.

### Removed
- Tracking of the `.claude/` directory and `doc/design/onconnecting-ci/` from version control via `.gitignore`.

### Fixed
- `.gitignore` now also excludes `backend/.venv/`, `__pycache__/`, `*.pyo`, `*.egg-info/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `node_modules/`, `frontend/dist/`, `.angular/`, and `*.swp` / `*.swo` swap files — previously these could have been accidentally committed.
