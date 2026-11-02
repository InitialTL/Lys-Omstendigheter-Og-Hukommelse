> **ARKIVERT TIDLIGERE PROTOKOLL.** Gjeldende oppsett er [protokoll 2.4](PROTOCOL_V24.md) med oransje, blå og nøytral grå.

# Foreløpig forsøksprotokoll — Hukommelse LM

**Status:** Pilotprotokoll, må kvalitetssikres før datainnsamling. V2.1, 31. oktober 2026.

## Forskingsspørsmål

> Hvordan påvirker varme, kalde og nesten svarte skjermbakgrunner læring og fri gjenhenting av nye ordassosiasjoner når deltakerne gjennomfører testen hjemme?

Ikke beskriv studien som en kontrollert sammenlikning av fargetemperatur i kelvin. Et CSS-felt med bestemte sRGB-verdier kan **ikke** levere en spesifisert målt fargetemperatur til øyet.

## Uavhengig variabel og nivåer

| Betingelse | CSS-bakgrunn | Omtrentlig sRGB-relativ luminans* |
|---|---|---:|
| WARM | `#D9AA91` | 0,4555 |
| COOL | `#9BB6E4` | 0,4603 |
| DARK | `#080B11` | 0,0033 |

*Beregnet fra sRGB-transferfunksjonen og relative kanalvekter; **ikke** målt fysisk luminans, lux eller kelvin. Visuell effekt avhenger av skjermkalibrering, lysstyrke, omgivelseslys og paneltype. Fargeutformingen kan fungere som deskriptive stimuli, men må testes før forskningspåstander.

I alle tre betingelser er læringsinnholdet plassert i det samme nøytrale, mørke kortet, med identiske tekstfarger og størrelser. Dette minimerer variasjon i lesbarhet, men gjør ikke totalt lysnivå likt.

## Design og randomisering

Et **innenpersonsdesign**: hver deltaker fullfører tre runder og møter alle tre betingelser. Deltakerne fordeles så jevnt som mulig mellom tre sekvenser:

- Gruppe A: WARM → COOL → DARK.
- Gruppe B: COOL → DARK → WARM.
- Gruppe C: DARK → WARM → COOL.

Dette balanserer posisjon (første, andre, tredje) for lysbetingelsene. I tillegg tildeles hver gruppe løpende én av seks permutasjoner av de tre ordlistene. Det gjør ordlistetildelingen uavhengig av den faste lyssekvensen over tid. Backend er autoritet for sekvens og fasit.

## Prosedyre per deltaker

1. Les informasjon og avgi frivillig samtykke. Oppgi språk, aldersgruppe og eventuelt kjønn.
2. Følg kalibreringssjekklisten: mørkt rom, ingen musikk eller varslinger, fast skjermlysstyrke og avskrudd dynamisk fargejustering. Velg operativsystem for innstillingsveiledning. Juster slik at et lysegrått symbol på hvitt og mørkegrått symbol på svart er så vidt synlige. Denne testen er subjektiv og ikke et lux-/Kelvin-instrument. Bruk fullskjerm der nettleseren tillater det.
3. 60 sekunder tilvenning til skjermbakgrunn med **bare fargen og en klokke**, uten et stort tekstkort.
4. 60 sekunder memorering av 10 faste pseudord knyttet til 10 vanlige objekter.
5. 30 sekunder hoderegning for å begrense aktiv repetisjon.
6. Fri gjenhenting: skriv objektnavn for de ti kunstige ordene (maks 120 sekunder, automatisk innsending).
7. Gjenta 3–6 med ny ordliste og en ny lysbetingelse.

### Målinger

Primært utfall: antall korrekt gjenhentede objektbetegnelser (0–10) per runde. Svarene skåres mot forhåndsdefinerte språkspesifikke varianter, med enkel normalisering av mellomrom, store/små bokstaver og diakritiske tegn. Analyser først **totalscore**, ikke enkeltsvarsdata som om de var uavhengige deltakere.

Sekundært: antall ganger fanen ble skjult under testen, total gjenhentingstid, og andel manglende/for sene svar. Disse er kvalitetsindikatorer, ikke objektiv registrering av juks eller lysforhold.

### Statistikk

For en registrert fullverdig studie: vurder en gjentatte-målinger-modell med deltaker som tilfeldig effekt og betingelse, posisjon og ordliste som forklaringsvariabler. Et enklere pilotoppsett kan vise deskriptiv statistikk for alle tre forhold med usikkerhetsintervaller. Unngå tre uavhengige t-tester på de 300 observasjonene, siden tre runder tilhører samme person. Lag en forhåndsregistrert analyseplan, inkl. håndtering av ufullstendige og for sent innsendte runder.

### Mulige feilkilder

- **Skjermvariasjon**: fysisk spektrum, lysstyrke og fargeprofil varierer mellom enheter.
- **Luminanskonfundering**: DARK har mye lavere lysmengde enn WARM/COOL; isolerer ikke fargeeffekten alene.
- **Tids- og øvingseffekter**: deltakere lærer testformatet gjennom rundene, eller blir slitne.
- **Oppgavevanskelighet**: 30 kunstige ordpar er ikke kalibrert; de tre listene kan være ulike i vanskelighetsgrad.
- **Språk og tidligere erfaring**: morsmål, ordforråd og evne til assosiasjonslæring varierer.
- **Døgnrytme**: tidspunkt for deltakelse, søvn og lys før testen kan påvirke årvåkenhet.
- **Selvrapportering**: kalibreringsinstruksene verifiserer ikke faktisk romlys eller skjerminnstillinger.

## Evolusjon, dag og natt i diskusjonen

Døgnrytmen hos mennesker har utviklet seg under regelmessige dag/natt-sykluser, og lys er et viktig signal i reguleringen av den biologiske klokken. Lys kan også påvirke våkenhet. Men et kort fjernforsøk som sammenlikner CSS-bakgrunner kan **ikke** bevise at forskjeller i læring skyldes slike evolusjonære mekanismer, og kan ikke skille melanopsinrelatert stimulering fra visuell, kognitiv eller forventningsrelatert påvirkning.

Skriv derfor en forskningsdiskusjon som **vurderer mulige mekanismer og alternative forklaringer**, ikke som hevder at evolusjon er bevist av dataene.

## Etikk og rekruttering

Ikke bruk spørreskjema for navn, fødselsdato, e-post eller presis adresse. Kun aldersgruppe og valgfritt kjønn lagres, sammen med studiesvar og en pseudonym deltaker-ID. Samtykket registreres. Deltakeren kan trekke samtykket tilbake ved å slette egne data gjennom nettsiden; dersom lagringen er flyttet eller eksportert, må forskningsansvarlig også håndtere sletting i kopier iht. oppgitt personvernerklæring.

**Viktig:** Før du rekrutterer mindreårige gjennom skolen eller på sosiale medier, må du avklare behandlingsgrunnlag, nødvendige samtykker, informasjonsskriv, sikker lagring, lagringstid, eventuelle meldekrav og prosjektansvar hos skole/veileder. Appen løser ikke dette juridisk eller organisatorisk.

## Pilot og beslutningskriterier

Før offentlig rekruttering: la et lite antall frivillige teste nettsiden og rapportere om 60 sekunder er for mye/lite, om noen lister er betydelig lettere enn andre, om mørk bakgrunn gjør lesingen vanskeligere, og om poengfordelingen har gulv- eller takeffekt. Frys deretter metode, fasit og fargedefinisjoner før full datainnsamling. Om du endrer lister eller metode, ikke slå sammen nye og gamle resultater uten en forhåndsdefinert strategi.

## Endringer fra versjon 2.0 til 2.1

- 60 sekunder tilvenning med rent fargefelt, mot 15 sekunder tidligere. Selve timeren styres av serveren.
- Nye pseudord. De gamle og de nye resultatene **må ikke kombineres som om det var samme forsøk**.
- Seks språk (nb/en/sv/de/fr/es) med språkspesifikk skåring. Sammenligning på tvers av språk krever å undersøke måleinvarians og ulike responsterskler.
- Separat tilfeldig tilgangstoken kreves for alle deltakerendepunkter. Hash lagres i SQLite. Dette begrenser innsyn, men bruk også TLS, sikker hosting og moderering ved offentlig datainnsamling.
- Studiens fullskjermfunksjon er valgfri og kan være utilgjengelig på enkelte mobile nettlesere.
