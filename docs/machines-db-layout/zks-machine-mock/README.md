# zks-machine-mock

Docker-basierte Simulation einer realen Zell-Kontaktier-Anlage (ZKS) mit
zwei industriellen Schnittstellen (OPC UA und S7/RFC1006) und einem
webbasierten Bedien-Dashboard.

> **Stand:** 03.05.2026

## Inhalt

- [Was die Anlage simuliert](#was-die-anlage-simuliert)
- [Anlage starten](#anlage-starten)
- [Bedienen und Beeinflussen](#bedienen-und-beeinflussen)
- [Schnittstellen verwenden - Schritt für Schritt](#schnittstellen-verwenden---schritt-für-schritt)

---

## Was die Anlage simuliert

Die Anlage stellt ein **Zell-Kontaktier-System (ZKS)** dar - eine
Produktionszelle, wie sie in der Batterie- bzw. Modulfertigung eingesetzt
wird. Sie verkettet zwölf Aluminium-Plättchen elektrisch über Widerstands-
schweißpunkte und prüft das Ergebnis am Ende des Zyklus.

### Bauteil

- **Trägerplatte:** 200 mm × 120 mm × 6 mm.
- **Aluminium-Plättchen:** 12 Stück, 20 mm × 15 mm × 1 mm, angeordnet in
  drei Reihen zu je vier Plättchen.
- **Schweißsequenz "Schlange":** 12 Schweißpunkte (Index 0..11), die
  zusammen elf elektrische Übergänge bilden.
- **Identifikation:** Jeder Träger trägt einen QR-Code, der eine eindeutige
  Serialnummer im Format Gen6 ON-SFC liefert (21 Zeichen, `ON` plus 19
  Zeichen, Aufbau siehe [docs/sfc-on-numbers.md](docs/sfc-on-numbers.md)).

### Stationen

| ID | Bezeichnung | Funktion | Datenblätter |
|---|---|---|---|
| A | Zuführung und Positionierung | Förderer, Anschlag, Niederhalter | [machine/01-station-a-zufuehrung](machine/01-station-a-zufuehrung/) |
| B | Identifikation | QR-Scan, Lichtschranke | [machine/02-station-b-identifikation](machine/02-station-b-identifikation/) |
| C | Roboter-Schweißzelle | 6-Achs-Roboter, Widerstandsschweißkopf | [machine/03-station-c-schweisszelle](machine/03-station-c-schweisszelle/) |
| D | In-Process-Prüfung | Strom, Spannung, Widerstand pro Segment | [machine/04-station-d-pruefung](machine/04-station-d-pruefung/) |
| E | Ausschleusung | OK-/NOK-Weiche, Zähler | [machine/05-station-e-ausschleusung](machine/05-station-e-ausschleusung/) |

Die nominale Zykluszeit beträgt rund 16 s pro Bauteil und ist über einen
Beschleunigungsfaktor (0.1× bis 10×) skalierbar.

Die vollständige Hardware-Referenz (Typenschild, Komponenten, Hersteller,
Schnittstellen, OPC-UA- und S7-Adressraum) steht im Master-Dokument
[machine/MACHINE.md](machine/MACHINE.md). Pro Funktion (Roboter,
Schweißzange, Schweißsteuerung, Prüfgerät, SPS, Sicherheits-SPS,
Lichtgitter, Netzteil, Pneumatik) gibt es ein eigenes Markdown-Datenblatt
im jeweiligen Stations-Unterordner unter [machine/](machine/).

### Was die Simulation erzeugt

- **Realistische Schweißdaten** je Punkt: Strom (kA), Spannung (V), Pulsdauer
  (ms), Elektrodenkraft (N), Energie (J), inkl. gaußscher Streuung und
  Elektrodenverschleiß-Drift über die Zeit.
- **Elektrische Prüfung** mit Gesamtwiderstand, elf Segmentwiderständen und
  Toleranzauswertung (IO/NOK).
- **Nacharbeitslogik:** Bei NOK schweißt der Roboter den fehlerhaften Punkt
  bis zu zweimal nach. Bleibt das Teil NOK, geht es als SCRAP aus.
- **Mengengerüst KPIs:** Stückzahl, OK-Quote (Yield), Durchsatz, Rework- und
  Scrap-Zähler, Laufzeit.
- **Roboterdaten:** Sechs Achspositionen mit Geschwindigkeit und Drehmoment,
  TCP-Position, Vibration, Temperatur.
- **Hilfsmedien:** Kühlwasserdurchfluss und -temperatur, Druckluft,
  elektrische Leistungsaufnahme.
- **Fehlerbilder:** QR-Lesefehler, zu niedriger Schweißstrom, zu hohe
  Elektrodenkraft, Test-Timeout, Roboterfehler, Kühlmittel/Druckluft niedrig,
  Not-Aus.
- **Logs** als JSON-Lines mit täglicher Rotation und 7 Tagen Aufbewahrung.

### Aufbau

Zwei Container im Bridge-Netz `zks_net`:

- **`zks-nodered`** - Simulation, OPC-UA-Server (Port 4840), Bedien-Dashboard
  und Editor (Port 1880).
- **`zks-s7server`** - Snap7-basierter S7/RFC1006-Server (Port 102) mit den
  Datenbausteinen DB1 (Maschine), DB2 (Schweißpunkte), DB3 (Prüfung),
  DB4 (Bauteil und Steuerbefehle).

Sämtliche Daten stehen zeitgleich auf beiden Schnittstellen zur Verfügung.
Externe Tools wie UAExpert, Prosys, TIA Portal oder eigene Konnektoren
greifen ausschließlich darüber zu.

Detaillierte Darstellung in [docs/architecture.md](docs/architecture.md),
[docs/data-model.md](docs/data-model.md),
[docs/opcua-address-space.md](docs/opcua-address-space.md) und
[docs/s7-db-layout.md](docs/s7-db-layout.md). Beschreibung der realen
Anlage (nicht der Simulation): [machine/MACHINE.md](machine/MACHINE.md).

---

## Anlage starten

### Voraussetzungen

- Docker Engine und Docker Compose v2
- Optional für externe Tests: Python 3.10+ mit `pip install asyncua python-snap7 PyYAML`
- Linux-Hinweis: Port 102 ist Well-Known und benötigt Root.
  Alternative: `S7_HOST_PORT=1102` in `.env` setzen.

### Hochfahren

```bash
make env       # .env aus .env.example anlegen (einmalig)
make up        # Container bauen und starten
```

Nach `make up` ist der Stack vollständig einsatzbereit. Die Anlage steht im
Zustand `IDLE` und wartet auf den Start-Befehl (siehe nächster Abschnitt).

> **Auto-Start (optional):** `AUTO_START_PRODUCTION=true` in `.env` setzen
> (akzeptiert auch `1` und `yes`); dann sendet Node-RED ca. 5 s nach dem
> Boot einmalig `cmd.start`, sodass die Anlage direkt in `RUNNING` geht
> ohne manuelle Bedienung. Default `false` bewahrt das bisherige
> IDLE-Verhalten.

### Weitere Targets

```bash
make ps        # Status der beiden Container
make logs      # Logs aller Services im Tail
make test      # Smoke + OPC-UA-Test + S7-Test
make rebuild   # Stoppen, alles neu bauen, starten
make down      # Stoppen
```

`make help` listet alle Targets.

### Endpunkte

| Schnittstelle | Adresse |
|---|---|
| Bedien-Dashboard | <http://localhost:1880/dashboard> |
| Node-RED-Editor (Entwickler) | <http://localhost:1880> |
| OPC UA | `opc.tcp://<OPCUA_ALT_HOSTNAME>:4840` (Wert aus `.env`) |
| S7 / RFC1006 | `localhost:102` (Rack 0, Slot 1) |

> **Hinweis OPC UA:** `OPCUA_ALT_HOSTNAME` muss in `.env` auf die Adresse
> gesetzt werden, unter der der Docker-Host für den OPC-UA-Client erreichbar
> ist (LAN-IP, DNS-Name oder `localhost`). Der Wert wird in
> `docker-compose.yml` als Container-Hostname (`hostname:`) durchgereicht
> und kommt damit als `os.hostname()` in die per Discovery publizierte
> `EndpointUrl`. Ohne ihn meldet UAExpert `BadHostUnknown`, weil die
> Container-ID außerhalb des Docker-Bridge-Netzwerks nicht aufgelöst
> werden kann (siehe OPEN_QUESTIONS A17).

---

## Bedienen und Beeinflussen

Die Anlage lässt sich auf drei gleichwertigen Wegen steuern: über das
**Dashboard**, über **OPC UA** (Schreiben auf `Commands.*`) und über **S7**
(Schreiben auf DB4 ab Offset 68.0). Jeder Befehl wirkt unabhängig vom
Eingangsweg gleich.

### Bedien-Dashboard

Aufruf: <http://localhost:1880/dashboard>. Sechs Seiten in industriellem
Dunkel-Theme.

#### Seite 1 - Übersicht

- **Status-Ampel:** grau = IDLE, grün = RUNNING, gelb = PAUSED, rot = ERROR,
  blau = MAINTENANCE.
- **Aktuelles Bauteil:** Serialnummer, Status, aktueller Schweißpunkt,
  Zykluszeit.
- **Zähler:** Parts, OK, NOK, Scrap, Rework.
- **KPIs:** Durchsatz (Teile/min, gleitend 5 min), Yield (OK-Quote in %).
- **Steuerbuttons:**
  - **Start** - Anlage in RUNNING setzen.
  - **Stop** - Anlage sauber in IDLE.
  - **Pause** - Zyklus anhalten.
  - **Resume** - aus Pause fortsetzen.
- **Aktuelles Teil NIO** - markiert das laufende Bauteil unabhängig vom
  Prüfergebnis als nicht in Ordnung.
- **Fehler injizieren** - Dropdown mit allen vorhandenen Fehlerbildern
  (siehe unten); per Auswahl wird der Fehler sofort wirksam.
- **Cycle Speed Factor** - Slider 0.1× bis 10× zur Beschleunigung des
  Zyklus, etwa für schnelle Mengentests oder zur Echtzeit-Demonstration.

#### Seite 2 - Schweißprozess

- 3×4-Grid des Bauteils mit Status pro Plättchen
  (offen, geschweißt, NOK, nachgearbeitet).
- Live-Diagramm Schweißstrom je Punkt.
- Live-Diagramm Energie je Punkt.
- Tabelle der elf Schweißpunkte mit Soll, Ist und Delta.

#### Seite 3 - Prüfung

- Gesamtwiderstand mit Trend.
- Bar-Chart der elf Segmentwiderstände mit Toleranzbändern.
- Anzeige FaultSegment bei NOK.

#### Seite 4 - Roboter und Anlage

- Sechs Achspositionen, Geschwindigkeiten, Drehmomente.
- TCP-Position.
- Vibration, Temperatur.
- Hilfsmedien: Kühlmittelfluss und -temperatur, Druckluft,
  Leistungsaufnahme.

#### Seite 5 - Logs und KPIs

- Live-Logtabelle (letzte 200 Einträge, filterbar nach DEBUG/INFO/WARN/ERROR).
- Yield-Verlauf 24 h.
- Histogramm der häufigsten Fehlerpositionen.
- Verteilung der Zykluszeiten.

#### Seite 6 - Service

- **Elektrodenwechsel** - setzt das Verschleißmodell zurück, der Yield
  steigt im Folgelauf wieder zum Sollwert.
- **Counter zurücksetzen** - alle Mengenzähler auf 0 (Parts, OK, NOK,
  Scrap, Rework).
- Anzeige Elektrodenverschleiß in % (Drift).
- Liste aktiver Fehler.

### Verfügbare Fehlerinjektionen

| Code | Wirkung |
|---|---|
| `ERR_QR_READ` | QR nicht lesbar - Bauteil wird verworfen (`SCRAP`). |
| `ERR_WELD_CURRENT_LOW` | Schweißstrom zu niedrig - NOK an einer Position. |
| `ERR_WELD_FORCE_HIGH` | Elektrodenkraft zu hoch - NOK an einer Position. |
| `ERR_TEST_TIMEOUT` | Prüfung läuft in den Timeout - Bauteil NOK. |
| `ERR_ROBOT_FAULT` | Roboterfehler - Maschine geht in `ERROR`, Stopp. |
| `ERR_COOLANT_LOW` | Kühlmittelstand niedrig - Warnung, kein Stopp. |
| `ERR_AIR_PRESSURE` | Druckluft zu niedrig - Pause. |
| `ERR_EMERGENCY_STOP` | Not-Aus - sofortiger Stopp. |

### Steuerung über die Schnittstellen

Sämtliche Buttons und Eingaben des Dashboards sind auch als schreibbare
Knoten über OPC UA (`Commands.*`) und als Bits in S7 DB4 (ab Offset 60.0)
verfügbar. Das vollständige Workflow-Beispiel folgt im nächsten Abschnitt.

### Was passiert, wenn der Bediener nichts macht

Im Default startet die Anlage nicht von selbst - sie verbleibt in `IDLE`.
Sobald `Start` ausgelöst wurde, läuft sie kontinuierlich bis zum nächsten
`Stop`, `Pause` oder bis ein Robot- bzw. Not-Aus-Fehler eintritt. Während
des Betriebs entstehen ohne weitere Eingaben automatisch typische
Verteilungen (rund 85 % IO, 13 % nach Nacharbeit IO, 2 % SCRAP) sowie ein
langsam ansteigender Elektrodenverschleiß bis zum nächsten
`Elektrodenwechsel`.

---

## Schnittstellen verwenden - Schritt für Schritt

Dieser Abschnitt zeigt einen praktischen Workflow vom ersten Verbindungs-
aufbau bis zum eigenen Konnektor. Die Schritte bauen aufeinander auf.

Voraussetzung für die Python-Beispiele:

```bash
pip install asyncua python-snap7
```

### Schritt 1 - Stack hochfahren und prüfen

```bash
make up
make ps
```

`make ps` muss beide Container als `Up (healthy)` anzeigen. Schneller
Funktionscheck:

```bash
curl -fsS http://localhost:1880/      # Node-RED-Editor antwortet
nc -zv localhost 4840                 # OPC-UA-Port offen
nc -zv localhost 102                  # S7-Port offen
```

### Schritt 2 - Smoke-Test ausführen

Vor eigenen Experimenten den eingebauten Test laufen lassen. Er prüft
beide Schnittstellen end-to-end:

```bash
make test
```

Das ruft im Hintergrund [`tests/opcua_client_test.py`](tests/opcua_client_test.py)
und [`tests/s7_client_test.py`](tests/s7_client_test.py) auf. Beide müssen
mit Exit-Code 0 enden.

### Schritt 3 - OPC UA: verbinden und Adressraum browsen

Ziel: Sich vergewissern, dass der Server antwortet und die erwartete
Knotenstruktur unter `Objects/ZKS` vorhanden ist.

**Mit UAExpert oder Prosys:**

1. Endpoint hinzufügen: `opc.tcp://localhost:4840`.
2. Anonymous Login wählen (alternativ `operator` / `zks2026`).
3. Im AddressSpace: `Objects/ZKS/Machine`, `.../Part`, `.../Welds`,
   `.../Test`, `.../Robot`, `.../Utility`, `.../Commands`.

**Mit Python (`asyncua`):**

```python
import asyncio
from asyncua import Client

async def main():
    async with Client("opc.tcp://localhost:4840") as c:
        root = c.nodes.root
        for child in await root.get_children():
            print(await child.read_browse_name())

asyncio.run(main())
```

### Schritt 4 - OPC UA: Werte lesen und abonnieren

```python
import asyncio
from asyncua import Client

async def main():
    async with Client("opc.tcp://localhost:4840") as c:
        ns = 5
        state = await c.get_node(f"ns={ns};s=Machine.State").read_value()
        parts = await c.get_node(f"ns={ns};s=Machine.PartCounter").read_value()
        yield_ = await c.get_node(f"ns={ns};s=Machine.Yield").read_value()
        print(f"State={state} Parts={parts} Yield={yield_:.1f}%")

asyncio.run(main())
```

Subscription auf den Schweißstrom des aktuellen Punkts:

```python
import asyncio
from asyncua import Client

class Sub:
    def datachange_notification(self, node, val, data):
        print("Update:", node, "=", val)

async def main():
    async with Client("opc.tcp://localhost:4840") as c:
        sub = await c.create_subscription(500, Sub())
        node = c.get_node("ns=5;s=Welds.Weld_03.Current")
        await sub.subscribe_data_change(node)
        await asyncio.sleep(30)

asyncio.run(main())
```

### Schritt 5 - OPC UA: Anlage steuern

Die Befehle aus dem Dashboard sind 1:1 unter `Commands` schreibbar:

```python
import asyncio
from asyncua import Client

async def main():
    async with Client("opc.tcp://localhost:4840") as c:
        ns = 5
        # Anlage starten und auf 5x beschleunigen
        await c.get_node(f"ns={ns};s=Commands.Start").write_value(True)
        await c.get_node(f"ns={ns};s=Commands.CycleSpeedFactor").write_value(5.0)
        await asyncio.sleep(15)

        # Fehler injizieren - Anlage geht in ERROR
        await c.get_node(f"ns={ns};s=Commands.InjectFault").write_value("ERR_ROBOT_FAULT")
        await asyncio.sleep(2)

        # Sauber stoppen, Counter zurücksetzen, Elektrode wechseln
        await c.get_node(f"ns={ns};s=Commands.Stop").write_value(True)
        await c.get_node(f"ns={ns};s=Commands.ResetCounters").write_value(True)
        await c.get_node(f"ns={ns};s=Commands.ChangeElectrode").write_value(True)

asyncio.run(main())
```

### Schritt 6 - S7: verbinden und DBs lesen

```python
import snap7
from snap7.util import get_int, get_dint, get_real

c = snap7.client.Client()
c.connect("127.0.0.1", 0, 1, tcpport=102)

# DB1 - Maschine
db1 = c.db_read(1, 0, 60)
print("State =", get_int(db1, 0))         # 0=IDLE 1=RUNNING 2=PAUSED 3=ERROR
print("Parts =", get_dint(db1, 4))
print("Yield =", get_real(db1, 28))

# DB3 - Test
db3 = c.db_read(3, 0, 60)
print("TotalRes(mOhm) =", get_real(db3, 4))
print("Result =", get_int(db3, 8))         # 0=PENDING 1=OK 2=NOK

c.disconnect()
```

### Schritt 7 - S7: Anlage steuern

Trigger-Bits in DB4 ab Offset 68.0 schreiben. Node-RED erkennt die Flanke,
führt den Befehl aus und setzt das Bit nach 200 ms automatisch zurück.

```python
import snap7
from snap7.util import set_bool, set_real

c = snap7.client.Client()
c.connect("127.0.0.1", 0, 1, tcpport=102)

# Cmd_Start = Bit 68.1
buf = bytearray(1)
set_bool(buf, 0, 1, True)
c.db_write(4, 68, bytes(buf))

# Cmd_CycleSpeedFactor = REAL bei Offset 92.0
speed = bytearray(4)
set_real(speed, 0, 5.0)
c.db_write(4, 92, bytes(speed))

c.disconnect()
```

### Schritt 8 - Akzeptanz-Szenarien automatisiert

Im Repo liegt ein vorgefertigter Szenario-Runner, der die Akzeptanz-
kriterien aus [docs/test-scenarios.md](docs/test-scenarios.md) durchläuft:

```bash
python3 tests/scenario_runner.py
```

Er führt nacheinander Szenario A (100 Bauteile bei Speed 10), B (manuelle
NIO-Markierung), C (Roboterfehler) und D (Elektrodenwechsel) aus und meldet
das Ergebnis je Szenario.

### Schritt 9 - Eigenen Konnektor bauen

Sobald die Beispiele laufen, lässt sich auf derselben Basis ein eigener
Konnektor entwickeln:

- Tag-Liste und Datentypen: [docs/data-model.md](docs/data-model.md)
- OPC-UA-NodeIds und Schema: [docs/opcua-address-space.md](docs/opcua-address-space.md)
- S7-DB-Offsets: [docs/s7-db-layout.md](docs/s7-db-layout.md)
- Architektur und Datenflüsse: [docs/architecture.md](docs/architecture.md)

Empfohlene Reihenfolge beim Konnektorbau:

1. Read-Pfad gegen OPC UA implementieren (`Machine.PartCounter`,
   `Machine.Yield`, `Test.Result`).
2. Subscription für Live-Größen ergänzen (`Welds.Weld_*.Current`).
3. Schreibpfad gegen `Commands.*` testen (Start/Stop, Speed).
4. Optional zweiten Read-Pfad gegen S7 DB1/DB3 zur Quervalidierung.

---

## Lizenz

MIT - siehe [LICENSE](LICENSE).