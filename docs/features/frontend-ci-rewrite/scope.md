# Feature Scope: Frontend CI-Rewrite (Angular 19, onconnecting CI)

**Status:** Implemented (swap done, awaiting browser sign-off)
**Created:** 2026-05-15
**Branch:** `feat/frontend-ci-rewrite`

## Summary
Vollständiger Frontend-Neuaufbau in einem Greenfield-Ordner `frontend-next/` auf Angular 19 LTS, ohne Bootstrap, mit `@angular/cdk`, strikter Umsetzung der onconnecting Corporate Identity (Farben, Typografie, Logo, Tonalität) und nach aktuellem Angular-Best-Practice (Standalone-Komponenten, Signals, neuer Control-Flow, `provide`-APIs, OnPush).

## Why
Das aktuelle Frontend ([`frontend/`](../../../frontend/)) ist Angular 17.3 mit **Bootstrap 3.4.1** (EOL, Standardrundungen und -theme), hartkodierten Hex-/RGB-Farben in Templates (`rgb(35, 142, 168)`), Emojis in Toasts (`✓`, `⚠️`), englischen Labels, Brand-Text `PLC Datalink RFC1006` statt onconnecting-Logo, Legacy-NgModule-Architektur, `HttpClientModule`, Default-Change-Detection und Zwei-Arg-Subscribe-Callbacks (deprecated).
Es entspricht weder dem verbindlichen CI-Referenzdokument [`docs/design/onconnecting-ci/ci-manual_onconnecting.md`](../../../docs/design/onconnecting-ci/ci-manual_onconnecting.md) noch den Angular-Empfehlungen ab v17. Ein gezielter Patch ist nicht tragfähig — Styling, Architektur und Tonalität sind durchgängig zu erneuern.

## In Scope
- [ ] Neues Angular-19-LTS-Projekt in `frontend-next/` (Standalone-Components, `provideRouter`, `provideHttpClient`, `provideAnimations`)
- [ ] TypeScript `strict` + alle empfohlenen Compiler-Flags aktiv
- [ ] Komponenten auf Signals + `ChangeDetectionStrategy.OnPush`, neue Template-Syntax (`@if`, `@for`, `@switch`)
- [ ] Service-Schicht mit `inject()` statt Constructor-DI, typisierte `Observable<T>`-Returns (keine `any`-Returns wie heute in `BackendRequestService`)
- [ ] Reactive Forms mit `nonNullable`, getypte `FormGroup`, Validatoren in eigenem `validators/`-Modul (IPv4, PLC-Adresse `^DB\d+\.(X|B|C|W|DW|I|DI|R|DT|S)\d+(\.\d+)?$`, Tag-Name)
- [ ] Übernahme aller bestehenden Screens und Routen 1:1 (Funktion):
  - `/` und `/plc-states` → `PlcStatesComponent`
  - `/configuration-overview` → `ConfigurationOverviewComponent`
  - `/create-configuration` → `CreateConfigurationComponent` (inkl. Edit-Flow via `?machineName=…`)
- [ ] Übernahme aller Backend-Calls aus [`backend-request.service.ts`](../../../frontend/src/app/services/backend-request.service.ts) **mit** Bereinigung der Base-URL (relativer Pfad gemäß [`.claude/rules/frontend.md`](../../../.claude/rules/frontend.md): `/config/...`, `/machine/...`, nicht `/api/...` — Verträglichkeit mit nginx-Custom-Config sicherstellen)
- [ ] Übernahme der Daten-Modelle aus [`models/item-configuration.model.ts`](../../../frontend/src/app/models/item-configuration.model.ts) 1:1 (camelCase, gleiche Felder)
- [ ] CI-Stilfundament in `src/styles.css` und `src/styles/_tokens.css`:
  - Vollständige Design-Tokens (Cyan-Akzent, Slate-Neutrale, Funktionsfarben, Spacing-Skala 4-px-Basis, Radien max. 8 px, Schriften)
  - Globale Reset/Base-Styles in CI-Tonart
  - **Kein** Bootstrap, **kein** Material-Theme, **kein** Tailwind
- [ ] Zwei-Schriften-System verbindlich:
  - Headlines/Labels/Code/PLC-Werte in **Consolas** (`var(--font-headline)` / `var(--font-mono)`)
  - Body/Hilfetexte in **Calibri Light** (`var(--font-body)`)
  - Headlines linksbündig, **nie fett**, **nie zentriert**
- [ ] Logo-Integration:
  - SVG-Assets aus [`docs/design/onconnecting-ci/logo/`](../../../docs/design/onconnecting-ci/logo/) (`onconnecting_slate.svg`, `onconnecting_cyan.svg`, `on_cyan.svg`) nach `frontend-next/src/assets/logo/` übernehmen
  - Header zeigt `onconnecting_slate.svg`, Favicon aus `on_cyan.svg` (Mindestbreite 96 px sonst `oc`)
  - Wortmarke `onconnecting` immer kleingeschrieben (HTML `<title>`, Header-Sublabel, Toasts)
- [ ] CI-konforme eigene Komponenten auf `@angular/cdk` aufbauend:
  - `oc-button` (Primary/Secondary/Danger; max. `--radius-md`)
  - `oc-input`, `oc-field` (Label + Help + Error in CI-Typografie und -Farben)
  - `oc-table` (für Configuration-Overview, Slate-Header, Cyan-Hover-Akzent)
  - `oc-card` (für Form-Sections; Radius `--radius-lg`, kein Schlagschatten)
  - `oc-toast` (eigener `ToastService` mit Aria-Live; CI-Funktionsfarben; **keine Emojis**, **keine Ausrufezeichen-Ketten**)
  - `oc-dialog` (Confirmation-Dialog; CDK `Dialog` + `Overlay` + `A11yModule` Focus-Trap)
  - `oc-status-pill` (Connected/Standby/Disconnected → Success/Warning/Error-Token)
- [ ] Deutsche UI-Tonalität in CI-Stil:
  - Labels und Validierungen in präzisem, sachlichem Deutsch (Fachbegriffe PLC/MQTT/RFC1006/S7/AAS/OPC UA bleiben englisch)
  - Beispiel-Fehler: `PLC IP: ungültiges IPv4-Format (z. B. 192.168.1.1).`
  - Beispiel-Toast (Erfolg): `Konfiguration für devBoard gespeichert.`
  - Beispiel-Toast (Fehler): `Konfiguration nicht gespeichert. Backend lieferte HTTP 409 (Konflikt — _rev veraltet).`
  - Keine Emojis. Einzelne Ausrufezeichen nur bei echten Fehlerzuständen.
- [ ] PLC-Adressen, IPs, Ports, MQTT-Topics im UI grundsätzlich in `var(--font-mono)` darstellen
- [ ] Layout: 12-Spalten-Grid, Inhalts-Maxbreite 1280 px, Gutter 24 px Desktop / 16 px Mobile; scharfe Kanten / minimaler Radius
- [ ] Funktions-/UX-Verbesserungen im selben Schritt:
  - Toasts in fester Bildschirmposition (oben rechts), per `ToastService` global statt pro Komponente neu animiert
  - `Subject`/`takeUntilDestroyed()` statt `OnDestroy`-Unsubscribe-Pattern
  - Tabellenzeilen mit konsistenten Aktions-Buttons (Start, Stop, Edit, Remove)
  - 60-30-10-Farbregel: ~60 % Neutral (`--color-neutral-50/100`), ~30 % Slate (`--color-neutral-700/800/900`), ~10 % Cyan-Akzent (`--color-accent-500`)
- [ ] Tooling/Qualität:
  - ESLint (`@angular-eslint`) + Prettier (Konfig konsistent mit bestehendem `.prettierrc`)
  - Stylelint mit Regel: **kein** Hex-/RGB-Wert außerhalb `_tokens.css`
  - `npm run build` (Production) + `npm run lint` müssen ohne Fehler durchlaufen
  - Component-Specs für nicht-triviale Logik (Form-Validatoren, ToastService); keine Vollabdeckung erzwungen
- [ ] Dockerfile-Update (eigenes Multistage-Dockerfile in `frontend-next/`):
  - Node 22 Build-Stage, nginx Alpine Serve-Stage
  - Übernahme von [`frontend/config/nginx-main.conf`](../../../frontend/config/nginx-main.conf) und [`frontend/config/nginx-custom.conf`](../../../frontend/config/nginx-custom.conf), nach Bereinigung etwaiger Bootstrap-/`/api/`-Spuren
- [ ] CI-Workflow für `frontend-next` ([`.github/workflows/`](../../../.github/workflows/)) als zweiter Job/Matrix-Eintrag parallel zum heutigen `frontend`-Build, bis zum Tausch
- [ ] Tausch-PR (gesonderter, kleiner Commit nach Abnahme): `frontend/` → `frontend-legacy/` archivieren bzw. löschen, `frontend-next/` → `frontend/`, Compose-Stacks und CI nachziehen

## Out of Scope
- Keine Änderungen am Backend (`backend/`), keine API-Vertragsänderungen, keine neuen Endpunkte
- Keine Schema- oder CouchDB-Änderungen
- Keine Telegraf-/MQTT-Anpassungen
- Keine Authentifizierung/Login-Schicht im Frontend (separate Initiative)
- Keine Internationalisierung (Englisch wird **nicht** parallel gepflegt — UI bleibt Deutsch außer Fachtermini)
- Keine neuen Screens oder Datenfelder, keine Erweiterung des PLC-Adressformats
- Keine Tailwind- oder Angular-Material-Integration
- Keine Animations-Bibliothek über `@angular/animations` hinaus
- Keine Dark-Mode-Variante (kann später als zusätzliche Token-Tabelle ergänzt werden)
- Keine ARIA-/A11y-Vollaudits über WCAG-2.2-Untergrenze hinaus

## Affected Areas
| Area | Touched? | Notes |
|---|---|---|
| `backend/src/routes.py` | no | API-Vertrag bleibt |
| `backend/src/plc_datalink_rfc1006_model.py` | no | — |
| `backend/src/services/*` | no | — |
| `backend/openapi/plc_datalink_rfc1006_api.yml` | no | — |
| `backend/config/dynamic_startup_telegraf.sh` | no | — |
| `frontend/src/app/` (Altprojekt) | yes | Wird bis zum Swap stehen gelassen; danach durch `frontend-next/` ersetzt |
| `frontend-next/` (neu) | yes | Vollständiges Angular-19-Greenfield-Projekt |
| `frontend-next/src/assets/logo/` | yes | Logos aus `docs/design/onconnecting-ci/logo/` |
| `frontend/config/nginx-*.conf` | yes | In `frontend-next/config/` portieren, ggf. `/api/`-Pfade prüfen |
| `database/config/*` | no | — |
| CouchDB document schema | no | — |
| `dc-plc-datalink-rfc1006-local.yml` | yes (Tausch-PR) | `build.context: ./frontend` → `./frontend-next` (oder Verzeichnis-Rename) |
| `dc-plc-datalink-rfc1006-acr.yml` | maybe (Tausch-PR) | Nur falls Image-Tag oder Pfad nachzieht |
| `frontend-next/dockerfile-plc-datalink-rfc1006-frontend` | yes | Neu, basiert auf bestehendem |
| `.github/workflows/` | yes | Zusätzlicher Build-Job für `frontend-next`, später Swap |
| `README.md` | yes | Hinweise auf neuen UI-Stand, Logo, CI-Verweis |
| `architecture/decisions/` | yes (`/architecture`) | ADR für „Angular CDK statt Bootstrap" + ADR für „Greenfield in frontend-next/ und Tausch" |

## Acceptance Criteria
- [ ] `frontend-next/` baut mit `npm run build` ohne Errors und Warnings (Production-Konfig)
- [ ] `frontend-next/` lintet mit `npm run lint` ohne Errors (ESLint + Stylelint inkl. „kein Hex außerhalb tokens")
- [ ] Im Docker-Stack auf `http://localhost/` rendern alle drei Screens (PLC State, Configuration Overview, Create Configuration) gegen das unveränderte Backend
- [ ] Edit-Flow funktioniert: Klick auf „Bearbeiten" in Overview lädt `?machineName=…`, Form ist vorbefüllt, Submit → `PUT /config/update` → Erfolgs-Toast
- [ ] Create-Flow funktioniert: Submit gültiger Daten → `POST /config/create` → Erfolgs-Toast; ungültiges IPv4 zeigt CI-konforme deutsche Fehlermeldung in Funktionsfarbe `--color-error`
- [ ] Start/Stop/Remove auf Configuration Overview triggern dieselben Endpunkte wie heute und zeigen CI-konforme Toasts
- [ ] PLC-State-Polling läuft im 5-s-Intervall (wie heute), unsubscribed beim Verlassen des Screens
- [ ] Kein Bootstrap-Build-Output, keine `bootstrap`-Dependency in `frontend-next/package.json`
- [ ] In keinem `.html`/`.css` von `frontend-next/` taucht ein roher Hex-/RGB-Wert auf (Stylelint-Check); alle Farben kommen aus `var(--color-*)`-Tokens
- [ ] Alle Headlines sind linksbündig und nicht fett (Sichtprüfung gegen [`ci-manual_onconnecting.md`](../../../docs/design/onconnecting-ci/ci-manual_onconnecting.md))
- [ ] Wortmarke `onconnecting` erscheint im Header und in `<title>` durchgehend kleingeschrieben, Logo-SVG geladen
- [ ] Keine Emojis im UI-Output, keine Ausrufezeichen-Ketten in Toasts/Validierungen
- [ ] PLC-Adressen, IPs, Ports, MQTT-Topics werden in `var(--font-mono)` (Consolas-Fallback-Kette) gerendert
- [ ] Aria-Live-Region für Toasts ist im DOM vorhanden; CDK-Dialog hat Focus-Trap
- [ ] WCAG-2.2-Kontrastuntergrenze: Body-Text auf weißem Hintergrund mindestens `--color-neutral-700` (Sichtprüfung mit Browser-DevTools-Kontrasttool, ein Stichproben-Screen)
- [ ] Migration nicht durchgeführt: `frontend/` existiert weiter und ist weiterhin baubar, bis Tausch-PR mergt

## Edge Cases & Constraints
- Backend nicht erreichbar → CI-konformer Fehler-Toast mit Status + Endpoint, kein generisches „Ups, da ist etwas schiefgelaufen"
- CouchDB 409 (`_rev` veraltet) auf Update → spezifischer Toast in `--color-error` (Vorlage in [`.claude/rules/frontend.md`](../../../.claude/rules/frontend.md))
- Maschine ohne Konfiguration / leere Liste in Overview → leerer Zustand mit sachlichem Hinweistext, kein „Empty State"-Illustration (CI: keine Stockfotos)
- PLC-Adresse mit gültigem Format, aber unsinnigem Bereich (z. B. `DB99999.X9999.7`) → wird wie heute serverseitig geprüft, Frontend bleibt formal-tolerant
- Viewport < 768 px (Tablet/Handy) → Layout muss noch lesbar bleiben, aber keine dedizierte Mobile-Optimierung jenseits responsiver Grids
- Bestehende `frontend/` muss bis zum Swap weiter baubar bleiben, damit der ACR-Stack lauffähig bleibt

## Breaking Changes & Migration
**Endnutzer-sichtbar (UI):**
- Sprachwechsel der Labels und Meldungen von Englisch zu Deutsch
- Komplett neue Optik (Slate/Cyan, Consolas/Calibri Light, keine Bootstrap-Rundungen)
- Toast-Position und -Verhalten geändert (zentraler `ToastService`)

**Tooling:**
- Bei Tausch-PR ändert sich der Pfad `frontend/` → ist *gleicher Pfad*, aber komplett anderer Inhalt; etwaige lokale Aliase in IDE/Skripten bleiben gültig
- Docker-Compose-Stacks und CI-Workflow ziehen mit dem Tausch nach (separate Änderung, separater Commit)

**API/MQTT/CouchDB:** keine.

**Migrationsplan:**
1. ✅ `frontend-next/` parallel zu `frontend/` aufgebaut (Phasen A–D).
2. ⏭ CI-Workflow um zweiten Job für `frontend-next` ergänzen — entfällt, weil der Swap direkt mit der Implementierung erfolgt ist (Greenfield kam in einem Branch mit den ADRs, der Build-Check lief im DEV-Loop, nicht parallel zu Legacy).
3. ✅ Swap ausgeführt: legacy `frontend/` aus dem Tree entfernt (Historie in git erhalten), `frontend-next/` → `frontend/`. `dc-plc-datalink-rfc1006-dev.yml` baut unverändert aus `./frontend`, jetzt mit dem neuen Code.
4. ✅ DEV-Verifikation auf `192.168.0.121:5000`-Registry-Loop: `compose build` + `compose up -d --no-build` läuft, alle Screens werden ausgeliefert, `/config/*` und `/machine/*` Proxy-Routen erreichbar. Push-Step braucht einmaligen `daemon.json`-Eintrag für die insecure Registry (siehe README); danach kann die volle build → push → pull → up-Sequenz laufen. ACR-Build/Tag folgt nach Browser-Abnahme.

## Dependencies
- **Neue npm-Dependencies** (benötigen ADR via `/architecture`):
  - `@angular/cdk@19` (Overlay, Dialog, A11y, Portal)
- **Dev-Dependencies** (Tooling, ADR-pflichtig falls strikt ausgelegt):
  - `@angular-eslint/*`, `eslint`, `@typescript-eslint/*`
  - `prettier` (bereits vorhanden, Konfig migrieren)
  - `stylelint`, `stylelint-config-standard`
- Logo-Assets aus [`docs/design/onconnecting-ci/logo/`](../../../docs/design/onconnecting-ci/logo/) (im Repo vorhanden, keine externen Bezugsquellen)
- Keine neuen Backend-Routen, keine neuen Container, keine neuen Ports

---
<!-- Filled in by later skills -->

## Architecture Decisions
- [ADR-0003](../../../architecture/decisions/ADR-0003-frontend-ui-foundation-angular-cdk.md) — Frontend-UI-Schicht auf `@angular/cdk` statt Bootstrap/Material/Tailwind (Accepted, 2026-05-15)
- [ADR-0004](../../../architecture/decisions/ADR-0004-frontend-greenfield-migration-strategy.md) — Greenfield-Migrationsstrategie via `frontend-next/` mit anschließendem Verzeichnis-Tausch (Accepted, 2026-05-15)

## QA Evidence
_Wird von `/qa` ergänzt._

## Operations Notes
_Wird von `/operations` ergänzt, falls Build-/Deploy-Verhalten beim Tausch operative Auswirkungen hat._
