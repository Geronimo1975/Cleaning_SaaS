# Rechtsgrundlagen der Zeiterfassungspflicht

Covers: why recording working time is compulsory in Germany, what exactly must be
recorded, by when, and how long it must be kept — separated into what the crawled
competitor pages actually say, what the repository code already asserts, and what is
domain knowledge the sources do not carry.

**Stand:** 2026-08-29. Material from the pland.app crawl of 2026-08-29 (blog and
Arbeitslexikon clusters) plus the repository at `/Users/Geronimo/Projects/Cleaning_SaaS`.
This is reference material, not legal advice. Every statutory and tariff value changes;
re-check each row against its source URL before relying on it.

Labels: **Fakt** = on a cited source page or at a cited file:line · **Vorschlag** =
design proposal · **Ungeprüft** = domain knowledge not covered by the sources.

---

## 1. The chain of authority, as the sources state it

| # | Instrument | What the source says it requires | Label | Source |
|---|---|---|---|---|
| 1 | **EuGH "Stechuhr-Urteil", 2019** | "durch das sogenannte „Stechuhr-Urteil" des Europäischen Gerichtshofs (EuGH) von **2019** weiter untermauert"; employers "müssen … ein **objektives, verlässliches und zugängliches System** zur Erfassung der täglichen Arbeitszeit einführen" | Fakt | https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger |
| 2 | EuGH ruling — **case number** | **Not stated on any crawled page.** No C-…/… docket, no date beyond the year. | Fakt (absence) | — |
| 3 | **BAG decision** | "Seit dem Urteil des Bundesarbeitsgerichts (BAG) im **September 2022** besteht in Deutschland eine klare Pflicht zur Arbeitszeiterfassung." | Fakt | https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger |
| 4 | BAG — **file number** | Printed as "**(1ABR 22/21)**" (no space; the standard rendering is 1 ABR 22/21) | Fakt | https://pland.app/blog/stundenzettel-vorlage-fuer-gebaeudereinigungen-kostenlos-herunterladen |
| 5 | BAG — **exact date** | **The date 13.09.2022 does not appear on any crawled page.** Only "September 2022". | Fakt (absence) | — |
| 6 | BAG — quoted holding | "„Der Arbeitgeber ist nach **§ 3 Abs. 2 Nr. 1 ArbSchG** verpflichtet, ein System einzuführen, mit dem die von den Arbeitnehmern geleistete Arbeitszeit erfasst werden kann."" | Fakt | https://pland.app/blog/stundenzettel-vorlage-fuer-gebaeudereinigungen-kostenlos-herunterladen |
| 7 | BAG — attributed quote | BAG-Präsidentin **Inken Gallner**: "„Wenn man das deutsche Arbeitsschutzgesetz mit der Vorgabe des Europäischen Gerichtshofs auslegt, dann besteht bereits eine Pflicht zur Arbeitszeiterfassung"" | Fakt | ibid. |
| 8 | **§ 3 ArbSchG** (Arbeitsschutzgesetz) | Named as the statutory anchor: "Diese Verpflichtung leitet sich aus **§ 3 des Arbeitsschutzgesetzes** ab" | Fakt | https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger |
| 9 | Scope of the ArbSchG duty | "gilt für **alle Betriebe in Deutschland, ganz egal, wie groß sie sind**. Und das auch **unabhängig davon, ob ein Betriebsrat existiert** oder nicht." | Fakt | https://pland.app/blog/stundenzettel-vorlage-fuer-gebaeudereinigungen-kostenlos-herunterladen |
| 10 | Effective date | "Die Pflicht zur Erfassung von Arbeitszeiten gilt **ab sofort**. … Das Urteil ist fortan **geltendes Recht**." | Fakt | ibid. |
| 11 | **Mindestlohngesetz** | "Gebäudereiniger sind nach dem **Mindestlohngesetz** verpflichtet, die Arbeitszeiten **genau und zeitnah** zu dokumentieren, um sie bei **unangekündigten Kontrollen des Zolls** nachweisen zu können." No paragraph cited. | Fakt | https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren |
| 12 | **Schwarzarbeitsbekämpfungsgesetz** | "Bereits vor dem BAG-Urteil bestand für diese Branche eine **Dokumentationspflicht gemäß dem Schwarzarbeitsbekämpfungsgesetz**." No paragraph cited. | Fakt | https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger |
| 13 | **§ 16 ArbZG** | **Never cited on any crawled page.** The only ArbZG references are generic ("Arbeitszeitgesetz") plus one "§ 3 Satz 1 Arbeitszeitgesetz" on the Erschwerniszuschläge page. | Fakt (absence) | — |
| 14 | **Koalitionsvertrag 2025** | "sieht vor, dass **kleine und mittlere Unternehmen (KMU)** sowie bestimmte Branchen zusätzliche Zeit erhalten, um die neuen Anforderungen umzusetzen." No duration, no KMU threshold, no sector list. | Fakt | https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger |
| 15 | **Delegation rule** | "Zwar kann die **Aufgabe** der Zeiterfassung an Mitarbeitende **delegiert** werden, jedoch bleibt die **Verantwortung** für die ordnungsgemäße Dokumentation **beim Arbeitgeber**." | Fakt | ibid. |

### 1a. What the repository already asserts

The repo states more precisely than the crawled pages do. Treat the extra precision as
**Ungeprüft** until confirmed against a primary source — but do **not** remove it, it is
already load-bearing in three places:

| Assertion | Where |
|---|---|
| "BAG 13.09.2022 (1 ABR 22/21), pe baza §3 Abs. 2 Nr. 1 ArbSchG, obligă angajatorul german să înregistreze întregul timp de lucru — nu doar orele suplimentare. Înregistrările se păstrează minimum doi ani (§16 Abs. 2 ArbZG)." | `apps/planning/attendance.py:8-11` (module docstring) |
| Same, condensed, as the reason for the pontaj columns on `Shift` | `apps/planning/models.py:154-156` |
| Same, as the reason the event journal is append-only | `tests/test_attendance.py:4-6` |
| User-visible: "Evidența timpului de lucru e obligatorie (BAG 1 ABR 22/21, §3 ArbSchG). Păstrare până la {{ … }} (§16 ArbZG)." | `templates/dashboard/time_records.html:5-6` |
| Dashboard tile subtitle: "Evidența timpului de lucru (§16 ArbZG)" | `apps/dashboard/panels.py:72-73` |

**Ungeprüft** (my domain knowledge, not from the crawl): the decision is
**BAG, Beschluss vom 13.09.2022 – 1 ABR 22/21**; it is a *Beschluss* in a
Beschlussverfahren, not an *Urteil* as the competitor pages call it throughout. Its
holding is narrow — a works council has no Initiativrecht to introduce time recording,
*because* the employer is already obliged under § 3 Abs. 2 Nr. 1 ArbSchG. The EuGH
ruling called the "Stechuhr-Urteil" is CCOO ./. Deutsche Bank, **C-55/18, 14 May 2019**.
Verify both before quoting them outside the code.

---

## 2. What exactly must be recorded

### 2a. The three ArbSchG data points (Fakt)

The only explicit required-field list in the whole crawl
(https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger):

| # | German | English | Present in the repo? |
|---|---|---|---|
| 1 | **Beginn der täglichen Arbeitszeit** | start of daily working time | yes — `Shift.checked_in_at` (`apps/planning/models.py:157`) |
| 2 | **Ende der täglichen Arbeitszeit** | end of daily working time | yes — `Shift.checked_out_at` (`:158`) |
| 3 | **Gesamtdauer der täglichen Arbeitszeit** | total duration of daily working time | partly — `Shift.actual_minutes` (`:159`) is **per shift**, not per **day**. A worker with two shifts in one day has no stored daily total. |

The draft-law page names the same triple in statutory wording — **Arbeitsbeginn,
Arbeitsende, Arbeitsdauer**
(https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen).

A second product page states a slightly wider triple including breaks: "Seit Mai 2019
gilt, dass Unternehmen die **gesamte Arbeitszeit** ihrer Mitarbeiter erfassen müssen
(**Anfang, Ende, Pausen**)" and "verpflichtet **Beginn, Ende und Dauer** der
Arbeitszeiten all seiner Mitarbeiter zu **erfassen und zu speichern**" — no court, no
statute named (https://pland.app/funktionen/zeiterfassung-gebaeudereinigung, FAQ).

**Consequence for the code (Vorschlag):** store the duration explicitly rather than
deriving it at read time — which the repo already does (`attendance.py:133-135` writes
`actual_minutes`), and which is correct precisely because it is a legally required
record, not a convenience. Do not replace it with a computed property.

### 2b. The seven Stundenzettel fields

Legally binding only if all seven are present — see
`stundenzettel-und-berechnung.md` §1 for the verbatim list and the field mapping.

---

## 3. Deadlines: when the record must exist

Three different standards appear across the crawl. Only the first is presented as
current law.

| Standard | Verbatim | Status | Source |
|---|---|---|---|
| **7 days** | "Zudem müssen Arbeitnehmer ihre Arbeitszeiten bis **spätestens sieben Tage** nach dem Ende des jeweiligen Arbeitstages dokumentieren." | current law per the source | https://pland.app/arbeitslexikon/stundenzettel |
| **7 days** (repeat) | employers "müssen Arbeitszeiten **innerhalb von sieben Tagen** erfassen"; paper or digital is the employer's choice | current law per the source | https://pland.app/blog/zeiterfassung-2-0-mit-dem-digitalen-stundenzettel , https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen |
| **same day (ideal)** | "Die Erfassung sollte **idealerweise am selben Tag** erfolgen." | recommendation, not law | https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger |
| **same day (mandatory)** | "jeweils am Tag der Arbeitsleistung **elektronisch und manipulationssicher**" | **draft only, not enacted** | https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen |

**Ungeprüft:** the "7 days" figure is almost certainly **MiLoG § 17**, which for the
sectors listed in § 2a SchwarzArbG (Gebäudereinigung among them) requires Beginn, Ende
und Dauer der täglichen Arbeitszeit to be recorded within 7 days and kept 2 years,
available in Germany in German for Zoll/FKS inspection. The crawled pages state the
deadline without attributing it. Confirm before citing.

**Consequence for the code:** the repo has **no** recording-deadline concept. A shift
can be checked out or corrected at any later time and nothing flags it. See
`implementierung-django.md` §5, gap G-07.

---

## 4. The shelved ArbZG amendment (Gesetzentwurf)

All rows from
https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen
(Fakt).

| Item | Content |
|---|---|
| Author | Arbeitsminister **Hubertus Heil (SPD)** |
| Substance | mandatory **digital** recording of **Arbeitsbeginn, -ende und -dauer** for all employees |
| Manner | "jeweils am Tag der Arbeitsleistung **elektronisch und manipulationssicher**" |
| Retention | **mindestens 2 Jahre** |
| Status quo it replaced | recording within **7 days**, medium (paper or digital) free |
| Stated purpose | "Entbürokratisierung durch Digitalisierung" and minimising "**Manipulation und Schwarzarbeit**" |
| Target sectors | Baugewerbe, **Gebäudereinigungsgewerbe**, Wach- und Sicherheitsdienste, Speditionen, Fahrdienste, Fleischereien Großbetriebe, Schaustellergewerbe |
| Outcome | became "zunächst einmal ein **Prüfungsauftrag der Regierung**, inwiefern eine Umsetzung überhaupt technisch möglich und umsetzbar ist" — **shelved, not enacted** |
| Other measures in the same package (ab Oktober 2022) | Mindestlohn **12 € die Stunde**; Minijob-Verdienstschwelle **520 € im Monat** |
| Opponents named | **Bundesinnungsverband des Gebäudereiniger-Handwerks (BIV)**, **Interessenverband Deutscher Zeitarbeitsunternehmen (iGZ)**, **Bundesvereinigung Bauwirtschaft** |
| BIV quote | "„Die Vorgaben zur Digitalisierung der Arbeitszeitaufzeichnungen sind fernab der betrieblichen Realität und faktisch nicht umsetzbar"" |
| BIV cost estimate | ca. **700.000 Erfassungsgeräte** plus software and training — "logistisch und aus Kostengründen kaum zu bewerkstelligen" |
| Bundesvereinigung Bauwirtschaft quote | "als reine Gängelei der breiten Masse von mittelständischen Handwerksbetrieben durch ein ‚Mehr' statt ‚Weniger' an Bürokratie" |

**Do not write "digital time recording is legally required" into product copy.** The
crawled pages contradict themselves on this: two headline a *digital* obligation while
two others state the medium is free and only the shelved draft would have mandated
electronic recording. What is required is a system that is *objektiv, verlässlich und
zugänglich*; digital is one way to satisfy it.

**Manipulationssicher** is nevertheless the right design target even though the draft
died — and the repo already meets it structurally via the append-only `ShiftEvent`
(`apps/planning/models.py:188-220`).

---

## 5. Retention

| Rule | Value | Label | Source |
|---|---|---|---|
| Employer must keep Stundenzettel | "**mindestens zwei Jahre** nach der erbrachten Arbeitsleistung an dem jeweiligen Tag" | Fakt | https://pland.app/arbeitslexikon/stundenzettel |
| Draft law retention | "**mindestens 2 Jahre**" | Fakt (of a shelved draft) | https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen |
| Retention of **Bewegungsdaten** (GPS) | **Not stated anywhere in the crawl.** | Fakt (absence) | — |
| Retention actually implemented | `RETENTION_YEARS = 2`; `retention_until = end + timedelta(days=365 * RETENTION_YEARS)` | Fakt (code) | `apps/planning/attendance.py:22`, `:205` |
| Test that locks it | `assert (records["retention_until"] - end).days >= 730` | Fakt (code) | `tests/test_attendance.py:175-178` |

**Ungeprüft:** § 16 Abs. 2 ArbZG obliges the employer to record working time *beyond*
the werktägliche Arbeitszeit (i.e. beyond 8 h) and to keep those records at least two
years — that is the pre-existing statutory retention rule the draft would have
generalised, so the "2 Jahre" the pages present as new is not new. MiLoG § 17 carries
the same two-year period for the covered sectors. The repo cites "§16 Abs. 2 ArbZG"
directly (`attendance.py:11`); that citation is not supported by the crawl, only by this
domain knowledge.

**Known weakness of the current implementation (Fakt, code):** `retention_until` uses
`365 * 2 = 730` days, not calendar years — it drifts by one day across a leap year and
it is computed per-query rather than stored per-record. It is a display value, not an
enforcement mechanism: nothing deletes anything, and nothing prevents deletion either
(a `Shift` row cascades away with its `ShiftPlan`, `apps/planning/models.py:141`).

**Vorschlag** — if retention is ever enforced:
- keep the raw record beyond the display horizon; delete only on an explicit, logged job;
- give GPS/Bewegungsdaten (if ever added) a **separate, shorter** retention than time
  records — see `geofence-und-dsgvo.md` §7 (item 3) and §4;
- make the period a per-tenant configuration with a `valid_from`, because it is a legal
  parameter that changes.

---

## 6. Evidence on demand (Zoll / FKS)

**Fakt (source):** documentation must be "genau und zeitnah" so it can be produced at
"**unangekündigten Kontrollen des Zolls**"
(https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren); the vendor's
claimed capability is being "immer in der Lage, **geforderte Arbeitszeiten vorzulegen**"
(https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen).

**Fakt (code):** `time_records(account, start, end, worker=None)`
(`apps/planning/attendance.py:178-205`) is exactly this artefact and says so in its
docstring. It returns `{"rows": [...], "totals_minutes": {worker_id: minutes},
"retention_until": date}`; each row carries worker, date, site, zone, planned, actual,
variance, status. It filters to `status__in=[DONE, MISSED]` (`:185`) and counts MISSED
shifts as 0 minutes (`:192`).

**Gaps against an inspection-grade export (Vorschlag / Ungeprüft):**
- there is **no CSV/PDF export** — it renders only to
  `templates/dashboard/time_records.html`;
- it reports **shift totals, not daily totals**, and no break minutes;
- it is **not bitemporal**: rerunning it after a correction returns the corrected
  figure, with no way to reproduce the record "as it stood on date X". The event journal
  holds the history (`ShiftEvent.payload["from"]/["to"]`) but nothing reconstructs a
  point-in-time view from it. For an audit that questions a past export this matters —
  add `worked_on` / `recorded_at` / `corrected_at` semantics before claiming
  audit-readiness.

---

## 7. Contradictions to carry forward, never to resolve silently

1. **"Digital is mandatory" vs. "the medium is free."** Two pages headline a digital
   obligation; two state the law leaves the medium open. Do not repeat the stronger
   claim.
2. **7 days vs. same day (ideal) vs. same day (draft law).** Three timing standards; only
   the 7-day one is current law per the sources.
3. **8-hour daily average reference window: 24 Wochen vs. 6 Monate.** Printed three
   times on one page, twice as 24 Wochen and once as 6 Monate
   (https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen). 24 weeks
   ≠ 6 months. Make it configurable.
4. **Article dates are unreliable.** Six of the eleven blog pages carry May 2025 dates
   while describing an October 2022 legislative package as forthcoming. Treat the dates
   as edit dates, not publication dates, and never as evidence of legal currency.
5. **The Stundenzettel-Vorlage page lists no columns.** It is a pure email-gated
   download; the seven-field list comes from the Arbeitslexikon page instead.

---

## Quellen

Source pages (pland.app, crawled 2026-08-29):
- https://pland.app/blog/digitale-zeiterfassung-ist-pflicht-auch-fuer-gebaeudereiniger
- https://pland.app/blog/stundenzettel-vorlage-fuer-gebaeudereinigungen-kostenlos-herunterladen
- https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen
- https://pland.app/blog/zeiterfassung-2-0-mit-dem-digitalen-stundenzettel
- https://pland.app/blog/zeiterfassung-in-gebaeudereinigung-einfuehren
- https://pland.app/blog/gebaeudereinigung-arbeitszeiten-korrekt-berechnen
- https://pland.app/arbeitslexikon/stundenzettel
- https://pland.app/funktionen/zeiterfassung-gebaeudereinigung

Repository (read 2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/attendance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/dashboard/panels.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/templates/dashboard/time_records.html`
- `/Users/Geronimo/Projects/Cleaning_SaaS/tests/test_attendance.py`
