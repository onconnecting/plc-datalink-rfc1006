# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — 2026-05-15

### Security
- Externalize CouchDB admin credentials and container registry settings via `.env` file. The compose stacks, `database/config/init-db.sh`, and the manual CouchDB test scripts under `database/test/` no longer carry hardcoded `admin:password` strings.

### Added
- `.env.example` at the repository root with `COUCHDB_USER`, `COUCHDB_PASSWORD`, `ACR_REGISTRY`, and `IMAGE_TAG` placeholders.
- `Configuration (.env)` section in `README.md` describing the `cp .env.example .env` workflow.

### Changed
- `dc-plc-datalink-rfc1006-local.yml` and `dc-plc-datalink-rfc1006-acr.yml` now read CouchDB credentials via `${COUCHDB_USER:-admin}` / `${COUCHDB_PASSWORD:-password}` and inject `DATABASE_USER_NAME` / `DATABASE_SECRET_KEY` into the backend container.
- The ACR compose file references images via `${ACR_REGISTRY:-onconnecting.azurecr.io}/...:${IMAGE_TAG:-latest}`.
- `backend/config/env` no longer carries the CouchDB credentials; they are supplied by the compose `environment:` section.
- `database/test/couch-cmd.sh` and `database/test/devBoard1Rest.sh` fail fast if `COUCHDB_USER` / `COUCHDB_PASSWORD` are not exported.

### Removed
- Tracking of the `.claude/` directory and `doc/design/onconnecting-ci/` from version control via `.gitignore`.
