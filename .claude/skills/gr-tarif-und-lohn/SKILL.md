---
name: gr-tarif-und-lohn
description: >
  Tarif- und Lohnwissen für die deutsche Gebäudereinigung, verbindlich für jede Arbeit
  in /Users/Geronimo/Projects/Cleaning_SaaS. Nutze diesen Skill, sobald Löhne, Stundenlöhne,
  Lohngruppen (LG 1–9), Tariflohn, Mindestlohn, Mindestlohntarifvertrag, Rahmentarifvertrag
  (RTV), Lohntarifvertrag, Allgemeinverbindlichkeit/AVE, § 7 AEntG, Zuschläge (Nacht-,
  Sonntags-, Feiertags-, Erschwernis-, Belastungszuschlag), Urlaubsanspruch, Urlaubsgeld,
  Entgeltfortzahlung, Krankmeldung, Kündigungsfristen, Minijob-/Midijob-Grenze,
  Beitragsbemessungsgrenzen, Ausbildungsvergütung, Zeitarbeit/AÜG/GVP-Tarifwerk,
  Lohnabrechnung, Lohnarten oder ein DATEV-/CSV-Payroll-Export berührt werden — auch dann,
  wenn die Anfrage nur „Stundenlohn prüfen", „Gehalt im Vertrag", „salary_min", „hourly_wage"
  oder „Compliance-Check" heißt. Gilt insbesondere für apps/contracts (WageFloor,
  MinijobThreshold, ContractDraft.compliance_issues, migrations/0002_seed_wage_floors.py),
  apps/planning (Shift, ShiftEvent, attendance.time_records) und apps/jobs (salary_min/max).
  Ohne diesen Skill schreibt ein Agent fast sicher falschen Code: er hardcodet Eurobeträge
  statt effektiv-datierter Zeilen, addiert Zuschläge kumulativ (verboten — nur der höchste
  gilt), prüft gegen den heutigen statt gegen den am Schichttag gültigen Lohn und übersieht,
  dass der Branchen-Mindestlohn allgemeinverbindlich ist und damit auch nicht tarifgebundene
  Betriebe bindet. Er überschreibt generische Payroll-Ratschläge.
metadata:
  author: Geronimo
  target: Cleaning_SaaS (Django 5.2, German Gebäudereinigung market)
  repo_root: /Users/Geronimo/Projects/Cleaning_SaaS
  sources: pland.app (crawled 2026-08-29, 237 pages) + repository code
---

# gr-tarif-und-lohn — Löhne, Tarif, Zuschläge, Lohnabrechnung

**Stand: 2026-08-29.** Tarif- und Sozialversicherungswerte ändern sich jährlich. Jede
Tabelle in `references/` trägt ihr eigenes „Stand" und ihre Quell-URL.

**Rechtlicher Hinweis:** Referenzmaterial, keine Rechtsberatung. Vor der ersten echten
Lohnabrechnung oder dem ersten unterschriebenen Vertrag gehört jeder Wert einmal durch
einen Fachanwalt für Arbeitsrecht bzw. gegen den Originaltarifvertrag geprüft.

## Kennzeichnung, die dieser Skill durchhält

| Marker | Bedeutung |
|---|---|
| **Fakt** | belegt durch eine pland.app-URL oder durch `datei:zeile` im Repo |
| **Vorschlag** | Design für Code, der noch nicht existiert |
| **Ungeprüft** | Domänenwissen, das die Quellen nicht abdecken — vor Produktion verifizieren |

Schreibe in Ausgaben, die auf diesen Skill zurückgehen, dieselben drei Marker. Wenn eine
Zahl in keiner Quelle steht, schreibe „nicht belegt / not established from the sources"
statt zu interpolieren.

---

## Die sieben Regeln, die nicht gebrochen werden dürfen

### R1 — Kein Eurobetrag wird hardcodiert
Jeder Lohn-, Grenz- und Zuschlagswert ist eine **effektiv-datierte Zeile in der DB**, nie
eine Python-Konstante. Das Repo macht das bereits richtig:
`apps/contracts/models.py:57-89` (`WageFloor` mit `valid_from` / `valid_to` /
`source_note`) und `apps/contracts/models.py:92-113` (`MinijobThreshold`). Gefüllt wird
über Data-Migrations, nicht über Code — Muster:
`apps/contracts/migrations/0002_seed_wage_floors.py` (Erstsaat) und
`apps/contracts/migrations/0005_wage_floor_2026.py` (Nachziehen einer Stufe).

### R2 — Der Lohnsatz wird zum Stichtag aufgelöst, nie zu `today()`
`WageFloor.current(kind, on)` nimmt ein Datum (`apps/contracts/models.py:83-89`). Für
Verträge ist der Stichtag `start_date`, für eine Lohnabrechnung der **Schichttag**, nie
der Tag des Rechenlaufs. Eine Dezember-2025-Nachrechnung muss nach dem 01.01.2026 noch
den 2025er Satz liefern. `timezone.localdate()` ist in `current()` nur der Fallback, wenn
`on` fehlt — dieser Fallback darf nie der Normalfall werden. Richtig gemacht:
`apps/contracts/views.py:77` ruft `contract.compliance_issues()`, und
`compliance_report()` löst beide Böden und die Minijob-Grenze über `self.start_date` auf
(`models.py:207-208`, `models.py:224`).

### R3 — Der Branchen-Mindestlohn ist allgemeinverbindlich
**Fakt:** Der Mindestlohntarifvertrag der Gebäudereinigung wurde am **28. Januar 2025**
durch **Rechtsverordnung nach § 7 AEntG** („Zehnte Verordnung über zwingende
Arbeitsbedingungen in der Gebäudereinigung", BGBl. vom 28.01.2025) für
allgemeinverbindlich erklärt und gilt damit **bundesweit für alle** Reinigungsbetriebe,
unabhängig von Tarifbindung oder Sitz im Ausland
(https://pland.app/arbeitslexikon/mindestlohntarifvertrag-2024,
https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026).
Konsequenz für den Code: der Tarifsatz ist **keine Option**, sondern eine Untergrenze für
jeden Mandanten. Die Prüfung „ist der Betrieb tarifgebunden?" darf die Prüfung nie
abschalten.

### R4 — Kein Lohn unter dem am Schichttag geltenden Boden
Der wirksame Boden ist `max(gesetzlicher Mindestlohn, tariflicher Mindestlohn der
zutreffenden Lohngruppe)` — so bereits implementiert in
`apps/contracts/models.py:209`. Der `GEBAEUDE`-Boden ist gestuft gesät und **aktuell**:
`14.25 €` für `2025-01-01`→`2025-12-31` und `15.00 €` ab `2026-01-01` (offen), gesetzt
durch `apps/contracts/migrations/0005_wage_floor_2026.py`. Ein Vertrag mit Beginn 2026 zu
14,25 € wird deshalb korrekt blockiert. Wenn die nächste Tarifstufe kommt: neue Zeile per
Data-Migration, siehe `references/implementierung-django.md`, Rezept „Neue WageFloor-Zeile".

### R5 — Zuschläge werden nie addiert
**Fakt (RTV § 3 Nr. 4.8):** „Treffen mehrere der vorgenannten Zuschläge zusammen, ist nur
der jeweils **höchste** zu zahlen."
(https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023). Auflösung
pro Zeitscheibe, nicht pro Schicht: eine Schicht 21:00–02:00 an einem Samstag/Sonntag
zerfällt in Scheiben mit je eigener Höchstauflösung. Unterdrückte Zuschläge werden
**gespeichert, nicht gelöscht** — Betriebsrat und Zoll fragen danach.
**Fakt:** „Die **Abgeltung von Zuschlägen aller Art durch erhöhten Lohn ist unzulässig**."
(https://pland.app/arbeitslexikon/zuschlaege-gebaeudereinigung) — ein „wir zahlen halt
1 € mehr Grundlohn statt Nachtzuschlag" muss der Code aktiv verhindern.

### R6 — `Decimal`, niemals `float`
Alle Geldfelder im Repo sind bereits `DecimalField` (`hourly_amount` 6,2;
`monthly_limit` 7,2; `hourly_wage` 6,2). Prozentsätze werden **so gespeichert, wie der
Tarif sie nennt**, nicht aus Vorher/Nachher rückgerechnet.

### R7 — Zeitdaten sind revisionssicher
Zeiterfassung ist Pflicht (`apps/planning/models.py:153-155` zitiert BAG 13.09.2022
– 1 ABR 22/21 und § 3 Abs. 2 Nr. 1 ArbSchG), das Journal ist append-only
(`ShiftEvent`, `apps/planning/models.py:188-221`). Korrekturen erzeugen neue Zeilen mit
Akteur und Grund (`apps/planning/attendance.py:148`), niemals In-place-Edits. Aufbewahrung
mindestens 2 Jahre; Dokumentation durch den Beschäftigten binnen 7 Tagen
(https://pland.app/arbeitslexikon/stundenzettel).

---

## Was im Repo existiert und was nicht

| Thema | Status | Ort |
|---|---|---|
| Effektiv-datierte Lohnuntergrenzen | **existiert** | `apps/contracts/models.py:57-89` |
| Minijob-Grenze, effektiv-datiert | **existiert** | `apps/contracts/models.py:92-113` |
| Seed-Rows (WageFloor, MinijobThreshold) | **existiert**, aktuell | `apps/contracts/migrations/0002_seed_wage_floors.py` + `0005_wage_floor_2026.py` |
| Compliance-Prüfung Vertrag (Boden, Minijob, AÜG, Scheinselbstständigkeit) | **existiert** | `compliance_report()` `apps/contracts/models.py:197-248` |
| Typisierte Befund-Severität (`ComplianceIssue` mit `code` / `message` / `blocking`) | **existiert** | `apps/contracts/models.py:45-55`; Filter in `apps/contracts/services.py:26` |
| Vier deutsche Vertragsvorlagen (VOLLZEIT/TEILZEIT/MINIJOB/WERKVERTRAG, v1.0, de) | **existiert** | `apps/contracts/migrations/0003_seed_templates.py` |
| Bundesland als Entität (`geo.Region`, Feld `code`) | **existiert** — aber nur `HH` und `SH` gesät | `apps/geo/models.py:4-17` |
| Schicht mit Datum, Startzeit, Dauer, Ist-Minuten | **existiert** | `apps/planning/models.py:140-186` |
| Nachweis-Export für Zoll/FKS | **existiert** (rudimentär) | `apps/planning/attendance.py:178` |
| **Lohngruppe (LG 1–9) als Modell** | **fehlt** | — |
| **Lohnsatz je Lohngruppe und Stichtag** | **fehlt** | — |
| **Zuschlagsarten und Zuschlagsberechnung** | **fehlt** | — |
| **Feiertagskalender je Bundesland** | **fehlt** | — |
| **Urlaubskonto, Urlaubsentgelt, Urlaubsgeld** | **fehlt** (`ContractDraft.vacation_days` ist ein einzelnes Int, Default **20**) | `apps/contracts/models.py:167` |
| **Entgeltfortzahlung, Krankmeldung, AU** | **fehlt** | — |
| **Lohnlauf / Lohnabrechnung / DATEV-Export** | **fehlt** | — |

Alles unter „fehlt" ist **Vorschlag**, nicht Bestand. Behaupte nie das Gegenteil.

---

## Routing — wohin für welche Frage

| Frage | Datei |
|---|---|
| Welcher Tarifvertrag regelt was? Wer sind die Parteien? Ist er allgemeinverbindlich? RTV-§-Struktur, Arbeitszeit, Mehrarbeit, Nachtarbeitsfenster, Wegezeit-/Zwischenzeit-Regeln, Teilzeit-Anpassungsanspruch, TZR, GVP-Tarifwerk Zeitarbeit | `references/tarifvertraege.md` |
| Was verdient LG 4 am 01.02.2026? Lohntabellen je Jahr, Lohngruppenbeschreibungen, Ausbildungsvergütung, gesetzlicher Mindestlohn, Minijob-/Midijob-Grenzen, Zeitarbeits-Entgeltgruppen, West/Ost | `references/lohngruppen-und-tabellen.md` |
| Wie hoch ist der Nachtzuschlag? Zuschlagssätze und ihre Bemessungsgrundlage, Erschwernis- und Belastungszuschlag, § 3b EStG, Urlaubsanspruch und -berechnung, zusätzliches Urlaubsgeld, Entgeltfortzahlung, Krankmeldung, Kündigungsfristen | `references/zuschlaege-und-abwesenheit.md` |
| Wie baue ich das in Django? WageFloor exakt wie er ist, neue Tarifzeile per Data-Migration, effektiv-datierte Speicherung, wo die Zuschlagsberechnung hingehört, was ein DATEV-/CSV-Export braucht | `references/implementierung-django.md` |

---

## Die vier Zahlen, die am häufigsten gebraucht werden

**Stand 2026-08-29.** Volle Tabellen mit allen Lohngruppen: `references/lohngruppen-und-tabellen.md`.

| Wert | Betrag | Gültig ab | Quelle |
|---|---|---|---|
| Tariflohn **LG 1** (Innen-/Unterhaltsreinigung) — der Branchen-Mindestlohn | **15,00 €/h** | 01.01.2026 | https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026 |
| Tariflohn **LG 6** (Glas-/Fassadenreinigung) | **18,40 €/h** | 01.01.2026 | ebd. + https://pland.app/arbeitslexikon/lohntarifvertrag-gebaeudereinigung-2023 |
| **Gesetzlicher** Mindestlohn (§ 1 MiLoG) | **13,90 €/h** | 01.01.2026 | https://pland.app/blog/das-neue-gpv-tarifwerk-2026 |
| Minijob-Grenze | **603 €/Monat** | 01.01.2026 | ebd. |

Der Tarif liegt über dem gesetzlichen Mindestlohn — in der Gebäudereinigung ist deshalb
**immer der Tarif** der bindende Boden, nie der MiLoG-Wert.

---

## Sprachkonvention beim Schreiben von Code hier

Nicht „reparieren", nur einhalten (bestätigt in
`scratchpad/dossier/_verified-ground-truth.md`):

- Python-Bezeichner, Modell- und Feldnamen, URL-`name=`-Werte: **Englisch**
- Kommentare und Docstrings: **Rumänisch**
- Dashboard-URL-Segmente: **Rumänisch**; öffentliche URL-Segmente: **Deutsch**
- Gesäte Domänendaten, `source_note`, Vertragstexte, Lohngruppenbezeichnungen: **Deutsch**

Konkret: ein neues Modell heißt `WageRate`, sein Docstring ist rumänisch, sein
`source_note`-Inhalt ist deutsch („Lohntarifvertrag 2025/2026, LG 4, ab 01.01.2026").

## Vor dem Absenden prüfen

1. Steht jeder Eurobetrag in einer datierten DB-Zeile mit `source_note` und Quell-URL?
2. Wird der Satz zum **Ereignisdatum** aufgelöst, nicht zu `today()`?
3. Werden Zuschläge maximiert statt summiert, und bleiben unterdrückte erhalten?
4. `Decimal` überall, `quantize(Decimal("0.01"))` bei Geldausgaben?
5. Sind neue Werte als **Fakt / Vorschlag / Ungeprüft** gekennzeichnet?
6. Tests: `.venv/bin/python -m pytest tests/test_contracts.py` — nach einer Data-Migration
   den ersten Lauf **ohne** `--reuse-db` (`pytest.ini` setzt `addopts = -q --reuse-db`).
