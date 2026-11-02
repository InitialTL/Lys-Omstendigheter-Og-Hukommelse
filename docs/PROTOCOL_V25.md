# Hukommelse LM — protokoll 2.5 (pilot)

Basert på [2.4](PROTOCOL_V24.md), med uforandrede fargeverdier, ordlister, sekvensbalansering og tidsintervaller.

## Enhetlig fargeeksponering

ORANGE `#F0A34B`, BLUE `#8AB7EA` og NEUTRAL `#B3B3B3` brukes nå som **identisk bakgrunn** for viewport, innholdskort, ordpar, matteøvelse og svarfeltene. Innholdet avgrenses av transparente mørke skillelinjer uten å endre bakgrunnsfargen. Kontraststerk, mørk tekst beholdes på alle tre betingelser. Tilvenningsskjermen viser fortsatt bare farge og klokke.

Tidligere versjon 2.4 hadde en hvit/ferskenfarget overflate rundt testinnholdet; det kan ha utvannet forskjellen i lys-/fargeeksponering. Den nye flaten kan endre selve stimuluseffekten. Resultater **må ikke samles på tvers av 2.4 og 2.5**. Dette er fremdeles ikke fysisk målt luminans eller kontrollert kelvin.

## Tidsgrenser

60 s tilvenning; 75 s læring; 30 s distraksjon; 120 s svar. Ved tidsutløp låses svarene og klienten forsøker å sende. Ved nettverksbrudd beholdes utløps-snapshot og kan sendes igjen, men ingen nye svar kan skrives. Serverens `submitted_late` settes etter en toleranse på fem sekunder; slike runder må vurderes separat/ekskluderes i forhåndsbestemt analyseplan. Klienttiden er ikke en verifisert svarfristsmåling.

## Pilotkontroll

Gjennomfør nettlesertest ved alle tre farger og flere enheter. Sjekk at beregnet `background-color` for `.ambient`, `.study-card`, ordpar og inputfelt er identisk. Verifiser automatisk sending ved tidsutløp og omstart uten tap av resultater. Kontroller at tilpasset lysstyrke holdes konstant og at grensesnittet er lesbart.
