# Umsetzung in diesem Repo — Django 5.2, Cleaning_SaaS

**Was diese Datei abdeckt:** was `apps/contracts` heute wirklich modelliert (Feld für Feld, mit
`datei:zeile`), wie effektiv-datierte Tarifdaten gespeichert werden müssen, damit ein
historischer Lohnlauf reproduzierbar bleibt, wie eine neue Lohnzeile per Data-Migration
nachgezogen wird, wohin die Zuschlagsberechnung gehört und was ein DATEV-/CSV-Export braucht.
**Stand: 2026-08-29**, verifiziert gegen den laufenden Code und die Dev-Datenbank.
**Herkunft:** direkte Lektüre von `/Users/Geronimo/Projects/Cleaning_SaaS`, ergänzt um
`scratchpad/dossier/contracts.md` und `scratchpad/dossier/_verified-ground-truth.md`.

Umgebung (verifiziert): Python **3.12.13**, **Django 5.2.17**, venv unter
`/Users/Geronimo/Projects/Cleaning_SaaS/.venv`. Python immer als
`/Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python` aufrufen. `pip` ist im venv **nicht**
verfügbar. Es gibt **kein `.git`** — Änderungen sind nicht zurückrollbar.
`config/settings.py:107-110`: `LANGUAGE_CODE = "de"`, `TIME_ZONE = "Europe/Berlin"`,
`USE_TZ = True`.

---

## 1. BESTAND — was heute existiert

### 1.1 `WageFloor` (`apps/contracts/models.py:57-89`) — **Fakt**

```python
class WageFloor(models.Model):
    class Kind(models.TextChoices):
        GENERAL  = "GENERAL",  "Mindestlohn general"
        GEBAEUDE = "GEBAEUDE", "Mindestlohn Gebäudereinigung LG1"

    kind          = models.CharField(max_length=16, choices=Kind.choices)
    hourly_amount = models.DecimalField(max_digits=6, decimal_places=2)
    valid_from    = models.DateField()
    valid_to      = models.DateField(null=True, blank=True)
    source_note   = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("kind", "-valid_from")
```

- Klassenmethode `current(cls, kind, on=None)` (`models.py:83-89`): `on` fällt auf
  `timezone.localdate()` zurück, filtert `valid_from__lte=on` und
  `Q(valid_to__isnull=True) | Q(valid_to__gte=on)`, nimmt `.first()`. Wegen
  `Meta.ordering = ("kind", "-valid_from")` gewinnt die Zeile mit dem **größten `valid_from`**.
  Gibt `Decimal` oder `None` zurück.
- **Es gibt keinen `region`-Wert und keine Lohngruppe.** `GEBAEUDE` steht ausschließlich für
  LG 1. LG 2–9 sind im Datenmodell nicht vorhanden.
- **Keine Constraint gegen überlappende Zeiträume.** Zwei offene Zeilen desselben `kind` sind
  technisch erlaubt; nur die `Meta.ordering` verhindert das falsche Ergebnis. Eine Änderung an
  `Meta.ordering` wäre still fatal.
- **Kein Django-Admin.** Es existiert **keine einzige `admin.py`** im Repo (`find apps -name
  admin.py` liefert nichts), obwohl der Docstring bei `models.py:59-60` verspricht, die Werte
  seien „fără deploy" korrigierbar. Heute sind sie es nur per Data-Migration oder Shell.

### 1.2 `MinijobThreshold` (`apps/contracts/models.py:92-113`) — **Fakt**

Gleiche Form ohne `kind`: `monthly_limit` `Decimal(7,2)`, `valid_from`, `valid_to`,
`source_note`, `Meta.ordering = ("-valid_from",)`, `current(on=None)` analog. Docstring
`models.py:93-97` hält die Formel fest: „Mindestlohn × 130 / 3, rotunjită în sus".

### 1.3 Die gesäten Zeilen (`0002_seed_wage_floors.py` **+** `0005_wage_floor_2026.py`) — **Fakt**

**`0002` allein beschreibt die DB nicht mehr.** Die `GEBAEUDE`-Stufe für 2026 kommt aus
`apps/contracts/migrations/0005_wage_floor_2026.py`, das die 2025er Zeile schließt und die
2026er einfügt. Wirksamer Stand, im Dev-DB am 2026-08-29 verifiziert:

| Modell | `kind` | Betrag | `valid_from` | `valid_to` | `source_note` | gesetzt von |
|---|---|---|---|---|---|---|
| `WageFloor` | `GENERAL` | `12.82` | 2025-01-01 | 2025-12-31 | `MiLoG 2025` | `0002` |
| `WageFloor` | `GENERAL` | `13.90` | 2026-01-01 | `None` | `MiLoG 2026 — DE CONFIRMAT` | `0002` |
| `WageFloor` | `GEBAEUDE` | `14.25` | 2025-01-01 | 2025-12-31 | `Gebäudereinigung LG1 Innenreinigung, Mindestlohntarifvertrag 2025` | `0005` |
| `WageFloor` | `GEBAEUDE` | `15.00` | 2026-01-01 | `None` | `Lohntarifvertrag LG 1, ab 01.01.2026, allgemeinverbindlich (§ 7 AEntG)` | `0005` |
| `MinijobThreshold` | — | `556.00` | 2025-01-01 | 2025-12-31 | `Geringfügigkeitsgrenze 2025` | `0002` |
| `MinijobThreshold` | — | `603.00` | 2026-01-01 | `None` | `Mindestlohn × 130/3 — DE CONFIRMAT` | `0002` |

Die Migrationen schreiben mit `update_or_create`, Schlüssel `(kind, valid_from)` bzw.
`(valid_from,)`; das `backwards` von `0002` löscht **alle** Zeilen beider Modelle
(`0002_seed_wage_floors.py:44-46`) — ein Rückwärtslauf ist also destruktiv. Das `backwards`
von `0005` fasst nur die eigenen Zeilen an; so gehört es gemacht.

Damit gilt `WageFloor.current("GEBAEUDE", date(2026, 6, 1)) == Decimal("15.00")` und
`… date(2025, 6, 1) == Decimal("14.25")` — ein Vertrag mit Beginn 2026 zu 14,25 € wird
korrekt blockiert (`tests/test_contracts.py:38-41`). **Hier ist nichts mehr zu reparieren.**

### 1.4 Der Compliance-Check (`compliance_report`, `apps/contracts/models.py:197-248`) — **Fakt**

Zwei Methoden, klar getrennt:

- **`compliance_report() -> list[ComplianceIssue]`** (`models.py:197-248`) ist die
  eigentliche Prüfung und **der Erweiterungspunkt**. Neue Regeln kommen hierhin.
- **`compliance_issues() -> list[str]`** (`models.py:193-195`) ist nur der Anzeige-Shim:
  `[issue.message for issue in self.compliance_report()]`.

`ComplianceIssue` (`models.py:45-55`) ist ein `@dataclass(frozen=True)` mit den Feldern
`code: str`, `message: str`, `blocking: bool` — **die Severität ist ein typisiertes Feld,
nicht etwas, das aus dem Meldungstext erraten wird.**

Was geprüft wird:

1. Boden = `max(general, sector)` über `WageFloor.current(..., self.start_date)`
   (`models.py:207-209`); bei `hourly_wage < floor` →
   `code="WAGE_FLOOR"`, `blocking=is_employment` (`models.py:213-222`). Die Meldung lautet
   wörtlich (`models.py:216-221`):
   „Salariul orar {hourly_wage} € este sub pragul de {floor} € valabil la {dd.mm.yyyy}."
   — bei `WERKVERTRAG` beginnt sie mit „Onorariul orar …". **Kein Wort „legal"**, und der
   **Stichtag steht mit in der Meldung**.
2. Bei `MINIJOB`: `monthly_gross > MinijobThreshold.current(self.start_date)` →
   `code="MINIJOB_LIMIT"`, `blocking=True` (`models.py:223-233`). `monthly_gross` ist
   `hours_per_month * hourly_wage`, `quantize(Decimal("0.01"))` (`models.py:189-191`).
3. `EngagementModel.TEMP_AGENCY` → `code="AUEG_LICENCE"`, `blocking=True`,
   „Detașarea de personal necesită licență AÜG. Blocat." (`models.py:234-238`).
4. `WERKVERTRAG` → `code="SCHEINSELBSTSTAENDIGKEIT"`, `blocking=False`, § 7 SGB IV
   (`models.py:240-248`).

`services.send_for_signature` (`apps/contracts/services.py:25-33`) filtert auf genau dieses
Feld: `blocking = [i.message for i in draft.compliance_report() if i.blocking]`
(`services.py:26`). Wer eine Regel ergänzt, setzt `blocking` explizit — es wird nie aus dem
Text abgeleitet. `tests/test_contracts.py:43-50` sichert das ab.

Alle Sätze werden **zum `start_date` aufgelöst**, nicht zu „heute":
`apps/contracts/views.py:77` (`ctx["issues"] = contract.compliance_issues()`) ist deshalb ein
Beispiel für **korrekte** Verwendung. `timezone.localdate()` in `current()` greift nur, wenn
`on` fehlt — auf diesem Pfad passiert das nie (`tests/test_contracts.py:68-74`).

### 1.5 Weiterer relevanter Bestand — **Fakt**

| Objekt | Ort | Warum es für Lohn relevant ist |
|---|---|---|
| `ContractDraft.hours_per_month`, `.hourly_wage` (`Decimal(6,2)`), `.vacation_days` (Default **20**) | `apps/contracts/models.py:163-164`, `:167` | Die Lohnbasis pro Vertrag. `vacation_days=20` liegt **unter** dem tariflichen 30-Tage-Anspruch (RTV § 14) — bewusst prüfen, bevor Verträge erzeugt werden |
| Eingefrorener Vertragstext + SHA-256 | `apps/contracts/models.py:170-171`, `services.render_contract` | Präzedenzfall für „historische Daten sind unveränderlich" — dieselbe Haltung braucht die Lohnabrechnung |
| `ContractSignature.save` wirft bei erneutem Speichern | `apps/contracts/models.py:256-283`, `raise` bei `:280` | Muster für echte Immutabilität |
| `Shift`: `date`, `start_time`, `duration_minutes`, `checked_in_at`, `checked_out_at`, `actual_minutes`, `billable_minutes` | `apps/planning/models.py:140-186` | Der Input jeder Zuschlagsberechnung. Es gibt **kein** `end_time` — das Ende ist `start_time + duration_minutes` |
| `ShiftEvent` als append-only Journal | `apps/planning/models.py:188-221` | Revisionssicherheit ist bereits Bestand |
| `attendance.correct_minutes(...)` | `apps/planning/attendance.py:148` | Korrektur = neues Ereignis mit Akteur und Grund |
| `attendance.time_records(account, start, end, worker=None)` | `apps/planning/attendance.py:178` | Docstring: „ce trebuie să poți arăta la un control (Zoll / FKS)" — der Keim des Nachweisexports |
| `geo.Region` = **Bundesland**, mit `code` („HH", „SH", …) | `apps/geo/models.py:4-17` | Der Feiertagskalender hängt hier an. **Achtung: nur 2 Zeilen gesät (HH, SH)** — die restlichen 14 Länder fehlen |
| `Site → Locality → Region` | `apps/planning/models.py:21-38`, `apps/geo/models.py:20-44` | Damit ist das Bundesland des **Objekts** ableitbar, wie es die Feiertagsregel verlangt |
| `JobPosting.salary_min/max/currency/unit` | `apps/jobs/models.py:38-43` | Öffentliche Gehaltsangabe; gesät mit 14,25–15,00 €/h, also LG 1 2025→2026 |

**Es gibt keinen Django-Admin, keine Lohngruppen, keine Lohnsätze je Gruppe, keine
Zuschlagsarten, keinen Feiertagskalender, kein Urlaubskonto, keine Entgeltfortzahlung, keinen
Lohnlauf und keinen Export.** Alles Folgende ist **Vorschlag**.

---

## 2. Wie effektiv-datierte Tarifdaten gespeichert werden müssen

Nicht verhandelbar, unabhängig davon, welches Modell die Daten trägt:

1. **Eine Zeile pro (Schlüssel, Gültigkeitsbeginn).** Ein Satz wird nie überschrieben. Der
   Lohntarifvertrag 2025/2026 enthält allein schon zwei Stufen (01.01.2025 und 01.01.2026)
   innerhalb eines Vertrags.
2. **Auflösung immer über ein übergebenes Datum.** Signaturen sehen aus wie
   `rate(lohngruppe, on: date)`, nie wie `rate(lohngruppe)`. Das Ereignisdatum ist der
   **Schichttag** (Lohnlauf), der **Vertragsbeginn** (Compliance) oder der **Urlaubsantritt**
   (Urlaubsgeld) — nie `today()`.
3. **`valid_to` der Vorgängerzeile beim Nachziehen schließen.** Formal reicht die Ordnung, aber
   offene Vorgängerzeilen machen die Tabelle unlesbar und die Korrektheit von einer
   `Meta.ordering` abhängig.
4. **`source_note` ist Pflicht, nicht Kosmetik.** Format: *Vertragsname, Gruppe, Wirkung ab,
   Quelle*. Beispiel: `"Lohntarifvertrag 2025/2026, LG 4, ab 01.01.2026 (pland.app/blog/tariflohn-2026-…)"`.
   `source_note` ist auf 200 Zeichen begrenzt — bei längeren Belegen die URL kürzen, nicht die
   Quelle weglassen.
5. **`DecimalField`, nie `FloatField`.** Prozentsätze werden gespeichert, wie der Tarif sie
   nennt, nicht aus Vorher/Nachher zurückgerechnet.
6. **Fehlender Satz = harter Stopp.** `current()` gibt `None` zurück, wenn keine Zeile passt
   (z. B. `WageFloor.current("GENERAL", date(2024,6,1))` → `None`). Ein Lohnlauf, der `None`
   bekommt, **bricht ab**; er weicht nicht auf den nächstbesten Wert aus.
7. **Ein historischer Lauf muss reproduzierbar sein.** Über die aufgelöste Rate hinaus speichert
   jede Abrechnungsposition den **verwendeten Satz, den verwendeten Prozentsatz und die
   Modell-ID der Quellzeile**. Nur so lässt sich ein Lauf nach einer Datenkorrektur noch
   erklären. Dasselbe Prinzip, das `ContractDraft.rendered_body` + `body_sha256` schon umsetzt.
8. **Regionsachse von Tag eins.** Auch wenn die Quellen 2025/2026 eine bundesweite Tabelle
   zeigen: `region` (`BUND` / `WEST` / `OST`) gehört in den Schlüssel. Nachrüsten heißt Rate-
   Tabelle migrieren.

---

## 3. Rezept 1 — neue Lohnuntergrenze per Data-Migration (**erprobtes Muster**)

Dieses Muster ist im Repo bereits **umgesetzt**:
`apps/contracts/migrations/0005_wage_floor_2026.py` zieht LG 1 zum 01.01.2026 auf 15,00 €
nach und schließt die 2025er Zeile auf `2025-12-31`. Es ist das Vorbild, **kein offener
Arbeitsauftrag** — 15,00 € ab 2026 steht schon in der DB.

**Letzte Migration der App ist `0005_wage_floor_2026`** (`ls apps/contracts/migrations/`:
`0001` … `0005`). Die nächste Lohnzeile kommt deshalb in
`apps/contracts/migrations/0006_<name>.py` mit
`dependencies = [("contracts", "0005_wage_floor_2026")]`. Eine zweite Datei mit der Nummer
`0005`, die wieder auf `0004` zeigt, erzeugt **zwei Leaf-Nodes** im Migrationsgraphen —
Django bricht den nächsten `migrate` mit „Conflicting migrations detected" ab.

Schablone für die nächste Stufe. Der Inhalt unten zeigt als **durchgerechnetes Beispiel**
den Schritt, den `0005_wage_floor_2026` bereits vollzogen hat (14,25 € → 15,00 €); für eine
neue Stufe werden Beträge, Daten, Dateiname und `dependencies` ausgetauscht:

```python
"""
EXEMPLU (deja aplicat în 0005_wage_floor_2026): tariful LG 1 din Gebäudereinigung
crește la 15,00 € de la 01.01.2026. Rândul vechi se ÎNCHIDE, nu se suprascrie —
un recalcul pentru 2025 trebuie să întoarcă în continuare 14,25 €.
"""

from datetime import date

from django.db import migrations

# (kind, valid_from, valid_to, hourly_amount, source_note)
NEW_ROWS = [
    ("GEBAEUDE", date(2026, 1, 1), None, "15.00",
     "Lohntarifvertrag 2025/2026, LG 1, ab 01.01.2026 (pland.app/blog/tariflohn-2026-...)"),
]
# (kind, valid_from al rândului care se închide, noua valid_to)
CLOSE = [
    ("GEBAEUDE", date(2025, 1, 1), date(2025, 12, 31)),
]


def forwards(apps, schema_editor):
    WageFloor = apps.get_model("contracts", "WageFloor")
    for kind, vf, vt, amount, note in NEW_ROWS:
        WageFloor.objects.update_or_create(
            kind=kind, valid_from=vf,
            defaults={"valid_to": vt, "hourly_amount": amount, "source_note": note},
        )
    for kind, vf, vt in CLOSE:
        WageFloor.objects.filter(kind=kind, valid_from=vf).update(valid_to=vt)


def backwards(apps, schema_editor):
    WageFloor = apps.get_model("contracts", "WageFloor")
    for kind, vf, *_ in NEW_ROWS:
        WageFloor.objects.filter(kind=kind, valid_from=vf).delete()
    for kind, vf, _vt in CLOSE:
        WageFloor.objects.filter(kind=kind, valid_from=vf).update(valid_to=None)


class Migration(migrations.Migration):
    dependencies = [("contracts", "0005_wage_floor_2026")]
    operations = [migrations.RunPython(forwards, backwards)]
```

Regeln, die dieses Muster trägt und die eine Abweichung nicht brechen darf:

- `apps.get_model(...)`, **nie** der direkte Import aus `apps.contracts.models` — eine Migration
  muss gegen den historischen Modellzustand laufen.
- `update_or_create` auf dem natürlichen Schlüssel `(kind, valid_from)`, damit ein erneuter Lauf
  idempotent ist.
- Ein `backwards`, das **nur die eigenen Zeilen** anfasst — anders als `0002`, das alles löscht.
- Ändert sich zugleich die Minijob-Grenze, kommt die `MinijobThreshold`-Zeile **in dieselbe
  Migration**, mit der Rechnung im `source_note` (z. B. `"13,90 × 130 / 3 = 602,33 → 603,00"`).
- Test ergänzen — Vorbild ist
  `tests/test_contracts.py::TestCompliance::test_tariful_de_ramura_creste_in_2026`
  (`tests/test_contracts.py:38-41`), das für die 2026er Stufe genau dieses Paar prüft:
  `assert WageFloor.current("GEBAEUDE", date(2026, 6, 1)) == Decimal("15.00")` **und**
  `assert WageFloor.current("GEBAEUDE", date(2025, 6, 1)) == Decimal("14.25")`.
  Jede weitere Stufe braucht ihr eigenes Paar (alter Satz vor, neuer Satz nach dem Stichtag).
- Ausführen:
  ```
  /Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python manage.py migrate contracts
  /Users/Geronimo/Projects/Cleaning_SaaS/.venv/bin/python -m pytest tests/test_contracts.py -p no:cacheprovider --create-db
  ```
  `pytest.ini` setzt `addopts = -q --reuse-db`; der **erste** Lauf nach einer Data-Migration
  braucht `--create-db`, sonst fehlt die neue Zeile in der wiederverwendeten Test-DB.

---

## 4. Rezept 2 — Lohngruppen und Sätze als eigene Tabelle (**Vorschlag**)

`WageFloor` bleibt, was es ist: die **Untergrenze** für die Vertragsprüfung. Für eine Abrechnung
über LG 1–9 braucht es ein zweites Paar. Empfohlen als neue App `apps/payroll` (die Lohnlogik
gehört nicht in `contracts`, weil sie an Schichten hängt, nicht an Verträgen):

```python
# apps/payroll/models.py — PROPUNERE, nu există încă în cod.

class WageGroup(models.Model):
    """Lohngruppe RTV § 8 (Fassung vom 31. Oktober 2019). Definiție, nu tarif."""
    number       = models.PositiveSmallIntegerField(unique=True)          # 1..9
    label        = models.CharField(max_length=120)                       # germană
    job_features = models.TextField()                                     # Tätigkeitsmerkmal verbatim
    is_minimum_wage_group = models.BooleanField(default=False)            # doar LG 1 și LG 6
    is_vacant    = models.BooleanField(default=False)                     # LG 5: tarifată, dar neocupată
    source_note  = models.CharField(max_length=200, blank=True)


class WageRate(models.Model):
    """Tarif pe grupă și dată. NICIODATĂ suprascris — un recalcul istoric trebuie să iasă la fel."""
    class Region(models.TextChoices):
        BUND = "BUND", "Bundesweit"
        WEST = "WEST", "West"
        OST  = "OST",  "Ost"

    group        = models.ForeignKey(WageGroup, on_delete=models.PROTECT, related_name="rates")
    region       = models.CharField(max_length=4, choices=Region.choices, default=Region.BUND)
    hourly_amount= models.DecimalField(max_digits=6, decimal_places=2)
    valid_from   = models.DateField()
    valid_to     = models.DateField(null=True, blank=True)
    increase_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    source_url   = models.URLField(blank=True)
    source_note  = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("group", "region", "-valid_from")
        constraints = [
            models.UniqueConstraint(fields=("group", "region", "valid_from"), name="uniq_rate_start"),
        ]
```

Seed-Inhalt: die 2025er und 2026er Spalten aus `lohngruppen-und-tabellen.md`, **nur diese**.
2023 und 2024 bleiben leer (außer LG 1 = 13,50 € und LG 6 = 16,70 € vor dem 01.01.2025, die
belegt sind). Nicht interpolieren.

`WageFloor` und `WageRate` müssen konsistent bleiben: die `GEBAEUDE`-Zeile ist per Definition der
LG-1-`WageRate` desselben Stichtags. Ein Test, der beide vergleicht, ist billiger als eine
Doppelpflege, die auseinanderläuft.

---

## 5. Wohin die Zuschlagsberechnung gehört (**Vorschlag**)

**Nicht** in `Shift`, **nicht** in eine View, **nicht** in einen Signal-Handler.

```
apps/payroll/
    models.py      WageGroup, WageRate, SurchargeType, Holiday,
                   PayrollRun, PayrollLine, SurchargePosition
    surcharges.py  slice_shift(shift) -> [TimeSlice]
                   applicable(slice, on) -> [SurchargeType]
                   resolve(slice) -> (winner, suppressed[])     # RTV 4.8
    services.py    run_payroll(account, month) -> PayrollRun    # tranzacțional
    export.py      datev_csv(run) / generic_csv(run)
```

Warum eine eigene App und ein eigenes Modul:

- `apps/planning` hält **Zeit**, nicht Geld. `Shift.billable_minutes`
  (`apps/planning/models.py:176-178`) ist der Übergabepunkt; alles Weitere gehört dahinter.
- `apps/contracts` hält die **Vertragsprüfung**. Sie fragt das Lohnsystem nach einer
  Untergrenze; sie rechnet keine Zuschläge.
- Die Zuschlagsberechnung ist eine reine Funktion über (Zeitscheibe, Sätze, Feiertagskalender)
  und deshalb ohne DB-Zugriff testbar, wenn Sätze und Kalender hineingereicht werden.

### Zeitscheiben schneiden

`Shift` speichert `date`, `start_time` und `duration_minutes` — kein `end_time`. Das Ende ist
`datetime.combine(date, start_time) + timedelta(minutes=duration_minutes)`. Weil
`TIME_ZONE = "Europe/Berlin"` und `USE_TZ = True` gesetzt sind
(`config/settings.py:107-110`), muss die Nachtfenster-Prüfung auf der **lokalen** Zeit laufen
(`django.utils.timezone.localtime`), sonst verschiebt sich das 22:00–05:00-Fenster zweimal im
Jahr um eine Stunde.

Schnittkanten pro Schicht:
- `22:00` und `05:00` (Nachtfenster, RTV 4.2)
- Mitternacht (Tageswechsel → anderer Feiertags-/Sonntagsstatus, RTV 4.3)
- Beginn/Ende einer Erschwernistätigkeit (der Zuschlag gilt „nur für die Zeit, in der sie eine
  der folgenden Tätigkeiten ausüben")

### Auflösung und Persistenz

- Pro Scheibe die Menge der anwendbaren Zuschlagsarten bilden, den **höchsten Prozentsatz**
  gewinnen lassen, die anderen als `SurchargePosition(suppressed_by=winner)` speichern.
- Jede `SurchargePosition` speichert: Minuten, Prozentsatz, Bemessungs-Stundenlohn, Betrag,
  die verwendete `WageRate`-ID und den Grund der Unterdrückung.
- Der **Belastungszuschlag** braucht einen Tages- **und** einen Wochenkontext (>8 h/Tag bzw.
  über die 40. Wochenstunde) — er lässt sich nicht aus einer einzelnen Scheibe ableiten und
  gehört in einen zweiten Durchgang über die Woche. Die tarifliche Regelwoche ist **39** h, die
  Zuschlagsschwelle **40** h; beide Zahlen bleiben getrennte Felder.
- Ein Validator muss die Abgeltungssperre durchsetzen: ein Beschäftigter mit
  zuschlagspflichtigen Stunden und **null** Zuschlagspositionen ist ein Fehler, kein Sonderfall
  („Die Abgeltung von Zuschlägen aller Art durch erhöhten Lohn ist unzulässig").

### Feiertagskalender

`geo.Region` ist das Bundesland und existiert bereits (`apps/geo/models.py:4-17`), gesät sind
aber nur **HH** und **SH**. Ein `Holiday(date, region, name, category)` mit
`category ∈ {STANDARD_80, HOCH_200, SONDER_150}` hängt an `Site → Locality → Region`, also am
**Objekt**, nicht am Mitarbeiter. Die Feiertagsseite sagt ausdrücklich, dass die übrigen
Feiertage „spezifisch für jedes Bundesland" sind. Eine Ausweitung des Vertriebsgebiets über
HH/SH hinaus verlangt zuerst neue `Region`-Zeilen.

---

## 6. Der Lohnlauf (**Vorschlag**)

Zustandsautomat, angelehnt an `DraftStatus` in `contracts`:

```
OFFEN → BERECHNET → GEPRUEFT → FREIGEGEBEN → EXPORTIERT → ABGESCHLOSSEN
```

- `FREIGEGEBEN` und später sind **unveränderlich**. Korrekturen erzeugen einen `Korrekturlauf`
  mit Verweis auf den Ursprungslauf — dasselbe Muster wie `ContractSignature.save`, das ein
  erneutes Speichern mit `RuntimeError` ablehnt (`apps/contracts/models.py:280`).
- Fälligkeit ist **abgeleitet**, nicht gespeichert: der 15. des Folgemonats
  (https://pland.app/arbeitslexikon/lohnabrechnung-gebaeudereinigung).
- Zustellung: `zustellart ∈ {ELEKTRONISCH, SCHRIFTLICH}` plus
  `elektronische_zustimmung_vorhanden` — ohne Zustimmung ist die **kostenfreie schriftliche**
  Abrechnung Pflicht.
- Pflichtpositionen auf der Abrechnung: **Gesamtlohn/Lohnsumme, Stundenlohn, Zuschläge/Zulagen,
  Abzüge**; TZR-Gesamtbetrag **gesondert**.

---

## 7. Payroll-Export — DATEV bzw. CSV (**Vorschlag**)

Kein Bestand im Repo. Was ein Export mindestens braucht, aufgeteilt nach Belegbarkeit:

**Aus den Quellen belegbar (Inhalt der Abrechnung):** Gesamtlohn, Stundenlohn, Zuschläge/Zulagen
je Art, Abzüge, TZR-Betrag gesondert, Abrechnungsmonat, Fälligkeit.

**Ungeprüft — eigenes Domänenwissen, vor der Umsetzung mit dem Steuerbüro klären:** Ein realer
DATEV-/LODAS-Import verlangt zusätzlich Betriebsnummer, Personalnummer, Sozialversicherungs-
nummer, Steuer-ID, Krankenkasse, Steuerklasse, Kinderfreibeträge, Konfession und Beitragsgruppen
— **kein einziges dieser Felder existiert heute im Datenmodell**, und keine der ausgewerteten
Quellen nennt sie. Ein Export ist deshalb kein Formatierungsproblem, sondern zuerst ein
Stammdatenproblem.

Pragmatischer Zuschnitt in dieser Reihenfolge:

1. **Nachweis-CSV zuerst** — eine Zeile je (Mitarbeiter, Datum, Objekt, Zone, Beginn, Ende,
   Pause, Gesamtzeit) mit den **sieben Pflichtfeldern des Stundenzettels**. Das ist genau der
   Bericht, den `attendance.time_records` (`apps/planning/attendance.py:178`) ansatzweise schon
   erzeugt („ce trebuie să poți arăta la un control (Zoll / FKS)"), und er ist ohne
   SV-Stammdaten lieferbar.
2. **Lohnarten-CSV** — je (Mitarbeiter, Monat, Lohnart, Menge, Satz, Betrag), mit einer
   `Lohnart` als konfigurierbarer Entität (`code`, `bezeichnung`, `typ ∈ {GRUNDLOHN, ZUSCHLAG,
   ZULAGE, ABWESENHEIT, EINMALZAHLUNG}`, `steuerpflichtig`, `sv_pflichtig`, `exportcode_datev`).
   Der Wettbewerber exponiert genau dieses Konzept an den Nutzer
   (https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland).
3. **DATEV zuletzt**, nach den Stammdaten und nach einer verbindlichen Feldliste des Steuerbüros.

Formatregeln für jeden Export: `Decimal` bis zur Ausgabe durchhalten, dann
`quantize(Decimal("0.01"))`; Dezimalkomma und `;` als Trenner, wenn das Ziel ein deutsches
Buchhaltungssystem ist; UTF-8 mit BOM nur, wenn der Empfänger es verlangt; die
`WageRate`/`SurchargeType`-IDs mitgeben oder zumindest den Satz und den Prozentsatz — ein Export
ohne die verwendeten Sätze ist bei einer Prüfung wertlos.

---

## 8. Testmuster, die schon da sind und fortgeführt werden sollten

`tests/test_contracts.py` (die Suite umfasst insgesamt **190 Tests**, alle grün —
`.venv/bin/python -m pytest -q`; `pytest.ini`, `DJANGO_SETTINGS_MODULE=config.settings`,
`testpaths=tests`). Die Fixture `draft` (`tests/test_contracts.py:19-28`) legt Verträge
standardmäßig mit `wage="15.00"` und `start=date(2026, 10, 1)` an:

- `test_pragurile_sunt_datate_nu_constante` (`:33`) — belegt, dass dieselbe Abfrage für 2025
  und 2026 **verschiedene** Werte liefert. Jede neue Ratentabelle braucht das Äquivalent.
- `test_tariful_de_ramura_creste_in_2026` (`:38`) — `GEBAEUDE` = 14,25 € für 2025 und
  15,00 € für 2026. Das Muster für jede weitere Tarifstufe.
- `test_severitatea_e_tipizata_nu_dedusa_din_text` (`:43`) — `blocking` wird aus
  `ComplianceIssue.blocking` gelesen, nicht aus dem Meldungstext.
- `test_sub_mindestlohn_de_ramura_e_semnalat` (`:68`) — prüft, dass der **höhere** der beiden
  Böden greift, und löst den Boden **dynamisch aus der DB** auf
  (`assert str(floor) in " ".join(d.compliance_issues())`), statt einen Eurobetrag zu
  hardcoden. Genau so gehören neue Lohntests geschrieben.
- `test_40_ore_la_tariful_2026_ramane_minijob_valid` (`:52`) — 40 h × 15,00 € = 600 € < 603 €,
  die reale Minijob-Obergrenze bei LG-1-Tarif 2026.
- `test_avertismentul_nu_blocheaza_trimiterea` (`:81`) — Warnung vs. Blocker sind unterschieden.

Für neue Lohnlogik zusätzlich:

| Test | Was er absichert |
|---|---|
| Schicht Sonntag 21:00 → Montag 02:00 | drei Scheiben, 80 / 80 / 30 %, Nachtzuschlag der zweiten Scheibe **unterdrückt und gespeichert** |
| Schicht am 1. Mai | 200 %, nicht 80 % |
| Schicht am 24.12. | 150 % aus dem TV Freistellung, nicht 80 % |
| Lohnlauf für 2025-12 nach dem 01.01.2026 ausgeführt | rechnet mit dem 2025er Satz |
| Fehlender Satz für den Stichtag | Lauf **bricht ab**, weicht nicht aus |
| Minijob, LG 1, 2026 | 603 € ÷ 15,00 € = 40,2 h — Planung über 40 h/Monat schlägt Alarm |

---

## 9. Sprach- und Stilkonvention beim Schreiben dieses Codes

Aus `scratchpad/dossier/_verified-ground-truth.md`, im Code durchgehend bestätigt:

- **Englisch:** Modell-, Feld- und Funktionsnamen, `TextChoices`-Konstanten,
  URL-`name=`-Werte (`WageFloor`, `hourly_amount`, `send_for_signature`).
- **Rumänisch:** Docstrings und Kommentare — auch in neuen Dateien
  („Praguri salariale legale, cu valabilitate în timp — NU constante în cod.",
  `apps/contracts/models.py:46-47`).
- **Deutsch:** `source_note`-Inhalte, Vertragstexte, Lohngruppenbezeichnungen, alle gesäten
  Domänendaten, öffentliche URL-Segmente.
- **Rumänisch:** Dashboard-URL-Segmente (`/dashboard/contracte/`, `/pontaj/`) und
  nutzersichtbare Meldungen im Dashboard — die Compliance-Meldungen sind heute rumänisch,
  wörtlich „Salariul orar {wage} € este sub pragul de {floor} € valabil la {dd.mm.yyyy}."
  bzw. „Onorariul orar …" beim `WERKVERTRAG` (`apps/contracts/models.py:216-221`). Das
  bleibt so, bis jemand bewusst umstellt.

Nichts davon „reparieren". Ein Patch, der Kommentare eindeutscht oder Dashboard-URLs übersetzt,
ist ungefragte Scope-Erweiterung.

---

## Quellen

Repo (alle Pfade absolut unter `/Users/Geronimo/Projects/Cleaning_SaaS`):

- `apps/contracts/models.py` — `ComplianceIssue` 45-55, `WageFloor` 57-89 (`current` 83-89),
  `MinijobThreshold` 92-113, `ContractDraft` 151-253, `compliance_issues` 193-195,
  `compliance_report` 197-248 (Boden-`max()` 209), `ContractSignature` 256-283
- `apps/contracts/migrations/0002_seed_wage_floors.py` — gesäte Zeilen 15-25, `forwards` 28-41
- `apps/contracts/migrations/0003_seed_templates.py` — vier deutsche Vorlagen, § 5 Urlaub, § 6 Kündigung
- `apps/contracts/migrations/0005_wage_floor_2026.py` — **letzte Migration der App**; LG 1 auf
  15,00 € ab 01.01.2026, 2025er Zeile geschlossen
- `apps/contracts/services.py` — `render_contract` 8-22, `send_for_signature` 25-33
  (Filter auf `i.blocking`, Zeile 26)
- `apps/contracts/views.py:77` — `compliance_issues()`, aufgelöst zum `start_date` (korrekt)
- `apps/planning/models.py` — `Site` 21-38, `Zone` 42-88, `Shift` 140-186, `ShiftEvent` 188-221
- `apps/planning/attendance.py` — `correct_minutes` 148, `time_records` 178
- `apps/geo/models.py` — `Region` (Bundesland) 4-17, `Locality` 20-44
- `apps/jobs/models.py:38-43` — `salary_min` / `salary_max` / `salary_unit`
- `config/settings.py:13-37` (INSTALLED_APPS), `:107-110` (Sprache, Zeitzone, USE_TZ)
- `tests/test_contracts.py` — Compliance-Tests
- `pytest.ini`

pland.app:

- https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026
- https://pland.app/arbeitslexikon/lohnabrechnung-gebaeudereinigung
- https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023
- https://pland.app/arbeitslexikon/feiertagsarbeit-gebaeudereinigung
- https://pland.app/arbeitslexikon/stundenzettel
- https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland

Dossiers: `scratchpad/dossier/_verified-ground-truth.md`, `scratchpad/dossier/contracts.md`
