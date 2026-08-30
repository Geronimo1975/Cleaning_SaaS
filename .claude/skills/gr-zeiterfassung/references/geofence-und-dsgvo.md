# Geofence, Standortkontrolle und die DSGVO-Grenzen

Covers: what location-based time recording looks like in the competitor's product, what
the crawled sources say German law requires before a worker's position may be recorded,
what the sources do **not** say (which is a lot), the works-council dimension, BYOD, and
a data-minimising design for this repository.

**Stand:** 2026-08-29. Material from the pland.app crawl of 2026-08-29 (Zeiterfassung
blog cluster, the GPS-consent lead-magnet page, the Freigabe onboarding lesson, the
Arbeitslexikon `stempeluhr` page, the module pages and the AVV) plus the repository.
Reference material, not legal advice — location tracking of employees is one of the
areas where a Datenschutzbeauftragte(r) and, where one exists, the Betriebsrat must be
involved before code ships.

Labels: **Fakt** · **Vorschlag** · **Ungeprüft**.

---

## 1. State of this repository

**Fakt (code, verified 2026-08-29):** there is **no location data anywhere**. A
grep across `apps/`, `config/` and `tests/` for `lat`, `lng`, `latitude`,
`longitude`, `geo`, `geofen`, `distance`, `haversine`, `radius`, `ceil` returns no
attendance hit at all; the only `toleran`/`round` hits are `MATCH_TOLERANCE`
(`apps/devices/services.py:14`, used at `:115-116` to attach telemetry sessions to a
shift window) and `round(ratio, 2)` (`:162`, `:171`) — neither rounds recorded minutes.
`apps/planning/attendance.py` itself contains no geofence, distance check, tolerance
window or rounding logic. Specifically:

| Thing | State |
|---|---|
| Position captured at check-in / check-out | **none** — `check_in` writes only `checked_in_at` and a `ShiftEvent` with `payload={"at": now.isoformat()}` (`apps/planning/attendance.py:113-124`) |
| Geofence / radius on a site | **none** — `Site` has `locality`, `street`, `postal_code`, `is_active` and nothing else (`apps/planning/models.py:21-39`) |
| Coordinates anywhere | only `Locality.latitude` / `Locality.longitude`, `DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)` (`apps/geo/models.py:30-31`) — town-level, nullable, and used by nothing in attendance |
| Consent infrastructure | **exists but does not cover location**: `ConsentRecord` (`apps/accounts/compliance.py:51-70`) is append-only, versioned by `policy_version`, records `ip_address` and `user_agent`; `ConsentType` = `PROFILE_PUBLICATION`, `TERMS`, `PRIVACY`, `MARKETING` (`compliance.py:44-48`). `POLICY_VERSION = "2026-09-01"` (`apps/accounts/services.py:15`) |

**This is a defensible starting position, not a gap to close carelessly.** Time
recording is legally required; location recording is not. Adding GPS adds a legal
obligation the product does not currently carry.

---

## 2. What the competitor does (Fakt)

| Capability | Detail as stated | Source |
|---|---|---|
| **Standortbasierte Zeiterfassung** | "Welcher Mitarbeiter ist eigentlich gerade bei welchem Objekt? Durch die standortbasierte Zeiterfassung stellen Sie sicher, dass Ihre Mitarbeiter immer am **richtigen Einsatzort** sind und Arbeitszeiten korrekt erfasst werden." | https://pland.app/blog/kostenlose-muster-einverstaendniserklaerung-fuer-die-gps-ortung-und-digitale-zeiterfassung |
| **Ortsbasierte Erfassung** | GPS data used "um sicherzustellen, dass Mitarbeiter sich am **richtigen Einsatzort** befinden" | https://pland.app/arbeitslexikon/stempeluhr |
| **Standortkontrolle** | "Werden Sie automatisch informiert, wenn Mitarbeiter **außerhalb des geplanten Objekt-Radius'** Zeiten erfassen." → an Objekt carries a configured radius | https://pland.app/funktionen/uebersicht |
| **Standortfehler threshold** | "jedes Mal, wenn eine Reinigungskraft sich **über 800 Meter** vom Objekt entfernt ein- oder ausstempelt, werden Euch die Zeiten noch einmal zur Kontrolle vorgelegt" | https://pland.app/onboardings/freigabe-von-zeiterfassungen |
| **Deaktivierte Standortfreigabe** | a Fehlerart in its own right: "alle Zeiten …, bei denen Mitarbeiter die **GPS-Ortung deaktiviert** haben" — the worker **can** switch GPS off; the refusal is visible, not blocked | ibid. |
| **GPS-Erfassung toggle** | "Die GPS-Ortung kann ganz einfach unter GPS-Erfassung **aktiviert oder deaktiviert** werden." (tenant level) | ibid. |
| **Check-In / Check-Out Standort in the approval view** | "hier können wir uns genau den **Check-In und den Check-Out Standort** anschauen" | ibid. |
| **Objekt address is mandatory** | required so the software can "bei der Zeiterfassung automatisch den **Standort des Mitarbeiters mit der Adresse des Einsatzortes abgleichen** kann" | https://pland.app/onboardings/kunden-objekte-in-pland |
| **AVV data category** | "**Standortdaten der Mitarbeiter**, soweit im Rahmen der Zeiterfassung erhoben (z.B. beim **Ein- und Ausstempeln**)" — the vendor's own contract scopes location capture to the clock events | https://pland.app/avv (Ziff. 2.2 Nr. 4) |

The AVV wording is the most useful thing in this table: even the vendor's own data
processing agreement describes location as captured **at the stamp events**, not
continuously. That is the design to copy.

The vendor's marketing rationale is *not*: routes "effektiver planen und dadurch mehr
Kunden betreuen" and "Außerdem sehen Sie genau **wie produktiv Mitarbeiter Ihre
Arbeitszeit nutzen**"; the Gesetzentwurf page states the goal openly as
"**Gewinnmaximierung**". That is Leistungs- und Verhaltenskontrolle framing and it is
exactly what attracts works-council and supervisory-authority scrutiny.

---

## 3. What the sources say the law requires (Fakt)

Two pages carry all of it:
https://pland.app/blog/kostenlose-muster-einverstaendniserklaerung-fuer-die-gps-ortung-und-digitale-zeiterfassung
and
https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen.

| Requirement | Verbatim |
|---|---|
| Legal in principle | "Digitale Zeiterfassung und GPS-Ortung von Mitarbeitern ist **prinzipiell erlaubt**." / "Es ist **prinzipiell erlaubt**, Mitarbeiter per GPS-Ortung zu überwachen." |
| Secure the legal position first | "Allerdings sollten Sie sich vorher immer erst **rechtlich absichern**, damit keine Datenschutzrichtlinien verletzt werden." |
| **Written, signed consent** | "benötigen Sie eine **schriftlich unterschriebene Einverständniserklärung** Ihrer Mitarbeiter" / "Es braucht dafür allerdings eine **unterschriebene Einverständniserklärung** der Mitarbeiter." |
| **Working time only** | "Außerdem sollte die GPS-Ortung **nur während der Arbeitszeit** erfolgen." / "die GPS-Ortung … darf, **wenn nicht explizit anders vereinbart, nur während der Arbeitszeit** erfolgen" |
| **Betriebsrat** | "sollten zunächst so **transparent wie möglich mit dem Betriebsrat** besprechen, inwiefern **Bewegungsdaten erfasst, ausgewertet und gespeichert** werden" / "sollte **zusammen mit dem Betriebsrat** festgelegt werden, **in welcher Form die Bewegungsdaten erfasst und ausgewertet** werden dürfen" |
| **Private devices** | "Wenn Sie die Arbeitszeiten Ihrer Mitarbeiter mit einer App auf den **privaten Smartphones** erfassen wollen, brauchen Sie dafür die **Zustimmung** oder müssen bei **Nichteinwilligung ein Erfassungsgerät bereitstellen**." |
| **No obligation to install an app** | "Die Mitarbeiter sind **nicht gezwungen**, sich eine Mitarbeiter App herunterzuladen … Besonders die **Standortbestimmung** ist dabei ein Problem." |
| Private phones are problematic per se | "Arbeitszeiten über die **privaten Smartphones** der Mitarbeiter zu erfassen, ist **aus Datenschutzgründen problematisch**." |

### 3a. What the sources do **not** say — do not fill these in from the competitor

| Missing | Status |
|---|---|
| Any **DSGVO article** | **Not stated.** Neither "DSGVO", "GDPR", Art. 6, Art. 7, Art. 88 nor "berechtigtes Interesse" appears in the GPS pages. |
| **§ 26 BDSG** | **Not stated.** |
| Whether consent in an employment relationship is genuinely free | **Not addressed.** |
| What happens on **withdrawal** of consent | **Not addressed.** |
| Whether a **Betriebsvereinbarung is mandatory**, and what applies when there is no Betriebsrat | **Not addressed** — the pages say only "sollte … besprochen werden", although a separate page stresses the *recording duty* applies regardless of whether a Betriebsrat exists. |
| **Retention** of Bewegungsdaten | **Not stated anywhere in the crawl.** |
| Whether raw coordinates or only a match/no-match result may be stored | **Not addressed.** |
| Contents of the **Muster-Einverständniserklärung** | **Not stated** — see §4. |

The general Datenschutzerklärung (a different page) does list the vendor's Art. 6 bases
for its *website and applicant* processing — lit. a (Einwilligung), lit. b (Vertrag),
lit. c (rechtliche Verpflichtung), lit. f (berechtigte Interessen), plus
**Art. 88 Abs. 1 DSGVO i.V.m. § 26 Abs. 1 BDSG** for Bewerberdaten
(https://pland.app/datenschutz). **None of these is asserted for GPS tracking.**

---

## 4. The sample Einverständniserklärung — what is actually known

**Fakt:** the page titled "Kostenlose Muster-Einverständniserklärung für die GPS-Ortung
und digitale Zeiterfassung" is an **email-gated lead magnet**. Its full call-to-action
is: "**Kostenloses Muster herunterladen** — Mit der kostenlosen GPS-Muster für
Zeiterfassung sind Sie auf der sicheren Seite! Sie erhalten den Download per Email.
Hiermit erklären Sie sich einverstanden, dass PlanD Ihnen Emails zusenden darf."

**The page reproduces not one clause of the declaration.** Its structure, scope,
revocation clause, data categories and retention period are **nicht belegt / not
established from the sources**. Any statement about "what the sample contains" would be
invention.

What the *page text around the gate* does establish as the substantive requirements is
exactly the list in §3 above: signed and in writing; working time only; discussed with
the Betriebsrat covering capture, evaluation **and storage**; and for a private device
either consent or an employer-provided Erfassungsgerät.

**Vorschlag / Ungeprüft — a consent declaration structure that matches those four
requirements.** This is a design proposal to be reviewed by a lawyer, not a reproduction
of the competitor's document:

| Section | Content |
|---|---|
| 1. Parties | employer (Verantwortlicher), employee, date |
| 2. Purpose | verification that the clock event occurred at the assigned Objekt — named narrowly, not "Produktivitätskontrolle" |
| 3. Data categories | position at **check-in** and **check-out** only; explicitly: no continuous tracking, no background location, no movement profile |
| 4. Time window | during working time only; the app must not be able to read position outside an open shift |
| 5. Device | company device / private device (BYOD); on refusal of a private device the employer provides an Erfassungsgerät |
| 6. Retention | a stated period for Standortdaten, **shorter than and separate from** the time-record retention |
| 7. Recipients | who inside the company can see it; any processor |
| 8. Voluntariness and consequences | consent is voluntary; refusing it must not disadvantage the employee, and time recording must remain possible without it |
| 9. Revocation | revocable at any time, effective for the future, with a named contact and no detriment |
| 10. Signature | employee signature, date; employer counter-signature |
| Annex | reference to the Betriebsvereinbarung, where one exists |

---

## 5. Works council and the deeper legal picture

**Ungeprüft — my domain knowledge; the crawled sources do not cover any of this.
Verify before relying on it.**

- **Consent is the weakest available basis.** Employee consent under
  Art. 6 Abs. 1 lit. a + Art. 7 DSGVO and § 26 Abs. 2 BDSG is fragile in an employment
  relationship because of the *freely given* test (the imbalance of power). Practitioners
  normally build employee location processing on **§ 26 Abs. 1 BDSG / Art. 6 Abs. 1
  lit. f DSGVO** *plus* a **Betriebsvereinbarung**, and treat individual consent as a
  supplement, not the foundation.
- **Co-determination is mandatory, not advisory.** **§ 87 Abs. 1 Nr. 6 BetrVG** gives
  the works council a *mandatory* co-determination right over technical devices suitable
  for monitoring the behaviour or performance of employees. A GPS-verified clocking
  system is squarely such a device. The competitor's "sollte … besprochen werden"
  understates this: without the works council's agreement, in a company that has one, the
  system may not be introduced at all.
- **A Datenschutz-Folgenabschätzung (Art. 35 DSGVO)** is generally expected for
  systematic location processing of employees.
- **Revocation must degrade gracefully** (Art. 7 Abs. 3 DSGVO): withdrawing consent must
  not break the worker's ability to record time. In product terms: the non-GPS clocking
  path must always exist — which is what the competitor's "deaktivierte
  Standortfreigabe" Fehlerart implicitly concedes.
- **Purpose limitation.** Data collected to verify presence at an Objekt may not be
  repurposed for performance ranking. The "sehen genau wie produktiv Mitarbeiter Ihre
  Arbeitszeit nutzen" framing is a purpose the consent above would not cover.

---

## 6. BYOD

**Fakt** (https://pland.app/blog/byod-bring-your-own-device-in-der-gebaudereinigung-effizienzsteigerung-durch-private-endgerate):
definition "Dabei nutzen Mitarbeitende ihre **privaten Smartphones oder Tablets** für
berufliche Zwecke"; six advantages listed (Kosteneinsparungen durch reduzierte
Hardwareanschaffungen; Mitarbeiterzufriedenheit und -bindung; Produktivität durch
vertraute Technologie; Kommunikation und Erreichbarkeit; Flexibilität; Unterstützung
moderner Arbeitsmodelle) and three challenges with their stated mitigation:

| Challenge | Mitigation as stated |
|---|---|
| **Datensicherheit** | "klare **Richtlinien und Sicherheitsmaßnahmen** implementieren, um Unternehmensdaten zu schützen" |
| **Compliance** | "Die Einhaltung gesetzlicher Vorgaben, **insbesondere im Datenschutz**, muss gewährleistet sein. Dies erfordert **regelmäßige Schulungen und klare Verhaltensregeln**." |
| **Technischer Support** | "Die **Vielfalt an Geräten** kann den IT-Support belasten. **Standardisierte Anwendungen und Plattformen** können hier Abhilfe schaffen." |

**The BYOD page contradicts the GPS page by omission** (Fakt): it sells cost saving as
advantage #1 without mentioning the rule stated on the GPS page — that an employee's
refusal obliges the employer to provide an Erfassungsgerät anyway. It also never
mentions consent, MDM, remote wipe or expense reimbursement.

**Ungeprüft:** German employers relying on private devices for work generally owe
**Aufwendungsersatz (§ 670 BGB analog)** for the pro-rata device and data cost, and a
BYOD policy needs container/MDM separation so a remote wipe cannot destroy private data.

**Vorschlag — model it, because it is a legal obligation with a deadline:**
`DeviceConsent(worker, mode ∈ {BYOD_PRIVATE, COMPANY_DEVICE, TERMINAL}, consented_at,
withdrawn_at)`. When `mode` is not `BYOD_PRIVATE` and no company device is issued, that
is a **blocking onboarding task for the employer**, not a warning.

---

## 7. A data-minimising geofence design for this repo (Vorschlag)

If location verification is ever built here, build the smallest thing that answers the
only legitimate question — *was the clock event at the assigned Objekt?*

**Do:**
1. Capture position **only at the two clock events**, never in the background, never
   between them. (This matches the competitor's own AVV wording, §2.)
2. Compute the match **on the device or at the request boundary**, and persist a
   **coarse verdict**, not raw coordinates:
   `location_check ∈ {NOT_REQUESTED, GRANTED_INSIDE, GRANTED_OUTSIDE, DENIED, UNAVAILABLE}`
   plus a bucketed `distance_band` (e.g. `<100m`, `100-800m`, `>800m`) if a distance is
   needed for the Freigabe queue at all.
3. Store the raw lat/lng **only** when the tenant has switched it on *and* an active
   consent record exists *and* the event is `GRANTED_OUTSIDE` (i.e. the disputed case)
   — and give it its own, shorter retention than the time record.
4. Hard-gate every capture on an active consent: a helper such as
   `location_capture_allowed(worker) -> bool` that checks the tenant switch **and** the
   latest `ConsentRecord` for a new `ConsentType.LOCATION_TRACKING`, reusing the existing
   append-only, `policy_version`-stamped model (`apps/accounts/compliance.py:51-70`).
5. Make refusal a **flag, never a block** — the worker must still be able to clock in.
   The competitor's "deaktivierte Standortfreigabe" Fehlerart is the right shape.
6. Put the site geometry on `Site`, not on `Locality`: `Site.latitude`,
   `Site.longitude`, `Site.geofence_radius_m` (default configurable per tenant; the
   competitor's threshold is **800 m**, which is a *review* threshold, not a *reject*
   threshold — copy that semantic). `Locality.latitude/longitude`
   (`apps/geo/models.py:30-31`) is town-level and unsuitable.
7. Add a `LOCATION_CONSENT_GRANTED` / `_WITHDRAWN` trail so a past record can be
   explained by the consent version that legitimised it.

**Do not:**
- store a movement profile, a route, or any position between clock events;
- block a check-in on a geofence miss — that turns a data-protection feature into a wage
  denial;
- surface location data in any productivity or ranking view;
- write coordinates into `ShiftEvent.payload` before the consent gate exists — the
  journal is immutable by design (`apps/planning/models.py:217-220`), so anything written
  there cannot be deleted through the ORM's normal paths.

**Open design question the sources do not answer:** the competitor's app works
**offline** ("Offline verfügbar", https://pland.app/funktionen/zeiterfassung-gebaeudereinigung). How an
offline clock event's position is reconciled against the Objekt radius when it is
uploaded later is never explained. If offline clocking is ever built here, decide
explicitly whether a late-uploaded position is trustworthy, and flag it if not.

---

## Quellen

Source pages (pland.app, crawled 2026-08-29):
- https://pland.app/blog/kostenlose-muster-einverstaendniserklaerung-fuer-die-gps-ortung-und-digitale-zeiterfassung
- https://pland.app/blog/gesetzentwurf-zur-digitalen-zeiterfassung-alles-was-sie-wissen-muessen
- https://pland.app/blog/byod-bring-your-own-device-in-der-gebaudereinigung-effizienzsteigerung-durch-private-endgerate
- https://pland.app/onboardings/freigabe-von-zeiterfassungen
- https://pland.app/arbeitslexikon/stempeluhr
- https://pland.app/funktionen/zeiterfassung-gebaeudereinigung
- https://pland.app/funktionen/uebersicht
- https://pland.app/avv (Ziff. 2.2)
- https://pland.app/datenschutz

Repository (read 2026-08-29):
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/compliance.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/accounts/services.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/geo/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/attendance.py`
