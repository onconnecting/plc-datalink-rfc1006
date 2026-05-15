# Feature Scope: Project Structure — Best Practices Alignment

**Status:** Phase A implemented (Phase B & C deferred)
**Created:** 2026-05-15
**Branch:** `master` (user opted to stay on the current branch)

## Summary
Repo-Layout an Best Practices ausrichten: fehlende Standard-Verzeichnisse anlegen (`docs/features/`, `architecture/decisions/`), `.gitignore` vervollständigen, Namens-Inkonsistenzen im Backend beseitigen, Test-Layout schärfen und ergänzende Tooling-Dateien (`.editorconfig`, `.dockerignore`, PR-Template) hinzufügen.

## Why
- Die Workflow-Skills (`/01-requirements`, `/02-architecture`, `/99-commit`) erwarten `docs/features/<name>/scope.md` und `architecture/decisions/ADR-*.md` — beides existiert heute nicht.
- `.gitignore` enthält keinen Eintrag für `backend/.venv/` oder `__pycache__/` → das vorhandene Virtualenv (`backend/.venv/`) könnte versehentlich committet werden.
- `backend/src/init.py` liegt neben `__init__.py`. Für neue Entwickler:innen ist das verwirrend; üblich ist `app.py` / `application.py` / Application-Factory in `__init__.py`.
- Im Backend mischen sich Shell-Tests (`backend/test/*.sh`) und ein Python-Helper (`plc_datalink_rfc1006_linux.py`) — Trennung nach Test-Typ (curl-Integration vs. lokal/dev) wäre klarer.
- `backend/config/env` ist eine namenlose ENV-Datei im Source-Tree. Unklar, ob Template oder Live-Config — ein klarer Name (`env.example`) reduziert das Risiko, dass dort versehentlich Credentials landen.
- `doc/` (Singular) enthält nur interne, gitignorierte Design-Dokumente. Ein klar erkennbares, eingechecktes `docs/` (Plural) für Feature-Scopes und User-Doku ist Standard.
- Kein `.editorconfig`, kein `.dockerignore`, kein PR-Template — kleine Hygiene-Lücken.

## In Scope
Phasenweise — der Nutzer kann nach Approval entscheiden, was tatsächlich umgesetzt wird.

### Phase A — Additiv, risikoarm (umgesetzt 2026-05-15)
- [x] `docs/features/` mit README angelegt
- [x] `architecture/decisions/` mit README und `ADR-0000-template.md` angelegt
- [x] `.gitignore` ergänzt um `.venv/`, `__pycache__/`, `*.pyo`, `*.egg-info/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `node_modules/`, `frontend/dist/`, `.angular/`, `*.swp`/`*.swo`
- [x] `.editorconfig` im Repo-Root (LF, UTF-8, 4 Spaces Python / 2 Spaces YAML+TS+JSON, Tabs in Makefiles)
- [x] `.dockerignore` für `backend/`, `frontend/`, `database/`
- [x] `.github/PULL_REQUEST_TEMPLATE.md`
- [x] `docs/features/project-structure-best-practices/scope.md` (= diese Datei)

### Phase B — Umbenennen / leichte Refactors (Approval pro Punkt)
- [ ] `backend/src/init.py` → entweder umbenennen in `backend/src/app.py` ODER Inhalt in `__init__.py` zusammenführen (Flask-App-Factory-Pattern). **Touch-Punkte:** Aufrufer von `from .init import …`, Dockerfile/supervisord Startbefehl
- [ ] `backend/config/env` → `backend/config/env.example` (markiert klar als Template); echte ENV bleibt außerhalb des Repos
- [ ] `backend/test/` aufsplitten: `backend/test/curl/` (Shell-Skripte) und `backend/test/scripts/` (Python-Helper) — keine Logikänderung, nur klarere Verzeichnisse
- [ ] `doc/` (Singular) auflösen: interne Design-Doku entweder umziehen in `docs/internal/` (gitignored) oder ganz aus dem Repo nehmen — Status klären
- [ ] Top-Level `Makefile` ODER `tasks.sh` mit Standard-Targets (`build`, `up`, `down`, `logs`, `test`)

### Phase C — Optional, höhere Auswirkung (nur mit explizitem Approval)
- [ ] `backend/pyproject.toml` einführen (PEP 621), `requirements.txt` bleibt zunächst parallel für Docker-Build — Modernisierung des Python-Setups
- [ ] Pre-commit-Hook (`.pre-commit-config.yaml`) mit Ruff/Black für Backend, Prettier für Frontend
- [ ] CI um Lint- und Test-Jobs erweitern (`.github/workflows/lint.yml`, `test.yml`); aktuell nur `docker-image.yml`
- [ ] Dependabot-Konfiguration (`.github/dependabot.yml`)

## Out of Scope
- Funktionale Änderungen an Backend, Frontend, Telegraf oder PLC-Logik
- Änderungen am MQTT-Payload-Format, CouchDB-Dokumentschema oder REST-API
- Migration von Flask auf ein anderes Framework
- Wechsel des Build-Systems (z. B. von docker-compose auf Helm/Kubernetes)
- Rewrite von Tests (nur Verschiebung)

## Affected Areas
| Area | Touched? | Notes |
|---|---|---|
| `backend/src/routes.py` | maybe | nur falls Phase B (`init.py` → `app.py`) — Imports prüfen |
| `backend/src/plc_datalink_rfc1006_model.py` | no | — |
| `backend/src/services/*` | no | — |
| `backend/openapi/plc_datalink_rfc1006_api.yml` | no | — |
| `backend/config/dynamic_startup_telegraf.sh` | no | — |
| `backend/config/supervisord.conf` | maybe | falls `init.py` umbenannt wird → Startbefehl anpassen |
| `backend/config/env` | yes (Phase B) | → `env.example` |
| `backend/dockerfile-plc-datalink-rfc1006-backend` | maybe | falls Entrypoint sich durch Umbenennung ändert |
| `backend/requirements.txt` | no (Phase C: parallel zu `pyproject.toml`) | — |
| `backend/test/*` | yes (Phase B) | reorganisieren in Unterordner |
| `frontend/src/app/` | no | — |
| `frontend/dockerfile-plc-datalink-rfc1006-frontend` | no | — |
| `database/config/*` | no | — |
| CouchDB document schema | no | — |
| `dc-plc-datalink-rfc1006-*.yml` | no | — |
| `.github/workflows/` | maybe (Phase C) | Lint/Test-Workflows ergänzen |
| `.github/` (PR-Template) | yes (Phase A) | neu |
| `.gitignore` | yes (Phase A) | erweitern |
| `.editorconfig`, `.dockerignore` | yes (Phase A) | neu |
| `README.md` | maybe | Verweis auf neue `docs/`-Struktur ergänzen |
| `CHANGELOG.md` | yes | Eintrag „chore(repo): align structure with best practices" |
| `doc/` | maybe (Phase B) | klären: löschen / umziehen / lassen |

## Acceptance Criteria
- [ ] `docs/features/` und `architecture/decisions/` existieren, im Git getrackt, mit kurzem README
- [ ] `git status` nach `pip install` zeigt **kein** `backend/.venv/` mehr als untracked
- [ ] `find . -name __pycache__ -type d` Treffer werden von `git status` ignoriert
- [ ] Phase B (falls gewählt): `docker compose -f dc-plc-datalink-rfc1006-local.yml up --build` startet alle 3 Container ohne Fehler; Backend-Logs zeigen „PLC-DATALINK-RFC1006 starting"
- [ ] Phase B (falls gewählt): `backend/test/curl/config_create.sh` läuft erfolgreich gegen das laufende Backend
- [ ] README erwähnt, wo neue Feature-Scopes und ADRs zu finden sind
- [ ] `.editorconfig`, `.dockerignore`, PR-Template existieren

## Edge Cases & Constraints
- **PLC unreachable / CouchDB unreachable:** nicht betroffen — keine Runtime-Logik wird verändert
- **Bestehende Deployments:** Image-Build-Pfade ändern sich nur, wenn Phase B den Backend-Entrypoint umbenennt. In dem Fall muss der `CMD`/`supervisord`-Eintrag im Backend-Dockerfile angepasst werden, sonst startet der Container nicht.
- **Open PRs / WIP-Branches:** Renames in Phase B können Merge-Konflikte erzeugen — vorher prüfen, ob laufende Arbeit auf `backend/src/init.py` oder `backend/test/` zugreift.
- **CI:** Wenn `.github/workflows/docker-image.yml` Pfade hartcodiert hat, vor Phase B prüfen.

## Breaking Changes & Migration
- **Phase A:** keine — rein additiv.
- **Phase B (`init.py` → `app.py`):** Lokaler Dev-Workflow ändert sich (Modulname). Migration: in einem Commit Datei umbenennen + Importer aktualisieren + supervisord/Dockerfile-Entrypoint anpassen. Rückwärtskompatibilität nicht nötig (kein externer Konsument).
- **Phase B (`backend/config/env` → `env.example`):** Falls die Datei aktuell zur Laufzeit gelesen wird, muss der Lese-Pfad angepasst werden — vor Umbenennung verifizieren (Verwendungen suchen: `grep -r "config/env" backend/`).
- **Phase C (`pyproject.toml`):** Erfordert separates Architecture-Review (ADR), da das Build-Setup substanziell betroffen ist.

## Dependencies
- Keine externen Library-Bumps in Phase A/B
- Phase C bringt neue Dev-Dependencies (ruff/black, pre-commit) — Approval erforderlich

---
<!-- Filled in by later skills -->

## Architecture Decisions
_Phase B & C sollten je ein ADR erhalten — Vorschlag:_
- ADR-0001 — Backend Application Entrypoint Layout (Flask App-Factory)
- ADR-0002 — Python Project Metadata (`pyproject.toml` vs. `requirements.txt`) — _nur falls Phase C gewählt_

## QA Evidence
_Wird von `/06-qa` ergänzt nach Umsetzung._

## Operations Notes
_Wird von `/08-operations` ergänzt, falls Phase B den Entrypoint ändert._
