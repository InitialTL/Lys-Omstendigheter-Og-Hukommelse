# Hukommelse LM · protokoll 2.7

Formålet og dei tre bakgrunnsfargane er uendra frå 2.6. Ordpar, læring, rekkjefølgje og tidsbruk i sjølve minnetesten er uendra.

## Rett etter den siste minnetesten

Kvar av dei tre hukommelsesrundane blir lagra som ei eiga transaksjon i SQLite ved levering av svar. Den siste runden blir lagra **før** skjemaet om opplevd effekt blir vist. At nokon lukkar nettlesaren i skjemaet, påverkar ikkje dei tre lagra resultata.

Deltakaren har maksimalt 90 sekund til å svare på dei to frivillige persepsjonsspørsmåla. Fristen er berekna frå tidsstempelet for lagringa av den tredje runden og blir kontrollert av tenaren. Etter fristen kan deltakaren sjå fasit og resultat utan å ha svart på skjemaet. Der eksisterer då **ikkje** ei persepsjonsregistrering, noko som blir skilt frå aktivt val av `SKIPPED`. Bruk manglande svar som eigen kategori ved analysen, ikkje som 'ingen effekt'. Eit skjema som er påbegynt, men aldri sendt inn, blir ikkje lagra.

Dersom nettverket fell bort, kan deltakaren vende tilbake seinare med den same økta og sjå resultatet. Ved avbrot *før* ei hukommelsesrunde er levert, er ikkje dei uleverte svara garantert lagra på tenaren. Delvis gjennomførte rundar finst framleis i `study_results` og kan analyserast som fråfall, ikkje som ferdige studiar.

`study_results` og `study_perceptions` er framleis separate tabellar. Det blir ikkje gjort automatiske skjulte skriveoperasjonar for persepsjonsskjemaet. Inga kontinuerleg serveroppgåve eller ekstra prosess er nødvendig.

Den siste ordoppgåva og spørjeteiknet i regneoppgåvene har elles fått ein meir einsarta, dempa tekststil, utan endring i innhaldet i regneoppgåvene.

## Merknad om brukargrensesnitt frå versjon 2.7.5

Tilvenningsfasen varer framleis 60 sekund rekna på tenaren, med uendra bakgrunnsfarge.
Frå programvareversjon 2.7.5 er det òg vist ei kort forklaring og ein diskret
«Tilbake til rundestart»-kontroll i same fargeplan. Kontrollens totrinnsstadfesting
hindrar utilsikta avbrot. Avbrot er berre lov **før** innlæringa har byrja;
rundestarten blir då sletta transaksjonelt og neste start får 60 nye sekund.
Ingen ferdige resultat, spørjeskjemasvar eller ordpar blir sletta eller endra.

Dette er ei **endring av det visuelle grensesnittet under stimulustida** i
forhold til den tidlegare formuleringa «berre farge og nedtelling». Sjølv om
teksten er den same i alle tre fargevilkår, kan han påverke deltakarens
oppmerksamheit. Noter distribusjonsdato og skil om nødvendig deltakarar etter
programvareversjon i metode og analyse. Ikkje bland umerka grupper frå før og
etter UI-endringa ved strenge samanlikningar.

## Personvernretting i programvare 2.7.6

Tilbaketrekking av samtykke er tilgjengeleg i alle forsøksfasar. Den tidlegare
nettlesardialogen er bytt med ei tydeleg stadfesting inne på nettsida.
Deltakaren blir send til startsida berre etter at tenaren har stadfesta
sletting av data. Ved feil blir økta halden ved lag og feilen vist.
Ingen fargebetingelsar, tidsfristar eller skåringsreglar er endra.

## Ny instruks om miljøkrav, 2. november 2026

Deltakarane må no bruke **eit heilt mørkt rom**, med testskjermen som
einaste lyskjelda. Den tidlegare instruksen tillét svakt lys. Dette
er ei metodisk endring i miljøkrava, sjølv om stimulusfargar, tider og
skåringsreglar er uendra. Dokumenter implementeringsdato og
skil om nødvendig deltakarkohortar før og etter innstramminga.
Mørkret kan ikkje verifiserast via nettlesaren.

Startsida kan vise anonymt tal på deltakarar med tre fullførte rundar.
Resultatsida kan dele offentleg studielenkje utan deltakaropplysningar.
