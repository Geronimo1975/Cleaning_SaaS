# Cleaning SaaS — Plan Faza 0 · Hamburg

**Piață:** Germania, lansare Hamburg · **Deadline:** 13 septembrie 2026 · **Execuție:** solo
**Entitate:** UG/GmbH germană · **Wedge:** job board pentru firme de Gebäudereinigung
**Referințe de piață:** MyHammer (lead-gen), Betreut.de (abonament), Helpling (comision pe tranzacție)

---

## 0. Gate-uri înainte de lansare — verifică ASTĂZI

Două lucruri pot bloca lansarea indiferent de cod.

**UG/GmbH înregistrată.** Impressum-ul trebuie să numească o entitate juridică reală. Constituirea unei UG trece prin notar + Handelsregister și durează în mod normal 2–4 săptămâni — mai mult decât ai. Dacă UG-ul nu e deja înregistrat:
- se poate lansa ca **Einzelunternehmen** (Gewerbeanmeldung la Bezirksamt, câteva zile) și se convertește ulterior, sau
- se lansează ca **UG i. G.** („in Gründung") — permis, dar trebuie marcat explicit în Impressum și scade credibilitatea la clienți B2B.

**Texte juridice.** În Germania lipsa lor înseamnă *Abmahnung* — scrisoare de punere în întârziere de la un concurent sau o casă de avocatură, cu costuri reale. Necesare: Impressum (§5 DDG), Datenschutzerklärung (DSGVO + TDDDG), AGB pentru platformă, Widerrufsbelehrung, banner de cookies conform. Se iau pe abonament de la un serviciu specializat (IT-Recht Kanzlei, Händlerbund, eRecht24), 10–30 €/lună. **Comandă-le în ziua 1, nu în ziua 13** — configurarea durează.

---

## 1. De ce job board pentru firme, și nu marketplace

Trei motive, în ordinea importanței.

**Legal.** Un job board nu intermediază munca, ci doar anunțul. Nu atinge nici *Scheinselbständigkeit*, nici *Arbeitnehmerüberlassung* (AÜG). În momentul în care platforma alocă lucrări, fixează prețuri și evaluează prestatorii, autoritățile germane au trei indicii clasice de raport de muncă — iar cel care plătește retroactiv contribuțiile sociale este clientul, nu platforma. E cel mai curat punct de intrare legal disponibil.

**Comercial.** Firmele de Gebäudereinigung din Hamburg au deficit acut de personal și plătesc deja pentru anunțuri pe Indeed și StepStone. Există buget, e recurent, și nu trebuie educată piața.

**Operațional.** Ai contacte de prestatori chiar în Hamburg. Anunțurile aduc aplicanți din Google for Jobs; aplicanții devin profiluri; profilurile devin oferta pentru marketplace-ul de mai târziu.

```
Stellenanzeige publicată → indexată în Google for Jobs → persoana aplică
    → aplicarea creează contul → profilul devine public → baza de prestatori crește
```

**Regulă absolută de monetizare:** plătește **angajatorul**, niciodată candidatul. §296 SGB III impune contract scris, plafonează onorariul de la candidat la 2.000 € și îl permite doar după încheierea contractului de muncă — iar pentru **Minijob plasarea contra cost de la candidat este complet interzisă**. Cum majoritatea joburilor de curățenie sunt Minijobs, orice taxă către candidat e ilegală în practică. Taxarea angajatorului nu e restricționată.

---

## 2. Constrângeri legale germane care modelează produsul

### Salarii — cifrele care intră direct în validarea formularului

| | 2026 |
|---|---|
| Mindestlohn general | **13,90 €/h** |
| Branchenmindestlohn Gebäudereinigung, Lohngruppe 1 (Innen-/Unterhaltsreinigung) | **15,00 €/h** |
| Branchenmindestlohn, Lohngruppe 6 (Glas-/Fassadenreinigung) | **18,40 €/h** |
| Plafon Minijob | **603 €/lună** |

Branchenmindestlohn-ul este **allgemeinverbindlich** — obligatoriu pentru toți angajatorii din branșă, indiferent de apartenența la patronat. Este mai mare decât salariul minim general, deci un anunț la 13,90 € este ilegal în curățenie.

**Consecință de produs, ieftin de construit și greu de copiat:** formularul de anunț respinge orice salariu sub pragul tarifar al categoriei alese. Devine promisiunea de brand — *„Alle Stellen mit Tariflohn"*. Indeed nu face asta; acolo circulă anunțuri sub prag.

**Calcul de afișat automat în formular:** la 15,00 €/h, plafonul de 603 € înseamnă **maximum 40 de ore pe lună** (~9,3 h/săptămână). Angajatorii greșesc constant acest calcul. Un câmp care îl face în locul lor e un motiv real să revină.

### Scheinselbständigkeit — de ce alocarea automată nu se poate face în forma gândită

Ideea originală („sistemul alocă automat serviciul unei persoane fizice disponibile") este, în context german, exact tiparul care produce recalificarea ca raport de muncă: platforma dă dispoziția, platforma stabilește prețul, platforma evaluează. Deutsche Rentenversicherung poate constata statutul printr-un *Statusfeststellungsverfahren*, iar consecința financiară cade pe client.

Există doar două ieșiri, ambele pentru mai târziu: fie prestatorii sunt **angajați** (de platformă sau de firme partenere — traseul pe care l-a luat Book a Tiger), fie platforma rămâne strict la **anunț și contact**, fără alocare și fără preț impus. Faza 0 alege a doua variantă în mod natural.

### §35a EStG — argumentul de vânzare pentru B2C, relevant în v2

Gospodăriile private din Germania își pot deduce **20% din costul serviciilor casnice, până la 4.000 €/an**, dar **numai cu factură și plată bancară** — plata cash nu se deduce. Asta răstoarnă recomandarea „plata direct între părți": pentru segmentul B2C, tocmai fluxul de plată prin platformă, cu factură, e ceea ce face serviciul deductibil și îl scoate din concurența cu piața neagră. De reținut pentru etapa de marketplace; irelevant pentru wedge-ul actual.

### Autorizare

**Gebäudereiniger este în Anlage B1 HwO — meserie fără obligație de maistru.** Nu e nevoie de Meisterbrief. Firma are nevoie de Gewerbeanmeldung și înscriere la Handwerkskammer (Anlage B). Bariera de intrare pentru prestatori e mică — bun pentru densitatea ofertei, dar înseamnă și că verificarea calității cade pe platformă.

---

## 3. Decizii de arhitectură care nu se pot repara ulterior

Rămân valabile din analiza inițială, cu adaptări germane.

**`Account` e entitatea centrală, nu `User`.** `User` face doar autentificare. `Membership` leagă User↔Account. Capacitățile (`ARBEITGEBER`, `ARBEITSKRAFT`, `DIENSTLEISTER`, `LIEFERANT`, `KUNDE`) sunt **rânduri în `AccountCapability`**, nu un câmp `role`. Rolul dublu devine un rând în plus.

**Acoperirea geografică se modelează pe PLZ, nu pe nume de oraș.** În Germania toată lumea gândește în coduri poștale — inclusiv „Ich suche im Umkreis von 20 km um 22765". Numele de cartier e doar pentru afișare și SEO.

**Slug-uri imutabile. Depublicarea se proiectează acum:** 410 + `noindex` + scos din sitemap + slug rezervat permanent. Cu DSGVO aplicată german, e o cerință, nu o eleganță.

**Limbile sunt câmp de primă clasă, pe ambele părți.** O parte însemnată dintre Reinigungskräfte din Hamburg nu are germana ca limbă maternă. Un flux de aplicare care funcționează în germană simplă plus câteva limbi de comunitate e un diferențiator real față de Indeed — și e ieftin. Tu ai acces natural la comunitatea vorbitoare de română din Hamburg; e un avantaj de distribuție pe care Helpling și MyHammer nu îl au.

---

## 4. Taxonomia serviciilor (germană, 23 de frunze)

### Unterhalts- und Gebäudereinigung
Unterhalts- und Büroreinigung · Treppenhausreinigung · Praxis- und Klinikreinigung · Hotel- und Zimmerreinigung · Ladenlokal- und Verkaufsflächenreinigung · Industrie- und Hallenreinigung

### Glas- und Außenbereich
Glas- und Fensterreinigung · Fassadenreinigung · Photovoltaik- und Solaranlagenreinigung · Außenanlagen- und Grünpflege · Winterdienst

### Sonder- und Spezialreinigung
Grundreinigung · Bauendreinigung · Teppich- und Polsterreinigung · Desinfektions- und Hygienereinigung · Küchen- und Lüftungsreinigung · Entrümpelung und Entsorgung · Fahrzeugaufbereitung

### Haushaltsnahe Dienstleistungen
Haushaltsreinigung / Putzhilfe · Haushaltshilfe (Minijob) · Fensterreinigung privat · Umzugs- und Endreinigung · Wäsche und Bügeln

Fiecare frunză poartă **Lohngruppa tarifară implicită**, care alimentează validarea salariului din formularul de anunț.

---

## 5. Geografie

**Val 1 — Hamburg**, 7 Bezirke: Hamburg-Mitte, Altona, Eimsbüttel, Hamburg-Nord, Wandsbek, Bergedorf, Harburg. Sub ele, Stadtteile pentru pagini SEO (Altona-Nord, St. Pauli, Eppendorf, Winterhude, Barmbek, Rahlstedt, Bergedorf ș.a.). PLZ: intervalele 20xxx–22xxx.

**Val 2 — Umland:** Norderstedt, Pinneberg, Wedel, Schenefeld, Ahrensburg, Reinbek, Glinde, Seevetal, Buxtehude, Henstedt-Ulzburg.

**Structura URL:**
`/reinigungskraft-jobs/hamburg/` · `/reinigungskraft-jobs/hamburg-altona/` · `/jobs/{slug}/` · `/reinigungsfirmen/hamburg/` · `/profil/{slug}/`

**Cuvinte-cheie de acoperit:** Reinigungskraft Jobs Hamburg · Putzfrau Job Hamburg · Minijob Reinigung Hamburg · Gebäudereinigung Jobs Hamburg · Reinigungskraft gesucht Hamburg · Büroreinigung Jobs Hamburg

---

## 6. Schema de date

### Identitate

| Entitate | Câmpuri esențiale |
|---|---|
| `User` | email (unic, câmp de login), password, is_active, date_joined |
| `Account` | entity_type (PERSON/UNTERNEHMEN), display_name, slug (unic, imutabil), legal_name, rechtsform, handelsregister_nr, ust_id, hwk_nr, strasse, plz, ort, status (DRAFT/PENDING/PUBLISHED/UNPUBLISHED/SUSPENDED), published_at, unpublished_at, verification_level |
| `Membership` | user FK, account FK, role (OWNER/ADMIN/MEMBER), unique(user, account) |
| `AccountCapability` | account FK, kind (ARBEITGEBER/ARBEITSKRAFT/DIENSTLEISTER/LIEFERANT/KUNDE), is_active, unique(account, kind) |

### Profiluri

| Entitate | Câmpuri esențiale |
|---|---|
| `WorkerProfile` | OneToOne account (doar PERSON), berufserfahrung_jahre, gewuenschte_beschaeftigungsart, verfuegbarkeit, fuehrerschein, eigenes_fahrzeug, sprachen M2M cu nivel (A1–C2), umkreis_km, bio |
| `CompanyProfile` | OneToOne account (doar UNTERNEHMEN), mitarbeiter_range, gruendungsjahr, website, betriebshaftpflicht (bool, versicherungssumme, gueltig_bis), tarifbindung, hwk_eingetragen |

### Taxonomie și acoperire

| Entitate | Câmpuri esențiale |
|---|---|
| `ServiceCategory` | parent (self FK), name_de, slug, lohngruppe_default, sort_order, is_active — adâncime maximă 2 |
| `PostalCode` | plz, ort, bezirk, stadtteil, bundesland, lat, lng, is_active |
| `CoverageArea` | account FK, plz FK, unique(account, plz) |
| `AccountService` | account FK, category FK (doar frunze), unique(account, category) |

### Job board

| Entitate | Câmpuri esențiale |
|---|---|
| `JobPosting` | account FK, titel, slug, beschreibung (HTML), category FK, plz FK, beschaeftigungsart (MINIJOB/TEILZEIT/VOLLZEIT/AUSHILFE), stundenlohn_min, stundenlohn_max, wochenstunden, arbeitszeiten, lohngruppe, tariflohn_geprueft (calculat), sprachniveau_erforderlich, status, published_at, valid_through, views_count |
| `Bewerbung` | job FK, applicant_account FK, nachricht, status (NEU/GESEHEN/EINGELADEN/ABGELEHNT/EINGESTELLT), unique(job, applicant_account) |

`stundenlohn_min` este **obligatoriu** — și pentru validarea tarifară, și pentru că Google for Jobs favorizează anunțurile cu `baseSalary`. `valid_through` obligatoriu, altfel Google penalizează anunțurile expirate lăsate active.

### Conformitate

| Entitate | Câmpuri esențiale |
|---|---|
| `VerificationDocument` | account FK, doc_type (GEWERBEANMELDUNG/HWK/HAFTPFLICHT/AUSWEIS/QUALIFIKATION), file (storage privat), status, reviewed_by, reviewed_at, expires_at, delete_after — **niciodată public** |
| `ConsentRecord` | account FK, consent_type (PROFIL_VEROEFFENTLICHUNG/AGB/DATENSCHUTZ/MARKETING), policy_version, granted, ip_address, user_agent, created_at — **append-only** |
| `AuditLog` | actor, action, target, ip, created_at — publicare / depublicare / verificare |

### Rezervat pentru v2
`ServiceRequest`, `Angebot`, `Vertrag`, `Zahlung`, `Bewertung`. Se construiesc peste vocabularul deja fixat: `Account` + `ServiceCategory` + `PostalCode`.

---

## 7. SEO și Google for Jobs

- JSON-LD `JobPosting` pe **pagina individuală** de anunț, niciodată pe listări.
- Obligatorii: `title`, `description`, `datePosted`, `hiringOrganization`, `jobLocation`. De pus oricum: `baseSalary`, `employmentType`, `validThrough`, `identifier`. Minijob se mapează extern pe `PART_TIME`, dar se păstrează intern ca tip propriu.
- **Detaliile anunțului trebuie vizibile fără login** — cerință Google. Doar aplicarea cere cont.
- **Google Indexing API la publicare**, recomandat explicit de Google pentru `JobPosting` în locul sitemap-ului. Diferența e între indexare în ~2 zile și în ~3 săptămâni. Pentru un termen de 14 zile, e obligatoriu.
- La `CLOSED`/`EXPIRED`: `noindex`, 410, eliminare din sitemap, notificare de ștergere prin Indexing API.
- `schema.org/Person` pe profilul de persoană, `LocalBusiness` pe cel de firmă.
- Conținutul, meta-urile și microdatele — integral în germană. `hreflang` doar dacă apare a doua limbă de interfață.

---

## 8. Plan pe zile

| Zile | Interval | Livrabil |
|---|---|---|
| 0 | 30 aug | Comandă texte juridice; clarifică statutul UG |
| 1–2 | 30–31 aug | Setup proiect, schema, data migration: taxonomie DE, PLZ Hamburg, Lohngruppen |
| 3–5 | 1–3 sept | Auth, `Account`/`Membership`/`AccountCapability`, dashboard angajator, CRUD `JobPosting` cu validare tarifară |
| 6–8 | 4–6 sept | Pagina publică de anunț, JSON-LD, sitemap, Indexing API, listări pe Bezirk și categorie |
| 9–11 | 7–9 sept | Flux `Bewerbung` → creare cont → `WorkerProfile`, notificări email |
| 12 | 10 sept | Profil public + căutare pe PLZ/Umkreis și categorie |
| 13 | 11 sept | Integrare texte juridice, consimțământ, depublicare, cookie banner, deploy |
| 14–15 | 12–13 sept | Seed cu firmele din Hamburg, primele anunțuri reale, lansare, distribuție |

**Distribuție la lansare:** Kleinanzeigen.de, grupuri Facebook de comunitate din Hamburg (inclusiv cele românești, poloneze, bulgărești), afișe în Stadtteile cu densitate mare de personal de curățenie, contact direct cu firmele din portofoliu.

---

## 9. Riscuri și decizii amânate

**Abmahnung** — riscul juridic german cu cea mai mare probabilitate. Se elimină cu texte juridice pe abonament. Nu improviza Impressum și AGB.

**Scheinselbständigkeit** — blocant pentru orice formă de alocare a muncii prin platformă. De reevaluat doar împreună cu un avocat de dreptul muncii, înainte de etapa de marketplace.

**Plăți și escrow** — amânate. Când vin: PSP cu marketplace (Stripe Connect, Mangopay, Lemonway), plus obligația de factură și plată bancară dacă vrei ca §35a să funcționeze pentru clienții B2C.

**Semnătura digitală** — eIDAS; semnătura electronică simplă (click + audit trail) e suficientă pentru contracte de prestări servicii. Nu blochează nimic.

**Verificarea firmelor** — Gewerbeanmeldung, înscriere HWK și Betriebshaftpflicht. În Faza 0 sunt câmpuri declarate cu document încărcat; verificarea manuală vine odată cu volumul.

**Model de venit de testat imediat:** anunțuri plătite pentru angajatori — pachet de anunțuri sau abonament lunar. Fără escrow, fără risc fiscal, fără AÜG. Prețuri de referință: un anunț pe Indeed sau StepStone în Germania costă de la câteva zeci până la câteva sute de euro; poziționarea hyperlocal permite un preț sub ele, cu conversie mai bună pe branșă.

---

## 10. Checklist înainte de lansare

- [ ] Entitate juridică lămurită și numită corect în Impressum
- [ ] Impressum, Datenschutzerklärung, AGB, Widerrufsbelehrung, cookie banner — de la serviciu specializat
- [ ] Consimțământ explicit și separat pentru publicarea profilului
- [ ] Documente de verificare în storage privat, cu termen de retenție
- [ ] Flux de depublicare testat: 410 + `noindex` + scos din sitemap
- [ ] Validare tarifară activă pe toate categoriile
- [ ] Calculul plafonului Minijob afișat în formular
- [ ] `valid_through` setat pe toate anunțurile
- [ ] Rich Results Test trecut pe pagina de anunț
- [ ] Indexing API funcțional și testat
- [ ] Zero căi prin care candidatul ar putea fi taxat
- [ ] Primele anunțuri reale de la firmele din portofoliu, publicate
- [ ] Backup automat al bazei de date
