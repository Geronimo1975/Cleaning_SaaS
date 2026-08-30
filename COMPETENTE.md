# Competențe necesare — Cleaning_SaaS

> **Ce este acest document.** Lista competențelor tehnice și non-tehnice de care are nevoie
> proiectul `Cleaning_SaaS`, dedusă din cod, nu din intenții. Fiecare competență e ancorată
> într-un fișier real din repo și marcată cu nivel, criticitate și raritate pe piață.
>
> **Nu confunda cu [`SKILLS.md`](SKILLS.md)** — acela e inventarul de *skill-uri Claude Code*
> (unelte pentru agenți). Acesta e despre **oameni**.
>
> **Bază de măsurare:** commit `acded85` + modificări necomise, **30 august 2026**.
> 12.350 linii Python · 13 aplicații Django · 26 migrări · 295 teste în 17 fișiere ·
> 36 template-uri (834 linii HTML) · `static/` gol.
>
> **Referințele indică fișiere, nu linii.** Arborele s-a modificat în timpul analizei
> (`apps/planning/views.py` a devenit pachetul `views/`), deci numerele de linie se învechesc
> în zile. Fișierul + numele funcției rezistă.

---

## Cum se citește, pe audiențe

| Dacă ești… | Citește | Ce obții |
|---|---|---|
| **Project manager** | §1 Rezumat · §3 Distribuția efortului · §5 Structura de echipă | Cine, câți, în ce ordine, ce blochează ce |
| **Team lead** | §4 Matricea completă · §6 Harta competență → cod | Cui asignezi ce, și ce nu se poate asigna nimănui din echipă |
| **Stakeholder / client** | §1 Rezumat · §2 Ce știe produsul să facă · §7 Riscuri | Ce capabilități sunt acoperite și unde e expunerea |
| **HR / recruiting** | §4 (coloanele Nivel/Raritate) · §5 · §8 Probe de interviu · §9 Ce NU recrutezi | Profiluri de post, întrebări de filtrare, capcane de evitat |

---

## 1. Rezumat executiv

**Cleaning_SaaS nu este un proiect mare. Este un proiect mic cu densitate juridică mare.**

12.350 de linii de Python sunt cât scrie o echipă de doi oameni în câteva luni. Dar o parte
disproporționată din acest cod nu implementează funcționalitate — **traduce lege germană în
constrângeri executabile**: un alocator de personal care refuză să încalce §3, §5 și §9 ArbZG;
un jurnal de pontaj imutabil care există pentru că BAG a decis așa pe 13.09.2022; salarii minime
modelate ca rânduri datate pentru că un tarif de ramură declarat general obligatoriu se schimbă
la o dată calendaristică; și — cel mai neobișnuit — **absența deliberată a unei funcționalități**
(alocarea automată), pentru că a o construi ar însemna Arbeitnehmerüberlassung fără licență.

Consecința pentru recrutare este contraintuitivă:

> **Nu ai nevoie de mulți oameni. Ai nevoie de puțini oameni cu combinații rare,
> plus consultanți externi plătiți la oră.**

Trei constatări care schimbă planul de resurse:

1. **Cea mai rară competență din proiect nu e tehnică.** Este reflexul de a spune „nu" unui
   feature din motive juridice. Un dezvoltator care răspunde „o oră, avem deja `score_offers`"
   la cererea „pune un buton de atribuire automată" este un risc juridic pentru companie.
2. **Cel mai mare gol vizibil este design-ul.** `static/` este gol, `templates/base.html` are
   16 linii și zero CSS. Produsul funcționează, dar nu poate fi arătat unui client german plătitor.
3. **Cel mai mare gol invizibil este comunicarea.** În tot repo-ul există **un singur** apel de
   trimitere de email. Un candidat aplică și nu primește nimic. Un prestator pierde licitația și
   nu află. Un contract intră în starea „trimis spre semnare" și nimeni nu e anunțat.

**Formă de echipă recomandată:** 2,5 FTE interni pentru a lansa Faza 0, 5,5 FTE când începe
facturarea — plus 3–4 consultanți externi obligatorii de la ziua 1 (§5).

---

## 2. Ce știe produsul să facă (pentru stakeholder)

Fără jargon: cinci capabilități construite, una specificată dar neconstruită.

| Capabilitate | Stare | Ce înseamnă practic |
|---|---|---|
| **Anunțuri de angajare indexabile** | ✅ Construit | Pagini de job optimizate pentru Google for Jobs, cu URL-uri permanente și retragere corectă (410, nu ștergere). Candidatură fără cont. |
| **Bursă de cereri și oferte** | ✅ Construit | Un client publică o cerere, firmele membre licitează, un algoritm de scoring transparent ordonează ofertele. **Atribuirea rămâne o decizie umană — prin proiectare.** |
| **Generare de contracte conforme** | ✅ Construit | Contractul se derivă din oferta câștigătoare (nimeni nu retastează cifre), se validează contra salariului minim de ramură valabil la data începerii, și se îngheață criptografic la semnare. |
| **Planificare săptămânală a personalului** | ✅ Construit | Un alocator care respectă bugetul de ore contractate, 8h/zi, 11h repaus, fără duminică. Ce nu încape rămâne explicit nealocat, cu motivul per lucrător. |
| **Pontaj și verificare prin telemetrie** | ✅ Construit | Jurnal de check-in/check-out imutabil; datele de la aspiratoare servesc drept semnal de discrepanță, nu drept măsurătoare a timpului de lucru. |
| **Facturare și încasare** | ❌ Specificat, neconstruit | Client, comandă, factură, plată — nu există niciun rând de cod. Vezi §4.10. |

**Ce nu poate face azi produsul, deși pare că ar trebui:** să trimită un email, să arate decent,
să importe portofoliul unui client din Excel, să încaseze bani.

---

## 3. Distribuția efortului (pentru PM)

Unde stă codul, deci unde stă riscul și unde se duce timpul:

| Zonă | Linii Python | Pondere | Competența dominantă |
|---|---:|---:|---|
| `apps/planning` — planificare, pontaj, calibrare | 2.121 | 24% | Algoritmi cu constrângeri + statistică robustă |
| `apps/accounts` — identitate, autorizare, vizibilitate | 1.713 | 19% | Multi-tenancy și minimizarea datelor |
| `apps/marketplace` — cereri, oferte, scoring | 1.241 | 14% | Mașini de stare + scoring explicabil |
| `apps/contracts` — contracte, salarii, conformitate | 938 | 11% | Drept german al muncii modelat în date |
| `apps/jobs` — anunțuri, candidaturi, indexare | 873 | 10% | SEO tehnic + cozi durabile |
| `apps/devices` — telemetrie | 617 | 7% | Ingestie machine-to-machine |
| `apps/cooperative`, `dashboard`, `geo`, `catalog`, `taxonomy`, `legal` | 1.359 | 15% | Modelare de date de referință |

**Trei observații pentru planificarea resurselor:**

- **43% din cod stă în două module** (`planning` + `accounts`) care sunt și cele mai greu de
  înlocuit: alocatorul și autorizarea. Ambele trebuie deținute intern, permanent. Nu se
  externalizează (§5.3).
- **`apps/catalog` (218 linii) este o a treia linie de business complet modelată și nemontată** —
  dealer B2B de consumabile, cu produse, TVA separată net/brut, categorii ierarhice. Zero rute,
  zero teste, zero views. Cineva a decis să o construiască și nimeni nu a decis dacă se lansează.
- **`static/` are 0 fișiere.** Toată munca de frontend vizual este încă în față, integral.

---

## 4. Matricea de competențe

**Legendă.** Nivel: Junior · Mid · Senior · Expert. Criticitate: **Blocant** (fără el nu se
livrează) · **Esențial** (produsul e incomplet) · **Important** (calitate/viteză) · **Util**.
Raritate pe piață: Comună · Moderată · Rară · Foarte rară.

> Lista e **deduplicată**. Analiza brută a produs 96 de competențe, dintre care ~20% descriau
> același cod sub nume diferite (imutabilitatea apărea de 4 ori, autorizarea de 3 ori). O matrice
> construită pe lista brută ar supraestima echipa cu circa 20%.

### 4.1 Backend Django și logică de domeniu

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Django 5.2 server-rendered, fără DRF și fără admin generic** | Nu există strat de API, nu există serializatoare, nu există build step JS. Toate ecranele sunt view-uri și formulare Django. Reflexele de „construiesc un API și un SPA" sunt active-nocive aici. | Mid | Blocant | Comună |
| **Izolare între conturi: capability × ownership, 403 vs 404** | Nu există câmp `role`. Dreptul se calculează ca *(contul activ are capabilitatea X)* AND *(obiectul aparține contului activ)*. Lipsa capabilității dă 403; un obiect străin dă **404**, ca un cont străin să nu afle nici măcar că URL-ul există. 62 de linii în `permissions.py`, atinse de fiecare request autentificat — o greșeală aici nu produce eroare, produce scurgere de date. | Senior | Blocant | Rară |
| **Proiecție de câmpuri pe nivel de relație (minimizare fail-closed)** | `visibility.py` proiectează un cont prin `AccountView` pentru un privitor anume; `FIELD_POLICY` mapează fiecare câmp la o relație minimă. Datele de contact se deblochează abia la ENGAGED — câștigat prin candidatură, contract trimis/semnat, sau ofertă **câștigată**; o ofertă doar depusă nu contează, altfel licitația devine unealtă de colectat adrese. **Un câmp nou pe `Account` e invizibil până e adăugat în `FIELD_POLICY`.** | Senior | Blocant | Foarte rară |
| **Mașini de stare scrise de mână în servicii tranzacționale** | Zero `django-fsm`, zero semnale, zero `post_save`. Efectele secundare stau explicit în funcții de serviciu sub `@transaction.atomic`. Cine caută magia framework-ului nu o găsește și o reintroduce, rupând tranzacționalitatea. | Senior | Blocant | Moderată |
| **Reguli legale ca rânduri datate, nu constante** | `WageFloor`, `MinijobThreshold` și `DispatchPolicy` au toate aceeași formă: `valid_from`/`valid_to` + `current(on=...)`. Se rezolvă întotdeauna contra **datei la care se întâmplă munca**, niciodată contra lui `today`. Un salariu hardcodat e un bug care se manifestă peste șase luni, la un audit. | Senior | Blocant | Rară |
| **Documente înghețate și semnătură pe hash** | `rendered_body` + `body_sha256`: textul șablonului se copiază la generare, deci editarea unui `ContractTemplate` nu poate rescrie contracte semnate. `ShiftEvent`, `ConsentRecord` și `ContractSignature` ridică excepție la re-salvare. O corecție e un eveniment nou, niciodată o suprascriere. | Senior | Blocant | Rară |
| **Scoring multicriterial explicabil, cu ponderi versionate** | `score_offers` produce un `breakdown` și un `explain()` — un prestator care pierde trebuie să poată afla de ce. Ponderile se fixează la publicarea cererii, deci un vot ulterior al membrilor nu poate reordona retroactiv o cerere pe care s-a licitat deja. | Senior | Esențial | Rară |
| **Custom User pe email + django-allauth 65 (API-ul nou)** | `User` fără `username`, fără nume, `USERNAME_FIELD = "email"`, manager scris de mână, model swappable fixat în migrarea `0001`. Configurarea folosește `ACCOUNT_LOGIN_METHODS` / `ACCOUNT_SIGNUP_FIELDS` — cine copiază tutoriale de dinainte de 2025 obține setări **ignorate silențios**, fără eroare. | Mid | Blocant | Moderată |
| **Middleware cu stare de tenant** | `ActiveAccountMiddleware` rezolvă un `Membership` pe request în `request.account`. Poziția în lanț contează (după `AuthenticationMiddleware` și după allauth), iar ramura de auto-vindecare tratează cazul în care contul din sesiune nu mai există. | Mid | Esențial | Moderată |
| **Django Forms: mai multe ModelForm-uri pe un singur POST** | Fluxurile cu mai mulți pași folosesc view-uri-funcție cu formulare compuse și queryset-uri legate în `__init__` — nu CBV. Judecata „când NU folosesc un CBV" e parte din competență. | Mid | Important | Comună |

### 4.2 Algoritmi și statistică aplicată

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Alocator greedy determinist cu constrângeri legale tari** | `generate_week_plan` nu optimizează — respectă. Bugetul de ore contractate e un **plafon legal**, nu o preferință; 8h/zi (§3 ArbZG), 11h repaus (§5), fără duminică (§9), lucrătorul trebuie să deservească localitatea. Capacitatea vine **doar** din contracte semnate: planificarea nu creează raporturi de muncă. | Senior | Blocant | Rară |
| **Explicabilitatea eșecului: nealocarea ca artefact de audit** | Ce nu încape nu dispare — ajunge în `unmet_demand` cu motiv per lucrător. Asta e o cerință de produs, nu o comoditate de debugging: un Betrieb trebuie să poată demonstra de ce o vizită nu s-a făcut. | Mid | Esențial | Moderată |
| **Statistică robustă aplicată: mediană + MAD** | `calibration.py` folosește mediana și abaterea mediană absolută, **niciodată media** — o singură tură uitată deschisă ar deplasa media. Prag dual (≥15% și ≥10 min), eșantion minim, cooldown. Cine „simplifică" la medie strică tăcut calibrarea. | Senior | Esențial | Rară |
| **Automatizare cu om în buclă** | Calibrarea **propune** întotdeauna; nu aplică niciodată singură. Telemetria verifică, nu măsoară — timpul de funcționare al unui aspirator e o limită inferioară și un semnal de discrepanță, nu timp de curățenie. | Senior | Esențial | Moderată |
| **Planificare all-or-nothing pentru blocuri indivizibile** | `Tour` se plasează prima, integral: un lucrător, o zi, opriri consecutive. Timpul de deplasare între opriri **este timp de lucru** și se scade din buget. | Senior | Esențial | Rară |
| **Aritmetica timpului și `Decimal` exact** | Zile ISO, conversie lună→săptămână (4,33 / 2,17), `USE_TZ`, alegerea `DateField` vs `DateTimeField`. Toate sumele în `Decimal` — un `float` într-un calcul de salariu e o eroare de conformitate. | Mid | Esențial | Comună |

### 4.3 Modelare de date și baze de date

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Modelare temporală + constrângeri declarative în DB** | Rânduri datate peste tot, plus `UniqueConstraint` parțial cu `condition`. Regulile trăiesc în schemă, nu în cod de aplicație. | Senior | Blocant | Rară |
| **Migrări de date pentru seed** | Localități, categorii, praguri salariale și politici de repartizare sunt **populate exclusiv prin migrări numerotate**, cu `apps.get_model` și `update_or_create` pe cheie naturală. Nu se seed-uiește din shell, nu se seed-uiește din admin. | Mid | Esențial | Moderată |
| **Politici de ștergere ca decizie juridică** | Localitățile și categoriile sunt FK `PROTECT`, niciodată text liber — textul liber distruge și filtrarea, și suprafața SEO „Reinigungskraft {oraș}". Alegerea PROTECT/CASCADE/SET_NULL e o decizie de retenție, nu una de comoditate. | Mid | Esențial | Moderată |
| **`ReservedSlug`: namespace global de identificatori publici** | Un singur spațiu de nume partajat de `Account`, `JobPosting` și `catalog.Product`. Un slug se revendică o dată și **nu se reciclează niciodată**, nici după depublicare. URL-urile sunt permanente. | Mid | Esențial | Moderată |
| **Paritate SQLite → PostgreSQL și regresie pe numărul de interogări** | Dev/CI pe SQLite, producție pe Postgres via `dj_database_url` + `psycopg`. `tests/test_queries.py` blochează N+1-uri: regula verificată e că numărul de interogări e **constant** în raport cu N — un `select_related` scos la refactorizare nu strică niciun test funcțional, se vede doar acolo. | Mid | Blocant | Comună |
| **Import și reconciliere de date murdare** *(gol — nu există cod)* | `services.py` numește explicit „import de portofoliu" ca a treia cale de creare a unui cont; nu există. Produsul **exportă** Reinigungsplan în Excel, dar nu poate **importa** — iar fiecare firmă din piață are deja acel fișier. Onboarding-ul unui Betrieb cu 40 de obiective înseamnă azi tastare manuală. Fiecare rând importat trebuie mapat pe taxonomie închisă. | Mid | Esențial | Comună |

### 4.4 Frontend și UX

> Stratul cel mai subțire din proiect și cel mai mare gol de recrutare. 36 de template-uri,
> 834 de linii de HTML, **zero CSS**, `static/` gol, `base.html` = 16 linii.

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **CSS și design system de la zero, fără framework și fără bundler** | Nu există Tailwind, nu există Node, nu există pas de build. Cineva trebuie să inventeze tokeni, tipografie și componente în CSS scris de mână. Estimare: 60–100 ore de muncă vizuală. Fără asta produsul se livrează cu randarea implicită a browserului. | Senior | Blocant | Rară |
| **Django Template Language fără build step** | Moștenire de template-uri, blocuri, includes, `{% url %}`. Un frontend developer de React nu poate atinge niciun rând util aici. | Mid | Blocant | Moderată |
| **UX pentru teren: pontajul pe telefon** | Utilizatorul real al ecranului de ture este o femeie de serviciu cu mănuși, la 5:40 dimineața, pe o casă a scării. Ținte de atingere, contrast, acțiuni distructive separate de cele frecvente. Azi „Confirmă" și „Refuză" stau în același formular, la două linii distanță. | Mid | Esențial | Rară |
| **Interfață bilingvă DE public / RO dashboard, fără i18n activ** | `LANGUAGE_CODE = "de"`, `USE_I18N = True`, dar **zero fișiere `.po`**. Split-ul lingvistic e ținut azi prin disciplină, nu prin unealtă. Azi lista de anunțuri afișează `<h1>Anunțuri</h1>` pe o pagină `<html lang="de">`. | Mid | Esențial | Rară |
| **Randare sigură a conținutului cu greutate juridică** | `|safe` pe corpuri de contract și escapare manuală a JSON-LD. Un XSS într-un document contractual e o problemă de altă categorie decât un XSS într-un comentariu. | Senior | Esențial | Moderată |
| **HTML semantic și accesibilitate (WCAG)** | Suprafață publică indexabilă + utilizatori pe teren. Accesibilitatea nu e opțională când Google e canalul principal de achiziție. | Mid | Important | Rară |
| **Livrabil XLSX: Reinigungsplan** | `openpyxl` ca extra opțional, import lazy, buffer în memorie. Este un **document care ajunge la client** — formatare, antet german, lizibilitate la print. Design de document, nu programare. | Junior | Important | Moderată |

### 4.5 DevOps și infrastructură

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Docker Compose în două topologii paralele** | `docker-compose.prod.yml` (stack propriu, Nginx) și `docker-compose.traefik.yml` (atașare la un Traefik existent). Sunt două modele operaționale diferite, cu două moduri de TLS: bootstrap `certbot` vs. certresolver prin etichete. | Mid | Blocant | Moderată |
| **Django în spatele unui lanț dublu de reverse proxy** | `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, `CSRF_TRUSTED_ORIGINS`, HSTS cu preload. Configurat greșit, `SECURE_SSL_REDIRECT` intră în buclă infinită — comentariul din `settings.py` documentează deja capcana. | Senior | Blocant | Rară |
| **Segregarea datelor personale prin topologia de volume** | `MEDIA_ROOT` e servit direct de Nginx, fără să treacă prin Django. De aceea actele de identitate și Führungszeugnis-urile merg într-un alias de stocare `"private"`, pe `PRIVATE_STORAGE_ROOT`, **în afara rădăcinii servite**, în spatele unui view care verifică proprietatea. Volumul privat nu se montează în containerul care servește static. | Senior | Blocant | Rară |
| **Dockerfile Django fără build de frontend** | Multi-stage, purge de toolchain în același layer, utilizator neprivilegiat (containerul ține acte de identitate), `collectstatic` la build ca procesul de producție să nu scrie în cod la pornire. | Mid | Esențial | Comună |
| **Backup și restaurare Postgres + arhivarea documentelor private** | Script de backup rulat din cron, cu retenție. Criteriul e **restaurarea testată**, nu existența fișierului. Azi backup-ul stă pe aceeași mașină cu baza. | Mid | Esențial | Comună |
| **Sarcini programate fără broker** | `flush_indexing` și `expire_requests` rulează din cron ca management commands idempotente. **Decizia de a nu introduce Celery/Redis este deliberată** — cine „modernizează" adaugă două servicii pentru două comenzi. | Mid | Important | Comună |
| **CI ca poartă de producție + unificarea dependențelor** | Pipeline-ul rulează `check --deploy`, `makemigrations --check`, pytest și build de imagine. Datorie tehnică imediată: `pyproject.toml`, `Dockerfile` și `ci.yml` declară liste de dependențe diferite; `ruff` e configurat dar neinstalat, deci **nu există pas de lint executabil**. | Mid | Esențial | Comună |
| **Observabilitate de producție** *(gol — nu există cod)* | Zero configurare `LOGGING`, zero error tracking, zero healthcheck. Azi nu ai cum să afli că `flush_indexing` e mort de trei săptămâni. | Senior | Esențial | Moderată |

### 4.6 Securitate și protecția datelor

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Arbeitnehmerdatenschutz: pontaj și telemetrie ca date personale** | Datele de check-in/check-out și telemetria de echipament sunt date personale ale angajatului (§26 BDSG). Führungszeugnis intră sub **Art. 10 DSGVO** — condamnări penale, cea mai strictă categorie. Retenția și limitarea scopului nu sunt opționale. | Expert | Esențial | Foarte rară |
| **Autentificare machine-to-machine fără sesiune** | Ingestia de telemetrie e `POST` cu Bearer comparat pe hash SHA-256, exceptată de CSRF, idempotentă. **O mașină nu are user** — reflexul de a atașa o sesiune e greșit aici. | Mid | Important | Moderată |
| **Hardening Django condiționat de `DEBUG`** | Blocul de întărire e activ doar în producție și **verificat în CI** prin `check --deploy --fail-level ERROR`. Configurația e corectă azi; ce lipsește e ca pipeline-ul să fie verde. | Mid | Esențial | Comună |
| **Testarea autorizării ca specificație executabilă** | `tests/test_isolation.py` este contractul de autorizare între conturi; `tests/test_visibility.py` este gardianul lui `FIELD_POLICY`. Nu sunt teste, sunt specificația — un câmp adăugat fără politică pică aici. | Senior | Esențial | Moderată |
| **Moderare de documente cu răspundere juridică** *(gol — proces inexistent)* | `VerificationDocument` are `status`, `reviewed_by`, `reviewed_at` — dar **nu există niciun formular sau view care să creeze unul**: un lucrător nu își poate încărca actul prin produs. Cine aprobă un Führungszeugnis, în ce termen, după ce criterii, cu ce răspuns către persoană — e o funcție operațională cu răspundere, nerevendicată de nimeni. | Mid | Esențial | Moderată |

### 4.7 Testare și asigurarea calității

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Teste ca oracol de conformitate legală datată** | Testele verifică *severitatea* unei constatări, nu doar prezența ei: salariul minim de ramură **blochează** un contract de muncă dar doar **avertizează** pe un Werkvertrag. Un test scris greșit aici transformă o eroare de conformitate într-un avertisment ignorat. | Senior | Blocant | Foarte rară |
| **pytest-django cu fixture-uri ancorate în migrări de seed** | Fixture-urile aduc localități și categorii **reale, seedate prin migrare**, căutate după slug — nu obiecte fabricate. Plus factory-uri ca `employer`, `worker`, `signed_contract`, `make_offer`. Numele testelor și docstring-urile sunt în română. | Mid | Esențial | Moderată |
| **Testarea invarianților de imutabilitate și non-retroactivitate** | Se testează că lucruri **nu se pot întâmpla**: că un `ShiftEvent` nu se poate rescrie, că editarea unui șablon nu atinge contractele semnate, că o schimbare de politică nu reordonează o cerere publicată. | Senior | Esențial | Rară |
| **Determinism temporal fără bibliotecă de înghețat ceasul** | Nu există `freezegun`. Testele care ating reguli datate trebuie să-și construiască singure datele relativ la o ancoră. | Senior | Important | Rară |
| **Testare fără mocking, prin seam injectat** | Transportul către Google se testează substituind stratul `_transport`, emailurile prin `mail.outbox`, configurația prin `settings`. Zero `unittest.mock` pe cod propriu. | Senior | Important | Moderată |
| **Ciclul bazei de test (`--reuse-db` vs `--create-db`)** | `pytest.ini` fixează `--reuse-db`. După ce adaugi o migrare de seed, baza cache-uită e stală și testele mint. Capcană clasică de onboarding. | Junior | Util | Moderată |

### 4.8 SEO și suprafață publică

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Semantica HTTP de depublicare** | Obiectele publicate **nu se șterg niciodată**. Se depublică, iar URL-ul răspunde **410 Gone + `X-Robots-Tag: noindex`**. Un `DELETE` pe rând sau un 404 în loc de 410 strică permanent istoria de indexare. | Senior | Esențial | Moderată |
| **Coadă durabilă pe trei straturi pentru Google Indexing API** | `enqueue` în tranzacție / `flush` din cron / `_transport` singurul cod care știe de Google. Publicarea nu depinde niciodată de disponibilitatea unui API extern; fără credențiale, `enqueue` funcționează și `flush` nu face nimic. | Senior | Esențial | Moderată |
| **Google for Jobs: JSON-LD `JobPosting`** | Construit în Python, cu escapare manuală pentru `ld+json`. **Paginile de job trebuie să rămână lizibile fără login**, altfel pică validarea Google. | Senior | Esențial | Rară |
| **SEO tehnic Django + SEO programatic oraș × categorie** | Sitemap secționat cu regula „doar URL-uri care întorc 200"; `DirectorySitemap` generează paginile oraș × categorie care chiar rankează, pe o taxonomie închisă de maximum două niveluri, cu doar frunzele selectabile. | Mid | Important | Moderată |
| **Poartă de publicare legată de §5 TMG** | Middleware-ul de publicare pune `noindex` pe **tot site-ul** cât timp datele operatorului sunt incomplete. Indexarea nu e o setare pe care cineva o poate uita — e derivată din validitatea Impressum-ului, pentru că un site german indexabil fără Impressum valid e motiv clasic de Abmahnung. | Senior | Esențial | Rară |
| **Copywriting german nativ pentru suprafața indexabilă** | „Treppenhaus- und Gemeinschaftsflächenreinigung" nu se traduce din română. Un dezvoltator român cu germană B2 nu e copywriter de piață. **URL-urile sunt permanente și slug-urile nu se eliberează niciodată** — deci textul greșit indexat rămâne. Se externalizează. | Senior | Important | Rară |

### 4.9 Domeniu Gebäudereinigung și drept german

> Aici stă valoarea defensibilă a produsului. Este și zona unde nicio persoană nu acoperă
> singură tot spectrul — vezi §5.3.

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **§7 SGB IV (Scheinselbstständigkeit) și AÜG ca decizie de arhitectură** | Alocarea automată de muncă unei persoane fizice îndeplinește criteriile de muncă dependentă și se apropie de Arbeitnehmerüberlassung, care cere licență de la Bundesagentur für Arbeit. De aceea platforma **sugerează** prestatori dar nu atribuie niciodată, iar planificarea alocă numai în interiorul unui singur angajator. `TEMP_AGENCY` e blocat în cod până când există licență. **Competența e de a traduce o constrângere juridică într-o absență deliberată de funcționalitate** — și de a o apăra la fiecare cerere de feature. | Expert | Blocant | Foarte rară |
| **Mindestlohntarifvertrag allgemeinverbindlich (§7 AEntG)** | Salariul minim de ramură e declarat general obligatoriu, deci leagă **și** firmele netarifare. Modelat ca rânduri efectiv-datate, rezolvat la data începerii contractului. Sporurile **nu se cumulează** — se aplică doar cel mai mare. | Senior | Blocant | Rară |
| **Arbeitszeitrecht operaționalizat** | §3 (8h/zi), §5 (11h repaus), §9 (fără duminică) trăiesc în alocator; §16 ArbZG plus decizia BAG din 13.09.2022 impun jurnalul de pontaj append-only. Legea nu e comentariu, e constrângere executabilă. | Senior | Esențial | Rară |
| **Statutul juridic al prestatorului ca axă de date** | `LegalStatus` (UNDECLARED / MINIJOB / SELBSTSTÄNDIG / KLEINUNTERNEHMER / COMPANY) decide **cine e plătitorul legal, cine facturează și dacă se poate genera un contract**. Generarea refuză explicit dacă statutul e nedeterminat. Praguri Minijob §8/§8a SGB IV, Kleinunternehmer §19 UStG. | Senior | Esențial | Rară |
| **Genossenschaft (eG) și guvernanța repartizării** | Operatorii sunt firme membre care co-decid prețurile și regulile de repartizare. Alocarea e **intermediere între întreprinderi**, niciodată instrucțiune către o persoană. Ponderile de scoring sunt un act de guvernanță, nu un parametru tehnic. | Senior | Important | Rară |
| **Germană profesională C1+ pe trei registre** | Juridic (contracte, praguri), de branșă (Leistungsverzeichnis, Festtour, Unterhaltsreinigung) și copy public indexabil. Trei registre diferite, nu unul. | Senior | Esențial | Rară |
| **Disciplina split-ului trilingv DE/RO/EN** | Argumentația juridică a proiectului trăiește în comentarii, docstring-uri și nume de teste **în română**; datele seed, contractele și textul public sunt **în germană**; identificatorii Python sunt în engleză. Un dev care nu citește română nu poate întreține `apps/planning`; unul care nu citește germană nu poate atinge `apps/contracts`. | Mid | Esențial | Rară |
| **Cunoaștere de teren Gebäudereinigung** | Cât durează o casă a scării de 6 etaje, ce înseamnă practic o rundă de dimineață, ce refuză un Betrieb. Fără asta, `minutes_per_visit` și calibrarea sunt ficțiune. **Nu e rol de inginerie** — ideal, un membru fondator al cooperativei. | Senior | Esențial | Rară |
| **Redactare de contracte germane de muncă și de prestări servicii** | §2 NachweisG, §622 BGB, §3 BUrlG, §4 TzBfG. Migrarea de șabloane își cere ea însăși trecerea printr-un Fachanwalt înainte de prima utilizare, iar praguri sunt marcate „DE CONFIRMAT". **Se externalizează integral** (§5.3). | Expert | Blocant | Foarte rară |

### 4.10 Faza comercială — competențe viitoare

> Nimic din această secțiune nu există în cod. Este specificată ca `gr-auftrag-und-faktura`
> și tratată ca **spec**, nu ca documentație. Relevanța pentru HR: recrutarea durează 3–6 luni,
> deci căutarea începe înainte de a fi nevoie.

| Competență | De ce va fi necesară | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **E-Rechnung germană: XRechnung 3.x / ZUGFeRD 2.x** | EN 16931, Leitweg-ID, validare KoSIT. Facturarea către sectorul public german o cere prin lege; prima factură invalidă e respinsă la recepție. Pool de candidați aproape inexistent în România, decent în Germania (ecosistem DATEV/ERP). | Senior | Blocant | Foarte rară |
| **Faktura conformă GoBD** | Numerotare fără goluri sub `select_for_update()`, documente emise imutabile, Storno/Gutschrift, Abschlags-/Teil-/Schlussrechnung, arhivare 10 ani. Developerul implementează; **cine semnează că rezistă la o Betriebsprüfung este contabilul**. | Senior | Blocant | Rară |
| **Plăți multi-party cu PSP de marketplace** | Stripe Connect sau Mangopay, onboarding KYC, SEPA, reconciliere. Cine e plătitorul legal depinde de `LegalStatus` — deci codul de plată nu se poate scrie înainte de a ști asta. | Senior | Important | Moderată |
| **Conformitate de lansare pe piața germană** | Impressum accesibil de oriunde, AGB, Datenschutzerklärung, Widerrufsbelehrung. Se acoperă prin abonament la un serviciu de texte juridice (10–30 EUR/lună), nu prin scris propriu. | Senior | Blocant | Rară |

### 4.11 Proces, produs și comunicare

| Competență | De ce în acest proiect | Nivel | Crit. | Rar. |
|---|---|---|---|---|
| **Comunicare tranzacțională** *(gol — cel mai mare din produs)* | Există **un singur** apel de trimitere email în tot repo-ul, zero template-uri de email, zero modele de notificare sau mesaj. Un candidat aplică → nu primește nimic. Un prestator pierde licitația → nu află, deși scoringul produce `explain()` tocmai ca să poată fi justificat. Un contract intră în SENT → nimeni nu e anunțat. Competența nu e „configurează SMTP" — e a proiecta **ce se trimite, cui, în ce limbă** (candidat german vs. lucrător român vs. client german) și cu ce temei DSGVO. | Senior | Blocant | Moderată |
| **Autorat de documentație normativă încărcabilă de agenți** | Proiectul își codifică propriile convenții ca skill-uri (~20.000 de linii). Documentația e artefact de prim rang, cu marcaje de certitudine și ancore în fișiere. Este și modul de onboarding al unui dezvoltator nou. | Expert | Esențial | Foarte rară |
| **Audit de derivă documentație ↔ cod** | Riscul real al abordării de mai sus: **azi `CLAUDE.md` afirmă „niciun `admin.py` nicăieri" în timp ce repo-ul are 10 fișiere `admin.py` și 692 de linii de admin**, iar numărul de teste apare ca 230 în documentație și 295 la rulare. Cineva trebuie să dețină reconcilierea, altfel documentația devine activ înșelătoare. | Senior | Esențial | Moderată |
| **Product ownership și prioritizare** *(gol — rol inexistent)* | Trei fluxuri de business paralele (recrutare, licitație, consumabile) fără ierarhie de prioritate. E-facturarea, importul de portofoliu și CSS-ul sunt punctate ca dificultate tehnică, niciodată **una față de alta**. Zero analytics de produs: nu se măsoară conversia candidatură→angajare, nici cererile expirate fără nicio ofertă — exact indicatorii care spun dacă marketplace-ul funcționează. | Senior | Esențial | Moderată |
| **Formare utilizatori și documentație end-user** *(gol)* | Zero ecrane de ajutor, zero ghid. Cele ~20.000 de linii de documentație sunt scrise **pentru agenți, nu pentru utilizatori**. Cineva trebuie să învețe o femeie de serviciu să folosească ecranul de pontaj, în română sau germană. | Mid | Important | Comună |
| **Igienă de control al versiunilor pentru cod generat în bloc** | Repo-ul e sub git de 5 commit-uri, cu muncă necomisă în lucru. Cod generat rapid produce istorie inutilizabilă dacă nu e disciplinat — iar acest document a fost nevoit să fie re-ancorat la jumătatea analizei fiindcă arborele s-a mutat sub el. | Mid | Esențial | Comună |
| **Conducerea dezvoltării asistate de agenți** | Ordine de încărcare a skill-urilor, rutare între ele, verificarea rezultatului. Este modul de lucru declarat al echipei, nu un accesoriu. | Senior | Important | Rară |

---

## 5. Structura de echipă și ordinea de recrutare

### 5.1 Minim viabil — 2,5 FTE interni + 3 consultanți

Suficient pentru a repara CI-ul, a face produsul prezentabil și a lansa Faza 0.
**Nu** este suficient pentru facturare.

| Rol | FTE | Acoperă din §4 |
|---|---:|---|
| **Senior Django / owner de domeniu** — RO nativ, DE minim B2 citit | 1,0 | 4.1 integral · 4.2 integral · 4.3 · 4.6 · 4.7 · plus dreptul de veto pe §7 SGB IV / AÜG |
| **Mid Django full-stack server-rendered** — RO nativ, DE B1+ | 1,0 | 4.4 integral · 4.8 (partea tehnică) · formulare și template-uri allauth, care azi nu există |
| **DevOps / platform** — contractor, nu angajat | 0,3–0,5 | 4.5 integral |

### 5.2 Confortabil — 5,5 FTE interni + 4 consultanți

Necesar din momentul în care începe faza comercială.

| Rol | FTE | Acoperă suplimentar |
|---|---:|---|
| **Tech lead / arhitect Django** | 1,0 | Ca 5.1, plus code review pe split-ul lingvistic și auditul de derivă doc↔cod (4.11) |
| **Senior backend „billing & compliance"** | 1,0 | 4.10 integral |
| **Mid backend / product engineer** | 1,0 | Extinderi în `planning` și `marketplace`, comunicare tranzacțională (4.11), import de portofoliu (4.3) |
| **Frontend server-rendered + UI** | 1,0 | 4.4 la calitate de produs, plus Core Web Vitals pe paginile indexabile |
| **DevOps / platform** | 0,5 | 4.5 plus observabilitate reală și proceduri de restaurare testate |
| **Ops / coordonator Gebäudereinigung** — RO+DE, om de teren | 1,0 | 4.9 „cunoaștere de teren". **Nu e rol de inginerie.** Validează `minutes_per_visit`, frecvențele, ce refuză un Betrieb |

> **Nu recomand un rol de QA separat.** Suita de teste e scrisă ca teste-contract de către oamenii
> care scriu codul, și asta e forma corectă aici. Ce lipsește e `pytest-cov` și un pas de lint —
> adică tooling, nu oameni.

### 5.3 Ce se combină într-o persoană și ce nu

**Se combină** (aceleași fișiere, același mod de gândire):

- Backend + modelare de date + migrări + strat de servicii — sunt literalmente aceleași fișiere.
- SEO **tehnic** + view-uri publice Django — totul e Python; un „specialist SEO" clasic nu poate atinge niciun rând. Ce se separă e copywriting-ul, nu SEO-ul.
- Frontend + CSS + accesibilitate + i18n de template — un singur profil, nu trei; nu există bundler.
- DevOps + backend senior, la 0,3–0,5 FTE — ~576 de linii de configurare nu justifică un SRE.
- Testare + backend — fixture-urile ancorate în migrări nu au sens scrise de altcineva.
- Cunoașterea **operațională** a pragurilor germane + backend senior — a ține minte „max(MiLoG, tarif de ramură), rezolvat la `start_date`" e disciplină de inginerie, nu drept.

**NU se combină — se externalizează explicit:**

| Nu se combină | De ce | Format |
|---|---|---|
| Django expert ≠ **Fachanwalt für Arbeitsrecht** | Nimeni nu e ambele. Avizul pe șabloane, §2 NachweisG, Textform vs Schriftform, poziția pe AÜG | Audit 8–12 h + retainer 2–4 h/lună |
| Developer ≠ **Steuerberater / expert GoBD** | Devul implementează numerotarea; contabilul **semnează** că rezistă la Betriebsprüfung | 8–16 h + 4–6 h/lună |
| Dev român cu DE B2 ≠ **copywriter DE de piață** | Textul trebuie să rankeze în Germania, iar slug-urile nu se eliberează niciodată | Proiect 20–40 h + mentenanță |
| Backend senior ≠ **designer** | Poate scrie CSS, dar rezultatul arată ca un produs de developer | Proiect 60–100 h, apoi ~0 |
| Oricine ≠ **Datenschutzbeauftragter** | Art. 10 DSGVO (Führungszeugnis) + §26 BDSG (pontaj) | Retainer permanent |
| Inginerie ≠ **cunoaștere de teren** | Nu se deduce din cod | Angajare part-time sau membru fondator |

### 5.4 Ordinea de recrutare

1. **Luna 0** — Senior Django + contractor DevOps 0,3 FTE. Prima livrare: CI verde, dependențe unificate, logging, backup restaurabil. Sunt 2–3 zile-om și blochează tot restul.
2. **Luna 0, în paralel** — deschide căutarea pentru Fachanwalt (durează) și semnează abonamentul de texte juridice; 30 EUR/lună elimină azi un risc de Abmahnung.
3. **Luna 1** — Mid Django full-stack. Prima livrare: CSS, i18n, template-uri allauth, ecranul de pontaj mobil.
4. **Luna 2–3** — copywriter DE, ca proiect. **Înainte** ca Google să indexeze varianta greșită: URL-urile sunt permanente.
5. **Luna 4–6** — începe căutarea pentru senior „billing & compliance". Faza comercială nu poate începe fără el.
6. **La intrarea în faza comercială** — completează la structura 5.2, inclusiv rolul de ops de teren.

---

## 6. Harta competență → cod (pentru team lead)

Pentru asignarea task-urilor. Referințele sunt fișiere, nu linii.

| Fișier / modul | Competențe necesare ca cineva să-l atingă |
|---|---|
| `apps/accounts/permissions.py` · `visibility.py` | Izolare între conturi · Proiecție de câmpuri · Testare de autorizare |
| `apps/accounts/models.py` · `middleware.py` | Custom User + allauth 65 · Middleware cu stare de tenant |
| `apps/planning/services.py` · `tours.py` | Alocator cu constrângeri · Arbeitszeitrecht · Explicabilitatea eșecului |
| `apps/planning/calibration.py` | Statistică robustă · Automatizare cu om în buclă |
| `apps/planning/attendance.py` | Imutabilitate · §16 ArbZG / BAG 13.09.2022 · Arbeitnehmerdatenschutz |
| `apps/planning/reinigungsplan.py` | XLSX ca livrabil către client · Germană de branșă |
| `apps/marketplace/scoring.py` · `services.py` | Scoring explicabil · Mașini de stare · Guvernanță de cooperativă |
| `apps/contracts/models.py` · `services.py` · `migrations/0002_*` | Reguli datate · Documente înghețate · Drept german al muncii *(+ Fachanwalt)* |
| `apps/jobs/indexing.py` · `config/sitemaps.py` | Cozi durabile · SEO tehnic · Semantica de depublicare |
| `apps/legal/publication.py` | §5 TMG · Poarta de publicare |
| `apps/devices/api.py` · `services.py` | Autentificare machine-to-machine · Telemetria ca verificare, nu măsurătoare |
| `templates/**` · `static/` | CSS de la zero · DTL · Accesibilitate · UX de teren · Copywriting DE |
| `Dockerfile` · `docker-compose.*` · `deploy/` | Cele două topologii · Reverse proxy dublu · Segregarea volumelor |
| `tests/test_isolation.py` · `test_visibility.py` | **Nu se modifică fără decizie explicită** — sunt specificația, nu teste |

---

## 7. Riscuri de resurse (pentru stakeholder și PM)

Ordonate după cât de greu se acoperă, nu după probabilitate.

| # | Risc | Consecință dacă nu se acoperă |
|---|---|---|
| 1 | **Fără Fachanwalt für Arbeitsrecht** | Lansarea e blocată **juridic, nu tehnic**. Generarea de contracte produce documente atacabile; `TEMP_AGENCY` rămâne blocat nedefinit. Caută-l în luna 0, nu în luna 5. |
| 2 | **Fără senior care spune „nu" din motive juridice** | Arhitectura se „optimizează" în detașare de personal fără licență. Filtru comportamental, nu tehnic — vezi proba din §8. |
| 3 | **Fără combinația RO tehnic + DE C1** | `apps/planning`, `apps/cooperative` și `tests/` sunt în română; `apps/contracts` și taxonomia sunt în germană. Pool restrâns, dar real: diaspora RO din DE/AT. |
| 4 | **Fără frontend cu gust vizual** | Produsul nu poate fi prezentat unui client german plătitor și pierde conversia candidaților pe mobil. Mii de „React developers", foarte puțini care scriu CSS de la zero. |
| 5 | **Fără dev cu XRechnung/ZUGFeRD + GoBD** | Nu e blocant azi (zero cod comercial), dar recrutarea durează 3–6 luni. Prima factură invalidă e respinsă la recepție. |
| 6 | **Fără comunicare tranzacțională** | Produsul funcționează și nimeni nu află nimic. Cel mai ieftin de reparat din listă, cel mai vizibil pentru utilizator. |
| 7 | **Fără DevOps part-time** | CI rămâne roșu, nu ai logging, nu afli că indexarea e moartă, backup-ul stă pe aceeași mașină cu baza. Ușor de acoperit. |
| 8 | **Derivă documentație ↔ cod** | Documentația normativă devine activ înșelătoare. Deja s-a întâmplat: `CLAUDE.md` afirmă „niciun `admin.py`" peste 10 fișiere reale. |

---

## 8. Probe de interviu (pentru HR și team lead)

Întrebări care separă profilul potrivit de unul generic. Fiecare are un răspuns greșit tipic.

**1. Filtrul juridic — cel mai important din listă.**
> „Clientul vrea un buton «atribuie automat celei mai bune oferte». Cât durează?"

- ❌ „O oră, avem deja scoringul." → **risc juridic pentru companie**
- ✅ Întreabă întâi dacă prestatorul e persoană fizică sau firmă, apoi invocă §7 SGB IV și AÜG.

**2. Izolare între conturi.**
> „De ce un obiect care aparține altui cont întoarce 404 și nu 403?"

- ✅ Ca un cont străin să nu afle nici măcar că resursa există. Bonus dacă distinge: lipsa capabilității → 403, obiect străin → 404.

**3. Reguli datate.**
> „Un contract începe pe 1 martie. Salariul minim de ramură s-a schimbat pe 1 ianuarie. Contra cărei valori validezi?"

- ❌ „Cea curentă." · ✅ „Cea valabilă la `start_date`" — și explică de ce hardcodarea sumei e un bug care apare peste șase luni, la un audit.

**4. Statistică aplicată.**
> „De ce mediană și MAD, nu media și deviația standard, la calibrarea duratelor?"

- ✅ O singură tură uitată deschisă deplasează media. Bonus: de ce pragul e dual (procent **și** minute absolute).

**5. Django, nivel de reflexe.**
> „Unde pui logica care creează un contract dintr-o ofertă câștigătoare?"

- ❌ Într-un semnal `post_save`. · ✅ Într-o funcție de serviciu sub `@transaction.atomic`. Repo-ul are zero semnale, deliberat.

**6. Vizibilitatea datelor.**
> „Adaugi un câmp `iban` pe `Account`. Ce mai trebuie făcut ca să nu se scurgă?"

- ✅ Adăugat în `FIELD_POLICY`. Bonus: implicit e `SELF`, deci fail-closed — dar un câmp nedeclarat e invizibil și pentru ecranele care ar trebui să-l arate.

**7. Frontend — filtru de profil.**
> „Nu există bundler, nu există Tailwind, `static/` e gol. Cum începi?"

- ❌ „Instalez Tailwind." · ✅ Tokeni CSS, scară tipografică, componente scrise de mână; întreabă de brand și de utilizatorul de pe teren.

**8. Limbă — se testează, nu se declară.**
> Dă-i un docstring românesc din `apps/planning/services.py` și un fragment din migrarea de șabloane de contract în germană. Cere-i să explice ambele.

---

## 9. Ce **nu** trebuie recrutat

Cea mai frecventă eroare la citirea unui stack Django. Niciuna dintre tehnologiile de mai jos
nu există în proiect, iar recrutarea pe ele produce oameni care nu pot atinge codul.

| Nu recruta pe… | Pentru că… |
|---|---|
| **Django REST Framework / API design** | Nu există strat de API, serializatoare sau routere. Totul e server-rendered. |
| **React / Vue / TypeScript / Node** | Nu există `package.json`, bundler sau pas de build. Un frontend developer de SPA nu poate atinge niciun rând util. |
| **Celery / Redis / brokere de task-uri** | Sarcinile periodice sunt management commands rulate din cron. Decizia e deliberată. |
| **Kubernetes / microservicii** | Un singur proces Django, două fișiere Compose, ~576 de linii de configurare totală. |
| **Tailwind / design systems bazate pe framework** | Nu e instalat. Competența cerută e CSS scris de mână. |
| **Django admin ca „locul unde se schimbă lucrurile"** | Admin-ul există (10 fișiere, 692 de linii) dar e o unealtă de conformitate internă, nu interfața produsului. Nu spune niciodată unui client „schimbi din admin". |
| **GraphQL / WebSockets / Channels / async Django** | Zero apariții în cod sau dependențe. |
| **„SEO specialist" clasic (non-tehnic)** | SEO-ul aici e Python: sitemap-uri, coduri HTTP, JSON-LD. Ce se externalizează e **copywriting-ul german**, nu SEO-ul. |
| **QA manual** | Nu există UI de testat manual în forma actuală, iar suita e scrisă ca teste-contract de autorii codului. |

---

## Anexă — note de metodă și limite

- **Derivat din cod, nu din intenții.** Fiecare competență e ancorată într-un fișier real. Ce nu are corespondent în repo e marcat explicit *(gol)* sau plasat în §4.10 (viitor).
- **Referințe la nivel de fișier.** Arborele s-a modificat în timpul acestei analize — `apps/planning/views.py` a devenit pachetul `views/` — deci numerele de linie se învechesc în zile.
- **Documentația repo-ului este parțial stală la data scrierii.** `CLAUDE.md` afirmă „niciun `admin.py` nicăieri" (repo-ul are 10) și „230 de teste" (rulează 295). Cifrele din acest document provin din măsurători proprii pe commit `acded85`, nu din documentație.
- **Deduplicare aplicată.** Analiza brută a produs 96 de competențe pe 12 dimensiuni; ~20% descriau același cod sub nume diferite. Grupurile unificate: imutabilitate (4 dimensiuni → 1), reguli datate (4 → 1), autorizare (3 → 1), split lingvistic (4 → 2), hardening proxy (3 → 1), drift de dependențe (4 → 1, reclasificat ca datorie tehnică).
- **Nu acoperă:** costuri salariale efective, evaluarea persoanelor din echipa actuală, planul de formare. Estimările de consultanță din §5.3 sunt orientative pentru piața DE.

**Recomandare de proces:** înghețați un commit înainte de următoarea revizuire a acestui document
și ancorați referințele pe acel SHA. Altfel matricea reproduce exact defectul pe care îl critică —
documentație care descrie un arbore care nu mai există.
