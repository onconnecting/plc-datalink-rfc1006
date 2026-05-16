# Feature Scope: E2E-Test stellt ZKS-Mock-Vorzustand wieder her

**Status:** Scoped
**Created:** 2026-05-16
**Branch:** `feat/test-strategy-finish` (kein neuer Branch — kleines Folge-Refinement der laufenden Test-Strategie, siehe [test-strategy/scope.md](../test-strategy/scope.md))

## Summary
Der einzige E2E-Test ([backend/test/scripts/integration/test_e2e_zks_mqtt.py](../../../backend/test/scripts/integration/test_e2e_zks_mqtt.py)) liest vor dem ersten manipulierenden Schreibzugriff den aktuellen Zustand der ZKS-Mock-Anlage (Laufzustand + CycleSpeedFactor) und stellt diesen am Ende — bei Erfolg **und** bei Fehler — wieder her.

## Why
Der Test ist heute nicht „mock-neutral":

- **Status-Override:** Im `finally`-Block / Cleanup wird `Cmd_Stop` gepulst (Schritt 8 im Test-Docstring). Der Mock landet danach immer in `IDLE`, egal ob er vorher `RUNNING` war.
- **Parameter-Override:** Schritt 5c überschreibt `Cmd_CycleSpeedFactor` mit `5.0` (REAL @ DB4 92). Der vorherige Wert ist verloren.

Konsequenz: Wer parallel zum Test eine Demo oder ein manuelles Debugging am Mock laufen hat (Node-RED-Dashboard auf `:1880`), bekommt nach jedem Testlauf eine veränderte Anlage zurück. Aktuell wird im Test bereits ein `initial_snapshot` gelesen, aber rein diagnostisch — er wird nicht zur Wiederherstellung genutzt.

Ziel: Der Mock sieht nach `pytest -q backend/test/scripts/integration/test_e2e_zks_mqtt.py` so aus wie davor.

## In Scope
- [ ] **Vorzustand erfassen** vor jedem schreibenden snap7-Call (vor Schritt 5b `Cmd_Stop`):
  - `Machine.State` (DB1 INT @ 0) — Werte: 0 = IDLE, 1 = RUNNING; anderes wird als „nicht-running" behandelt
  - `Cmd_CycleSpeedFactor` (DB4 REAL @ 92)
- [ ] **Wiederherstellung** in einem `try/finally` (oder pytest-Fixture mit `yield`), läuft auf jedem Pfad:
  - Falls vorher `RUNNING` (State == 1) → `Cmd_CycleSpeedFactor` zurückschreiben, dann `Cmd_Start` (DB4 Bit 68.1) pulsen, kurz auf State-Übergang pollen
  - Falls vorher nicht `RUNNING` → `Cmd_CycleSpeedFactor` zurückschreiben, dann `Cmd_Stop` (DB4 Bit 68.2) pulsen, kurz auf State-Übergang pollen (heutiges Verhalten als Fallback)
- [ ] **Reihenfolge** im Cleanup: erst Mock-Vorzustand wiederherstellen (snap7) **vor** `/machine/stop` und `/config/remove`, damit der Restore noch über den S7-Port zum Mock durchkommt
- [ ] **Skip-/Fail-Robustheit:** Wenn `zks_endpoint` skippt (Mock nicht erreichbar) oder die Vor-Snapshot-Verbindung fehlschlägt, läuft kein Restore — es gibt nichts zu restaurieren bzw. nichts Zuverlässiges, das man wiederherstellen könnte
- [ ] **Test-Docstring aktualisieren** (Schritt 8): neue Cleanup-Semantik dokumentieren („Mock endet im Vorzustand, nicht zwangsweise IDLE")

## Out of Scope
- Wiederherstellung weiterer DB4-Felder außer `Cmd_CycleSpeedFactor` — der Test schreibt aktuell nichts anderes; kein vorsorglicher Snapshot ganzer DBs
- Wiederherstellung der KPIs in DB1 (`PartCounter`, `OkCounter`, …) — diese werden vom Mock selbst getrieben, der Test schreibt sie nicht
- Persistieren des Vorzustands über Testläufe hinweg (z. B. in einer Datei) — nur in-process
- Backend-Code-Änderungen, OpenAPI-Änderungen, neue Endpunkte
- Frontend, Database, Compose, Dockerfiles — rein test-internes Refinement
- Änderung der Acceptance Criteria des übergeordneten [test-strategy](../test-strategy/scope.md)-Scopes — diese Erweiterung ist additiv

## Affected Areas
| Area | Touched? | Notes |
|---|---|---|
| [backend/test/scripts/integration/test_e2e_zks_mqtt.py](../../../backend/test/scripts/integration/test_e2e_zks_mqtt.py) | **yes** | Vorzustand-Snapshot + Restore-Block; Docstring (Schritt 8) |
| [backend/test/scripts/integration/conftest.py](../../../backend/test/scripts/integration/conftest.py) | **maybe** | Restore optional als Fixture extrahieren (`yield`-basiert), falls lesbarer als inline `try/finally` |
| `backend/src/*` | no | — |
| `backend/openapi/*` | no | — |
| `backend/config/*` | no | — |
| `frontend/**` | no | — |
| `database/**` | no | — |
| CouchDB Doc-Schema | no | — |
| `dc-plc-datalink-rfc1006-*.yml` | no | — |
| `**/Dockerfile` | no | — |
| `.github/workflows/` | no | — |
| `README.md` / OpenAPI | no | — |
| [docs/features/test-strategy/scope.md](../test-strategy/scope.md) | **yes (light)** | Querverweis-Zeile auf diesen Scope; Acceptance-Criteria-Eintrag „Mock-Vorzustand wiederhergestellt" ergänzen |

## Acceptance Criteria
- [ ] Vor dem ersten `db_write`-Call liest der Test `pre_state = Machine.State` und `pre_speed = Cmd_CycleSpeedFactor` und speichert beide
- [ ] Bei `pre_state == 1` (RUNNING) hinterlässt der Test den Mock im Zustand RUNNING mit dem ursprünglichen `Cmd_CycleSpeedFactor`
- [ ] Bei `pre_state != 1` hinterlässt der Test den Mock im Zustand IDLE mit dem ursprünglichen `Cmd_CycleSpeedFactor`
- [ ] Restore läuft auf dem Fehlerpfad (provoziert z. B. durch einen `assert False` mitten im Test) — verifiziert manuell beim Umsetzen
- [ ] Wenn der ZKS-Mock nicht erreichbar ist, skippt der Test wie heute (`pytest.skip`); kein Restore-Versuch, keine Fehlermeldung
- [ ] Der Test-Docstring (Schritt 8) beschreibt die neue Semantik

## Edge Cases & Constraints
- **State-Wertebereich:** Der Mock-Zustandsautomat (Node-RED) liefert in DB1 INT@0 derzeit 0 (IDLE) und 1 (RUNNING). Übergangswerte sind nicht dokumentiert. **Regel:** State == 1 → RUNNING-Restore; alles andere → IDLE-Restore. Vermeidet, dass ein transient gelesener Zwischenwert den Restore in einen ungültigen Zustand schickt.
- **CycleSpeedFactor-Wertebereich:** REAL. Wenn der Vor-Wert exotisch ist (z. B. `0.0` oder `NaN`), wird er trotzdem zurückgeschrieben — der Test bewertet ihn nicht. Verantwortung liegt beim, der den Mock vorher in diesen Zustand gebracht hat.
- **Trigger-Bit-Mechanik:** `Cmd_Start` / `Cmd_Stop` sind Flanken-getriggert; Node-RED setzt das Bit nach ~200 ms wieder zurück. Der Restore muss also pulsen, nicht halten — gleiche Mechanik wie die bestehenden `pulse_trigger_bit`-Helpers.
- **Reihenfolge:** snap7-Restore muss **vor** `/machine/stop` laufen — sobald Telegraf die einzige aktive S7-Session beendet, kann der Mock anders reagieren (in der Praxis sollten parallele Sessions kein Problem sein, aber wir minimieren Annahmen).
- **Doppelte `_force_cleanup`:** Die bestehende `cleanup_machine`-Fixture ruft `_force_cleanup` zweimal auf (pre + post). Der Pre-Cleanup ist irrelevant — er räumt nur Reste eines vorherigen Fehl-Laufs auf. Der Vorzustand wird **erst danach** gelesen (im Test selbst), damit ein hängender alter Telegraf-Prozess nicht den S7-Read stört.
- **Was, wenn pre_speed nicht gelesen werden konnte?** (snap7-Read schlägt fehl): Restore wird übersprungen, Fehler wird im Test geloggt, aber der eigentliche Testfehler/-erfolg bleibt führend.

## Breaking Changes & Migration
Keine. Rein test-internes Refinement; keine API-, MQTT-, DB- oder Container-Änderungen.

## Dependencies
- Keine neuen Python-Deps — `python-snap7` und `paho-mqtt` sind bereits via [test-strategy](../test-strategy/scope.md) eingeführt
- Keine ADR nötig — keine strukturelle Entscheidung (Test-internes Verhalten, kein API-Vertrag)
- Bezug zu [test-strategy/scope.md](../test-strategy/scope.md) Section 4 (E2E-ZKS): additives Verhalten, ändert keine dortige Acceptance Criterion

---
<!-- Filled in by later skills -->

## Architecture Decisions
_Nicht erforderlich._

## QA Evidence
_Wird durch `/06-qa` ergänzt — manuelle Verifikation: Mock vor Test in RUNNING + Speed=2.0 versetzen, Test laufen lassen, prüfen dass nach Testende RUNNING + Speed=2.0 wieder vorliegt._

## Operations Notes
_Nicht relevant — Test-Stack ist Dev-only._
