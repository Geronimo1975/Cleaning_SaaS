# Zuschläge, Urlaub, Krankheit, Kündigung

**Was diese Datei abdeckt:** jeden Zuschlag mit Satz und Bemessungsgrundlage, die
Kollisionsregel, den steuerlichen Rahmen des § 3b EStG, dazu Urlaubsanspruch und seine
Berechnung, zusätzliches Urlaubsgeld, Entgeltfortzahlung im Krankheitsfall, das
Krankmeldeverfahren mit seinen Fristen, und die Kündigungsfristen.
**Stand: 2026-08-29.**
**Herkunft:** pland.app Arbeitslexikon (RTV-Seite im Wortlaut abgeglichen gegen
`txt/arbeitslexikon__rahmentarifvertrag-gebaeudereinigung-2023.md` und
`txt/arbeitslexikon__erschwerniszuschlaege.md`), plus die Produkt-Onboardings zu Lohnarten,
Zuschlägen und Urlaubstageberechnung.
**Rechtlicher Hinweis:** Referenzmaterial, keine Rechtsberatung.

---

## 1. Die Zuschlagstabelle

**Quellen (alle vier nennen dieselben Sätze):**
https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023 (RTV § 3 Nr. 4.7),
https://pland.app/arbeitslexikon/nachtarbeit-gebaeudereinigung,
https://pland.app/arbeitslexikon/sonntagsarbeit-gebaeudereinigung,
https://pland.app/arbeitslexikon/feiertagsarbeit-gebaeudereinigung

| Zuschlag | Satz | Auslösendes Zeitfenster | Bemessungsgrundlage | Fundstelle |
|---|---|---|---|---|
| **Nachtarbeit** | **30 v.H.** | **22.00 – 5.00 Uhr** | Stundenlohn | RTV 4.7 a) |
| **Sonn- und Feiertagsarbeit** | **80 v.H.** | **0.00 – 24.00 Uhr** des Tages | Stundenlohn | RTV 4.7 b) |
| **1. Mai, Neujahrstag, 1. und 2. Weihnachtsfeiertag** | **200 v.H.** | **0.00 – 24.00 Uhr** | Stundenlohn | RTV 4.7 c) |
| **24.12. (Heiligabend) oder wahlweise 31.12.** | **150 %** | die an dem Tag geleistete Arbeit | Stundenlohn | TV Freistellung § 2; https://pland.app/arbeitslexikon/tarifvertrag-zur-freistellung-an-heiligabend-oder-silvester |
| **Belastungszuschlag (Überstunden)** | **25 %** | mehr als **8 Stunden täglich** (§ 3 Satz 1 ArbZG) **oder**, alternativ, „für die über die **40. Arbeitsstunde** hinausgehende Arbeitszeit pro Woche" | Stundenlohn | https://pland.app/arbeitslexikon/erschwerniszuschlaege |
| **Erschwerniszuschläge** | **5 / 10 / 15 / 20 / 40 %** | nur „für die Zeit, in der sie eine der folgenden Tätigkeiten ausüben" | „auf der Grundlage des **für den Arbeitsbereich geltenden Lohnsatzes**" | ebd. |

### Erschwerniszuschläge im Detail (verbatim)

„Arbeiten, bei denen ein **vorgeschriebener Schutzanzug (mit PVC o.ä. beschichtet)** verwendet wird:"

| Ausrüstungskombination | Satz |
|---|---|
| Mit Überschuhen, Kapuze, Brille und Handschuhen | **5 %** |
| Mit Überschuhen, Kapuze und Handschuhen, Filterschutzmaske oder luftunterstützenden Beatmungssystemen | **15 %** |
| Mit Überschuhen, Kapuze und Handschuhen, Druckluftschlauchgerät (Pressluftatmer), Frischluftsaugschlauchgerät oder ein Regenerationsgerät | **20 %** |
| In Form des Vollschutzes oder des Chemikalienschutzanzuges (Form C) mit Gesichts- und Atemschutz | **40 %** |
| Arbeiten, bei denen eine vorgeschriebene **Atemschutzmaske** verwendet wird | **10 %** |

Beispiele für PSA auf der Seite: „Atemschutzgerät, Handschuhe, Schutzbekleidung".

**Anspruchsvoraussetzung, verbatim:** „Der Anspruch auf Erschwerniszuschläge setzt voraus, dass
Beschäftigte die einschlägigen **Arbeitsschutzvorschriften einhalten**." — im Modell ein
Pflichtfeld `arbeitsschutz_bestaetigt`, nicht ein Kommentar.

**Beachte die abweichende Bemessungsgrundlage:** Der Erschwerniszuschlag rechnet auf den
**Lohnsatz des Arbeitsbereichs**, nicht zwingend auf den persönlichen Stundenlohn des
Beschäftigten. Wer für eine LG-6-Tätigkeit eingesetzt wird, obwohl er in LG 1 eingruppiert ist,
bekommt den Erschwerniszuschlag auf den Satz des Arbeitsbereichs.

---

## 2. Die drei Regeln, die jede Zuschlagsberechnung binden

**1 — Bemessungsgrundlage.** „Die Zuschläge sind **aus dem Stundenlohn** zu berechnen."
(RTV 4.8; wörtlich wiederholt auf `zuschlaege-gebaeudereinigung` und `erschwerniszuschlaege`.)

**2 — Höchster gewinnt, nie kumulativ.** „Treffen mehrere der vorgenannten Zuschläge zusammen,
ist **nur der jeweils höchste** zu zahlen." (RTV 4.8; identisch auf `zuschlaege-…`,
`nachtarbeit-…`, `sonntagsarbeit-…`, `feiertagsarbeit-…`, `erschwerniszuschlaege`.)
Der Wettbewerber implementiert genau das: „Sollten Nacht, Feiertag und Sonntagszuschlag
gleichzeitig anfallen, nimmt PlanD automatisch immer nur den **höchsten** Zuschlag (siehe
Lohntarifvertrag)." (https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland)

**3 — Keine Abgeltung über den Grundlohn.** „Die **Abgeltung von Zuschlägen aller Art durch
erhöhten Lohn ist unzulässig**." (https://pland.app/arbeitslexikon/zuschlaege-gebaeudereinigung)
Ebenso: „Die **Vergütung von Prämien jeglicher Art durch Lohnerhöhungen ist nicht zulässig**."
(https://pland.app/arbeitslexikon/lohnabrechnung-gebaeudereinigung)

### Auflösung pro Zeitscheibe (**Vorschlag** — die Regeln selbst sind Fakt)

Eine Schicht von Sonntag 21:00 bis Montag 02:00 zerfällt in:

| Scheibe | Anwendbare Zuschläge | Gezahlt | Unterdrückt |
|---|---|---|---|
| So 21:00–22:00 | Sonntag 80 % | **80 %** | — |
| So 22:00–24:00 | Sonntag 80 %, Nacht 30 % | **80 %** | Nacht 30 % |
| Mo 00:00–02:00 | Nacht 30 % | **30 %** | — |

Regeln für die Implementierung:
- Zerlege nach **Minuten**, nicht nach Schichten. Ein Schichtwechsel um Mitternacht wechselt
  gleichzeitig Kalendertag, Feiertagsstatus und Nachtfenster.
- Die **unterdrückten** Positionen werden persistiert, mit Verweis auf die gewinnende Position.
  Betriebsrat und Zoll fragen, warum eine Sonntagsstunde keinen Nachtzuschlag trug.
- Der Vergleich läuft über den **Prozentsatz**, nicht über den Eurobetrag — die Erschwernis
  rechnet ggf. auf einen anderen Lohnsatz und wäre sonst nicht vergleichbar. Wo die
  Grundlagen auseinanderfallen, dokumentiere die getroffene Entscheidung; der Wortlaut regelt
  diesen Fall **nicht** (nicht belegt).
- Feiertage sind **per Bundesland** zu bestimmen: außer 1. Mai / Neujahr / 1.+2.
  Weihnachtsfeiertag sind die Feiertage „**spezifisch für jedes Bundesland**"
  (https://pland.app/arbeitslexikon/feiertagsarbeit-gebaeudereinigung). Der Bezugspunkt ist das
  **Bundesland des Objekts**, nicht das des Mitarbeiters oder des Betriebssitzes.

---

## 3. § 3b EStG — Steuerfreiheit der Zuschläge

**Auf keiner der ausgewerteten pland.app-Seiten steht etwas dazu.** Eine Volltextsuche über den
gesamten Arbeitslexikon-Cluster nach „EStG", „steuerfrei" und „Steuer" liefert **einen** Treffer:
die 1.800-€-Grenze für steuerfreie Entgeltumwandlung auf der TZR-Seite. Keine Zuschlagsseite
erwähnt Steuer oder Sozialversicherung. Ein Blogtext nennt „steuerfreie Zuschläge" nur als
Feature (https://pland.app/blog/digitale-lohnabrechnung-ein-blick-auf-die-vorteile-in-der-gebaudereinigung),
ohne Sätze oder Grenzen.

**Ungeprüft — eigenes Domänenwissen, ausdrücklich als Recherche-Auftrag, nicht als Daten:**
§ 3b EStG stellt **tatsächlich gezahlte** Zuschläge für Sonntags-, Feiertags- und Nachtarbeit
innerhalb gesetzlicher Höchstsätze steuerfrei, berechnet auf einen **gedeckelten
Grundstundenlohn**; die sozialversicherungsrechtliche Freiheit folgt einer eigenen, niedrigeren
Deckelung. Die Höchstsätze liegen dem Vernehmen nach unter den tariflichen Prozentsätzen dieser
Branche.

**Was daraus für den Code folgt und was nicht:**
- **Folgt:** Jede Zuschlagsposition braucht die Felder `betrag_steuerfrei` und
  `betrag_steuerpflichtig` sowie die verwendete **Bemessungsgrundlage**, weil eine Aufteilung
  praktisch sicher nötig wird. Die Struktur ist begründbar, ohne dass eine einzige Zahl geraten
  wird.
- **Folgt nicht:** Irgendein Prozentsatz oder Deckel darf gesät werden. Der steuerfreie Anteil
  bleibt `None`, bis ein belegter Wert vorliegt, und ein Lohnlauf, der ihn braucht, **blockiert**.

---

## 4. Urlaub — RTV § 14

Quelle für den gesamten Abschnitt:
https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023

### 4.1 Urlaubsanspruch (Ziff. 1), Basis Fünf-Tage-Woche

| Zeitraum | Anspruch |
|---|---|
| **bis 31. Dezember 2019**, 1. Beschäftigungsjahr | **28 Arbeitstage** |
| bis 31. Dezember 2019, 2. Beschäftigungsjahr | **29 Arbeitstage** |
| bis 31. Dezember 2019, 3. Beschäftigungsjahr | **30 Arbeitstage** |
| **ab 1. Januar 2020**, 1. Beschäftigungsjahr | **29 Arbeitstage** |
| ab 1. Januar 2020, ab dem 2. Beschäftigungsjahr | **30 Arbeitstage** |
| **ab 1. Januar 2021** | **30 Arbeitstage** |

Weitere Regeln, verbatim bzw. eng paraphrasiert:

- Andere Wochenarbeitstage: „Sofern die Beschäftigung mehr oder weniger als fünf Tage in der
  Woche erfolgt, **erhöht oder verringert sich die Anzahl der Urlaubstage entsprechend**."
- „**Zeiten eines Berufsausbildungsverhältnisses gelten insoweit als Beschäftigungszeiten.**"
- Ausscheiden **innerhalb der ersten sechs Monate**: Anspruch richtet sich nach
  **§§ 3 und 5 Bundesurlaubsgesetz**.
- **Schwerbehinderte**: zusätzlicher Urlaub **nach gesetzlicher Maßgabe** (Ziff. 1.2).
- Voller Jahresurlaub bleibt erhalten bei **Kuren oder Heilverfahren** eines
  Sozialversicherungs- oder sonstigen Sozialleistungsträgers (Ziff. 1.3).
- Beginn/Ende im Laufe des Urlaubsjahres: **1/12 für jeden vollen Kalendermonat**;
  „Der **gesetzliche Mindesturlaub darf nicht unterschritten werden**." (Ziff. 1.4)
- „**Urlaubsjahr ist das Kalenderjahr.** Für die Berechnung der Urlaubsdauer sind die am
  **01. Januar** des Urlaubsjahres erreichten Beschäftigungsjahre maßgebend." (Ziff. 1.5)

### 4.2 Urlaubsantritt (Ziff. 3)

- **Wartezeit:** voller Urlaub erstmals nach **sechs Monaten**, bei **Jugendlichen nach drei
  Monaten** ununterbrochener Dauer beim gleichen Arbeitgeber.
- Zeitpunkt bestimmt der Arbeitgeber „unter Berücksichtigung der Wünsche der Beschäftigten nach
  den Bedürfnissen des Betriebes".
- Urlaub **möglichst zusammenhängend**; Urlaub Jugendlicher **soll während der Berufsschulferien**
  gewährt werden.
- **Übertragung** ins Folgejahr nur bei „dringenden betrieblichen oder in der Person der
  Beschäftigten liegenden Gründen".
- **Verbrauchsreihenfolge:** „wird zunächst der **gesetzliche** Urlaubsanspruch erfüllt, sodann
  der **tarifliche**."
- **Verfall:** bei Übertragung erlischt der Anspruch **drei Monate nach Ablauf des Kalenderjahres**
  — es sei denn, er konnte **wegen Krankheit** nicht genommen werden; dann erlischt der
  **tarifliche** Anspruch **drei Monate nach Ablauf des Urlaubsjahres**.

### 4.3 Urlaubslohn (Ziff. 2)

- Höhe: „den **durchschnittlichen Lohn der letzten 12 Monate**, **mindestens jedoch den für ihre
  Tätigkeit zum Zeitpunkt des Urlaubsantritts jeweils gültigen tariflichen Mindestlohn**, für
  ihre aktuelle regelmäßige Arbeitszeit."
- **Nicht** in den Durchschnitt: „unverschuldete Fehltage, wie z.B. **Krankheitstage außerhalb
  des gesetzlichen Entgeltfortzahlungszeitraumes**, **Kurzarbeitszeiten** usw."
- **Aus der Bemessung ausgeschlossen:** „**Einmalvergütungen, Aufwendungsersatz**, wie z. B.
  **Gratifikationen, Fahrtkosten und Auslösung**."
- Weniger als zwölf Monate beschäftigt → diese Monate bilden die Basis.
- Auszahlbar nur, wenn (a) der Urlaub **tatsächlich angetreten** wird, (b) er wegen
  **Beendigung des Arbeitsverhältnisses** nicht mehr gewährt/genommen werden kann, oder
  (c) der Beschäftigte **verstirbt** — Hinterbliebene müssen Erbberechtigung nachweisen und
  haben **keinen** Anspruch auf Urlaubslohn, der nur wegen Krankheit nicht erloschen ist.
- Bei Beendigung: Arbeitgeber muss eine **Bescheinigung über den im laufenden Kalenderjahr
  gewährten oder abgegoltenen Urlaub** aushändigen.

### 4.4 Urlaubstageberechnung in der Praxis

Der Wettbewerber setzt den Branchenwert als Default und leitet die effektiven Tage aus den
Wochenarbeitstagen ab:

| Aussage | Quelle |
|---|---|
| „in der Gebäudereinigungsbranche sind dies **laut Rahmentarifvertrag 30 Tage**" — Default in den Einstellungen | https://pland.app/onboardings/einstellungen-fur-die-urlaubstageberechnung |
| Konfigurierbar: Jahresanspruch in Tagen, **Wartezeit** für Neueinstellungen, **Übernahme der Urlaubstage in einen neuen Zyklus** (Übertrag) | ebd. |
| „Die effektiven Urlaubstage werden **auf der Basis der Anzahl der Arbeitstage in der Woche** berechnet" | https://pland.app/onboardings/urlaubsanspruch-von-mitarbeitern |
| Individuelle **Anpassungen** möglich, ausdrücklich auch: **Überstunden** aus einem Jahr als zusätzliche Urlaubstage ins nächste übertragen. **Jede Löschung einer Anpassung löst eine automatische Neuberechnung aus** | ebd. |
| Beispiel: bei **3-Tage-Woche** verbraucht eine volle Abwesenheitswoche nur **3 Urlaubstage** | https://pland.app/onboardings/urlaubstage-im-urlaubsantrag |
| Beim Antrag: Abwesenheit wird gegen Arbeitswochenstunden und Restanspruch gebucht, der Restanspruch aktualisiert sich automatisch und ist in der App sichtbar | ebd. |

**Die arithmetische Formel steht auf keiner Seite** — nur der Bezug auf die Wochenarbeitstage.
Die naheliegende Umsetzung (**Vorschlag**) ist die Pro-rata-Regel des RTV:

```
anspruch_tage = round(30 * arbeitstage_pro_woche / 5)   # RTV § 14 Ziff. 1.1, ab 01.01.2021
```

Das Rundungsverfahren ist **nicht belegt** — es muss eine bewusste, dokumentierte Entscheidung
sein (aufrunden ist die für den Beschäftigten sichere Variante), und der **gesetzliche
Mindesturlaub darf nie unterschritten werden** (RTV Ziff. 1.4).

**Ungeprüft:** Nach EuGH-/BAG-Rechtsprechung verfällt der **gesetzliche** Urlaubsanspruch nur,
wenn der Arbeitgeber nachweislich über Anspruch und Verfall belehrt hat. Die flache
„erlischt drei Monate nach Jahresende"-Regel des RTV bildet das nicht ab. Ein Urlaubsmodul
sollte diese **Hinweisobliegenheit** revisionssicher protokollieren.

---

## 5. Zusätzliches Urlaubsgeld

Quelle: https://pland.app/arbeitslexikon/tarifvertrag-uber-ein-zusatzliches-urlaubsgeld

| Fakt | Wert |
|---|---|
| Voraussetzung | **Betriebszugehörigkeit von sechs Monaten** |
| Höhe | **1,85 Tarifstundenlöhne pro Urlaubstag** |
| Bemessung | **Tarifstundenlohn der jeweiligen Entgeltgruppe**, gültig **zum Zeitpunkt des Urlaubs** |
| Teilzeit | anteilig entsprechend der vereinbarten Arbeitszeit |
| Auszubildende | **1/169** der bei Urlaubsantritt geltenden Ausbildungsvergütung |
| Auszahlung | **zusammen mit dem Urlaubslohn** gemäß RTV § 14 Ziff. 2 |
| gilt für Ansprüche | erworben **ab dem 1. Januar 2007** |

Rechenbeispiel (arithmetisch aus den belegten Werten, LG 1 ab 01.01.2026 = 15,00 €):
1,85 × 15,00 € = **27,75 € pro Urlaubstag**, bei 30 Tagen **832,50 €** im Jahr — vollzeit,
5-Tage-Woche. Die Faktoren sind Fakt, das Produkt ist reine Multiplikation.

**Achtung:** die Bemessung ist der **Tarifstundenlohn**, nicht der individuell vereinbarte
Stundenlohn. Wer über Tarif zahlt, zahlt das Urlaubsgeld trotzdem auf den Tarifsatz — sofern
nicht vertraglich mehr zugesagt ist.

---

## 6. Krankheit — Meldung, Nachweis, Entgeltfortzahlung

Quellen: https://pland.app/arbeitslexikon/krankmeldung und
https://pland.app/arbeitslexikon/krankheitsausfall

### 6.1 Meldepflicht des Beschäftigten

- **unverzüglich** melden, unter Angabe der **voraussichtlichen Dauer** — „Dies gilt auch wenn
  Sie sich im **Ausland** befinden."
- **möglichst vor dem Arbeitsbeginn**; ein Versäumnis **kann zu einer Abmahnung führen**.
- Der **Grund muss nicht** genannt werden: „Den Grund für die Krankmeldung muss der Arbeitnehmer
  dabei nicht preisgeben."
- Bevorzugter Kanal laut Seite: **persönlich über das Telefon**; „Krankmeldungen via **Email,
  SMS oder Anrufbeantworter**" garantieren keinen rechtzeitigen Zugang.

### 6.2 Arbeitsunfähigkeitsbescheinigung (AU)

| Quelle | Frist wie gedruckt |
|---|---|
| `krankheitsausfall` | „Wenn die Arbeitsunfähigkeit länger als **3 Tage** andauert, muss der Arbeitnehmer **spätestens am 4. Tag** unaufgefordert eine ärztliche Bescheinigung … vorzulegen." |
| `krankmeldung`, zitiert **§ 5 EntgFG** | „Dauert die Arbeitsunfähigkeit länger als **drei Kalendertage**, hat der Arbeitnehmer eine ärztliche Bescheinigung … **spätestens an dem darauffolgenden Arbeitstag** vorzulegen." |

**Das sind nicht dieselben Fristen** (4. Kalendertag vs. nächster Arbeitstag). Beide sind
dokumentiert; in einer Implementierung sollte der **Gesetzeswortlaut** gewinnen. Weiter:
- Der Arbeitgeber ist berechtigt, die Vorlage **früher zu verlangen**.
- Dauert die AU länger als bescheinigt, ist eine **Folgebescheinigung** vorzulegen.
- Für Mitglieder einer **gesetzlichen Krankenkasse** trägt die Bescheinigung den Vermerk, dass
  der Kasse eine Bescheinigung mit **Befund und voraussichtlicher Dauer** übermittelt wird.

**Ungeprüft:** Seit 2023 ruft der Arbeitgeber die **eAU** für gesetzlich Versicherte bei der
Krankenkasse ab, statt eine Papierbescheinigung entgegenzunehmen. Der „AU im App hochladen"-Flow
des Wettbewerbers (https://pland.app/arbeitslexikon/abwesenheitsverwaltung) liegt damit hinter
dem aktuellen Rechtsmechanismus — eine echte Differenzierungschance, aber vor dem Bau prüfen.

### 6.3 Entgeltfortzahlung

| Fakt | Wert | Quelle |
|---|---|---|
| Fortzahlung bei Krankheit **oder Arbeitsunfall** | **bis zu 6 Wochen** beim **durchschnittlichen Gehalt der letzten 12 Monate** | `krankheitsausfall` |
| Neueinstellungen | „erhalten in den **ersten vier Wochen** ihrer Beschäftigung **keine Lohnfortzahlung**" | `krankheitsausfall` |
| Krankheit und bezahlter Urlaub | „müssen **bis zu 6. Wochen** weiter bezahlt werden" (ohne Einschränkung) | https://pland.app/arbeitslexikon/lohnabrechnung-gebaeudereinigung |

Die letzten beiden Zeilen widersprechen sich (Karenz für Neueinstellungen ja/nein). Beide
dokumentiert; nicht stillschweigend auflösen.

Der Wettbewerber lässt die **Bemessungsbasis pro Abwesenheit wählen**: **Vertragsstunden** /
**Planstunden** / **Stundendurchschnitt der letzten 3 Monate**
(https://pland.app/arbeitslexikon/… bzw. https://pland.app/onboardings/abwesenheiten-in-pland).
Der RTV nennt für den Urlaubslohn den **12-Monats**-Durchschnitt — die 3 Monate sind eine
Produktentscheidung des Wettbewerbers, keine Tarifregel.

### 6.4 Krankengeldzuschuss bei Betriebsunfällen

Quelle: `krankheitsausfall`

- Beginn: **ab der 7. Krankheitswoche**.
- Höhe: **drei Stundenlöhne pro Arbeitstag**.
- Dauer nach Betriebszugehörigkeit, Schwellen **wie gedruckt**:

| Betriebszugehörigkeit | bezahlt bis Ende der |
|---|---|
| **< 3. Jahre** | **9. Krankheitswoche** |
| **> 3. Jahre** | **12. Krankheitswoche** |
| **> 5 Jahre** | **15. Krankheitswoche** |
| **> 7 Jahre** | **17. Krankheitswoche** |

- Deckel: „**Krankengeld und Beihilfe dürfen zusammen den bisherigen Nettolohn nicht
  übersteigen.**"
- Verlust: „Beruht die Arbeitsunfähigkeit auf **grober Fahrlässigkeit** des Arbeitnehmers, so
  **erlischt der Anspruch**."

> **Lücke in den Schwellen:** „< 3." und „> 3." lassen **genau 3 Jahre** (ebenso 5 und 7)
> undefiniert. Die Grenzbehandlung muss eine explizite, konfigurierbare Entscheidung sein,
> nicht ein stilles `>=` im Code.

---

## 7. Abwesenheitsarten

Quelle: https://pland.app/arbeitslexikon/abwesenheitsverwaltung — die Aufzählung der Seite:

1. **Krankmeldungen** 2. **Urlaub** 3. **Dienstreisen** 4. **Elternzeit**
5. **Mutterschutz** 6. **Bildungsurlaub**

Produktseitig (https://pland.app/onboardings/abwesenheiten-in-pland): Basistypen **Urlaub** und
**Krankheit**, weitere über „Abwesenheitsart erstellen" mit drei Einstellungen je Typ — eine
**Lohnnummer**, ob Beschäftigte sie **selbst beantragen** dürfen, und ob sie den
**Urlaubsanspruch reduziert** (Beispiel: unbezahlter Urlaub). Abwesenheitstage werden
**automatisch aus dem Vertrag** berechnet.

---

## 8. Lohnabrechnung — Fristen und Pflichtinhalte

Quellen: https://pland.app/arbeitslexikon/lohnabrechnung-gebaeudereinigung,
https://pland.app/arbeitslexikon/zuschlaege-gebaeudereinigung,
https://pland.app/arbeitslexikon/mindestlohntarifvertrag-2024

| Fakt | Wert |
|---|---|
| Frequenz | **monatlich** |
| Zahlungsfrist | „Der Lohn muss **spätestens am 15. des Folgemonats bargeldlos** bezahlt werden." |
| Abrechnungsfrist | „Die Abrechnung hat **spätestens bis zum 15. des nächsten Monats** zu erfolgen." |
| Mindestlohn-Fälligkeit | „**spätestens bis zum 15. des Folgemonats** fällig" |
| **Verfallklausel Mindestlohn** | „Ansprüche auf den Mindestlohn verfallen, wenn sie **nicht innerhalb von sechs Monaten nach Fälligkeit gerichtlich geltend gemacht** werden." |
| Verstetigter Monatslohn | zulässig **für geringfügig Beschäftigte**, „sofern die Arbeitszeit **regelmäßig und gleichbleibend** ist" |
| Pflichtinhalt der Abrechnung | „eine genaue **Aufstellung der Lohnsumme, des Stundenlohns, der Zuschläge und Abzüge**" bzw. „Abrechnung über **Gesamtlohn, Stundenlohn, Zulagen und Abzüge**" |
| Zustellung | elektronisch nur „in einer **datenschutzrechtlich zulässigen** elektronischen Form"; ohne Zustimmung des Beschäftigten ist eine **schriftliche Lohnabrechnung kostenfrei** zu liefern |
| TZR | Gesamtbetrag der Altersversorgung **gesondert ausweisen** |

Bezug zum Repo: die gesäte Vollzeit-Vorlage sagt „Die Zahlung erfolgt bargeldlos **zum
Monatsende**" (`apps/contracts/migrations/0003_seed_templates.py`, § 4 Vergütung) — früher als
die tarifliche Frist und damit unproblematisch, aber die **Bargeldlosigkeit** ist tariflich
gefordert und steht dort zu Recht.

---

## 9. Kündigungsfristen — wie die Quelle sie druckt, mit Warnung

Quelle: https://pland.app/arbeitslexikon/kuendigung

Definition, verbatim: „eine **einseitige empfangsbedürftige Willenserklärung**, mit der das
Arbeitsverhältnis nach dem Willen des Kündigenden für die Zukunft sofort oder unmittelbar nach
Ablauf der Kündigungsfrist beendet werden soll."

| Beschäftigungsdauer | Frist wie gedruckt |
|---|---|
| Standard, beidseitig | **zwei Wochen** |
| **Bis zu zwei Wochen nach der Anstellung** | beidseitig **innerhalb von einem Werktag** |
| **Ab 5 Jahren** | **1 Monat zum Ende eines Kalendermonats** |
| **Ab 8 Jahren** | **3 Monat zum Ende eines Kalendermonats** |
| **Ab 10 Jahre** | **4 Monat zum Ende eines Kalendermonats** |
| **Ab 12 Jahre** | **5 Monat zum Ende eines Kalendermonats** |
| **Ab 15 Jahre** | **6 Monat zum Ende eines Kalendermonats** |
| **Ab 20 Jahre** | **7 Monat zum Ende eines Kalendermonats** |

(Die Seite schreibt „3 Monat", „4 Monat" — verbatim übernommen, Grammatikfehler inklusive.
**Die Seite nennt keine Rechtsgrundlage für diese Leiter.**)

> **Diese Leiter darf keine Berechnung antreiben.** Sie weicht an der 5-Jahres-Stufe von der
> bekannten Struktur des § 622 BGB ab und lässt die 2-Jahres-Stufe aus. Das Repo macht es
> richtig: die gesäte Vertragsvorlage verweist auf „die gesetzlichen Kündigungsfristen nach
> **§ 622 BGB**" und auf zwei Wochen in der Probezeit
> (`apps/contracts/migrations/0003_seed_templates.py`, § 6 Kündigung). Wenn eine
> Fristberechnung gebaut wird, dann als **effektiv-datierte Regeltabelle** mit Quellenangabe je
> Zeile, und mit der günstigeren Regel aus Gesetz/Tarif/Vertrag als Ergebnis
> (Günstigkeitsprinzip — **Ungeprüft**).

**Pflichten bei Beendigung** (dieselbe Seite):
- **Arbeitspapiere** aushändigen und den **Rest des Lohnes** auszahlen.
- „Der Verlust von **Arbeitslosengeld und Lohn** wegen **verspäteter Aushändigung der
  Arbeitspapiere** geht **zu Lasten des Arbeitgebers**."
- Rückgabe des Firmeneigentums in gutem Zustand: **Reinigungsmaterialien, Arbeitskleidung,
  Geräte, Geschäftsunterlagen**.
- „Dem/der Arbeitnehmer/in ist **auf Verlangen ein Zeugnis** auszustellen."
- **Ausschlussfrist:** „Jeglicher Anspruch aus dem Arbeitsverhältnis **verfällt innerhalb von
  zwei Monaten** nach der **Ablehnung** oder dem **Fristablauf**, solang er nicht vorher
  **gerichtlich geltend gemacht** wird."
- Kündigungsgründe, drei Formen: **verhaltensbedingt** (u. a. Arbeitsverweigerung, Alkohol- und
  Drogenmissbrauch, Beleidigungen, rassistische Äußerungen, Verstöße gegen die Betriebsordnung,
  **Vortäuschen von Krankheit**), **personenbedingt** (fehlende Arbeitserlaubnis, Straftaten,
  langfristig eignungsbeeinträchtigende Krankheit, Gefängnisaufenthalt), **betriebsbedingt**
  (Auftragsmangel, Gewinn-/Umsatzrückgang, Betriebseinstellung, dauerhafter Personalabbau).

---

## 10. Vier Ausschluss-/Verfallfristen, die getrennt bleiben müssen

| Frist | Gegenstand | Form | Quelle |
|---|---|---|---|
| **6 Monate** ab Fälligkeit | Mindestlohnansprüche | **gerichtlich** geltend machen | https://pland.app/arbeitslexikon/mindestlohntarifvertrag-2024 |
| **2 Monate** ab Ablehnung/Fristablauf | jeder Anspruch aus dem Arbeitsverhältnis | **gerichtlich** | https://pland.app/arbeitslexikon/kuendigung |
| **3 Monate** ab Vorliegen der Voraussetzungen | Anpassung der Arbeitszeit, RTV § 3 Nr. 2 | **schriftlich** gegenüber dem Arbeitgeber | https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023 |
| **3 Jahre** ab Schluss des Entstehungsjahres | TZR-Ansprüche (Verjährung); „Ausschlussfristen des § 22 RTV gelten entsprechend" | — | https://pland.app/arbeitslexikon/tarifvertrag-zur-regelung-der-tariflichen-zusatz-rente-tzr-2024 |

Keine Quelle erklärt, wie diese Fristen zueinander stehen. Vier eigene Regeln, nicht eine
verallgemeinerte.

---

## 11. Zeiterfassung als Voraussetzung jeder Zuschlagsrechnung

Quellen: https://pland.app/arbeitslexikon/stundenzettel und
https://pland.app/arbeitslexikon/stempeluhr

Sieben Pflichtfelder — der Stundenzettel ist „nur als rechtlich bindendes Dokument gültig, wenn
folgende Informationen darauf vorhanden sind":

1. Name des Mitarbeiters 2. Datum des Arbeitstages 3. Ort der Arbeit 4. Arbeitsbeginn
5. Arbeitsende 6. Gesamtarbeitszeit 7. Pausenzeiten

Zusätzlich: vom **Arbeitnehmer unterschrieben**, aufbewahrt zur Prüfung der Einhaltung des
**Arbeitszeitgesetzes** und zu **Beweiszwecken**.

| Frist | Wert |
|---|---|
| Aufbewahrung durch den Arbeitgeber | „**mindestens zwei Jahre** nach der erbrachten Arbeitsleistung an dem jeweiligen Tag" |
| Dokumentation durch den Beschäftigten | „bis **spätestens sieben Tage** nach dem Ende des jeweiligen Arbeitstages" |

**Revisionssicherheit:** Zeitdaten „werden sicher gespeichert und **können nicht nachträglich
manipuliert werden**". Das Repo bildet das mit dem append-only `ShiftEvent`-Journal ab
(`apps/planning/models.py:188-221`) und mit `correct_minutes(...)`, das eine Korrektur als
**neues Ereignis mit Akteur und Grund** schreibt (`apps/planning/attendance.py:148`).

**Ungeprüft:** Die 7-Tage- und 2-Jahres-Zahlen entsprechen der Dokumentationspflicht aus
§ 17 MiLoG / § 19 AEntG für Mindestlohnbranchen; die Quellseite nennt keine der beiden Normen.

---

## 12. Arbeitszeitgrenzen, gegen die der Planer prüfen muss

Quelle: https://pland.app/arbeitslexikon/sollarbeitszeit — die Seite listet vier Grenzen
**ohne Paragrafenangabe**:

| Grenze | Wert |
|---|---|
| Maximale tägliche Arbeitszeit | **8 Stunden**, verlängerbar auf **bis zu 10 Stunden** |
| Wöchentliche Höchstarbeitszeit | **48 Stunden** |
| Ruhezeit zwischen zwei Arbeitstagen | **mindestens 11 Stunden** |
| Pausenzeiten | **30 Minuten bei mehr als 6 Stunden** Arbeitszeit |
| (aus `fahrzeiten`) 8-h-Durchschnitt | darf im Zeitraum von **24 Wochen** nicht überschritten werden |

Die Seite nennt für die **Sollarbeitszeit** vier Eingangsgrößen (vereinbarte Wochenstunden,
Arbeitstage pro Woche, Berücksichtigung von Feiertagen und Urlaubstagen, Ausgleich von
Mehr-/Minderarbeit) — **aber keine Formel, keinen Monatsdivisor und keine Rundungsregel**.
Nicht belegt; nicht erfinden.

Das Repo kennt die Grenzen bereits als Prinzip: „maximum 8 h pe zi (§3), minimum 11 h de odihnă
între ture (§5), duminica liberă (§9)" (`apps/planning/models.py:10-12`).

---

## Quellen

- https://pland.app/arbeitslexikon/rahmentarifvertrag-gebaeudereinigung-2023
- https://pland.app/arbeitslexikon/zuschlaege-gebaeudereinigung
- https://pland.app/arbeitslexikon/erschwerniszuschlaege
- https://pland.app/arbeitslexikon/nachtarbeit-gebaeudereinigung
- https://pland.app/arbeitslexikon/sonntagsarbeit-gebaeudereinigung
- https://pland.app/arbeitslexikon/feiertagsarbeit-gebaeudereinigung
- https://pland.app/arbeitslexikon/tarifvertrag-uber-ein-zusatzliches-urlaubsgeld
- https://pland.app/arbeitslexikon/tarifvertrag-zur-freistellung-an-heiligabend-oder-silvester
- https://pland.app/arbeitslexikon/tarifvertrag-zur-regelung-der-tariflichen-zusatz-rente-tzr-2024
- https://pland.app/arbeitslexikon/krankmeldung
- https://pland.app/arbeitslexikon/krankheitsausfall
- https://pland.app/arbeitslexikon/kuendigung
- https://pland.app/arbeitslexikon/abwesenheitsverwaltung
- https://pland.app/arbeitslexikon/lohnabrechnung-gebaeudereinigung
- https://pland.app/arbeitslexikon/mindestlohntarifvertrag-2024
- https://pland.app/arbeitslexikon/stundenzettel
- https://pland.app/arbeitslexikon/stempeluhr
- https://pland.app/arbeitslexikon/sollarbeitszeit
- https://pland.app/arbeitslexikon/fahrzeiten
- https://pland.app/onboardings/lohnarten-und-zuschlage-in-pland
- https://pland.app/onboardings/einstellungen-fur-die-urlaubstageberechnung
- https://pland.app/onboardings/urlaubsanspruch-von-mitarbeitern
- https://pland.app/onboardings/urlaubstage-im-urlaubsantrag
- https://pland.app/onboardings/abwesenheiten-in-pland
- https://pland.app/blog/digitale-lohnabrechnung-ein-blick-auf-die-vorteile-in-der-gebaudereinigung
- Repo: `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/models.py`
- Repo: `/Users/Geronimo/Projects/Cleaning_SaaS/apps/planning/attendance.py`
- Repo: `/Users/Geronimo/Projects/Cleaning_SaaS/apps/contracts/migrations/0003_seed_templates.py`
