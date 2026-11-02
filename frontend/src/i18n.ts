/** Curated interface languages. Unknown keys fall back to English deliberately. */
export const LANGUAGE_NAMES = {
  nb: 'Norsk', en: 'English', sv: 'Svenska', de: 'Deutsch', fr: 'Français', es: 'Español',
  it: 'Italiano', pt: 'Português', nl: 'Nederlands', da: 'Dansk', pl: 'Polski', ro: 'Română',
} as const;
export type Language = keyof typeof LANGUAGE_NAMES;

/** A vetted study language is required for scoring. The UI may be switched
 * independently without changing the language used to grade the word pairs. */
export function detectBrowserLanguage(languages: readonly string[] = ['en']): Language {
  for (const locale of languages) {
    const primary = locale.toLowerCase().split(/[-_]/)[0];
    const code = primary === 'no' || primary === 'nn' ? 'nb' : primary;
    if (Object.prototype.hasOwnProperty.call(LANGUAGE_NAMES, code)) return code as Language;
  }
  return 'en';
}

/** Future vetted RTL packs use the same layout without CSS rewrites. */
export function directionForLanguage(locale: string): 'rtl' | 'ltr' {
  return /^(ar|he|fa|ur|ps|dv|ku)(-|$)/i.test(locale) ? 'rtl' : 'ltr';
}


// Each entry has Swedish, German, French and Spanish versions of the English key.
const MESSAGES: Record<string, [string, string, string, string]> = {
  'Research study': ['Forskningsstudie','Forschungsstudie','Étude scientifique','Estudio científico'],
  'A DIGITAL RESEARCH EXPERIMENT': ['ETT DIGITALT FORSKNINGSEXPERIMENT','EIN DIGITALES FORSCHUNGSEXPERIMENT','UNE EXPÉRIENCE SCIENTIFIQUE EN LIGNE','UN EXPERIMENTO CIENTÍFICO DIGITAL'],
  'Can the colors around us': ['Kan färgerna omkring oss','Können die Farben um uns herum','Les couleurs autour de nous peuvent-elles','¿Pueden los colores a nuestro alrededor'],
  'affect our memory?': ['påverka vårt minne?','unser Gedächtnis beeinflussen?','influencer notre mémoire ?','afectar nuestra memoria?'],
  'Join a short research study comparing orange, blue and gray screen backgrounds to see whether background color affects word memory.':
    ['Delta i en studie som jämför orange, blå och grå skärmbakgrunder och undersöker om färgen påverkar ordminnet.', 'Nimm an einer Studie teil, die orange, blaue und graue Bildschirmhintergründe vergleicht und untersucht, ob die Farbe das Wortgedächtnis beeinflusst.', 'Participez à une étude comparant des fonds d’écran orange, bleu et gris pour examiner leur effet sur la mémoire des mots.', 'Participa en un estudio que compara fondos de pantalla naranja, azul y gris para examinar su efecto en la memoria de palabras.'],
  'minutes': ['minuter','Minuten','minutes','minutos'],
  'rounds': ['omgångar','Runden','tours','rondas'],
  'No names': ['Inga namn','Keine Namen','Aucun nom','Sin nombres'],
  'recorded': ['registreras','gespeichert','enregistré','registrados'],
  'HOW IT WORKS': ['SÅ FUNGERAR DET','SO FUNKTIONIERT ES','DÉROULEMENT','CÓMO FUNCIONA'],
  'Prepare your screen': ['Förbered din skärm','Bildschirm vorbereiten','Préparer votre écran','Prepara tu pantalla'],
  'A simple checklist before beginning': ['En enkel checklista före start','Eine kurze Checkliste vor dem Start','Quelques vérifications avant de commencer','Una lista breve antes de empezar'],
  'Learn 8 word pairs': ['Lär dig 8 ordpar','8 Wortpaare lernen','Apprendre 8 paires de mots','Aprende 8 pares de palabras'],
  'You have 75 seconds to memorize': ['Du har 75 sekunder på dig','Du hast 75 Sekunden Zeit','Vous avez 75 secondes','Tienes 75 segundos'],
  'Test your memory': ['Testa ditt minne','Gedächtnis testen','Tester votre mémoire','Pon a prueba tu memoria'],
  'A short distraction before you recall the answers': ['En kort distraktion före minnestestet','Kurze Ablenkung vor dem Erinnerungstest','Une courte distraction avant le rappel','Una breve distracción antes de recordar'],
  'PARTICIPATE': ['DELTA','TEILNEHMEN','PARTICIPER','PARTICIPA'],
  'Get started': ['Kom igång','Los geht’s','C’est parti','Empezar'],
  'Answer a few brief questions before starting. You may withdraw consent and delete your data at any time.':
    ['Svara på några frågor först. Du kan återkalla ditt samtycke och radera dina uppgifter när som helst.', 'Beantworte zuerst einige Fragen. Du kannst deine Einwilligung jederzeit widerrufen und deine Daten löschen.', 'Répondez d’abord à quelques questions. Vous pouvez retirer votre consentement et supprimer vos données à tout moment.', 'Responde unas preguntas primero. Puedes retirar tu consentimiento y eliminar tus datos en cualquier momento.'],
  'Language': ['Språk','Sprache','Langue','Idioma'],
  'Choose your study language': ['Välj språk för studien','Sprache für die Studie wählen','Choisissez la langue de l’étude','Elige el idioma del estudio'],
  'Suggested from your browser language, without an IP lookup. You can change it before starting.': ['Föreslås från webbläsarens språk utan IP-sökning. Du kan ändra innan du börjar.', 'Vorschlag anhand der Browsersprache, ohne IP-Abfrage. Vor Beginn änderbar.', 'Proposé selon la langue du navigateur, sans rechercher votre IP. Modifiable avant de commencer.', 'Sugerido según el idioma del navegador, sin consultar tu IP. Puedes cambiarlo antes de comenzar.'],
  'HELP FOR YOUR DEVICE': ['HJÄLP FÖR DIN ENHET','HILFE FÜR DEIN GERÄT','AIDE POUR VOTRE APPAREIL','AYUDA PARA TU DISPOSITIVO'],
  'How to adjust brightness': ['Så ändrar du ljusstyrkan','So passt du die Helligkeit an','Comment régler la luminosité','Cómo ajustar el brillo'],
  'Using an external monitor or TV?': ['Använder du extern skärm eller TV?','Externer Monitor oder Fernseher?','Vous utilisez un écran externe ou une TV ?','¿Usas un monitor externo o un televisor?'],
  'Age': ['Ålder','Alter','Âge','Edad'],
  'Prefer not to say': ['Vill inte uppge','Keine Angabe','Préfère ne pas répondre','Prefiero no decirlo'],
  'Gender (optional)': ['Kön (frivilligt)','Geschlecht (optional)','Genre (facultatif)','Género (opcional)'],
  'Woman': ['Kvinna','Frau','Femme','Mujer'], 'Man': ['Man','Mann','Homme','Hombre'],
  'Non-binary': ['Icke-binär','Nichtbinär','Non binaire','No binario'],
  'Other': ['Annat','Andere Angabe','Autre','Otro'],
  'I participate voluntarily and agree that my age range, optional gender, language and test results are stored under a random participant ID for research. No names or email addresses are collected.':
    ['Jag deltar frivilligt och godkänner att åldersgrupp, eventuellt kön, språk och testresultat lagras med ett slumpmässigt deltagar-ID. Inga namn eller e-postadresser samlas in.', 'Ich nehme freiwillig teil und stimme zu, dass Altersgruppe, optionales Geschlecht, Sprache und Ergebnisse unter einer zufälligen Teilnehmer-ID gespeichert werden. Namen und E-Mail-Adressen werden nicht erfasst.', 'Je participe volontairement et accepte que ma tranche d’âge, mon genre éventuel, ma langue et mes résultats soient enregistrés sous un identifiant aléatoire. Aucun nom ni courriel n’est recueilli.', 'Participo voluntariamente y acepto que mi rango de edad, género opcional, idioma y resultados se guarden bajo un identificador aleatorio. No se recogen nombres ni correos electrónicos.'],
  'Under 18: consent requirements must be confirmed with the study organizer.': ['Under 18 år: kontrollera samtyckeskraven med studieansvarig.','Unter 18 Jahren: Einwilligungsregeln mit der Studienleitung klären.','Moins de 18 ans : vérifier les conditions de consentement avec le responsable.','Menores de 18 años: consultar los requisitos de consentimiento con el responsable.'],
  'Registering…': ['Registrerar…','Registrierung…','Inscription…','Registrando…'],
  'Begin experiment': ['Starta experimentet','Experiment starten','Commencer l’expérience','Comenzar el experimento'],
  'Approximately 10–15 minutes': ['Cirka 10–15 minuter','Etwa 10–15 Minuten','Environ 10 à 15 minutes','Aproximadamente 10–15 minutos'],
  'A study of screen color and word memory': ['En studie om skärmfärg och ordminne','Eine Studie zu Bildschirmfarben und Wortgedächtnis','Une étude sur la couleur de l’écran et la mémoire des mots','Un estudio sobre color de pantalla y memoria verbal'],
  'Preparation': ['Förberedelser','Vorbereitung','Préparation','Preparación'],
  'STEP 1 OF 2': ['STEG 1 AV 2','SCHRITT 1 VON 2','ÉTAPE 1 SUR 2','PASO 1 DE 2'],
  'Prepare your screen for the study': ['Förbered skärmen för studien','Bereite deinen Bildschirm für die Studie vor','Préparez votre écran pour l’étude','Prepara tu pantalla para el estudio'],
  'To make results as comparable as possible, keep the same settings throughout all three rounds.':
    ['Behåll samma inställningar under alla tre omgångar för att kunna jämföra resultaten.', 'Behalte für vergleichbare Ergebnisse in allen drei Runden dieselben Einstellungen bei.', 'Pour permettre des comparaisons, gardez les mêmes réglages pendant les trois tours.', 'Para comparar los resultados, mantén la misma configuración durante las tres rondas.'],
  'Use a dark or dimly lit room': ['Sitt i ett mörkt eller svagt upplyst rum','Nutze einen dunklen oder schwach beleuchteten Raum','Installez-vous dans une pièce sombre ou peu éclairée','Usa una habitación oscura o con poca luz'],
  'Keep room lighting unchanged throughout the study.': ['Ändra inte rummets belysning under studien.','Verändere die Raumbeleuchtung während der Studie nicht.','Ne changez pas l’éclairage de la pièce pendant l’étude.','No cambies la iluminación de la habitación durante el estudio.'],
  'Turn off automatic color and brightness': ['Stäng av automatisk färg och ljusstyrka','Automatische Farb- und Helligkeitsanpassung ausschalten','Désactiver les réglages automatiques de couleur et luminosité','Desactiva el color y brillo automáticos'],
  'Disable night mode, True Tone, Night Shift, and automatic brightness.': ['Stäng av nattläge, True Tone, Night Shift och automatisk ljusstyrka.','Nachtmodus, True Tone, Night Shift und automatische Helligkeit ausschalten.','Désactivez le mode nuit, True Tone, Night Shift et la luminosité automatique.','Desactiva modo noche, True Tone, Night Shift y brillo automático.'],
  'Set a fixed screen brightness': ['Välj en fast ljusstyrka','Feste Bildschirmhelligkeit einstellen','Régler une luminosité fixe','Establece un brillo fijo'],
  'Set brightness about halfway on the slider (around 50%), provided text is easy to read. Do not change it between rounds.':
    ['Ställ ljusstyrkan ungefär mitt på reglaget (cirka 50 %) om texten är lättläst. Ändra den inte mellan omgångarna.', 'Stelle die Helligkeit ungefähr auf die Mitte des Reglers (ca. 50 %), sofern der Text gut lesbar bleibt. Zwischen den Runden nicht ändern.', 'Réglez la luminosité environ à mi-course (50 %) si le texte reste lisible. Ne la modifiez pas entre les manches.', 'Ajusta el brillo aproximadamente a la mitad (50 %) si el texto se lee bien. No lo cambies entre rondas.'],
  'Mute music and other audio': ['Stäng av musik och annat ljud','Musik und andere Töne ausschalten','Couper la musique et les autres sons','Silencia la música y otros sonidos'],
  'Turn off music, videos, notifications and headphones with audio during the entire study.':
    ['Stäng av musik, videor, aviseringar och ljud i hörlurar under hela studien.', 'Schalte Musik, Videos, Benachrichtigungen und Kopfhörerton während der gesamten Studie aus.', 'Coupez musique, vidéos, notifications et son des écouteurs pendant toute l’étude.', 'Desactiva música, vídeos, notificaciones y audio de auriculares durante todo el estudio.'],
  'Try fullscreen': ['Aktivera helskärm','Vollbild einschalten','Activer le plein écran','Activar pantalla completa'],
  'Exit fullscreen': ['Lämna helskärm','Vollbild verlassen','Quitter le plein écran','Salir de pantalla completa'],
  'Fullscreen is not supported here. Use the browser’s fullscreen control if available.':
    ['Helskärm stöds inte här. Använd webbläsarens funktion om den finns.', 'Vollbild wird hier nicht unterstützt. Verwende ggf. die Browserfunktion.', 'Le plein écran n’est pas disponible ici. Utilisez l’option du navigateur si possible.', 'La pantalla completa no está disponible aquí. Usa la opción del navegador si existe.'],
  'OPERATING SYSTEM': ['OPERATIVSYSTEM','BETRIEBSSYSTEM','SYSTÈME D’EXPLOITATION','SISTEMA OPERATIVO'],
  'How to change brightness': ['Så ändrar du ljusstyrkan','So änderst du die Helligkeit','Comment régler la luminosité','Cómo cambiar el brillo'],
  'SCREEN CHECK': ['SKÄRMKONTROLL','BILDSCHIRMKONTROLLE','VÉRIFICATION DE L’ÉCRAN','COMPROBACIÓN DE PANTALLA'],
  'Can you distinguish the symbols from their backgrounds?': ['Kan du urskilja symbolerna mot bakgrunderna?', 'Kannst du die Symbole vom Hintergrund unterscheiden?', 'Distinguez-vous les symboles de leur arrière-plan ?', '¿Puedes distinguir los símbolos de sus fondos?'],
  'On many phones, both symbols remain visible at every brightness setting. Do not try to make them disappear: This is only a simple check of low contrast.':
    ['På många mobiler syns båda symbolerna oavsett ljusstyrka. Försök inte få dem att försvinna: detta är bara en enkel kontroll av låg kontrast.', 'Auf vielen Smartphones bleiben beide Symbole bei jeder Helligkeit sichtbar. Versuche nicht, sie verschwinden zu lassen: Dies ist nur eine einfache Kontrastkontrolle.', 'Sur de nombreux téléphones, les deux symboles restent visibles quelle que soit la luminosité. N’essayez pas de les faire disparaître : il s’agit seulement d’un contrôle du faible contraste.', 'En muchos móviles, ambos símbolos siguen visibles con cualquier brillo. No intentes hacerlos desaparecer: esto solo comprueba de forma sencilla el bajo contraste.'],
  'Set brightness about halfway on your device slider, provided the screen is easy to read. Keep that setting for all rounds. This does not produce equal physical brightness across devices.':
    ['Ställ ljusstyrkan ungefär mitt på reglaget om skärmen är lättläst. Behåll inställningen under alla omgångar. Det ger inte samma fysiska ljusstyrka på olika skärmar.', 'Stelle die Helligkeit ungefähr auf die Mitte des Reglers, sofern alles gut lesbar ist. Behalte die Einstellung bei. Das erzeugt nicht auf allen Geräten dieselbe physikalische Leuchtdichte.', 'Réglez la luminosité environ à mi-course, si l’écran reste lisible. Gardez ce réglage pendant toutes les manches. Cela ne donne pas la même luminance réelle sur tous les appareils.', 'Ajusta el brillo aproximadamente a la mitad si puedes leer bien. Mantén el ajuste durante todas las rondas. Esto no iguala la luminancia física entre dispositivos.'],
  'checks completed': ['kontroller klara','Punkte erledigt','étapes terminées','pasos completados'],
  'I am ready': ['Jag är redo','Ich bin bereit','Je suis prêt(e)','Estoy listo/a'],
  'ROUND': ['OMGÅNG','RUNDE','TOUR','RONDA'],
  'Warm background': ['Varm bakgrund','Warmer Hintergrund','Fond chaud','Fondo cálido'],
  'Cool background': ['Kall bakgrund','Kühler Hintergrund','Fond froid','Fondo frío'],
  'Dark background': ['Mörk bakgrund','Dunkler Hintergrund','Fond sombre','Fondo oscuro'],
  'Look at the screen and adapt to the color': ['Titta på skärmen och vänj dig vid färgen','Betrachte den Bildschirm und gewöhne dich an die Farbe','Regardez l’écran et habituez-vous à la couleur','Mira la pantalla y acostúmbrate al color'],
  'Start this round': ['Starta omgången','Runde starten','Commencer ce tour','Comenzar esta ronda'],
  'You will see only the color and a timer for 60 seconds. Do not change your screen brightness.':
    ['Du ser bara färgen och en timer i 60 sekunder. Ändra inte ljusstyrkan.', 'Du siehst 60 Sekunden lang nur die Farbe und einen Timer. Ändere die Helligkeit nicht.', 'Vous ne verrez que la couleur et un chronomètre pendant 60 secondes. Ne modifiez pas la luminosité.', 'Solo verás el color y un temporizador durante 60 segundos. No cambies el brillo.'],
  'MEMORIZATION': ['INLÄRNING','EINPRÄGEN','MÉMORISATION','MEMORIZACIÓN'],
  'Remember these word pairs': ['Kom ihåg dessa ordpar','Merke dir diese Wortpaare','Mémorisez ces paires de mots','Memoriza estos pares de palabras'],
  'You have 60 seconds. Try to remember which object each invented word represents.':
    ['Du har 60 sekunder. Kom ihåg vilket föremål varje påhittat ord står för.', 'Du hast 60 Sekunden. Merke dir, welches Objekt jedes erfundene Wort bezeichnet.', 'Vous avez 60 secondes pour retenir l’objet associé à chaque mot inventé.', 'Tienes 60 segundos para recordar qué objeto representa cada palabra inventada.'],
  'Do not write down or photograph the word pairs.': ['Skriv inte av och fotografera inte ordparen.','Schreibe die Wortpaare nicht auf und fotografiere sie nicht.','Ne notez pas et ne photographiez pas les paires de mots.','No escribas ni fotografíes los pares de palabras.'],
  'DISTRACTION TASK': ['DISTRAKTIONSUPPGIFT','ABLENKUNGSAUFGABE','TÂCHE DE DISTRACTION','TAREA DE DISTRACCIÓN'],
  'A quick mental reset': ['En kort mental paus','Eine kurze Denkpause','Une courte pause mentale','Una breve pausa mental'],
  'Solve the arithmetic problems. Do not rehearse the word pairs while waiting.':
    ['Lös uppgifterna. Repetera inte ordparen under tiden.', 'Löse die Rechenaufgaben. Wiederhole die Wortpaare dabei nicht.', 'Résolvez les calculs sans répéter les paires de mots.', 'Resuelve las operaciones sin repetir los pares de palabras.'],
  'WHAT IS THE SUM?': ['VAD BLIR SUMMAN?','WIE VIEL IST DIE SUMME?','QUELLE EST LA SOMME ?','¿CUÁL ES LA SUMA?'],
  'Submit': ['Svara','Antworten','Valider','Enviar'],
  'Problems attempted': ['Försök','Versuche','Tentatives','Intentos'],
  'RECALL TEST': ['MINNESTEST','GEDÄCHTNISTEST','TEST DE RAPPEL','PRUEBA DE MEMORIA'],
  'What do these words mean?': ['Vad betyder orden?','Was bedeuten diese Wörter?','Que signifient ces mots ?','¿Qué significan estas palabras?'],
  'Type the object you remember for each word. Leave an answer blank if you do not remember.':
    ['Skriv föremålet du minns för varje ord. Lämna tomt om du inte minns.', 'Gib für jedes Wort das erinnerte Objekt ein. Lass Felder leer, wenn du dich nicht erinnerst.', 'Indiquez l’objet associé à chaque mot. Laissez le champ vide si vous ne savez plus.', 'Escribe el objeto asociado a cada palabra. Déjalo vacío si no lo recuerdas.'],
  'Object…': ['Föremål…','Objekt…','Objet…','Objeto…'],
  'Saving…': ['Sparar…','Speichern…','Enregistrement…','Guardando…'],
  'Submit answers': ['Lämna in svaren','Antworten abgeben','Envoyer les réponses','Enviar respuestas'],
  'Answers are submitted automatically when time runs out.':
    ['Svaren skickas automatiskt när tiden är slut.', 'Die Antworten werden nach Ablauf der Zeit automatisch gesendet.', 'Les réponses sont envoyées automatiquement à la fin du temps imparti.', 'Las respuestas se envían automáticamente al terminar el tiempo.'],
  'STUDY COMPLETED': ['STUDIEN AVSLUTAD','STUDIE ABGESCHLOSSEN','ÉTUDE TERMINÉE','ESTUDIO FINALIZADO'],
  'Thank you for participating!': ['Tack för att du deltog!','Vielen Dank für deine Teilnahme!','Merci de votre participation !','¡Gracias por participar!'],
  'You have completed all three rounds. Your answers have been saved and contribute to this study.':
    ['Du har klarat alla tre omgångar. Dina svar har sparats till studien.', 'Du hast alle drei Runden abgeschlossen. Deine Antworten wurden gespeichert.', 'Vous avez terminé les trois tours. Vos réponses ont été enregistrées.', 'Has completado las tres rondas. Se han guardado tus respuestas.'],
  'Rounds completed': ['Omgångar klara','Runden abgeschlossen','Tours terminés','Rondas completadas'],
  'Word associations': ['Ordassociationer','Wortzuordnungen','Associations de mots','Asociaciones de palabras'],
  'No names or email addresses were collected. You can close this page.':
    ['Inga namn eller e-postadresser samlades in. Du kan stänga sidan.', 'Es wurden keine Namen oder E-Mail-Adressen erfasst. Du kannst die Seite schließen.', 'Aucun nom ni courriel n’a été recueilli. Vous pouvez fermer cette page.', 'No se han recogido nombres ni correos electrónicos. Puedes cerrar esta página.'],
  'Withdraw consent and delete my data': ['Återkalla samtycket och radera mina uppgifter','Einwilligung widerrufen und Daten löschen','Retirer mon consentement et supprimer mes données','Retirar mi consentimiento y eliminar mis datos'],
  'Time remaining': ['Tid kvar','Verbleibende Zeit','Temps restant','Tiempo restante'],
  'Pseudonymous study': ['Pseudonym studie','Pseudonyme Studie','Étude pseudonymisée','Estudio seudónimo'],
  'Keep screen settings unchanged': ['Ändra inte skärminställningarna','Bildschirmeinstellungen nicht ändern','Ne modifiez pas les réglages de l’écran','No cambies los ajustes de pantalla'],
  'Withdraw': ['Återkalla','Widerrufen','Retirer','Retirar'],
  'Start a new session for this version': ['Starta en ny session för denna version','Neue Sitzung für diese Version starten','Commencer une nouvelle session pour cette version','Iniciar una sesión nueva para esta versión'],
  'Retry': ['Försök igen','Erneut versuchen','Réessayer','Reintentar'],
  'Connecting to study…': ['Ansluter till studien…','Verbindung zur Studie…','Connexion à l’étude…','Conectando con el estudio…'],
  'Unable to connect': ['Kunde inte ansluta','Verbindung fehlgeschlagen','Connexion impossible','No se pudo conectar'],
  'Withdraw consent? All data associated with this participant ID will be permanently deleted.':
    ['Återkalla samtycket? All data kopplad till detta deltagar-ID raderas permanent.', 'Einwilligung widerrufen? Alle Daten zu dieser Teilnehmer-ID werden dauerhaft gelöscht.', 'Retirer le consentement ? Toutes les données liées à cet identifiant seront définitivement supprimées.', '¿Retirar el consentimiento? Todos los datos asociados a este identificador se eliminarán permanentemente.'],
  'Orange': ['Orange','Orange','Orange','Naranja'],
  'Blue': ['Blå','Blau','Bleu','Azul'],
  'Neutral gray': ['Neutralgrå','Neutralgrau','Gris neutre','Gris neutro'],
  'Orange screen background': ['Orange skärmbakgrund','Oranger Bildschirmhintergrund','Fond d’écran orange','Fondo de pantalla naranja'],
  'Blue screen background': ['Blå skärmbakgrund','Blauer Bildschirmhintergrund','Fond d’écran bleu','Fondo de pantalla azul'],
  'Gray screen background': ['Grå skärmbakgrund','Grauer Bildschirmhintergrund','Fond d’écran gris','Fondo de pantalla gris'],
  'Your answers, at last': ['Dina svar, till sist','Deine Antworten im Überblick','Enfin, vos réponses','Tus respuestas, al final'],
  'View your answers': ['Visa dina svar','Antworten ansehen','Voir vos réponses','Ver tus respuestas'],
  'Your answer': ['Ditt svar','Deine Antwort','Votre réponse','Tu respuesta'],
  'Correct answer': ['Rätt svar','Richtige Antwort','Bonne réponse','Respuesta correcta'],
  'Not answered': ['Inget svar','Keine Antwort','Sans réponse','Sin respuesta'],
  'Correct': ['Rätt','Richtig','Correct','Correcto'],
  'Not quite': ['Inte riktigt','Nicht ganz','Pas tout à fait','No del todo'],
  'Arithmetic questions': ['Räkneuppgifter','Rechenaufgaben','Calcul mental','Cálculo mental'],
  'You can now review every word and see which answers were accepted.':
    ['Nu kan du gå igenom alla ord och se vilka svar som godkändes.','Du kannst jetzt alle Wörter und ihre Bewertungen ansehen.','Vous pouvez revoir tous les mots et les réponses acceptées.','Ahora puedes revisar todas las palabras y los aciertos.'],
  'Results appear only when all three rounds are complete, so they cannot influence your next round.':
    ['Resultaten visas efter tre omgångar, så de inte påverkar nästa.','Ergebnisse erscheinen erst nach allen drei Runden.','Les résultats apparaissent après les trois tours.','Los resultados aparecen después de las tres rondas.'],
  'The words will appear in a different order when you answer.':
    ['Orden visas i en annan ordning när du svarar.','Die Wörter erscheinen beim Antworten in anderer Reihenfolge.','Les mots apparaîtront dans un autre ordre lors du rappel.','Las palabras aparecerán en otro orden al responder.'],
  'The order is shuffled. Take your time and recall the meaning of each word.':
    ['Ordningen är blandad. Ta din tid och försök minnas betydelsen.','Die Reihenfolge ist gemischt. Erinnere dich an die Bedeutung.','L’ordre est mélangé. Prenez le temps de retrouver chaque sens.','El orden es aleatorio. Recuerda el significado de cada palabra.'],
  'Well done for finishing': ['Bra jobbat med att slutföra','Gut gemacht, du hast es geschafft','Merci d’avoir terminé','Gracias por terminar'],
  'Every answer helps us understand how people learn.':
    ['Varje svar hjälper oss förstå hur människor lär sig.','Jede Antwort hilft uns, das Lernen zu verstehen.','Chaque réponse nous aide à comprendre l’apprentissage.','Cada respuesta nos ayuda a entender cómo aprendemos.'],
  'The study is complete': ['Studien är klar','Die Studie ist abgeschlossen','L’étude est terminée','El estudio ha terminado'],
  'How did the colors feel?': ['Hur upplevde du färgerna?','Wie hast du die Farben wahrgenommen?','Comment avez-vous ressenti les couleurs ?','¿Cómo percibiste los colores?'],
  'Two optional questions before you see your results. There are no right or wrong answers.':
    ['Två frivilliga frågor innan du ser dina resultat. Det finns inga rätt eller fel svar.',
     'Zwei freiwillige Fragen, bevor du deine Ergebnisse siehst. Es gibt keine richtigen oder falschen Antworten.',
     'Deux questions facultatives avant de voir vos résultats. Il n’y a pas de bonne ou de mauvaise réponse.',
     'Dos preguntas opcionales antes de ver tus resultados. No hay respuestas correctas o incorrectas.'],
  'Did remembering the words feel different between the background colors?':
    ['Kändes det olika lätt att minnas orden med olika bakgrundsfärger?',
     'Fühlte sich das Erinnern der Wörter bei den verschiedenen Hintergrundfarben unterschiedlich an?',
     'Avez-vous perçu une différence pour mémoriser les mots selon la couleur de fond ?',
     '¿Sentiste diferencias al recordar palabras con los distintos colores de fondo?'],
  'No difference': ['Ingen skillnad','Kein Unterschied','Aucune différence','Ninguna diferencia'],
  'Small difference': ['Liten skillnad','Kleiner Unterschied','Petite différence','Poca diferencia'],
  'Noticeable difference': ['Tydlig skillnad','Deutlicher Unterschied','Différence notable','Diferencia perceptible'],
  'Large difference': ['Stor skillnad','Großer Unterschied','Grande différence','Gran diferencia'],
  'Not sure': ['Osäker','Unsicher','Je ne sais pas','No estoy seguro/a'],
  'With which background did remembering words feel easiest?':
    ['Med vilken bakgrund kändes det lättast att minnas orden?',
     'Bei welcher Hintergrundfarbe fiel dir das Erinnern der Wörter am leichtesten?',
     'Avec quelle couleur de fond était-il le plus facile de mémoriser les mots ?',
     '¿Con qué color de fondo te resultó más fácil recordar las palabras?'],
  'About the same': ['Ungefär lika','Ungefähr gleich','À peu près pareil','Más o menos igual'],
  'Gray': ['Grå','Grau','Gris','Gris'],
  'See my results': ['Visa mina resultat','Meine Ergebnisse anzeigen','Voir mes résultats','Ver mis resultados'],
  'Skip these questions': ['Hoppa över frågorna','Fragen überspringen','Passer ces questions','Omitir estas preguntas'],
  'These impressions are stored separately from memory scores and are used only to explore perceived differences.':
    ['Dina upplevelser sparas separat från minnespoängen och används bara för att utforska upplevda skillnader.',
     'Diese Eindrücke werden getrennt von den Gedächtniswerten gespeichert und nur zur Untersuchung wahrgenommener Unterschiede verwendet.',
     'Ces impressions sont stockées séparément des scores et servent uniquement à étudier les différences ressenties.',
     'Estas impresiones se almacenan por separado de las puntuaciones y solo se usan para estudiar diferencias percibidas.'],
  'I participate voluntarily and agree that my age range, optional gender, language, test results and optional color-perception feedback are stored under a random participant ID for research. No names or email addresses are collected.':
    ['Jag deltar frivilligt och samtycker till att åldersgrupp, eventuellt kön, språk, testresultat och valfria synpunkter om färger lagras under ett slumpmässigt deltagar-ID för forskning. Inga namn eller e-postadresser samlas in.',
     'Ich nehme freiwillig teil und stimme zu, dass Altersgruppe, optionales Geschlecht, Sprache, Testergebnisse und freiwillige Angaben zur Farbwahrnehmung unter einer zufälligen Teilnehmer-ID gespeichert werden. Es werden keine Namen oder E-Mail-Adressen erhoben.',
     'Je participe volontairement et accepte que ma tranche d’âge, mon genre facultatif, ma langue, mes résultats et mes impressions facultatives sur les couleurs soient enregistrés sous un identifiant aléatoire. Aucun nom ni courriel n’est recueilli.',
     'Participo voluntariamente y acepto que mi grupo de edad, género opcional, idioma, resultados e impresiones opcionales sobre los colores se guarden bajo un identificador aleatorio. No se recopilan nombres ni correos electrónicos.'],

};

export function translate(nb: string, en: string, lang: Language): string {
  if (lang === 'nb') return nb;
  if (lang === 'en') return en;
  const record = MESSAGES[en];
  const index = ({ sv:0, de:1, fr:2, es:3 } as Partial<Record<Language, number>>)[lang];
  // Further study languages currently use a clearly disclosed English UI fallback.
  return record && index !== undefined ? record[index] : en;
}

export type OSName = 'windows' | 'macos' | 'linux' | 'ios' | 'android' | 'external' | 'generic';

export const OS_HELP: Record<OSName, Partial<Record<Language, string>>> = {
  generic: { nb:'Åpne enhetens innstillinger for skjerm eller hurtiginnstillinger og velg fast lysstyrke. Slå av automatisk lysstyrke, nattmodus og fargejustering hvis det er mulig.', en:'Open the device display settings or quick settings and choose a fixed brightness. Turn off auto brightness, night mode and color adjustments if possible.' },
  windows: {nb:'Windows 10/11: Innstillinger → System → Skjerm → Lysstyrke, eller bruk Fn-tastene. Slå av nattlys. På ekstern skjerm bruker du knappene på skjermen.', en:'Windows 10/11: Settings → System → Display → Brightness, or use Fn keys. Turn off Night light. External monitors use their own controls.', sv:'Windows 10/11: Inställningar → System → Bildskärm → Ljusstyrka, eller Fn-tangenter. Stäng av nattläge. Externa skärmar har egna knappar.', de:'Windows 10/11: Einstellungen → System → Anzeige → Helligkeit oder Fn-Tasten. Nachtmodus ausschalten. Externe Monitore separat einstellen.', fr:'Windows 10/11 : Paramètres → Système → Affichage → Luminosité, ou touches Fn. Désactivez l’éclairage nocturne. Utilisez les boutons de l’écran externe.', es:'Windows 10/11: Configuración → Sistema → Pantalla → Brillo, o teclas Fn. Desactiva luz nocturna. Los monitores externos tienen sus propios controles.'},
  macos: {nb:'macOS: Kontrollsenter → Skjerm / Lysstyrke, eller Systeminnstillinger → Skjermer. Slå av True Tone, Night Shift og automatisk lysstyrke.', en:'macOS: Control Center → Display / Brightness or System Settings → Displays. Disable True Tone, Night Shift and automatic brightness.', sv:'macOS: Kontrollcenter → Skärm / Ljusstyrka eller Systeminställningar → Bildskärmar. Stäng av True Tone, Night Shift och automatisk ljusstyrka.', de:'macOS: Kontrollzentrum → Display / Helligkeit oder Systemeinstellungen → Displays. True Tone, Night Shift und automatische Helligkeit ausschalten.', fr:'macOS : Centre de contrôle → Écran / Luminosité ou Réglages Système → Moniteurs. Désactivez True Tone, Night Shift et la luminosité auto.', es:'macOS: Centro de control → Pantalla / Brillo o Ajustes del Sistema → Pantallas. Desactiva True Tone, Night Shift y brillo automático.'},
  linux: {nb:'Linux: Bruk skrivebordsmiljøets skjerm-/strøminnstillinger (GNOME/KDE) eller lysstyrketastene. Slå av nattmodus. For ekstern skjerm, bruk skjermens knapper.', en:'Linux: Use your desktop environment’s display/power settings (GNOME/KDE) or brightness keys. Turn off Night Light. External displays use their controls.', sv:'Linux: Använd skrivbordsmiljöns skärm- eller energiinställningar (GNOME/KDE) eller ljusstyrketangenter. Stäng av nattläge.', de:'Linux: Helligkeit über Anzeige-/Energieeinstellungen (GNOME/KDE) oder Funktionstasten regeln. Nachtmodus ausschalten.', fr:'Linux : utilisez les paramètres écran/alimentation (GNOME/KDE) ou les touches de luminosité. Désactivez le mode nuit.', es:'Linux: usa la configuración de pantalla/energía (GNOME/KDE) o teclas de brillo. Desactiva la luz nocturna.'},
  ios: {nb:'iPhone/iPad: Kontrollsenter → Lysstyrke. Slå av Night Shift og True Tone under Innstillinger → Skjerm og lysstyrke. Automatisk lysstyrke finnes under Tilgjengelighet.', en:'iPhone/iPad: Control Center → Brightness. Disable Night Shift and True Tone in Settings → Display & Brightness. Auto-Brightness is under Accessibility.', sv:'iPhone/iPad: Kontrollcenter → Ljusstyrka. Stäng av Night Shift och True Tone under Inställningar → Visning och ljusstyrka.', de:'iPhone/iPad: Kontrollzentrum → Helligkeit. Night Shift und True Tone unter Einstellungen → Anzeige & Helligkeit ausschalten.', fr:'iPhone/iPad : Centre de contrôle → Luminosité. Désactivez Night Shift et True Tone dans Réglages → Luminosité et affichage.', es:'iPhone/iPad: Centro de control → Brillo. Desactiva Night Shift y True Tone en Ajustes → Pantalla y brillo.'},
  android: {nb:'Android: Sveip ned til hurtiginnstillinger → Lysstyrke. Slå av adaptiv lysstyrke og nattlys/øyekomfort i skjerminnstillingene.', en:'Android: Swipe down for Quick Settings → Brightness. Turn off Adaptive Brightness and Night Light/Eye Comfort in Display settings.', sv:'Android: Svep ned till snabbinställningar → Ljusstyrka. Stäng av adaptiv ljusstyrka och nattläge i skärminställningarna.', de:'Android: Schnelleinstellungen öffnen → Helligkeit. Adaptive Helligkeit und Nachtlicht/Augenkomfort unter Display deaktivieren.', fr:'Android : paramètres rapides → Luminosité. Désactivez la luminosité adaptative et le mode nuit dans les paramètres d’affichage.', es:'Android: ajustes rápidos → Brillo. Desactiva brillo adaptable y luz nocturna/protección ocular en Pantalla.'},
  external: {nb:'Ekstern skjerm/TV: Bruk skjermens egne knapper eller meny (OSD) for lysstyrke. Slå av automatisk kontrast, dynamisk lysstyrke og fargetilpasning.', en:'External monitor/TV: Use the physical buttons or on-screen display (OSD) to set brightness. Turn off dynamic contrast, adaptive brightness and color adjustments.', sv:'Extern skärm/TV: Använd skärmens knappar eller meny (OSD) för ljusstyrka. Stäng av dynamisk kontrast och automatisk anpassning.', de:'Externer Monitor/TV: Mit den Monitortasten bzw. dem Bildschirmmenü (OSD) die Helligkeit ändern. Dynamischen Kontrast und Automatik deaktivieren.', fr:'Moniteur externe/TV : réglez la luminosité avec les boutons ou le menu de l’écran (OSD). Désactivez le contraste dynamique et les réglages automatiques.', es:'Monitor externo/TV: ajusta el brillo con los botones o menú (OSD). Desactiva contraste dinámico y ajustes automáticos.'},
};
