# Feature Scope: Vollständige Test-Strategie — Unit-Tests pro Layer + Integration-Tests gegen ZKS-Machine-Mock

**Status:** In Progress — Phase 1 (Suiten Backend/Frontend/Database/E2E) implementiert auf `master`; Phase 2 (Skill-Integration, Hooks, Verifikation, Doku) läuft auf `feat/test-strategy-finish`
**Created:** 2026-05-15
**Updated:** 2026-05-16
**Branch:** `feat/test-strategy-finish` (Abschluss-Sprint, abgezweigt von `master` am 2026-05-16). Phase 1 lief auf `feat/e2e-zks-mqtt-test` und ist via Commits `3426b48`, `ddef690`, `8f56d0f` u. a. nach `master` gelangt.

## Summary
Aufbau einer zweistufigen, automatisierten Test-Basis:

1. **Unit-Tests pro Layer** — isoliert, schnell, ohne externe Anlage:
   - **Backend:** pytest mit gemockten Services (CouchDB-/Subprocess-/HTTP-Mocks) und Flask-Test-Client
   - **Frontend:** Jest + jest-preset-angular mit `HttpTestingController`/`ComponentFixture`
   - **Database:** pytest + `testcontainers[couchdb]` — startet ein frisches CouchDB-Image pro Test-Session; bewusst kein In-Memory-Mock, weil die echte HTTP-Semantik der Punkt ist (für die Zwecke dieses Scopes zählen wir das als Unit-Ebene: kein externes System, kein laufender App-Stack)

2. **Integration-Tests gegen die [ZKS Machine Mock](../../machines-db-layout/zks-machine-mock/README.md)** — vollständiger Pfad REST-API → CouchDB → supervisord/Telegraf → S7/RFC1006 (`localhost:102`) → MQTT (`mosquitto:1883`). Der Mock ist ein eigenständiger Docker-Stack (Node-RED + Snap7-S7-Server) mit deterministischem Schweiß-, Prüf- und Fehlerverhalten — siehe README dort

Die Skills `/03-backend`, `/04-frontend`, `/05-database` werden so erweitert, dass sie nach inhaltlichen Änderungen die jeweiligen Unit-Tests laufen lassen; `/06-qa` deckt die Integration-Tests ab. Flankierende **PostToolUse-Hooks** in `.claude/settings.json` erzwingen den Unit-Test-Lauf auch dann, wenn der Skill umgangen wird.

## Why
Aktueller Stand:
- **Backend:** pytest ist in `pyproject.toml` konfiguriert (`testpaths = ["test/scripts"]`), aber unter [backend/test/scripts/](../../../backend/test/scripts/) liegt nur ein loses Linux-Helper-Skript — keine echte Suite. [backend/test/curl/](../../../backend/test/curl/) sind manuelle Shell-Snippets ohne Asserts
- **Database:** Nur zwei manuelle Skripte (`couch-cmd.sh`, `devBoard1Rest.sh`) — kein Framework, keine Asserts
- **Frontend (Angular 19, greenfield per ADR-0003/0004):** **Kein Test-Framework konfiguriert.** Schematics sind sogar auf `skipTests: true` gestellt → neue Komponenten/Services entstehen ohne Spec
- **E2E:** Es gibt aktuell keinen automatisierten Lauf über die volle Strecke REST-API → CouchDB → supervisord/Telegraf → S7 → MQTT

Konsequenz: Bei jedem Code-Change muss manuell geprüft werden, ob OpenAPI, Telegraf-Rendering, CouchDB-Doc-Schema und MQTT-Payload noch zueinander passen. Mit der frisch dokumentierten [zks-machine-mock](../../machines-db-layout/zks-machine-mock/README.md) (vollständiger deterministischer S7-Server) ist erstmals eine realistische Testumgebung verfügbar — der richtige Moment, die Test-Basis sauber aufzusetzen.

## Ist-Zustand (2026-05-16, Beginn `feat/test-strategy-finish`)

**Phase 1 — strukturell umgesetzt, Verifikation steht aus.**
Die Code-Tree-Ordner `unit/` und `integration/` pro Layer wurden in Phase 1 angelegt — sie spiegeln nicht 1:1 die hier verwendete Taxonomie wider (siehe Tabelle):

| Layer | Code-Pfad | Taxonomie laut Scope | Anmerkung |
|---|---|---|---|
| Backend | `backend/test/scripts/unit/` (5 Files: model, routes, couchdb_service, machine_configuration_service, telegraf_service) + Snapshot `snapshots/sample_machine.conf` | **Unit** | passt |
| Backend | `backend/test/scripts/integration/test_e2e_zks_mqtt.py`, `test_zks_telegraf_render.py`, `test_couchdb_zks_roundtrip.py`, `test_zks_s7_smoke.py`, `zks_fixtures.py`, `mosquitto.conf` | **Integration (ZKS)** | passt |
| Frontend | `frontend/test/unit/` (9 Specs: app, configuration-overview, create-configuration, header, plc-states, machine.service, config.service, plc-validators, error-message) — Config: [`jest.config.js`](../../../frontend/jest.config.js), `setup-jest.ts`, `tsconfig.spec.json` | **Unit** | passt |
| Frontend | `frontend/test/integration/machine.service.int.spec.ts`, `config.service.int.spec.ts` — Config: [`jest.config.int.js`](../../../frontend/jest.config.int.js) | **Unit** (HttpClient gegen `HttpTestingController`, kein lebendes Backend) | Pfadname trügerisch — bleibt aus pragmatischen Gründen erstmal so |
| Database | `database/test/python/unit/` (4 Files: local_ini, zks_layout, init_db_script, dockerfile) | **Unit** | passt |
| Database | `database/test/python/integration/test_couchdb_bootstrap.py`, `test_zks_machine_doc_crud.py` (via `testcontainers[couchdb]`) | **Unit** (laut neuer Taxonomie — kein externes System, isoliertes Container-Bootstrapping) | Pfadname trügerisch — Umbenennung in Phase 2 optional |
| Compose | [`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml), [`dc-plc-datalink-rfc1006-test.yml`](../../../dc-plc-datalink-rfc1006-test.yml) | Integration-Stack bzw. kanonischer Test-Einstieg | implementiert |

ADRs flankierend erfasst: [ADR-0006](../../../architecture/decisions/ADR-0006-jest-for-frontend-tests.md), [ADR-0007](../../../architecture/decisions/ADR-0007-post-tool-use-hooks-test-auto-run.md), [ADR-0008](../../../architecture/decisions/ADR-0008-testcontainers-couchdb-integration-tests.md). `.claude/settings.json` enthält bereits Permissions für `pytest`, `npm test`, `ng test`, `docker compose`.

**Phase 2 — offen (dieser Sprint):**
1. Skill-Integration: `/04-frontend` und `/06-qa` `SKILL.md` ergänzen (`/03-backend` und `/05-database` referenzieren pytest bereits). Final-Step-Wording vereinheitlichen.
2. PostToolUse-Hooks in `.claude/settings.json` mit Pfad-Match (`backend/src/**`, `frontend/src/**`, `database/config/**`). Müssen **im Container** laufen, nicht im lokalen venv ([siehe Memory: Tests laufen im Container](../../../.claude/projects/-home-ofitz-plc-datalink-rfc1006/memory/feedback-tests-in-container.md)).
3. Verifikation aller Acceptance Criteria (alle Unit-Suiten grün im Container via [`dc-plc-datalink-rfc1006-test.yml`](../../../dc-plc-datalink-rfc1006-test.yml); Integration-Suite grün gegen einen laufenden [ZKS-Mock](../../machines-db-layout/zks-machine-mock/README.md)).
4. `angular.json`: `schematics.skipTests` auf `false` prüfen/drehen.
5. `README.md`: Verweis auf Test-Setup pro Layer + ZKS-Mock-Voraussetzung für Integration-Lauf.
6. `CHANGELOG.md`: Eintrag für die fertige Test-Basis (am Ende, via `/99-commit`).
7. **Offen zur Diskussion:** Ordner-Umbenennung in `frontend/test/integration/` → `frontend/test/unit-http/` (oder ähnlich) und `database/test/python/integration/` → `…/container/`, damit der Tree die Taxonomie spiegelt. Default: nicht umbenennen, um Diff klein zu halten.

## In Scope

### 1. Backend — Unit-Tests (pytest)
- [x] Pfad `backend/test/scripts/` als pytest-Testpfad (bereits in `pyproject.toml`) beibehalten; Dateien `test_*.py`
- [x] Model-Tests: Roundtrip `PlcDatalinkRFC1006Model.from_dict / to_dict`, Default-Werte (siehe [telegraf.md](../../../.claude/rules/telegraf.md))
- [x] PLC-Address-Validation (alle Typen aus README: `X B C W DW I DI R DT S`) — Abdeckung im Verifikationsschritt prüfen
- [x] Service-Tests mit Mocks (z. B. `requests-mock` oder `unittest.mock`):
  - `couchdb_service.py` — Create/Read/Update/Delete + Fehlerpfade (404, 409)
  - `machine_configuration_service.py` — Telegraf-Config-Rendering: Snapshot-Vergleich gegen `backend/config/example-machines/`
  - `telegraf_service.py` — supervisord-Calls mit gemocktem `subprocess`
- [x] Routen-Tests mit Flask-Test-Client + gemockten Services: jede Route → erwarteter Status-Code + JSON-Form
- [x] Bestehende curl-Skripte unter `backend/test/curl/` bleiben als manuelle Smoke-Tools erhalten (kein Ersatz, keine Migration)

### 2. Frontend — Unit-Tests (Jest + jest-preset-angular)
- [x] Dev-Deps ergänzen: `jest`, `jest-preset-angular`, `@types/jest`, `jest-environment-jsdom`
- [x] `jest.config.{js,int.js}` + `setup-jest.ts` im Frontend-Root (Unit/Integration-Split statt einer `.ts`-Datei — Divergenz vom Scope, von User akzeptiert)
- [x] `package.json`-Script: `"test": "jest"` (sowie `test:watch`, `test:ci`) — im Verifikationsschritt prüfen
- [ ] `angular.json`: `schematics.skipTests` für `@schematics/angular:component | directive | pipe` auf **`false`** drehen, damit neue Artefakte automatisch Specs bekommen
- [x] Baseline-Specs:
  - `app.component.spec.ts` — Smoke (Rendering, Title)
  - Je ein Spec für vorhandene Komponenten unter [frontend/src/app/](../../../frontend/src/app/): `configuration-overview`, `create-configuration`, `header`, `plc-states`
  - Je ein Spec für jeden Service unter `services/` (HttpClient mit `provideHttpClientTesting`) — `machine.service`, `config.service`
  - Je ein Spec für Validators unter `validators/` (PLC-Adress-Validierung) — `plc-validators`, `error-message`
- [x] Coverage-Schwelle bewusst **nicht** verbindlich setzen (kein Coverage-Gate) — Ziel ist Baseline, nicht 100 %

### 3. Database — Unit-Tests (pytest + testcontainers)
_Hinweis: Der `testcontainers`-Ansatz wird hier als Unit-Ebene gewertet (isoliert, kein lebendes App-Stack-Setup, kein externes System) — abgrenzend zu Section 4, die gegen die laufende ZKS-Mock testet. Die ADR-0008-Begründung bleibt unverändert._

- [x] Neuer Pfad `database/test/python/` mit pytest-Suite (`test_*.py`)
- [x] **Best-Practice-Stack:** `pytest` + `testcontainers[couchdb]` — der Test bootstrappt einen frischen CouchDB-Container pro Session via Fixture, kein zusätzliches `docker compose up` nötig. Vorteile gegenüber dem manuellen Compose-Setup: deterministischer Startzustand, automatische Aufräumarbeiten, Tests bleiben portabel
- [x] `conftest.py` mit Session-Fixture für den Container und Function-Fixture für eine frische DB pro Test (Cleanup über DB-Drop)
- [x] Tests gegen die **echte** CouchDB (kein In-Memory-Mock — der Wert liegt in der echten HTTP-Semantik):
  - Init-Skript [`init-db.sh`](../../../database/config/init-db.sh) legt erwartete Datenbanken an — `test_couchdb_bootstrap.py`
  - Admin-Auth aus [`local.ini`](../../../database/config/local.ini) greift (negativer Test: Anfrage ohne Auth → 401) — im Verifikationsschritt prüfen
  - Doc-Roundtrip (Create / Read / Update / Delete), `_rev`-Konflikt erzeugt 409 — `test_zks_machine_doc_crud.py`
  - Bulk-Read über `_all_docs` liefert die erwarteten Doc-IDs — im Verifikationsschritt prüfen
- [x] Bestehende `couch-cmd.sh` / `devBoard1Rest.sh` bleiben als manuelle Tools erhalten

### 4. Integration-Tests — ZKS Machine Mock
_Ziel: durchgängiger Pfad **REST-API → CouchDB → supervisord/Telegraf → S7/RFC1006 → MQTT** mit der laufenden [ZKS Machine Mock](../../machines-db-layout/zks-machine-mock/README.md) als realistischer S7-Gegenstelle._

**Voraussetzungen zur Laufzeit:**
- ZKS-Mock-Stack läuft (im ZKS-Repo: `make up`); S7-Port `102` (bzw. `1102` ohne Root), OPC UA `4840`, Dashboard `1880` erreichbar
- Backend + CouchDB + Mosquitto starten via [`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml); ZKS-Mock bleibt extern auf dem Host, erreichbar über `host.docker.internal:host-gateway`
- ZKS-Mock im Default-Zustand `IDLE`; Test setzt `Cmd_Start` (DB4 Bit 68.1) per `python-snap7` und beendet sauber wieder

**Implementierungsstand (alles bereits umgesetzt in Phase 1):**
- [x] Test-Compose-Stack [`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml) — Backend + CouchDB + Mosquitto; ZKS-Mock extern
- [x] Python-Runner [`backend/test/scripts/integration/test_e2e_zks_mqtt.py`](../../../backend/test/scripts/integration/test_e2e_zks_mqtt.py)
- [x] Erstellt Konfiguration `zks-mock` per `POST /config/create` mit repräsentativem Tag-Subset (Tabelle unten, kanonische Quelle: [`zks_fixtures.py`](../../../backend/test/scripts/integration/zks_fixtures.py))
- [x] Prüft `GET /config/read/one`, startet via `GET /machine/start`, verifiziert `GET /machine/online`
- [x] Subscribe via `paho-mqtt`; Assert: Payload-Form (`name`, `tags.machine`, `fields.*`, `timestamp` ms), plausible Werte je Typ
- [x] Fehlerinjektion mit `python-snap7` direkt auf DB4 (`Cmd_InjectFault = "ERR_WELD_CURRENT_LOW"`) — prüft Auswirkung auf MQTT-Stream
- [x] Cleanup: stop + remove, idempotent (im `cleanup_machine`-Fixture proaktiv und reaktiv)

**Verifikations-Ergänzungen (Phase 2) — Snapshot-Vergleich (von User definiert 2026-05-16):**
- [ ] Test-Sequenz im einzigen E2E-Test:
  1. Initial-Snapshot von DB1 lesen (`Machine.State`, `PartCounter`, `OkCounter`, `NokCounter`, `ScrapCounter`, `ReworkCounter`, `Throughput`, `Yield`, `Uptime`) — diagnostische Baseline
  2. `Cmd_Stop` (DB4 Bit 68.2) pulsen, ~3 s warten, KPI-Snapshot lesen
  3. `Cmd_CycleSpeedFactor = 5.0` (REAL @ DB4 92), `Cmd_Start` (Bit 68.1) pulsen
  4. 30 s warten (~9 Teile bei 5×)
  5. KPI-Snapshot lesen
  6. **Pass-Bedingung:** `Machine.State` **und** mindestens eine KPI haben sich zwischen Snapshot 2 und 5 geändert
  7. MQTT-Stream lebt nachweislich noch (mindestens eine zusätzliche Nachricht nach dem Run)
- [ ] Skip-Pfad: ZKS-Mock nicht erreichbar (TCP-Check auf `host.docker.internal:102`) → `pytest.skip(...)` statt Fail (bereits via `zks_endpoint`-Fixture)
- [ ] Cleanup idempotent (stop + remove, im `cleanup_machine`-Fixture proaktiv und reaktiv) — bereits umgesetzt

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

### 5. Skill-Integration — Test-Auslösung (zweistufige Policy)

**Policy:**

| Wann | Was läuft | Wer triggert |
|---|---|---|
| Nach **jeder Änderung an Code oder Config** (Edit/Write unter `backend/src/**`, `backend/config/**`, `frontend/src/**`, `database/config/**`) | **Unit-Tests** des jeweiligen Layers | PostToolUse-Hook in [`.claude/settings.json`](../../../.claude/settings.json) **und** finaler Schritt in `/03-backend`, `/04-frontend`, `/05-database` SKILL.md (Belt-and-Suspenders) |
| Sobald ein **Requirement vollständig umgesetzt** ist (alle Acceptance Criteria eines `docs/features/<name>/scope.md` abgehakt) | **Integration-Test gegen ZKS-Mock** (Section 4), zusätzlich zur Unit-Suite des betroffenen Layers | Skill-Final-Step im jeweiligen Implementations-Skill (`/03-backend`, `/04-frontend`, `/05-database`) und in `/06-qa`. **Nicht** über Hook — Hook würde nach jeder Bearbeitung den vollen Integration-Lauf starten (>30 s + ZKS-Mock-Start) und das Arbeiten zäh machen |

**Konkrete Umsetzung:**
- [~] `/03-backend` SKILL.md: finaler Schritt erweitern auf zweistufig — (a) immer `cd backend && pytest -q test/scripts/unit` nach Edits; (b) bei Requirement-Abschluss zusätzlich `pytest -q test/scripts/integration` mit Hinweis, dass ZKS-Mock laufen muss. Datei erwähnt pytest bereits — Wortlaut/Position prüfen
- [ ] `/04-frontend` SKILL.md: ergänze (a) `cd frontend && npm test -- --watchAll=false` nach Edits; (b) bei Requirement-Abschluss zusätzlich Integration-Lauf delegieren („→ `/06-qa` triggern für ZKS-Integration")
- [~] `/05-database` SKILL.md: ergänze (a) `cd database && pytest -q test/python/unit` nach Edits; (b) bei Schema-/Init-Änderungen zusätzlich `…/integration` (testcontainers) **und** Hinweis auf `/06-qa` für End-to-End-Pfad. Datei erwähnt pytest bereits — Wortlaut/Position prüfen
- [ ] `/06-qa` SKILL.md: nimmt den Integration-Lauf gegen ZKS verbindlich auf (Voraussetzung-Check für ZKS-Mock auf `host.docker.internal:102`, danach `pytest -q backend/test/scripts/integration`)
- [ ] `.claude/settings.json`: **PostToolUse-Hooks** für `Edit`/`Write` mit Pfad-Match — nur Unit-Suite, nicht Integration:
  - `backend/src/**` oder `backend/config/**` → `cd backend && pytest -q test/scripts/unit` (im Container, nicht im venv — siehe Memory `feedback-tests-in-container`)
  - `frontend/src/**` → `cd frontend && npm test -- --watchAll=false` (im Container)
  - `database/config/**` → `cd database && pytest -q test/python/unit` (im Container)
- [ ] Hook-Befehle sind kurz (Exit-Code-only), keine ausführliche Ausgabe; bei Fehler bricht der Tool-Aufruf nicht ab, sondern flaggt das Ergebnis
- [x] Permissions in `.claude/settings.json` werden für `pytest` ergänzt (bereits da: `Bash(npm test:*)`, `Bash(ng test:*)`, `Bash(pytest:*)`, `Bash(cd backend && pytest:*)`, `Bash(cd frontend && npm test:*)`, `Bash(cd database && pytest:*)`)

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

### Integration (ZKS Machine Mock)
- [ ] `pytest -q backend/test/scripts/integration` läuft grün mit hochgefahrenem Test-Stack ([`dc-plc-datalink-rfc1006-e2e.yml`](../../../dc-plc-datalink-rfc1006-e2e.yml)) und laufendem [ZKS-Mock](../../machines-db-layout/zks-machine-mock/README.md)
- [ ] Innerhalb ≤ 15 s erscheinen MQTT-Nachrichten zum konfigurierten Topic (Payload-Form: `name`, `tags.machine`, `fields.*`, `timestamp` in ms)
- [ ] Snapshot-Sequenz erfolgreich: `Cmd_Stop` → KPI-Snapshot A → `Cmd_CycleSpeedFactor=5.0` + `Cmd_Start` → 30 s warten → KPI-Snapshot B
- [ ] `Machine.State` (DB1 INT@0) hat zwischen Snapshot A und B gewechselt
- [ ] Mindestens eine KPI (`PartCounter`, `OkCounter`, `NokCounter`, `ScrapCounter`, `ReworkCounter`, `Throughput`, `Yield`, `Uptime`) hat zwischen A und B einen anderen Wert
- [ ] MQTT-Stream lebt nachweislich noch nach dem 30-s-Run (mindestens eine weitere Nachricht)
- [ ] ZKS-Mock nicht erreichbar → `pytest.skip(...)` statt Fail (verifiziert 2026-05-16 ohne ZKS-Mock: 7 skipped, 0 failed)
- [ ] Test räumt nach Erfolg **und** Fehler sauber auf (stop + remove, idempotent)

### Skill-Integration
- [ ] Nach Edit/Write unter `backend/src/**` oder `backend/config/**` werden Backend-**Unit**-Tests vom Hook ausgelöst; Skill `/03-backend` weist Claude an, das Ergebnis im Chat zu reporten
- [ ] Analog für Frontend (`frontend/src/**`) und Database (`database/config/**`) — jeweils Unit-Suite
- [ ] Bei Requirement-Abschluss läuft zusätzlich der **Integration-Test gegen den ZKS-Mock** — getriggert durch das Implementations-Skill und/oder `/06-qa`, nicht durch den Hook
- [ ] Hook-Lauf scheitert nicht still — Fehlerstatus erscheint im Toolresult

## Edge Cases & Constraints
- **CouchDB-Tests starten ihren Container selbst** über `testcontainers[couchdb]`; auf der Entwicklermaschine muss Docker laufen (Standard-Voraussetzung). CI-Anpassung folgt im separaten CI-Scope
- **ZKS-Mock externer Stack:** der Mock ist eigenständig (`make up` in seinem Repo). E2E-Test prüft Erreichbarkeit vor Start; bei nicht-erreichbarem Mock skippen, nicht failen (pytest `pytest.skip(...)`)
- **Telegraf-Render-Snapshot:** kleinste Whitespace-Änderung im Rendering bricht den Test — Snapshot wird einmalig generiert und committed; Updates über `pytest --snapshot-update` (oder eigene Logik)
- **Jest + Angular Zone:** `jest-preset-angular` benötigt `zone.js/testing` in `setup-jest.ts`
- **Hook-Performance:** PostToolUse-Hooks dürfen nicht länger als ~3 s laufen, sonst wird das Arbeiten zäh — pytest-Aufruf auf das jeweils geänderte Modul fokussieren (`pytest <path>`), nicht volle Suite. **Daher Hook ausschließlich Unit-Suite**, nie Integration (ZKS-Mock-Start braucht mehrere Sekunden zusätzlich).
- **Permissions:** `.claude/settings.json` enthält bereits `Bash(pytest:*)`, `Bash(cd backend && pytest:*)`, `Bash(cd frontend && npm test:*)`, `Bash(cd database && pytest:*)` — keine Erweiterung mehr nötig
- **Trigger für Integration-Lauf:** wird **vom Skill** ausgelöst, sobald alle Akzeptanzkriterien eines Requirements abgehakt sind — nicht vom Hook. Voraussetzung: ZKS-Mock auf `host.docker.internal:102` erreichbar; sonst `pytest.skip(...)`

## Branch
- Phase 1 lief auf `feat/e2e-zks-mqtt-test` (abgezweigt von `feat/frontend-ci-rewrite`); nach `master` gelangt.
- Phase 2 (Abschluss) läuft auf `feat/test-strategy-finish` (abgezweigt von `master` am 2026-05-16).

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
