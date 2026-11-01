# Hukommelse LM — pilotversjon 2.5

En responsiv React/TypeScript-frontend med FastAPI og SQLite for et anonymt, fjernbasert pilotforsøk. **Gjeldende forskningsspørsmål:** Påvirker **oransje, blå eller nøytral grå skjermbakgrunn** hvor godt deltakerne husker nylig lærte assosiasjoner mellom pseudord og objekter?

[Les den gjeldende forsøksprotokollen](docs/PROTOCOL_V24.md). Tidligere [protokoll 2.3](docs/PROTOCOL_V23.md) og [eldre prosjektnotater](docs/PROTOCOL.md) er arkivert og skal ikke brukes som beskrivelse av den nye datainnsamlingen.

## Fargebetingelser i 2.5

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

Hver deltaker får individuell, lagret stokking. Etter alle tre runder kan deltakeren se svarene sine, fasiten og regneoppgavetotalene. Fasit deles aldri ut før hele forsøket er fullført. 12 studiespråk er støttet for ordlistene; flere av de siste seks språkene bruker fremdeles engelske grensesnitttekster og trenger språklig pilotkontroll.

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
* Nye deltakere merkes `protocol_version = 2.5`. Deltakerøkter fra 2.0–2.4 er **ikke** gyldige i den nye protokollen, men tidligere resultater beholdes i databasen. Nye testdeltakere må registrere seg på nytt.
* `python backend/analyze_cli.py` viser kun resultater for den aktive protokollen. `python backend/export_cli.py` kan eksportere alle historiske protokoller med versjonsmerking; analyser dem separat.
* Deltakerøkt krever både tilfeldig deltaker-ID og eget hemmelig token. API-et har vert-/origin-sjekk, begrensede forespørselsstørrelser og sikkerhetsoverskrifter, men dette erstatter **ikke** sikker produksjonsdrift.
* Bruk HTTPS via Cloudflare Tunnel med ingen direkte tilgang til origin, egnet rate limiting, sikker administratortilgang og oppdaterte avhengigheter. Se [sikkerhetsveiledningen](docs/SECURITY.md) og [språkstøtte](docs/I18N.md).
* Korrigeringsdata og brukeropplevelse må pilottestes før en vitenskapelig konklusjon trekkes. Ikke kombiner skår fra ulike protokollversjoner.

## Endring i 2.5: stimulus og svarfrist

Læringsskjermen, regneoppgavene og svarfeltene bruker nå **nøyaktig samme CSS-bakgrunnsfarge** som omkringliggende viewport. Kortet har bare en mørk, transparent kantlinje. Dette gir mer konsekvent eksponering for fargebetingelsen, men er en vesentlig endring i forsøksstimulus: resultater fra 2.4 må ikke slås sammen med 2.5.

Etter 120 s låses svaret klienten og automatisk sending starter. Nettverksfeil viser en knapp som sender **de allerede låste svarene** på nytt, ikke flere skrivesekunder. Serveren tidsstempler mottak og merker for sent mottatte svar. Analysekommandoen ekskluderer nå forsinkede innsendinger fra hovedgjennomsnittet og rapporterer antallet.
