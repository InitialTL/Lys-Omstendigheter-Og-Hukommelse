# Hukommelse LM — pilotprotokoll 2.7 · programvare 2.7.3


## Tilgjengelighet på mobil og språkvalg

Nettleserens foretrukne språk (`navigator.languages`) foreslås automatisk ved første besøk, uten IP-geolokalisering eller ekstern tjeneste. Deltakeren kan enkelt endre språk før registrering. Valgt testspråk lagres sammen med studiesesjonen for korrekt skåring. Et manuelt valgt språk huskes lokalt i nettleseren.

Kalibreringen ber ikke om operativsystem. Den viser veiledende lysstyrkeråd fra lokale nettlesersignaler og har egne tips for eksterne skjermer. Signalet kan være feil og sendes **ikke** til backend. Skjermen tilpasses responsivt, og fullskjermknappen vises bare i nettlesere som støtter funksjonen. Disse UI-endringene endrer **ikke** forskningsprotokoll 2.7.

## Host the research site without your own computer

For a low-maintenance public pilot, use **Railway Hobby** with a `/data` persistent
volume (approximately $5/month minimum). For the lowest running cost, the same
Dockerfile supports **Fly.io** with one 512 MB Machine and a 1 GB volume
(typically about $3.50–$5+ per month). Both include HTTPS hostnames; no
Cloudflare Tunnel is required. **Read [the complete Railway and Fly.io setup
guide](docs/HOSTING.md) before deploying.**

The hosting update retains experimental protocol 2.7. The application refuses
to start on supported managed platforms if `/data` is not a mounted volume.
When launched with elevated permission only to initialize root-owned storage,
it then runs the application as non-root UID 10001.

En responsiv React/TypeScript-frontend med FastAPI og SQLite for et anonymt, fjernbasert pilotforsøk. **Gjeldende forskningsspørsmål:** Påvirker **oransje, blå eller nøytral grå skjermbakgrunn** hvor godt deltakerne husker nylig lærte assosiasjoner mellom pseudord og objekter?

[Les den gjeldende forsøksprotokollen](docs/PROTOCOL_V27.md). Tidligere [protokoll 2.6](docs/PROTOCOL_V26.md), [protokoll 2.3](docs/PROTOCOL_V23.md) og [eldre prosjektnotater](docs/PROTOCOL.md) er arkivert og skal ikke brukes som beskrivelse av den nye datainnsamlingen.

## Fargebetingelser i 2.7

| Betingelse | sRGB-farge | Beregnet relativ luminans |
| --- | --- | ---: |
| ORANGE | `#F0A34B` | 0,4523 |
| BLUE | `#8AB7EA` | 0,4521 |
| NEUTRAL | `#B3B3B3` | 0,4508 |

Betingelsene har nesten samme **beregnede relative sRGB-luminans**, men det er **ikke fysisk målt skjermlys**. Ulike skjermer, romlys, lysstyrke og ulik opplevd fargelyshet kan fortsatt påvirke resultatene. Testen undersøker ikke Kelvin, lux eller døgnrytme.

Hver deltaker gjennomfører alle tre betingelsene, motbalansert mellom gruppene A/B/C. I hver runde:

1. 60 sekunders fargetilvenning med kun farge og nedtelling.
2. 75 sekunder til å memorere 8 pseudord–objektpar.
3. 30 sekunder med enkle regneoppgaver.
4. Opptil 120 sekunder til å skrive inn de huskede objektene i ny, tilfeldig rekkefølge.

Hver deltaker får individuell, lagret stokking. Etter alle tre runder kan deltakeren frivillig svare på to nøytrale spørsmål om opplevd effekt før vedkommende ser svarene sine, fasiten og regneoppgavetotalene. Fasit deles aldri ut før hele forsøket er fullført. 12 studiespråk er støttet for ordlistene; flere av de siste seks språkene bruker fremdeles engelske grensesnitttekster og trenger språklig pilotkontroll.

**Nytt i 2.7:** Regneoppgavenes spørsmålstegn har samme dempede farge som resten av likningen. De tre hukommelsesrundene er lagret på serveren før de valgfrie spørsmålene vises. Skjemaet har nå en serverkontrollert svarfrist på 90 sekunder, og resultatene vises automatisk etter utløpet. Manglende spørreskjemasvar skilles fra bevisst «Hopp over». Se [protokoll 2.7](docs/PROTOCOL_V27.md). Tidligere resultater beholdes med sin opprinnelige versjonsmerking. Dette er ikke en måling av placeboeffekt.

## Driftssikker oppdatering i programvare 2.7.1

Denne rettinga **endrar ikkje forsøksstimuli eller forsøksprotokoll 2.7**. Deltakarar i protokoll 2.7 kan halde fram med den same sikre økta. Alle åtte svarfelta blir lagra i nettlesaren og blir i tillegg sende til ein autentisert, versjonert SQLite-sikkerheitskopi under svarfasen (med kort utsetjing for å spare Raspberry Pi-ressursar). Ved lukking av fana prøver klienten å sende siste kopi med `keepalive`.

* Når ein deltakar kjem att før fristen, blir siste godtekne kopi frå serveren gjenoppretta, eller ein nyare lokal kopi når denne finst.
* **Etter svarfristen er det berre svar som allereie var lagra på serveren før fristen, som kan telje.** Ein innsending etter fristen blir merka `submitted_late=1` og utelaten frå hovudanalysen.
* Ufullførte, serverlagra utkast blir verande i `study_drafts` og kan eksporterast separat via autorisert `GET /api/admin/drafts.csv`. Dei blir **ikkje** blanda inn i skåra svar eller markerte som ferdige deltakarar.
* Ved tilbaketrekking av samtykke blir også utkast sletta.
* Ei nettverksfråkopling før **noka** sikkerheitskopi er motteken kan ikkje garanterast løyst av ei nettside. Lokale svar blir forsøkt gjenoppretta på same eining.

Sjå [stegvis produksjonsveiledning](docs/DEPLOYMENT.md) med Cloudflare Tunnel, Raspberry Pi, automatisk oppstart, backups og sikkerheitskontrollar. For trygg online SQLite-backup: `python scripts/backup_sqlite.py /sikker/mappe/for/backups` og kopiér backupfilene kryptert til ei anna eining. **Ikkje ta berre ei filkopi av ein aktiv WAL-database.**

## Utvikling lokalt

Krever Python 3.10+ og Node.js 22.12+ (eller kompatibel Node 20.19+). Kjør i **to terminaler** fra prosjektets rotmappe:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Åpne `http://127.0.0.1:5173`. Vite sender `/api` til FastAPI. API-helse: `http://127.0.0.1:8000/api/health`. Bruk ikke `--reload` ved offentlig publisering.

Produksjonsbygg:

```powershell
cd frontend
npm install
npm run build
cd ../backend
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
```

Da leverer FastAPI også de kompilerte frontendfilene på `http://127.0.0.1:8000`. På Raspberry Pi 3 skal **ikke** Vite eller Node kjøre i produksjon; bygg frontend på en kraftigere maskin først.

## Tester

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

```powershell
cd frontend
npm install
npm run test:timing
npm run test:locale
npm run build
```

GitHub Actions kjører også en tre-runders ende-til-ende-test i Chromium på flere skjermstørrelser. Testene bruker en **midlertidig database**, ikke reelle deltakerdata.

## Personvern, eldre protokoller og drift

* `backend/results.db` inneholder deltakerdata og skal **aldri** legges i Git eller deles. Ta sikkerhetskopi før oppdateringer. SQLite WAL-filer kan også eksistere mens serveren kjører.
* Nye deltakere merkes `protocol_version = 2.7`. Deltakerøkter fra 2.0–2.6 er **ikke** gyldige i den nye protokollen, men tidligere resultater beholdes i databasen. Nye testdeltakere må registrere seg på nytt.
* `python backend/analyze_cli.py` viser kun resultater for den aktive protokollen. `python backend/export_perceptions_cli.py` eksporterer frivillige svar separat. `python backend/export_cli.py` kan eksportere alle historiske protokoller med versjonsmerking; analyser dem separat.
* Deltakerøkt krever både tilfeldig deltaker-ID og eget hemmelig token. API-et har vert-/origin-sjekk, begrensede forespørselsstørrelser og sikkerhetsoverskrifter, men dette erstatter **ikke** sikker produksjonsdrift.
* Bruk HTTPS via Cloudflare Tunnel med ingen direkte tilgang til origin, egnet rate limiting, sikker administratortilgang og oppdaterte avhengigheter. Se [sikkerhetsveiledningen](docs/SECURITY.md) og [språkstøtte](docs/I18N.md).
* Korrigeringsdata og brukeropplevelse må pilottestes før en vitenskapelig konklusjon trekkes. Ikke kombiner skår fra ulike protokollversjoner.

## Endring i 2.5: stimulus og svarfrist (historisk)

Læringsskjermen, regneoppgavene og svarfeltene bruker nå **nøyaktig samme CSS-bakgrunnsfarge** som omkringliggende viewport. Kortet har bare en mørk, transparent kantlinje. Dette gir mer konsekvent eksponering for fargebetingelsen, men er en vesentlig endring i forsøksstimulus: resultater fra 2.4 må ikke slås sammen med 2.5.

Etter 120 s låses svaret klienten og automatisk sending starter. Nettverksfeil viser en knapp som sender **de allerede låste svarene** på nytt, ikke flere skrivesekunder. Serveren tidsstempler mottak og merker for sent mottatte svar. Analysekommandoen ekskluderer nå forsinkede innsendinger fra hovedgjennomsnittet og rapporterer antallet.
