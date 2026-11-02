# Forsøksprotokoll 2.6 – grensesnitt, fargetransisjon og etterspørsmål

**Hovedmål:** Samanlikne hukommelse for åtte pseudord–objektassosiasjonar under tre sRGB-bakgrunnsfargar: oransje `#F0A34B`, blå `#8AB7EA` og grå `#B3B3B3`. Dei er omtrent like i *berekna relativ sRGB-luminans*, ikkje faktisk målt lysstyrke. Ulike skjermar og lysforhold er feilkjelder.

## Endringar frå 2.5

1. Studiegrensesnittet nyttar ein samanhengande bakgrunnsflate. Tekst, knappar og inndatafelt har ikkje kvite bakgrunnar; tekst og kantlinjer har tilstrekkeleg kontrast.
2. Overgang mellom bakgrunnsfargane skjer på 1,85 sekund gjennom CSS. Første overgang startar når deltakaren går frå kalibrering til **oppsett**, altså før serveren startar tidsstyrt tilvenning. Vidare fargeskifte skjer under oppsettet til neste runde. Skjermens innstillingar skal vere uendra. Ved ønske om redusert rørsle blir animasjonen deaktivert.
3. Etter at tredje runde er levert, får deltakaren to **frivillige, nøytralt formulerte spørsmål**, før vedkomande får sjå fasit og resultat:
    - Opplevde deltakaren ulik lettheit i å hugse ord mellom fargane? Ingen / liten / tydeleg / stor forskjell / usikker.
    - Kva farge kjendest enklast? Oransje / blå / grå / omtrent likt / usikker.
   Deltakaren kan hoppe over begge. Eit svar kan berre registrerast éin gong per deltakar. Dataa blir lagra i eiga tabell `study_perceptions`.
4. Alle gamle resultat blir verande i databasen under si opphavlege protokollmerking. Nye deltakarar er merkte med `2.6`. Nye økter må starte frå registrering.

## Tidsstyrt protokoll (uendra)

- 60 s tilvenning med berre farge og tid.
- 75 s innlæring av åtte pseudord–objektpar, i individuell tilfeldig rekkefølgje.
- 30 s distraksjonsrekning.
- Maksimalt 120 s fri gjenkalling i annleis tilfeldig rekkefølgje; utløp låser svar.
- Tre motbalanserte runder, og fasit berre etter at alle runder er leverte.

## Analyse

Objektiv hukommelsesskår og frivillig, retrospektiv oppleving er **forskjellige variablar**. Den subjektive vurderinga kan brukast i ei utforskande drøfting av forventning og oppleving; svara etablerer ikkje placeboeffekt eller årsak. Rapporter svarprosent og `SKIPPED` separat, og unngå å samanlikne uvaliderte språk som om vanskegraden er identisk.

Analyse av hovudutfall skal ikkje blande skår frå 2.6 med 2.5 eller tidlegare utgåver. Seinare overgangar er ein protokollendring, og dei bør ikkje justerast vidare under hovuddatainnsamlinga.

## Eksport

- `python backend/export_cli.py` eksporterer objektive historiske resultat med protokollmerking.
- `python backend/export_perceptions_cli.py` eksporterer frivillige svar separat.
- API-eksport via `/api/admin/perceptions.csv` krev `STUDY_ADMIN_TOKEN` som all annan administrativ eksport.
- Tilbaketrekking av samtykke slettar begge datasetta for den aktuelle deltakar-ID-en.
