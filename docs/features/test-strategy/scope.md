# Feature Scope: Vollständige Test-Strategie (Backend / Frontend / Database / E2E)

**Status:** Scoped
**Created:** 2026-05-15
**Branch:** `feat/e2e-zks-mqtt-test` (abgezweigt von `feat/frontend-ci-rewrite`; bleibt bewusst unter altem Namen)

## Summary
Aufbau einer durchgängigen, automatisierten Test-Basis für die drei Container der Anwendung — **Backend (pytest), Frontend (Jest), Database (pytest + CouchDB-Integration)** — plus ein **End-to-End-Lauf gegen die ZKS-Machine-Mock**. Die Skills `/03-backend`, `/04-frontend`, `/05-database` werden so erweitert, dass sie nach inhaltlichen Änderungen die jeweils passenden Tests laufen lassen; flankierende **PostToolUse-Hooks** in `.claude/settings.json` erzwingen den Lauf auch dann, wenn der Skill umgangen wird.

## Why
Aktueller Stand:
- **Backend:** pytest ist in `pyproject.toml` konfiguriert (`testpaths = ["test/scripts"]`), aber unter [backend/test/scripts/](../../../backend/test/scripts/) liegt nur ein loses Linux-Helper-Skript — keine echte Suite. [backend/test/curl/](../../../backend/test/curl/) sind manuelle Shell-Snippets ohne Asserts
- **Database:** Nur zwei manuelle Skripte (`couch-cmd.sh`, `devBoard1Rest.sh`) — kein Framework, keine Asserts
- **Frontend (Angular 19, greenfield per ADR-0003/0004):** **Kein Test-Framework konfiguriert.** Schematics sind sogar auf `skipTests: true` gestellt → neue Komponenten/Services entstehen ohne Spec
- **E2E:** Es gibt aktuell keinen automatisierten Lauf über die volle Strecke REST-API → CouchDB → supervisord/Telegraf → S7 → MQTT

Konsequenz: Bei jedem Code-Change muss manuell geprüft werden, ob OpenAPI, Telegraf-Rendering, CouchDB-Doc-Schema und MQTT-Payload noch zueinander passen. Mit der frisch dokumentierten [zks-machine-mock](../../machines-db-layout/zks-machine-mock/README.md) (vollständiger deterministischer S7-Server) ist erstmals eine realistische Testumgebung verfügbar — der richtige Moment, die Test-Basis sauber aufzusetzen.

## In Scope

### 1. Backend — Unit- & Service-Tests (pytest)
- [ ] Pfad `backend/test/scripts/` als pytest-Testpfad (bereits in `pyproject.toml`) beibehalten; Dateien `test_*.py`
- [ ] Model-Tests: Roundtrip `PlcDatalinkRFC1006Model.from_dict / to_dict`, Default-Werte (siehe [telegraf.md](../../../.claude/rules/telegraf.md))
- [ ] PLC-Address-Validation (alle Typen aus README: `X B C W DW I DI R DT S`)
- [ ] Service-Tests mit Mocks (z. B. `requests-mock` oder `unittest.mock`):
  - `couchdb_service.py` — Create/Read/Update/Delete + Fehlerpfade (404, 409)
  - `machine_configuration_service.py` — Telegraf-Config-Rendering: Snapshot-Vergleich gegen `backend/config/example-machines/`
  - `telegraf_service.py` — supervisord-Calls mit gemocktem `subprocess`
- [ ] Routen-Tests mit Flask-Test-Client + gemockten Services: jede Route → erwarteter Status-Code + JSON-Form
- [ ] Bestehende curl-Skripte unter `backend/test/curl/` bleiben als manuelle Smoke-Tools erhalten (kein Ersatz, keine Migration)

### 2. Frontend — Jest + jest-preset-angular
- [ ] Dev-Deps ergänzen: `jest`, `jest-preset-angular`, `@types/jest`, `jest-environment-jsdom`
- [ ] `jest.config.ts` + `setup-jest.ts` im Frontend-Root
- [ ] `package.json`-Script: `"test": "jest"` (sowie `test:watch`, `test:ci`)
- [ ] `angular.json`: `schematics.skipTests` für `@schematics/angular:component | directive | pipe` auf **`false`** drehen, damit neue Artefakte automatisch Specs bekommen
- [ ] Baseline-Specs:
  - `app.component.spec.ts` — Smoke (Rendering, Title)
  - Je ein Spec für vorhandene Komponenten unter [frontend/src/app/](../../../frontend/src/app/): `configuration-overview`, `create-configuration`, `header`, `plc-states`
  - Je ein Spec für jeden Service unter `services/` (HttpClient mit `provideHttpClientTesting`)
  - Je ein Spec für Validators unter `validators/` (PLC-Adress-Validierung)
- [ ] Coverage-Schwelle bewusst **nicht** verbindlich setzen (kein Coverage-Gate) — Ziel ist Baseline, nicht 100 %

### 3. Database — Integration-Tests (pytest + testcontainers)
- [ ] Neuer Pfad `database/test/python/` mit pytest-Suite (`test_*.py`)
- [ ] **Best-Practice-Stack:** `pytest` + `testcontainers[couchdb]` — der Test bootstrappt einen frischen CouchDB-Container pro Session via Fixture, kein zusätzliches `docker compose up` nötig. Vorteile gegenüber dem manuellen Compose-Setup: deterministischer Startzustand, automatische Aufräumarbeiten, Tests bleiben portabel
- [ ] `conftest.py` mit Session-Fixture für den Container und Function-Fixture für eine frische DB pro Test (Cleanup über DB-Drop)
- [ ] Tests gegen die **echte** CouchDB (kein In-Memory-Mock — der Wert liegt in der echten HTTP-Semantik):
  - Init-Skript [`init-db.sh`](../../../database/config/init-db.sh) legt erwartete Datenbanken an
  - Admin-Auth aus [`local.ini`](../../../database/config/local.ini) greift (negativer Test: Anfrage ohne Auth → 401)
  - Doc-Roundtrip (Create / Read / Update / Delete), `_rev`-Konflikt erzeugt 409
  - Bulk-Read über `_all_docs` liefert die erwarteten Doc-IDs
- [ ] Bestehende `couch-cmd.sh` / `devBoard1Rest.sh` bleiben als manuelle Tools erhalten

### 4. End-to-End — ZKS-Machine-Mock
_(unveränderter ursprünglicher Scope, jetzt eingebettet)_

- [x] Test-Compose-Stack: Backend + CouchDB + Mosquitto + ZKS-Mock — implementiert in [`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml); ZKS-Mock bleibt extern auf dem Host, erreichbar über `host.docker.internal:host-gateway`
- [x] Python-Runner [`backend/test/scripts/integration/test_e2e_zks_mqtt.py`](../../../backend/test/scripts/integration/test_e2e_zks_mqtt.py) (Pfad innerhalb des neuen `unit/` vs `integration/`-Splits)
- [x] Erstellt Konfiguration `zks-mock` per `POST /config/create` mit repräsentativem Tag-Subset (Tabelle unten, kanonische Quelle: [`zks_fixtures.py`](../../../backend/test/scripts/integration/zks_fixtures.py))
- [x] Prüft `GET /config/read/one`, startet via `GET /machine/start`, verifiziert `GET /machine/online`
- [x] Subscribe via `paho-mqtt`; Assert: Payload-Form (`name`, `tags.machine`, `fields.*`, `timestamp` ms), plausible Werte je Typ
- [x] Fehlerinjektion mit `python-snap7` direkt auf DB4 (`Cmd_InjectFault = "ERR_WELD_CURRENT_LOW"`) — prüft Auswirkung auf MQTT-Stream
- [x] Cleanup: stop + remove, idempotent (im `cleanup_machine`-Fixture proaktiv und reaktiv)

#### Repräsentativer ZKS-Tag-Subset
| DB | Offset | Backend-Adresse | Backend-Typ | Quelle |
|---|---|---|---|---|
| DB1 | 0 | `DB1.I0` | INT | Machine.State |
| DB1 | 4 | `DB1.DI4` | DINT | Machine.PartCounter |
| DB1 | 28 | `DB1.R28` | REAL | Machine.Yield |
| DB1 | 38 | `DB1.S38.20` | STRING | Machine.LastError |
| DB2 | 0 | `DB2.X0.0` | BOOL | Welds[0].Done |
| DB2 | 2 | `DB2.R2` | REAL | Welds[0].Current |
| DB3 | 4 | `DB3.R4` | REAL | Test.TotalResistance |
| DB3 | 8 | `DB3.I8` | INT | Test.Result |
| DB4 | 0 | `DB4.S0.32` | STRING | Part.Serial |

> Adress-Syntax beim `/03-backend`-Schritt gegen [README.md](../../../README.md#plc-address-specification) verifizieren — insbesondere String-Format `S<offset>.<max>` (Byte-Offset des Strings im DB, gefolgt von der maximalen Stringlänge; siehe README-Beispiel `DB2000.S30.13`).

### 5. Skill-Integration — Tests nach Änderungen erzwingen
- [ ] `/03-backend` SKILL.md: ergänze finalen Schritt „Run `cd backend && pytest -q` after edits and report result"
- [ ] `/04-frontend` SKILL.md: ergänze „Run `cd frontend && npm test -- --watchAll=false` after edits"
- [ ] `/05-database` SKILL.md: ergänze „Run `cd database && pytest -q test/python` after edits"
- [ ] `/06-qa` SKILL.md: erwähnt den E2E-Test als Bestandteil der QA-Pflicht
- [ ] `.claude/settings.json`: **PostToolUse-Hooks** für `Edit`/`Write` mit Pfad-Match:
  - `backend/src/**` → pytest backend
  - `frontend/src/**` → npm test frontend
  - `database/config/**` → pytest database
- [ ] Hook-Befehle sind kurz (Exit-Code-only), keine ausführliche Ausgabe; bei Fehler bricht der Tool-Aufruf nicht ab, sondern flaggt das Ergebnis
- [ ] Permissions in `.claude/settings.json` werden für `pytest` ergänzt (bereits da: `Bash(npm test:*)`, `Bash(ng test:*)`)

## Out of Scope
- Frontend-E2E-Test (Cypress/Playwright) — kein UI-Klick-Test in diesem Scope
- Visual-Regression / Screenshot-Tests
- Coverage-Gates oder Mutation-Testing
- CI-Integration der Tests in `.github/workflows/` — folgt in eigenem Scope, sobald Tests lokal grün sind
- Lasttest, Durchsatzmessung, Stress
- TLS/Auth-Härtung für MQTT (Default bleibt Port 1883 ungesichert; siehe [telegraf.md](../../../.claude/rules/telegraf.md))
- Schreibpfad **Anwendung → PLC** (existiert in der Codebasis nicht)
- Migration der bestehenden Bash-Skripte unter `backend/test/curl/` und `database/test/`

## Affected Areas
| Area | Touched? | Notes |
|---|---|---|
| `backend/src/*` | no | Produktionscode bleibt; Tests werden ergänzt |
| `backend/test/scripts/` | **yes** | pytest-Suite (unit, service, route, e2e) |
| `backend/pyproject.toml` | **yes** | Dev-Deps: `pytest-mock`, `requests-mock`, `paho-mqtt`, `python-snap7`; ggf. `testcontainers` für DB |
| `backend/openapi/*` | no | — |
| `backend/config/example-machines/` | no | dient als Snapshot-Referenz für Render-Test |
| `frontend/jest.config.ts`, `setup-jest.ts` | **yes (neu)** | Jest-Konfig |
| `frontend/package.json` | **yes** | Dev-Deps + `test`-Scripts |
| `frontend/angular.json` | **yes** | `skipTests: false` für Component/Directive/Pipe-Schematics |
| `frontend/src/**/*.spec.ts` | **yes (neu)** | Baseline-Specs für AppComponent, Komponenten, Services, Validators |
| `frontend/tsconfig.spec.json` | **yes (neu)** | TS-Config für Tests (`types: ["jest"]`) |
| `database/test/python/` | **yes (neu)** | pytest-Integrations-Tests gegen CouchDB |
| `database/test/conftest.py` | **yes (neu)** | Fixtures, ggf. via `testcontainers` |
| `database/config/*` | no | — |
| `dc-plc-datalink-rfc1006-{acr,dev}.yml` | no | Produktions-Compose unberührt |
| `dc-plc-datalink-rfc1006-e2e.yml` (neu) | **yes** | Test-Compose-Stack (Backend + CouchDB + Mosquitto, ZKS-Mock extern) |
| `**/Dockerfile` (canonical) | no | bestehende Images werden im Test-Compose nur konsumiert |
| CouchDB Doc-Schema | no | — |
| `.claude/skills/03-backend/SKILL.md` | **yes** | Test-Schritt am Ende |
| `.claude/skills/04-frontend/SKILL.md` | **yes** | Test-Schritt am Ende |
| `.claude/skills/05-database/SKILL.md` | **yes** | Test-Schritt am Ende |
| `.claude/skills/06-qa/SKILL.md` | **yes (light)** | E2E referenzieren |
| `.claude/settings.json` | **yes** | PostToolUse-Hooks + Permissions für pytest |
| `.github/workflows/` | no | folgt separat |
| `README.md` | **yes (light)** | Verweis auf Test-Setup pro Layer |
| `CHANGELOG.md` | **yes** (am Ende) | Eintrag für die Test-Basis |

## Acceptance Criteria

### Backend
- [ ] `cd backend && pytest -q` läuft grün, ≥ 1 Test je Service (`couchdb_service`, `machine_configuration_service`, `telegraf_service`)
- [ ] Model-Roundtrip-Test deckt alle Datentypen aus [telegraf.md](../../../.claude/rules/telegraf.md) ab
- [ ] Mindestens 80 % der Routen aus [routes.py](../../../backend/src/routes.py) haben einen Happy-Path-Test mit Flask-Test-Client

### Frontend
- [ ] `cd frontend && npm test -- --watchAll=false` läuft grün
- [ ] AppComponent-Smoke-Test besteht
- [ ] Mindestens je 1 Spec für `configuration-overview`, `create-configuration`, `header`, `plc-states`
- [ ] Mindestens je 1 Spec für jeden Service unter `frontend/src/app/services/`
- [ ] Mindestens je 1 Spec für jeden Validator unter `frontend/src/app/validators/`
- [ ] `ng generate component foo` erzeugt ohne weitere Flags ein `foo.component.spec.ts`

### Database
- [ ] `cd database && pytest -q test/python` läuft grün gegen einen lokal gestarteten CouchDB-Container
- [ ] Init-Test: erwartete Datenbanken existieren nach `init-db.sh`
- [ ] Doc-Roundtrip-Test besteht; `_rev`-Konflikt liefert 409

### E2E
- [ ] `pytest backend/test/scripts/test_e2e_zks.py` mit hochgefahrenem Test-Stack läuft grün
- [ ] Innerhalb ≤ 15 s erscheinen MQTT-Nachrichten je definiertem Tag
- [ ] Fehlerinjektion `ERR_WELD_CURRENT_LOW` zeigt Effekt im MQTT-Stream innerhalb ≤ 30 s
- [ ] Test räumt nach Erfolg **und** Fehler sauber auf

### Skill-Integration
- [ ] Nach Edit/Write unter `backend/src/**` werden Backend-Tests vom Hook ausgelöst; Skill `/03-backend` weist Claude an, das Ergebnis im Chat zu reporten
- [ ] Analog für Frontend (`frontend/src/**`) und Database (`database/config/**`)
- [ ] Hook-Lauf scheitert nicht still — Fehlerstatus erscheint im Toolresult

## Edge Cases & Constraints
- **CouchDB-Tests starten ihren Container selbst** über `testcontainers[couchdb]`; auf der Entwicklermaschine muss Docker laufen (Standard-Voraussetzung). CI-Anpassung folgt im separaten CI-Scope
- **ZKS-Mock externer Stack:** der Mock ist eigenständig (`make up` in seinem Repo). E2E-Test prüft Erreichbarkeit vor Start; bei nicht-erreichbarem Mock skippen, nicht failen (pytest `pytest.skip(...)`)
- **Telegraf-Render-Snapshot:** kleinste Whitespace-Änderung im Rendering bricht den Test — Snapshot wird einmalig generiert und committed; Updates über `pytest --snapshot-update` (oder eigene Logik)
- **Jest + Angular Zone:** `jest-preset-angular` benötigt `zone.js/testing` in `setup-jest.ts`
- **Hook-Performance:** PostToolUse-Hooks dürfen nicht länger als ~3 s laufen, sonst wird das Arbeiten zäh — pytest-Aufruf auf das jeweils geänderte Modul fokussieren (`pytest <path>`), nicht volle Suite
- **Permissions:** `.claude/settings.json` muss `Bash(pytest:*)` und `Bash(cd backend && pytest:*)` zulassen — aktuell noch nicht enthalten

## Branch
- Aktueller Branch ist `feat/e2e-zks-mqtt-test` (abgezweigt von `feat/frontend-ci-rewrite`)
- Wird **nicht** umbenannt, obwohl der Scope breiter geworden ist — Entscheidung des Users am 2026-05-15

## Breaking Changes & Migration
Keine — rein additiv. Keine API-, MQTT- oder DB-Schema-Änderungen. Bestehende Shell-Skripte bleiben.

## Dependencies
**Backend (Python, Dev):**
- `pytest` (bereits in optional-dependencies dev) — `pytest-mock`, `requests-mock`
- `paho-mqtt` (MQTT-Subscribe im E2E)
- `python-snap7` (Fehlerinjektion ZKS)
- optional: `testcontainers[couchdb]` (Database-Tests)

**Frontend (Node, Dev):**
- `jest`, `jest-preset-angular`, `@types/jest`, `jest-environment-jsdom`

**Test-Stack:**
- `eclipse-mosquitto:2`
- `couchdb:3` (bereits vorhanden)
- ZKS-Mock-Images (externer Stack)

**Keine Bezüge zu** [frontend-ci-rewrite](../frontend-ci-rewrite/scope.md) (Build-Pipeline-Umbau) und [dev-prod-split](../dev-prod-split/scope.md) (Compose-Aufteilung) — kann unabhängig umgesetzt werden.

---
<!-- Filled in by later skills -->

## Architecture Decisions
- [ADR-0006: Jest as the Test Framework for the Angular 19 Frontend](../../../architecture/decisions/ADR-0006-jest-for-frontend-tests.md)
- [ADR-0007: PostToolUse Hooks Trigger Layer-Specific Tests After Edits](../../../architecture/decisions/ADR-0007-post-tool-use-hooks-test-auto-run.md)
- [ADR-0008: testcontainers[couchdb] for Database Integration Tests](../../../architecture/decisions/ADR-0008-testcontainers-couchdb-integration-tests.md)

## QA Evidence
_Wird durch `/06-qa` ergänzt._

## Operations Notes
_Nicht relevant — keine Betriebsänderung. Test-Stack ist Dev-only._
