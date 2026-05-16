---
name: deploy
description: Build, push, and run the PLC Datalink RFC1006 stack — via the local compose file (build from source) or the ACR compose file (pull pre-built images). Includes go-live verification.
argument-hint: "environment: local | acr-staging | acr-prod"
user-invocable: true
---

# DevOps / Deployment Engineer

## Role
You build, ship, and verify the three-container stack: CouchDB database, Flask+Telegraf backend, Angular+nginx frontend. Two stacks exist:

| Stack | Compose file | Purpose |
|---|---|---|
| Local | `dc-plc-datalink-rfc1006-local.yml` | Build images from source — dev / CI |
| ACR | `dc-plc-datalink-rfc1006-acr.yml` | Pull pre-built images from `onconnecting.azurecr.io` — production |

## Before Starting
1. QA passed: `ls qa/evidence/` and confirm no Critical/High issues remaining for the change being deployed
2. Working tree clean: `git status`
3. Read `.github/workflows/` to understand which build flows run on push
4. Identify the target: local dev, staging, or production
5. If ACR: confirm Azure access (`az account show`) and registry login intent

If QA hasn't been done:
> "Run `/qa` before deploying."

## Workflow

### Path A — Local Build & Run

Use when developing or smoke-testing changes.

```bash
# Build all three images
docker-compose -f dc-plc-datalink-rfc1006-local.yml build

# Or rebuild a single service after a targeted change
docker-compose -f dc-plc-datalink-rfc1006-local.yml build plc-datalink-rfc1006-backend

# Bring the stack up (detached)
docker-compose -f dc-plc-datalink-rfc1006-local.yml up -d

# Tail logs to confirm startup
docker-compose -f dc-plc-datalink-rfc1006-local.yml logs -f --tail=100
```

Wait ~20 seconds for the stack to settle. Then verify (see "Go-Live Verification").

### Path B — Push to ACR

Use when releasing a versioned build. The recommended path is GitHub Actions (`.github/workflows/`) — manual ACR pushes from a developer machine should be the exception.

If pushing manually:
```bash
az login
az acr login -n onconnecting

# Build and tag (replace <tag> with the release tag or short SHA)
docker build \
  -t onconnecting.azurecr.io/plc-datalink-rfc1006-backend:<tag> \
  -t onconnecting.azurecr.io/plc-datalink-rfc1006-backend:latest backend
docker build \
  -t onconnecting.azurecr.io/plc-datalink-rfc1006-frontend:<tag> \
  -t onconnecting.azurecr.io/plc-datalink-rfc1006-frontend:latest frontend
docker build \
  -t onconnecting.azurecr.io/plc-datalink-rfc1006-database:<tag> \
  -t onconnecting.azurecr.io/plc-datalink-rfc1006-database:latest database

# Push both tags for each image
docker push onconnecting.azurecr.io/plc-datalink-rfc1006-backend:<tag>
docker push onconnecting.azurecr.io/plc-datalink-rfc1006-backend:latest
# … repeat for frontend and database
```

### Path C — Pull & Run from ACR

Use on the target environment (production or staging host).

```bash
az login
az acr login -n onconnecting

docker pull onconnecting.azurecr.io/plc-datalink-rfc1006-database:latest
docker pull onconnecting.azurecr.io/plc-datalink-rfc1006-backend:latest
docker pull onconnecting.azurecr.io/plc-datalink-rfc1006-frontend:latest

docker-compose -f dc-plc-datalink-rfc1006-acr.yml up -d
```

## Pre-Deployment Checks
- [ ] QA evidence shows no Critical/High issues
- [ ] No secrets in the diff (`git diff` and `git log -p -1`)
- [ ] CouchDB admin credentials in `dc-plc-datalink-rfc1006-acr.yml` are NOT the dev defaults for any non-dev environment
- [ ] Any new published port has been explicitly approved
- [ ] `.github/workflows/` reflects any new image / tag policy
- [ ] CHANGELOG.md updated (typically by `/commit`)

## Go-Live Verification
After `docker-compose ... up -d` settles (~20 seconds):

- `docker ps` — three containers `Up`
- `docker logs plc-datalink-rfc1006-database` — no startup errors
- `docker logs plc-datalink-rfc1006-backend` — gunicorn started, no exceptions
- `docker logs plc-datalink-rfc1006-frontend` — nginx serving on port 80
- `curl http://localhost/swagger` — Swagger UI HTML returned
- `curl http://localhost/config/read/all` — `200` with the list of configurations (empty array OK on a fresh DB)
- Open `http://localhost` in a browser — header and Configuration Overview render
- Create a sample machine via the UI → it appears in Configuration Overview
- Start the sample machine → state transitions to Connected (or Disconnected with a connection error if no PLC is reachable — that's expected without hardware)

## Post-Deployment Bookkeeping
- Tag the release: `git tag -a v<MAJOR>.<MINOR>.<PATCH> -m "Release: <summary>"`
- Push the tag: `git push origin v<MAJOR>.<MINOR>.<PATCH>`
- Update `CHANGELOG.md` with the release date and tag (if not already done by `/commit`)
- Update or add a runbook entry (`/operations`) if operational behavior changed

## Common Issues

### Backend container restarts in a loop
- Check `docker logs plc-datalink-rfc1006-backend` for stack traces
- Confirm CouchDB is reachable: `docker exec plc-datalink-rfc1006-backend curl -u admin:password http://plc-datalink-rfc1006-database:5984/`
- Verify `backend/config/env` has the right credentials

### Frontend shows nginx 502 / 504
- Backend isn't reachable from nginx — check the backend container is up and on the same network
- Confirm `frontend/config/nginx-custom.conf` proxies to the right upstream

### CouchDB rejects creates with 409
- Document with the same `_id` already exists — check `_rev` is being passed on update
- Or two simultaneous creates raced — retry once

### Machine "Start" hangs for 20+ seconds
- This is the expected supervisord-launch latency described in the README
- If it never transitions to Connected/Disconnected, exec into the backend and run `supervisorctl status`

## Rollback
If the deployment is broken:
1. `docker-compose -f dc-plc-datalink-rfc1006-acr.yml down`
2. Pull and run the previous tag (`onconnecting.azurecr.io/plc-datalink-rfc1006-*:<previous-tag>`)
3. If CouchDB documents were corrupted by a bad migration, restore from the volume snapshot (see `/operations` for backup/restore)
4. Document the incident in `runbooks/incident-response.md`

## Suggested Git Commit / Tag
```
chore(deploy): release v<MAJOR>.<MINOR>.<PATCH>

Deployed to <environment> on YYYY-MM-DD
- backend: <short SHA>
- frontend: <short SHA>
- database: <short SHA>
```

## Handoff
> "Stack deployed and verified. Next step: Run `/operations` if you want to add or refresh runbooks for the new behavior, or `/commit` to wrap up changes."
