---
paths:
  - "dc-plc-datalink-rfc1006-*.yml"
  - "dc-registry-local.yml"
  - "**/dockerfile-*"
  - ".github/workflows/**"
---

# Docker & CI/CD Rules

The platform ships as three containers on a shared bridge network. The repo defines the following Compose stacks (see [ADR-0005](../../architecture/decisions/ADR-0005-local-insecure-registry-for-dev-image-flow.md)):

| File | Use |
|---|---|
| `dc-registry-local.yml` | Run a self-hosted insecure Docker registry (`registry:2`) on `192.168.0.121:5000` — DEV only |
| `dc-plc-datalink-rfc1006-dev.yml` | DEV: build, push, pull, and run the app stack via the local registry (`image:` + `build:` combined) |
| `dc-plc-datalink-rfc1006-acr.yml` | PROD: pull pre-built images from Azure Container Registry (`onconnecting.azurecr.io`) |

## Containers
| Service | Image | Ports | Volume | Depends on |
|---|---|---|---|---|
| `plc-datalink-rfc1006-database` | CouchDB-based | `5984:5984` | `plc-datalink-rfc1006-database-data → /opt/couchdb/data` | — |
| `plc-datalink-rfc1006-backend` | Python/Flask + Telegraf + supervisord | (none external) | `plc-datalink-rfc1006-backend-data → /etc/telegraf` | database |
| `plc-datalink-rfc1006-frontend` | nginx + Angular bundle | `80:80` | — | backend |

Network: `plc-datalink-rfc1006-network` (bridge).

## Compose Rules
- Keep service names, container names, and hostnames identical (`plc-datalink-rfc1006-{database,backend,frontend}`) — they are referenced from configs and docs
- The DEV and ACR app stacks (`dc-plc-datalink-rfc1006-dev.yml` and `dc-plc-datalink-rfc1006-acr.yml`) must stay in sync for: network, volumes, depends_on, env vars, port mappings
- DEV `image:` references resolve to `${LOCAL_REGISTRY:-192.168.0.121:5000}/plc-datalink-rfc1006-{service}:dev`; ACR references resolve to `${ACR_REGISTRY:-onconnecting.azurecr.io}/plc-datalink-rfc1006-{service}:${IMAGE_TAG:-latest}`
- DEV uses the single tag `dev` — every build overwrites it; no SHA or timestamp suffixes
- `dc-registry-local.yml` is a separate lifecycle stack — never merge the registry service into the app stack
- Do not introduce new published ports without an explicit user approval (security and conflict risk)
- The CouchDB admin credentials in compose are **dev defaults** — never reuse in production

## Dockerfile Rules
- Pin base image tags (`python:3.X-slim`, `node:X-alpine`, `couchdb:X`) — do not use `:latest`
- Backend image must include Telegraf and supervisord (see existing dockerfile)
- Frontend image must build the Angular bundle in a builder stage and copy into the nginx stage
- Database image must apply `local.ini` and run `init-db.sh` on first start
- Multi-stage where possible — keep final images small

## CI/CD (.github/workflows/)
- One workflow per image build (database / backend / frontend) or one matrix workflow
- Tag images with `latest` AND the short commit SHA when pushing to ACR
- Never push to ACR from a feature branch by default — only from `master` / tagged releases
- Secrets (ACR credentials) live in GitHub repo secrets — never inline in YAML

## Deployment
- DEV (one-time, per host): add `{"insecure-registries":["192.168.0.121:5000"]}` to `/etc/docker/daemon.json` and `systemctl restart docker`
- DEV (one-time): `docker compose -f dc-registry-local.yml up -d`
- DEV (per iteration):
  1. `docker compose -f dc-plc-datalink-rfc1006-dev.yml build`
  2. `docker compose -f dc-plc-datalink-rfc1006-dev.yml push`
  3. `docker compose -f dc-plc-datalink-rfc1006-dev.yml pull`
  4. `docker compose -f dc-plc-datalink-rfc1006-dev.yml up -d --no-build`
- DEV and PROD stacks must not run on the same host simultaneously — stop one before starting the other (same ports, same container names)
- PROD pull: requires `az login` + `az acr login -n onconnecting`, then `docker compose -f dc-plc-datalink-rfc1006-acr.yml up -d`
- After `up`, give the stack ~20 seconds to settle before exercising the UI (matches the README's expected start latency)

## Quality Standards
- Verify both app compose stacks (`dev.yml` and `acr.yml`) build/start cleanly before committing changes that touch images or compose files
- After dockerfile changes, rebuild locally (`docker compose -f dc-plc-datalink-rfc1006-dev.yml build`) and confirm the stack starts
- Do not commit Docker image tarballs or build artifacts
