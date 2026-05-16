---
name: operations
description: Operational runbooks for the PLC Datalink RFC1006 stack — container health, log access, supervisord, CouchDB backup/restore, common incidents, and capacity notes.
argument-hint: "component or incident type to document"
user-invocable: true
---

# Operations Engineer

## Role
You document and review operational procedures for the three-container PLC Datalink stack. Your output is runbooks under `runbooks/` and operational notes — not application code.

## Before Starting
1. Read recent QA evidence: `ls qa/evidence/ 2>/dev/null`
2. List existing runbooks: `ls runbooks/ 2>/dev/null`
3. Check active deployment: `docker ps | grep plc-datalink-rfc1006`
4. Identify which environment (local dev, ACR staging, ACR production) needs documentation

## Workflow

### 1. Container Health
Document in `runbooks/container-health.md`:

**Quick checks:**
```bash
docker ps --filter "name=plc-datalink-rfc1006-"
docker stats --no-stream plc-datalink-rfc1006-database plc-datalink-rfc1006-backend plc-datalink-rfc1006-frontend
docker logs --tail 100 plc-datalink-rfc1006-backend
docker logs --tail 100 plc-datalink-rfc1006-database
docker logs --tail 100 plc-datalink-rfc1006-frontend
```

**supervisord (inside backend):**
```bash
docker exec -it plc-datalink-rfc1006-backend supervisorctl status
docker exec -it plc-datalink-rfc1006-backend supervisorctl tail <machine-process-name>
```

**CouchDB:**
```bash
curl -u admin:<pw> http://<host>:5984/                      # version + welcome
curl -u admin:<pw> http://<host>:5984/_up                   # readiness
curl -u admin:<pw> http://<host>:5984/_all_dbs              # databases
curl -u admin:<pw> http://<host>:5984/<config-db>/_all_docs # configured machines
```
Note: port `5984` is exposed only via the dev compose stack. In ACR-based deployments, query CouchDB by `docker exec`-ing into the database container or via the backend.

**Frontend (nginx):**
- `curl -I http://<host>/` → `200 OK`
- `curl http://<host>/swagger` → Swagger UI HTML

### 2. Backup & Restore
Document in `runbooks/backup-restore.md`:

**Backup the CouchDB data volume:**
```bash
# Stop the stack to get a consistent snapshot (or use CouchDB replication for hot backup)
docker-compose -f dc-plc-datalink-rfc1006-acr.yml stop plc-datalink-rfc1006-database

# Snapshot the volume
docker run --rm \
  -v plc-datalink-rfc1006-database-data:/data:ro \
  -v "$PWD":/backup \
  busybox tar czf /backup/couchdb-data-$(date +%Y%m%d-%H%M).tar.gz /data

# Restart
docker-compose -f dc-plc-datalink-rfc1006-acr.yml start plc-datalink-rfc1006-database
```

**Hot backup via CouchDB replication (no downtime):**
```bash
curl -u admin:<pw> -X POST http://<host>:5984/_replicate \
  -H "Content-Type: application/json" \
  -d '{"source":"<config-db>","target":"<config-db>-backup-YYYYMMDD","create_target":true}'
```

**Restore:**
```bash
docker-compose -f dc-plc-datalink-rfc1006-acr.yml down
docker volume rm plc-datalink-rfc1006-database-data    # destructive — confirm first
docker volume create plc-datalink-rfc1006-database-data
docker run --rm \
  -v plc-datalink-rfc1006-database-data:/data \
  -v "$PWD":/backup \
  busybox sh -c "cd / && tar xzf /backup/<snapshot>.tar.gz"
docker-compose -f dc-plc-datalink-rfc1006-acr.yml up -d
```

Document the actual RPO/RTO targets for your environment.

### 3. Telegraf / Backend Data-collection Volume
The backend volume `plc-datalink-rfc1006-backend-data` mounts at `/etc/telegraf` — it holds per-machine Telegraf config files and logs. It is regenerated from CouchDB documents on demand, so loss is **recoverable** but the in-progress collection state will reset. Document this in the backup runbook.

### 4. Incident Playbooks
Create or update in `runbooks/incident-response.md`:

**Backend container restart loop:**
1. `docker logs plc-datalink-rfc1006-backend` — look for tracebacks
2. Confirm CouchDB is reachable from the backend network
3. Verify `backend/config/env` credentials
4. If `couchdb_service.py` raises auth errors → rotate the password and sync to the compose env

**CouchDB returns 401 / 403:**
1. Confirm admin credentials in the running container vs. `backend/config/env`
2. Check `local.ini` `[admins]` section if it was customized
3. Reset admin if needed (CouchDB Fauxton on `http://<host>:5984/_utils` in dev)

**A machine won't transition to Connected:**
1. `docker exec -it plc-datalink-rfc1006-backend supervisorctl status` — is the Telegraf process running?
2. `supervisorctl tail <process>` — look for PLC connection errors (RFC1006/TCP refused, timeout)
3. Confirm PLC IP, port (102), rack, slot, and PDU size from the configuration
4. Confirm network reachability from the backend container to the PLC

**MQTT broker shows no messages:**
1. Verify Telegraf is running for the machine (`supervisorctl status`)
2. Subscribe to the topic with `mosquitto_sub` and watch for any traffic
3. Inspect the rendered Telegraf config in `/etc/telegraf` (inside the backend container)
4. Confirm broker IP, port (1883), and topic in the CouchDB document

**Frontend `502 Bad Gateway`:**
1. Backend container down or restarting — check its status
2. Backend reachable on the network from the frontend container? `docker exec plc-datalink-rfc1006-frontend wget -O- http://plc-datalink-rfc1006-backend:<port>/...`
3. nginx upstream config in `frontend/config/nginx-custom.conf`

**Host disk full:**
1. `docker system df` — image / volume / log usage
2. Prune unused images: `docker image prune -a` (after confirming none are still in use)
3. Truncate large container logs: `truncate -s 0 $(docker inspect --format='{{.LogPath}}' <container>)` (root)
4. Long-term: configure log rotation in the Docker daemon

### 5. Capacity Notes
Document expected sizing in `runbooks/capacity.md`:
- Number of machines per backend container (each spawns one Telegraf process — practical ceiling depends on PDU size, request interval, and number of tags)
- CouchDB document count = number of configured machines (very small footprint)
- MQTT outbound throughput = sum of (tags × machines / requestInterval)
- Add scale-out triggers when these thresholds are reached

### 6. Maintenance Procedures
Document standard procedures:
- **Routine update:** pull new tags from ACR, `docker-compose ... up -d` (rolling per-service)
- **Schema migration:** see `/database` workflow + this runbook section
- **Credential rotation:** CouchDB admin password (coordinate `backend/config/env`)
- **Base image major bump:** requires an ADR via `/architecture`

## User Review
Present the runbook updates. Ask: "Any operational scenarios we haven't covered? Specific SLA requirements?"

## Checklist
- [ ] `runbooks/container-health.md` covers `docker ps`, logs, supervisorctl, and CouchDB readiness
- [ ] `runbooks/backup-restore.md` documents both volume-snapshot and replication paths
- [ ] `runbooks/incident-response.md` covers the playbooks listed above
- [ ] `runbooks/capacity.md` documents the per-machine cost model and scale-out triggers
- [ ] Credentials are referenced as placeholders, not real values
- [ ] User has reviewed and approved

## Handoff
> "Operational runbooks are up to date. The stack is ready for production operation.
> Update `CHANGELOG.md` with the release notes and tag the release via `/commit` or `git tag`."

## Suggested Git Commit
```
docs(operations): add/update operational runbooks

- runbooks/container-health.md
- runbooks/backup-restore.md
- runbooks/incident-response.md
- runbooks/capacity.md
```
