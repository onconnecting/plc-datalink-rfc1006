---
paths:
  - "frontend/**"
---

# Frontend (Angular) Rules

Das Frontend ist eine Angular-SPA, die von nginx auf Port 80 ausgeliefert wird und mit dem Flask-Backend über relative HTTP-Pfade kommuniziert.

**Verbindliches Design-Referenzdokument:** [`docs/design/onconnecting-ci/ci-manual_onconnecting.md`](../../../docs/design/onconnecting-ci/ci-manual_onconnecting.md) — Corporate Identity Manual onconnecting v1.5.
Alle UI-Änderungen müssen diesem CI folgen. Bei Widerspruch gewinnt das CI gegenüber jeglichen Tailwind- oder Material-Defaults.

## Verzeichnisstruktur

```
frontend/
├── src/
│   ├── app/
│   │   ├── app.module.ts
│   │   ├── app.component.{ts,html,css,spec.ts}
│   │   ├── header/
│   │   ├── create-configuration/      # Formular für neue/geänderte Machine-Konfiguration
│   │   ├── configuration-overview/    # Liste persistierter Konfigurationen + Start/Edit/Remove
│   │   ├── plc-states/                # Live-PLC-Statusansicht (Start/Stop/Remove)
│   │   ├── modals/                    # Wiederverwendbare Dialoge
│   │   ├── models/                    # TypeScript-Interfaces parallel zum Backend-Model
│   │   └── services/                  # HTTP-Clients zum Flask-Backend
│   ├── assets/                        # u. a. Logo-Dateien aus docs/design/onconnecting-ci/logo/
│   ├── index.html
│   ├── main.ts
│   └── styles.css                     # Globale Design-Tokens (CI-konform)
├── config/
│   ├── nginx-main.conf
│   └── nginx-custom.conf
├── angular.json
├── package.json / package-lock.json
├── tsconfig.{json,app.json,spec.json}
└── Dockerfile
```

---

## Corporate Identity — verbindliche Vorgaben

### Farben (CI § 3)

Die folgenden Design-Tokens müssen 1:1 als CSS-Custom-Properties in `frontend/src/styles.css` (oder einem dedizierten `_tokens.css`) definiert sein und sind die einzige zulässige Farbquelle. **Keine** Inline-Hex-Werte in Komponenten-Styles, keine Tailwind-Defaults, keine Material-Theme-Farben.

```css
:root {
  /* Akzent (Primärpalette Cyan) */
  --color-accent-50:  #ECFEFF;
  --color-accent-300: #67E8F9;
  --color-accent-500: #06B6D4;  /* Primärfarbe, CTAs, Highlights */
  --color-accent-600: #0891B2;  /* Hover, aktive Zustände */
  --color-accent-700: #0E7490;  /* Tiefe Akzente */

  /* Neutral (Slate) */
  --color-neutral-50:  #F8FAFC;
  --color-neutral-100: #F1F5F9;
  --color-neutral-200: #E2E8F0;
  --color-neutral-300: #CBD5E1;
  --color-neutral-400: #94A3B8;
  --color-neutral-500: #64748B;
  --color-neutral-600: #475569;
  --color-neutral-700: #334155;
  --color-neutral-800: #1E293B;
  --color-neutral-900: #0F172A;

  /* Sekundärgrau (bewusste zweite Markenfarbe) */
  --color-gray-400: #94A3B8;
  --color-gray-700: #334155;

  /* Funktionsfarben */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error:   #EF4444;
}
```

**60-30-10-Regel** (CI § 3.6):
- 60 % Neutral (Weiß und helle Slate-Töne `--color-neutral-50/100`)
- 30 % mittlere/tiefe Slate-Töne (`--color-neutral-700/800/900`)
- 10 % Cyan-Akzent (`--color-accent-500`)

Cyan ist **Signalfarbe** (CTAs, aktive Zustände, hervorgehobene Verbindungen, Statusindikatoren wie "Connected"), kein Flächenfüller. Keine Cyan-Hintergründe auf großen Flächen.

**Funktionsfarben** ausschließlich für Statusrückmeldung:
- `--color-success` für `Connected` / erfolgreiches Submit / "Machine läuft"
- `--color-warning` für `Standby` / Validierungs-Hinweise
- `--color-error` für `Disconnected (Fehler)` / Backend-4xx/5xx / ungültige Eingaben
- Standard-/Idle-Zustände bleiben neutral.

### Typografie (CI § 4)

Zwei-Schriften-System ist **verbindlich**:

| Funktion | Schrift | Variable |
|---|---|---|
| Headlines, Subheads, Labels, technische Werte (IP, Port, PLC-Adresse), Code | **Consolas** Regular | `var(--font-headline)` / `var(--font-mono)` |
| Body, Beschreibungen, Hilfetexte | **Calibri Light** | `var(--font-body)` |

```css
:root {
  --font-headline: Consolas, "Cascadia Mono", "DejaVu Sans Mono",
                   "Liberation Mono", "Courier New", monospace;
  --font-body:     "Calibri Light", "Segoe UI Light", "Helvetica Neue Light",
                   -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono:     Consolas, "Cascadia Mono", "DejaVu Sans Mono", monospace;

  --font-size-xs:   0.75rem;
  --font-size-sm:   0.875rem;
  --font-size-base: 0.9375rem;
  --font-size-lg:   1.125rem;
  --font-size-xl:   1.375rem;
  --font-size-2xl:  1.75rem;
  --font-size-3xl:  2rem;
  --font-size-4xl:  2.625rem;
  --font-size-5xl:  3.5rem;

  --line-height-tight:   1.1;
  --line-height-snug:    1.3;
  --line-height-normal:  1.5;
  --line-height-relaxed: 1.65;
}

body  { font-family: var(--font-body); font-size: var(--font-size-base); line-height: var(--line-height-relaxed); color: var(--color-neutral-700); background:#FFFFFF; }
h1,h2,h3,h4 { font-family: var(--font-headline); font-weight: 400; letter-spacing: -0.01em; }  /* Headlines NIE fett (CI § 4.1) */
code, pre, .mono { font-family: var(--font-mono); }
```

Regeln (CI § 4.6):
- Headlines linksbündig, **nie zentriert**, **nie fett** (Hierarchie über Größe/Position, nicht über Weight).
- Body linksbündig, Flattersatz rechts.
- Zeilenlänge im Body 60–75 Zeichen.
- PLC-Adressen, IPs, Ports, Topic-Pfade, Tag-Namen werden im UI immer in `--font-mono` gerendert (z. B. `DB2000.X0.0`, `192.168.1.1`, `on/ot-connector/devBoard/raw`).

### Logo und Markenname (CI § 5)

- **Wortmarke** `onconnecting` immer **kleingeschrieben** — auch am Satzanfang, in Toasts, in Browser-Tabs, in `<title>`. Niemals `Onconnecting`, `OnConnecting`, `ONCONNECTING`.
- Logo-Dateien aus [`docs/design/onconnecting-ci/logo/`](../../../docs/design/onconnecting-ci/logo/) verwenden, **nicht** neu generieren oder umfärben.
- Drei zulässige Farbvarianten: Cyan `#06B6D4`, Slate `#0F172A`, Gray `#94A3B8`. Weiß `#FFFFFF` nur auf dunklen Hintergründen.
- Schutzraum = Höhe des Kleinbuchstabens `o` auf allen vier Seiten — keine UI-Elemente in diesen Bereich legen.
- Mindestbreite auf Bildschirm: 96 px. Darunter Kürzel `oc` (gleiche Schrift, gleiche Farbregeln) verwenden — relevant für Favicons.
- Header-Komponente (`src/app/header/`) trägt das Logo in `--color-neutral-900` als Standard, in `--color-accent-500` nur dort, wo der CI-Akzent gewünscht ist.

### Layout, Spacing, Radius (CI § 7)

Spacing-Skala auf 4-px-Basis:

```css
:root {
  --space-1:  0.25rem;   /* 4 px  */
  --space-2:  0.5rem;    /* 8 px  */
  --space-3:  0.75rem;   /* 12 px */
  --space-4:  1rem;      /* 16 px */
  --space-6:  1.5rem;    /* 24 px */
  --space-8:  2rem;      /* 32 px */
  --space-12: 3rem;      /* 48 px */
  --space-16: 4rem;      /* 64 px */
  --space-24: 6rem;      /* 96 px */

  --radius-none: 0;
  --radius-sm:   2px;    /* Tags, Labels */
  --radius-md:   4px;    /* Buttons, Inputs */
  --radius-lg:   8px;    /* Karten */
}
```

- 12-Spalten-Grid, Gutter 24 px Desktop / 16 px Mobile, Inhalts-Maxbreite 1280 px.
- **Scharfe Kanten oder minimaler Radius**. Stark abgerundete Elemente (Pillen, vollständig runde Buttons) widersprechen dem technisch-grafischen Charakter und sind nicht zulässig.
- Keine Schlagschatten auf Diagrammen, keine 3D-Effekte (CI § 6.3).

### Bildsprache (CI § 6)

- Technische Diagramme/Schaltbilder statt Stockfotos.
- Linien-Icons im Stil technischer Zeichnungen: 1 px Stärke, monochrom; Hervorhebungen 1.5 px.
- Cyan ausschließlich als Signalfarbe für aktive Verbindungen oder hervorgehobene Knoten.
- Beschriftungen in Consolas 10–12 pt.
- Werkzeuge für eingebettete Diagramme: Mermaid (in Doku) oder draw.io-Export — kein generischer Stockfoto-Import.

### Tonalität in UI-Texten (CI § 2)

Gilt für jedes vom Frontend gerenderte Wort — Labels, Buttons, Tooltips, Validierungs-Meldungen, Toast-Texte, Fehlermeldungen, Hilfetexte, `aria-label`, Browser-`<title>`:

- Sachlich-präzise, kurze Sätze, aktiv statt passiv.
- Fachterminologie korrekt: **PLC**, **RFC1006**, **S7**, **MQTT**, **OPC UA**, **AAS** — keine Marketing-Übersetzungen.
- Konkrete Zahlen, Versionen, Quellen statt Floskeln.
- **Keine Emojis. Keine Ausrufezeichen-Ketten.** Einzelne Ausrufezeichen nur bei tatsächlichen Fehlerzuständen.
- Englische Fachbegriffe bleiben englisch (Shopfloor, Asset Administration Shell), wenn keine etablierte deutsche Entsprechung existiert.
- Markenname immer `onconnecting`, kleingeschrieben.

Beispiele:

| Statt | Sondern |
|---|---|
| "Maschine erfolgreich gestartet!" | "Machine `<name>` gestartet. Telegraf läuft." |
| "Ups, da ist etwas schiefgelaufen!" | "Konfiguration nicht gespeichert. CouchDB lieferte 409 (Konflikt — `_rev` veraltet)." |
| "Bitte gib eine gültige IP-Adresse ein!" | "PLC IP: ungültiges IPv4-Format (z. B. `192.168.1.1`)." |
| "Smart configuration for your industrial setup" | "Konfiguration für S7/RFC1006 → MQTT." |

### Accessibility und Kontrast

- WCAG 2.2 als Untergrenze (CI § 12). Body-Text auf weißem Grund mindestens `--color-neutral-600` (`#475569`), idealerweise `--color-neutral-700` (`#334155`).
- Cyan `--color-accent-500` auf Weiß ist nur für mittelgroße/große Schrift kontraststark genug — für Body-Text **nicht** als Vordergrundfarbe einsetzen.

---

## Komponenten-Konventionen

- Ein Feature-Verzeichnis pro UI-Bereich (vorhandene Struktur: `header`, `create-configuration`, `configuration-overview`, `plc-states`, `modals`).
- Jedes Komponenten-Verzeichnis enthält `.ts`, `.html`, `.css`, `.spec.ts`.
- Templates bleiben deklarativ — Zustand und Seiteneffekte in der Komponentenklasse oder einem Service.
- Komponenten-eigenes CSS nutzt **ausschließlich** die Design-Tokens aus `:root` — keine Inline-Hex-Werte, keine Magic-Numbers für Spacing.
- PLC-Adressen (`<area>.<type><address>[.extra]`) und IPv4-Eingaben werden im Formular validiert, nicht erst im Backend.

## Service-Konventionen

- Ein Angular-Service pro Backend-Ressourcenfamilie (`machine`, `config`, …).
- Services nutzen `HttpClient` und liefern `Observable<T>`, typisiert gegen die Interfaces in `models/`.
- Keine `fetch`-Aufrufe direkt in Komponenten — immer über einen Service.
- Basis-URL wird über denselben nginx ausgeliefert — relative Pfade verwenden (`/config/read/all`, `/machine/start`, …).
- Fehlerausgaben an den Nutzer folgen der Tonalität oben — kein technischer Trace, aber präzise.

## Model-Konventionen

- TypeScript-Interfaces in `src/app/models/` spiegeln das Backend-JSON 1:1 (camelCase: `machineName`, `plcIp`, `mqttTopic`, `tagAddress`, …).
- Backend-Modell und Frontend-Modell werden in derselben Änderung aktualisiert (siehe [.claude/rules/backend.md](backend.md)).

## nginx-Konfiguration

- `nginx-main.conf` global, `nginx-custom.conf` Server-Block.
- API-Proxying explizit halten — keine Wildcard-Fallbacks für `/swagger`, `/static`, `/config`, `/machine`.
- Neue `location`-Blöcke nur, wenn sie reale Backend-Routen abdecken.

## Qualitätsstandards

- `ng build` (bzw. `npm run build`) ohne TypeScript-Fehler vor jedem Commit.
- `ng test` für vorhandene Specs; neue Specs nur bei nichttrivialer Logik oder auf Anforderung.
- **Keine neuen npm-Pakete ohne explizite Freigabe** — insbesondere keine UI-Frameworks (Material, Bootstrap, PrimeNG), die das CI überschreiben würden. Wenn ein UI-Helper nötig ist: ADR via `/architecture`. UI-Primitive (Overlay, Dialog, Focus-Trap, ARIA-Live) kommen ausschließlich aus `@angular/cdk` — siehe [ADR-0003](../../architecture/decisions/ADR-0003-frontend-ui-foundation-angular-cdk.md). Größere Frontend-Umbauten erfolgen als Greenfield in `frontend-next/` mit anschließendem Verzeichnis-Tausch — siehe [ADR-0004](../../architecture/decisions/ADR-0004-frontend-greenfield-migration-strategy.md).
- Vor dem Commit prüfen: kein eingeschleustes Tailwind/Material-Theme, keine fett gesetzten Headlines, keine Emojis in Strings, keine 3D/Schatten-Effekte, kein zentriert ausgerichteter Body-Text.
- Bei jeder UI-Änderung manuell im Chromium-basierten Browser auf `http://localhost` gegen die CI-Vorgaben prüfen (Farben, Schrift, Spacing, Tonalität).
