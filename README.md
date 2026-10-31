# Hukommelse LM — versjon 2.1

En komplett **React + TypeScript / FastAPI / SQLite**-app for et fjernbasert pilotforsøk om hvorvidt varme, kalde og mørke **skjermbakgrunner** påvirker læring av nye ordassosiasjoner. Nettsiden er tilgjengelig på norsk, engelsk, svensk, tysk, fransk og spansk og har responsivt design.

> **Forskningspresisjon:** Dette er et forsøk med presise **sRGB/HEX-verdier**, ikke en kalibrert måling av 3000 K, 10000 K, lux eller lys som når netthinnen. Svart bakgrunn gir mye lavere lysmengde enn fargebakgrunnene. Den forskjellen må omtales som en begrensning i rapporten. Dette er en teknisk komplett pilot, men **ikke** en ferdig vitenskapelig validert metode eller automatisk godkjent for offentlig forskning.

## Funksjoner

- Registrering: språk (norsk/engelsk/svensk/tysk/fransk/spansk), aldersgruppe, valgfritt kjønn og eksplisitt samtykke.
- Lokal lagring av deltaker-ID, valgt språk og ufullstendige svar for gjenopptakelse.
- Kalibreringsveiledning for Windows, macOS, Linux, iOS, Android og eksterne skjermer; ingen musikk eller lyd, fast skjermlysstyrke og fargejustering av.
- Svak lys-på-lys/mørk-på-mørk kontrastkontroll: kun en subjektiv tilpasning, **ikke** et validert lysmåleinstrument.
- Fullskjermknappen veksler mellom å gå inn i og ut av fullskjerm og viser feilmelding om nettleseren blokkerer funksjonen.
- Tre bakgrunnsfarger: `WARM #D9AA91`, `COOL #9BB6E4`, `DARK #080B11`.
- Gruppefordeling A/B/C med motbalansert lysrekkefølge, pluss seks motbalanserte ordliste-rekkefølger **innen hver gruppe**.
- Hver runde: **60 sekunder tilvenning med bare skjermfarge og nedtelling**, 60 sekunder memorering, 30 sekunder regnedistraksjon og maks 120 sekunder fri gjenhenting.
- Tidsgrenser fra serveren: en refresh nullstiller ikke memoreringstiden; fasen oppdateres etter serverklokken.
- 3 × 10 nye kunstige ord med færre åpenbare semantiske assosiasjoner og faste, språklig kvalitetssikrede objektnavn på seks språk. Verifiser likevel ordlikhet i en pilot.
- Scoring og fasit bare på serveren, SQLite-lagring av resultater, tidsbruk og antall ganger fanen ble skjult.
- Sikker CSV-eksport med lokal kommandolinje eller et beskyttet administrasjonsendepunkt.
- Deltaker-ID kombineres med et separat 256-bit tilgangstoken. Bare SHA-256-hashen lagres på serveren. API-et krever tokenet for å lese, starte, levere og slette deltakerdata.
- API- og nettlesersikkerhet: ingen CORS-utvidelse, sikre responsoverskrifter, `no-store`, restriktiv CSP ved produksjonsservering og enkel begrensning av antall registreringer. Bruk i tillegg en HTTPS-reverse proxy med rate limiting ved offentlig publisering.
- Tilbaketrekking av samtykke: deltakeren kan slette alle sine **nye** studiedata via nettsiden.
- **Ingen av de gamle `participants`- eller `experiment_results`-tabellene blir endret eller slettet.** Tidligere V2.0-deltakere arkiveres som egen protokollversjon. De må registrere seg på nytt for å teste V2.1; tidligere resultater beholdes, men blandes ikke automatisk med V2.1-analysen.
- `backend/results.db` og `.pyc`-filer skal ikke lagres i Git. Dersom de tidligere ble sporet, må de fjernes fra Git-indeksen; tidligere commits kan fortsatt inneholde kopier.

## Slik starter du lokalt (Windows PowerShell)

Krever Python 3.10+ og Node.js 20.19+ eller 22.12+. I **to terminaler**:

**Terminal 1 — backend**

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend**

```powershell
cd frontend
npm install
npm run dev
```

Åpne `http://127.0.0.1:5173` i nettleseren. Vite sender `/api` videre til FastAPI. API-status kan sjekkes på `http://127.0.0.1:8000/api/health`.

**Linux/macOS:** Opprett miljø med `python3 -m venv .venv`, aktiver med `source .venv/bin/activate` og bruk `python -m uvicorn ...`.

### Starte fra én port etter frontend-bygg

```bash
cd frontend
npm install
npm run build
cd ../backend
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Åpne først `http://127.0.0.1:5173` i utviklingsmodus. Når `frontend/dist` finnes, serverer FastAPI den ferdige nettsiden fra `http://127.0.0.1:8000/`. For offentlig publisering må dette settes bak en HTTPS-reverse proxy / egnet host. Ikke eksponer en utviklingsserver med `--reload` på internett.

## Oppdater ditt eksisterende GitHub-prosjekt

1. **Ta en kopi av din eksisterende `backend/results.db`** før du overskriver kode.
2. Pakk ut denne prosjektmappen og kopier innholdet inn i ditt eksisterende Git-repositorium. Erstatt den gamle `frontend/`-koden og gamle Python-filer du ikke lenger trenger, men **ikke** overskriv eller slett `backend/results.db`.
3. Den nye `database.init_db()` oppretter nye tabeller: `study_participants`, `study_rounds`, `study_results`. Gamle resultater ligger urørt i sine gamle tabeller.
4. Prøv forsøket lokalt først. Kjør testene og gjennomfør alle tre rundene.
5. Når alt virker: `git add .`, `git commit -m "Build vocabulary and screen-color study v2"`, `git push`.

Av sikkerhetsgrunner ignoreres lokale databaser (`*.db`) og hemmeligheter (`.env`) av `.gitignore`. Ikke committ deltakerdata på GitHub.

## Docker (alternativ)

For en enklere serverinstallasjon med persistent datavolum kan prosjektet bygges med Docker. Applikasjonen blir da tilgjengelig **bare lokalt** på `127.0.0.1:8000`. Sett opp en ekstern HTTPS-reverse proxy dersom den skal nås offentlig.

```bash
docker compose up --build -d
```

Databasen lagres i Docker-volumet `study-data`; ta backup før du fjerner volumet. Docker importerer **ikke automatisk** en tidligere `backend/results.db`. For å bevare eldre data, kjør den lokale løsningen eller migrer kopien inn i volumet selv.

## Teste backend

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

## CSV-eksport og analyse

Direkte fra backend-mappen:

```bash
python export_cli.py study_results.csv
```

Du kan også konfigurere en hemmelig eksportnøkkel som miljøvariabel:

```powershell
$env:STUDY_ADMIN_TOKEN = "velg-en-tilfeldig-lang-hemmelig-verdi"
```

Deretter sende `GET /api/admin/export.csv` med HTTP-headeren `X-Admin-Token`. **Aldri** legg nøkkelen inn i frontend-koden, GitHub eller i URL-adressen.

For et raskt lokalt sammendrag kan du også kjøre `python analyze_cli.py` i backend-mappen.

Exporten inneholder pseudonyme UUID-er, språk, alder, ev. kjønn, gruppe, ordliste, lysforhold, svar, poengsummer, tidsbruk og faneskjulinger. Spred ikke rådata offentlig; aggreger resultater først.

## Forskning og personvern

Les [docs/PROTOCOL.md](docs/PROTOCOL.md) før du rekrutterer deltakere. Dette er en pilot. Du må gjennomføre en separat pilot for å undersøke ordlistenes vanskelighetsgrad, lesehastighet, språkforskjeller, tak-/gulveffekter og skjermfargenes luminans. Planlegg statistikken før datainnsamling. Avklar samtykkekrav, personvern og eventuelle krav til foresatte eller skole før rekruttering av mindreårige.

Den nye løsningen inkluderer **ikke Google Translate API**. Den støtter seks nøye avgrensede språk med faste oversettelser av 30 objektord. Å støtte alle verdens språk krever oversettelse og kvalitetssikring av både grensesnitt og svarvarianter. Dette gjør at resultatene ikke avhenger av ustabile oversettelser, Google-kostnader eller en ekstern API-nøkkel. Nye språk må kvalitetssikres separat før de brukes.

### Viktige begrensninger

- En nettside kan **ikke** stille inn fysisk skjermlysstyrke eller måle lux, spektrum eller faktisk korrelert fargetemperatur.
- Skjermkalibrering er en sjekkliste, ikke måleutstyr. Ulike paneler, nattmodus, romlys og øyeavstand gir usikkerhet.
- To fargede forhold er valgt til omtrent lik **beregnet sRGB-relativ luminans**. Dette tilsvarer ikke lik målt lysmengde på forskjellige skjermer.
- Den mørke betingelsen har med vilje lavere luminans og blander derfor effektene av lysmengde og farge.
- Ordparene er **ikke psykometrisk validert**. De er utgangspunkt for en pilot og bør testes for vanskelighetsgrad.
- Fullskjerm kan avvises av nettleseren. Avbrutt/flyttet nettleserfane registreres grovt, men dette er ikke juksesikring.
- Offentlig publisering krever ekstern hosting med HTTPS, backup, sikker konfigurasjon, rate limiting og gjennomgang av personvern. Ingen data sendes til en tredjeparts oversettelsestjeneste.


## Sikkerhet og pilotversjon 2.1

- Husk å oppdatere fra `feature/hukommelse-lm-v2` (utviklingsgrenen) når endringene er publisert på GitHub.
- **Gammel deltakelse:** V2.0-registreringer har ikke tilgangstoken og er ikke kompatible med V2.1. På feilsiden kan du velge «Start på nytt med denne versjonen»; tidligere data forblir lagret.
- 60 sekunder tilvenning må gjennomføres helt før ordparene blir tilgjengelige. Tiden håndheves av serverklokken og kan ikke startes på nytt ved refresh.
- Ved offentlig publisering må serveren kjøre bak HTTPS, med backups, begrensede nettverkstilganger, ekstern rate limiting og plan for sletting av data. Ikke publiser databasen eller administrasjonstokenet. UUID og tilgangstoken er autentisering, men ikke fullverdig brukeradministrasjon.
- Ta sikkerhetskopi før databaseoppgradering. En eksisterende V2.0-database migreres i en transaksjon: gamle deltaker-ID-er og resultater beholdes, men den nye protokollen tildeler nye ID-er og nye tilgangstokener.

### Oppdatering: hukommelsestesten hopper over svarfeltene

En tidligere frontend-feil gjorde at `00:00` fra distraksjonsfasen kortvarig ble
brukt i hukommelsesfasen, og at tomme svar dermed kunne sendes automatisk.
Nedtellingen beregnes nå fra den **nye fasens egen frist** ved første visning,
og automatisk innsending verifiserer også at serverens reelle frist er nådd.
Du skal få opptil 120 sekunder til å skrive svarene. Kjør
`npm run test:timing` for regresjonstester og `python -m pytest -q`
i backend for API-testene.

Svar som tidligere ble automatisk registrert som tomme, må behandles som
**ugyldige pilotdata** i analysen; feilen kan ikke gjenskape det deltakeren
faktisk husket. Start en ny frivillig testøkt etter kodeoppdateringen.


## V2.2: gjennomgang av design, språk, sikkerhet og svak maskinvare

Denne versjonen har fått et eget **nøkternt forskningsdesign** i
`frontend/src/editorial.css`, responsivt layout for telefon/nettbrett/PC,
tilgjengelige knapper og inndatafelt, skjermutsnitt for iPhone, og valg av
brukergrensesnittspråk i alle stadier utenom selve fargetilvenningen.
Nettleserspråket foreslås automatisk. Under forsøket forblir **språket for
ordpar og skåring fast** selv om du endrer språket i grensesnittet.

**Viktig:** Seks komplette, kontrollerbare studiespråk støttes. Les
[docs/I18N.md](docs/I18N.md) for hvorfor ubegrenset automatisk oversettelse
ikke kan brukes som validerte forskningsdata. Se [docs/DESIGN.md](docs/DESIGN.md)
for designkriterier og [docs/SECURITY.md](docs/SECURITY.md) for trusselmodell,
Cloudflare Tunnel, opprinnelsesbeskyttelse og håndtering av studiedata.

En Raspberry Pi 3 skal **bare kjøre den ferdigbygde FastAPI/SQLite-serveren**,
ikke Node, Vite eller TypeScript-kompilatoren. Bygg frontend på din PC eller i
GitHub Actions og distribuer `frontend/dist` sammen med backend. Docker Compose
binder tjenesten til `127.0.0.1`, bruker én prosess, read-only-filsystem og
begrenset minne. Fysiske Pi 3-ytelsestester gjenstår.

Tester:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
cd ../frontend
npm install
npm run test:timing
npm run test:locale
npm run build
```

`python scripts/ui_smoke.py` kjører en full Chromium-test med en midlertidig
SQLite-database på fire skjermstørrelser, men krever at Playwright/Chromium er
installert. GitHub Actions gjør dette automatisk. Ingen automatiserte tester
kan erstatte en ekte mobil- og Raspberry Pi 3-test.


### Kontrollert i CI for versjon 2.2

GitHub Actions bygger TypeScript/Vite og kjører backend-tester, nedtellingstester,
språktester og ekte Chromium-integrasjonstest på **320×640, 390×844,
768×1024 og 1280×850**. Nettlesertesten kontrollerer hele første runde,
inkludert at svarskjermen ikke forsvinner for tidlig, at et svar lagres, og
at siden ikke har horisontal overflyt på teststørrelsene. Testsuiten bruker
midlertidig SQLite-database og endrer ikke ekte deltakerdata.

Både Cloudflare-konfigurasjon og skikkelig belastning på en **fysisk Raspberry
Pi 3** må fortsatt verifiseres på den faktiske maskinen. Bygg og testing
garanterer ikke at alle nettlesere, operativsystemer og skjermstørrelser er
feilfrie, eller at løsningen er immune mot angrep.
