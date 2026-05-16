---
paths:
  - "backend/config/env"
  - "database/config/local.ini"
  - "**/dockerfile-*"
  - "dc-plc-datalink-rfc1006-*.yml"
  - ".github/workflows/**"
  - ".env*"
---

# Security Rules

## Secrets Management
- NEVER commit passwords, API keys, ACR credentials, or PLC credentials to git
- The compose files contain **development defaults only** (`COUCHDB_USER=admin`, `COUCHDB_PASSWORD=password`) — these must be overridden via environment variables or a non-committed `.env` file in any non-dev environment
- Store local credentials in a `.env` file — ensure `.env` is in `.gitignore`
- Document required environment variables in `README.md` with placeholder values only

## CouchDB Security
- The default admin credentials in `database/config/local.ini` and the compose files are **dev only**
- Production deployments MUST rotate the admin password and not expose port `5984` outside the docker bridge network
- Restrict CORS in `local.ini` if external clients are added — by default, only the backend service on the docker network should reach CouchDB

## Backend Security
- Validate all user input on routes — never pass raw `request.args` or JSON into Telegraf config rendering without checking shape and PLC address syntax
- Treat `machine_name` as a path/filename component when it lands in `MachineConfigurationService` — sanitize to prevent path traversal into `/etc/telegraf` or `/var/log/*`
- Never log credentials or full Telegraf configs at INFO level — drop to DEBUG and redact MQTT broker passwords if added
- Flask is served via gunicorn in the container — do not run with `flask run` / debug mode in production

## MQTT Security
- The default MQTT port is `1883` (plain). If the broker requires authentication or TLS, plumb credentials via environment variables — never hardcode in `dynamic_startup_telegraf.sh` or example configs
- Do not log full payloads at INFO level if they may include sensitive process values

## Network Exposure
- Only port `80` (frontend nginx) is mapped to the host by default
- Do NOT publish CouchDB (`5984`) or the backend Flask port outside the docker bridge network unless explicitly approved
- Any new published port requires an ADR and explicit user approval

## Container Hardening
- Run containers as non-root where the base image supports it
- Mount config files read-only where possible
- Pin all base image tags (no `:latest`)

## Code Review Triggers — REQUIRE explicit user approval
- Changing CouchDB admin credentials or auth mode
- Adding TLS termination, certificate handling, or new auth flows
- Exposing additional ports on the host
- Adding outbound network calls from the backend (besides the existing PLC + MQTT + CouchDB endpoints)
- Bumping a base image to a new major version
- Any change to `.github/workflows/` that touches secrets or deployment targets

## Sensitive Files — never stage in a commit
- `.env`, `.env.*`
- `*.key`, `*.pem`, `*.p12`, `*.jks`
- `certs/`, `secrets/`
- `backend/.venv/`
