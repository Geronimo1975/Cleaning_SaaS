

Vreau să dezvolt o platformă SaaS de tip piață/bursă pentru servicii de curățenie, cu backend Django (Python) și frontend HTML/HTMX sau React. Ajută-mă să clarific și să structurez modelul de date și deciziile arhitecturale critice înainte să mă apuc de implementare.

## Contextul Afacerii

Platforma conectează patru tipuri de utilizatori:

- Persoane fizice care lucrează independent (curățenie manuală)
- Firme autorizate care oferă servicii de curățenie
- Firme care vând materiale/produse de curățenie
- Firme sau persoane beneficiare care au nevoie de servicii de curățenie

Mecanismul de bază: beneficiarul publică o nevoie, iar prestatorii (firme sau persoane fizice) depun candidaturi/oferte. Nu există negociere directă a prețului — funcționează ca o bursă, unde beneficiarul alege oferta câștigătoare pe baza mai multor criterii (preț, distanță, calitate, rating etc.), nu neapărat cel mai mic preț. În anumite situații, sistemul trebuie să poată aloca automat serviciul unei persoane fizice disponibile, fără intervenție manuală.

Pe lângă angajarea de prestatori, beneficiarul poate cumpăra materiale de curățenie direct de la firmele furnizoare din platformă.

**Fluxul integral trebuie digitalizat**: plată automatizată cu decontare online către toate părțile implicate (model asemănător Liferanto), plus semnătură digitală pentru contracte/confirmări.

## Ce Explorăm Împreună

Ai validat deja nevoile cu utilizatori din fiecare segment și ai chiar clienți în așteptare. Știi ce vrei și ai o parte din arhitectură — acum ai nevoie de feedback la planul de execuție și clarificare pe punctele critice ale modelului.

Concentrează-te pe aceste întrebări-cheie:

- **Modelul de date și roluri**: Cum ar trebui gândit sistemul de permisiuni și relații între entități, având în vedere că actori pot avea roluri duble (ex: o firmă poate fi simultan prestator și cumpărător de materiale)? Ce implicații are asta pentru schema de bază de date și autentificare?
- **Logica de matching și alocarea automată**: Ce criterii și algoritm ar avea sens pentru scoring și selecție de oferte pe bază de prioritate multiplu? Cum ar trebui să funcționeze alocarea automată către o persoană fizică disponibilă — ce date e nevoie să fie disponibile în timp real, și ce toleranță de eroare e acceptabilă?
- **Sistem de plăți multi-parte**: Ce implică tehnic un model tip split payments cu decontare automată către toți stakeholder-ii (platformă, prestatori, furnizori, eventual escrow)? Ce procesatori de plăți sunt realiști pentru România/UE la această etapă (Stripe, Wise, altii), și cum ar integra asta cu Django?
- **Semnătură digitală**: Ce e necesar din perspectivă tehnică și legală pentru contracte digitale semnate pe platformă în contextul România/UE? Ce librării sau servicii existente poți folosi?
- **Frontend: HTML/HTMX vs React**: În ce condiții ar avea sens fiecare opțiune pentru: dashboard-uri diferite per rol, actualizări în timp real pentru licitații/oferte, formulare complexe, și complexitatea asta va crește în timp?
- **MVP realist**: Ce funcționalități sunt cu adevărat esențiale pentru a testa modelul de piață cu primele firme și persoane fizice? Ce poate rămâne pentru etape ulterioare?

## Ghidare pentru Explorare

În locurile unde modelul tău are presupuneri neclare sau decizii deschise, pune întrebări și scoate riscurile în evidență. Unde lipsesc detalii importante (volum estimat de utilizatori, zonă geografică de lansare, integrări de plată specifice), semnalează și ajută-mă să le definesc.

Nu vreau un document de arhitectură finalizat — vreau să gândim împreună prin aceste decizii, să identifici riscurile în modelul meu, și să-mi pui întrebările potrivite acolo unde e necesar.
