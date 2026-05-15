# Feature Scope: DEV/PROD-Splitting via lokale Registry

**Status:** Scoped
**Created:** 2026-05-15
**Branch:** feat/dev-prod-split (geplant, von `feat/frontend-ci-rewrite` abzweigen)

## Summary
Trennung des Deployment-Workflows in DEV (lokal auf `192.168.0.121` über eine selbstgehostete Insecure-Docker-Registry) und PROD (bleibt ACR-basiert). Bedienung ausschließlich über `docker compose`; das vorhandene Makefile entfällt.

## Why
- Heute existieren zwei Compose-Stacks: `…-local.yml` (Build aus Source) und `…-acr.yml` (Pull aus Azure Container Registry). Der lokale Stack mischt „Bauen" und „Starten" in einem Schritt und verhält sich dadurch anders als der PROD-Pull-Flow.
- Ziel ist ein DEV-Loop, der näher am PROD-Verhalten liegt: ein Image wird gebaut, in eine Registry gepusht und von dort gestartet. Damit lassen sich Registry-/Tag-bezogene Fehler bereits in DEV finden.
- Der User möchte den Stack ohne Makefile-Wrapper direkt mit `docker compose` bedienen (klarere Sichtbarkeit der ablaufenden Befehle, weniger Indirektion).
- PROD ist aktuell noch nicht konkret zugewiesen (Server, Zugang, Pipeline-Trigger), bleibt daher bewusst außerhalb dieses Scopes.

## In Scope
- [ ] Neuer Compose-Stack `dc-registry-local.yml` mit `registry:2` auf `192.168.0.121:5000`, Daten in Named Volume
- [ ] Neuer Compose-Stack `dc-plc-datalink-rfc1006-dev.yml` für alle drei App-Services mit kombinierter `image:`-/`build:`-Definition; `image:` zeigt auf `192.168.0.121:5000/<service>:dev`
- [ ] Image-Tag-Strategie: ausschließlich `dev` (jeder Build überschreibt das Tag, keine SHA-/Timestamp-Suffixe)
- [ ] Workflow rein über `docker compose` (`build`, `push`, `pull`, `up -d --no-build`)
- [ ] Entfernen von `dc-plc-datalink-rfc1006-local.yml`
- [ ] Entfernen des `Makefile`
- [ ] README.md: DEV-Setup, Registry-Vorbereitung, neuer Workflow, Voraussetzung Insecure-Registry-Eintrag in `/etc/docker/daemon.json`
- [ ] CHANGELOG.md: Eintrag für Tooling-/Workflow-Wechsel
- [ ] Dokumentation der einmaligen Docker-Daemon-Konfiguration für die Insecure-Registry (als Setup-Schritt)

## Out of Scope
- PROD-Server, PROD-Pipeline-Anpassungen, PROD-Tag-Strategie — bleiben offen
- Änderungen an `dc-plc-datalink-rfc1006-acr.yml` (PROD-Compose bleibt unangetastet)
- TLS-Absicherung der lokalen Registry
- Authentifizierung an der lokalen Registry
- Hot-Reload-Volumes / Inner-Dev-Loop ohne Rebuild
- Anpassungen in `.github/workflows/` (CI ändert sich nicht; pusht weiter nach ACR aus master)
- Änderungen an `backend/`, `frontend/`, `database/`, Telegraf-Configs, Dockerfiles, OpenAPI

## Affected Areas
| Area | Touched? | Notes |
|---|---|---|
| `backend/src/routes.py` | no | — |
| `backend/src/plc_datalink_rfc1006_model.py` | no | — |
| `backend/src/services/*` | no | — |
| `backend/openapi/plc_datalink_rfc1006_api.yml` | no | — |
| `backend/config/dynamic_startup_telegraf.sh` | no | — |
| `frontend/src/app/` | no | — |
| `database/config/*` | no | — |
| CouchDB document schema | no | — |
| `dc-plc-datalink-rfc1006-local.yml` | **delete** | Wird durch `…-dev.yml` ersetzt |
| `dc-plc-datalink-rfc1006-dev.yml` | **new** | `image:` zeigt auf lokale Registry, `build:` aus Source |
| `dc-registry-local.yml` | **new** | `registry:2` mit Named Volume `plc-datalink-rfc1006-registry-data` |
| `dc-plc-datalink-rfc1006-acr.yml` | no | PROD-Stack bleibt unverändert |
| `**/dockerfile-*` | no | — |
| `Makefile` | **delete** | komplett entfernt |
| `.github/workflows/` | no | — |
| `README.md` | yes | neuer DEV-Workflow, Registry-Setup, Daemon-Konfiguration |
| `CHANGELOG.md` | yes | Eintrag „Tooling: docker-compose only, lokale Registry für DEV" |
| `.env.example` | maybe | ggf. Variable `LOCAL_REGISTRY=192.168.0.121:5000` einführen statt Hardcoding |

## Acceptance Criteria
- [ ] `docker compose -f dc-registry-local.yml up -d` startet die Registry, `curl http://192.168.0.121:5000/v2/_catalog` antwortet `{"repositories":[]}` beim Erststart
- [ ] `docker compose -f dc-plc-datalink-rfc1006-dev.yml build` baut alle drei App-Images mit Tag `dev` und referenziert sie unter `192.168.0.121:5000/plc-datalink-rfc1006-{database,backend,frontend}:dev`
- [ ] `docker compose -f dc-plc-datalink-rfc1006-dev.yml push` lädt die drei Images erfolgreich in die lokale Registry
- [ ] `docker compose -f dc-plc-datalink-rfc1006-dev.yml pull` zieht die drei Images aus der lokalen Registry erfolgreich (verifiziert nach `docker image prune` der lokalen Images)
- [ ] `docker compose -f dc-plc-datalink-rfc1006-dev.yml up -d --no-build` startet den Stack; die UI ist unter `http://192.168.0.121:80` erreichbar
- [ ] `dc-plc-datalink-rfc1006-local.yml` existiert nicht mehr im Repo
- [ ] `Makefile` existiert nicht mehr im Repo
- [ ] `README.md` enthält einen DEV-Abschnitt mit den vier `docker compose`-Schritten und einen Hinweis auf den Insecure-Registry-Eintrag in `/etc/docker/daemon.json`
- [ ] `CHANGELOG.md` führt den Wechsel auf den Compose-only-DEV-Workflow auf
- [ ] `dc-plc-datalink-rfc1006-acr.yml` ist im Diff unverändert

## Edge Cases & Constraints
- **Registry nicht erreichbar:** `up --no-build` schlägt fehl, falls weder lokale Images noch Registry-Connectivity vorhanden sind. Doku muss `up` der Registry als ersten Schritt nennen.
- **Insecure-Registry-Eintrag fehlt:** `push`/`pull` schlagen mit „http: server gave HTTP response to HTTPS client" fehl. README dokumentiert den Daemon-Eintrag und das nötige `systemctl restart docker`.
- **Registry-Volume voll:** Tag `dev` wird zwar überschrieben, aber alte Manifests bleiben (Layer-Akkumulation). Operations-Note: periodisches `registry garbage-collect` möglich, hier außerhalb des Scopes.
- **Server-IP-Wechsel:** Da die IP `192.168.0.121` in `image:`-Strings hardcodiert ist, würde ein IP-Wechsel das Setup brechen. Mitigation: optionale Env-Variable `LOCAL_REGISTRY` in `.env`, Default `192.168.0.121:5000`.
- **PLC-Connectivity nach Restart:** keine Änderung — Telegraf-Verhalten unverändert.
- **CouchDB-Daten:** Volume `plc-datalink-rfc1006-database-data` bleibt namens- und mount-gleich, bestehende Daten überleben den Wechsel.

## Breaking Changes & Migration
**Breaking für lokale Entwickler:**
- `dc-plc-datalink-rfc1006-local.yml` ist weg → Aufrufe wie `docker compose -f dc-plc-datalink-rfc1006-local.yml up` funktionieren nicht mehr.
- `make build`/`make up`/`make down`/`make logs`/`make ps`/`make clean` funktionieren nicht mehr (Makefile entfernt).
- `make lint`/`make format` entfallen ebenfalls — ersetzt durch direkte `ruff`-Aufrufe in `backend/`, dokumentiert in README.

**Migration:**
1. Einmalig: Registry-Eintrag in `/etc/docker/daemon.json` ergänzen und Docker-Dienst neu starten.
2. Einmalig: `docker compose -f dc-registry-local.yml up -d`.
3. Loop pro Iteration: `build` → `push` → `pull` → `up -d --no-build` (siehe README).

**Keine Breaking-Changes nach außen:**
- MQTT-Payload, REST-API, CouchDB-Schema, Telegraf-Pipeline: unverändert
- PROD-Pfad (ACR-Compose): unverändert

## Dependencies
- Docker Engine auf `192.168.0.121` mit Insecure-Registry-Eintrag (`/etc/docker/daemon.json`)
- Erreichbarkeit von `192.168.0.121:5000` für alle pullenden Hosts (vorerst nur der Server selbst)
- Keine neuen Python-/npm-Dependencies
- Architekturelle Entscheidung wird in einem nachgelagerten ADR (`/architecture`) festgehalten — voraussichtlich ADR-0005

---
<!-- Filled in by later skills -->

## Architecture Decisions
- [ADR-0005](../../../architecture/decisions/ADR-0005-local-insecure-registry-for-dev-image-flow.md) — Local Insecure Docker Registry for DEV Build-Push-Pull Loop (Accepted, 2026-05-15)

## QA Evidence
_Filled in by `/qa`_

## Operations Notes
_Filled in by `/operations` if operational behavior changes_
