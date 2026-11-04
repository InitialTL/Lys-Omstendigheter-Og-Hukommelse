// Device-specific brightness directions in every supported interface language.
export const extraDeviceHelp: Readonly<Record<string, Readonly<Record<string, string>>>> = {
  "generic": {
    "ru": "Откройте настройки экрана или быстрые настройки устройства и установите постоянную яркость. По возможности отключите автоматическую яркость, ночной режим и автоматическую коррекцию цвета.",
    "sv": "Öppna skärminställningarna eller snabbinställningarna och välj en fast ljusstyrka. Stäng av automatisk ljusstyrka, nattläge och färganpassning om möjligt.",
    "de": "Öffne die Bildschirm- oder Schnelleinstellungen und wähle eine feste Helligkeit. Deaktiviere nach Möglichkeit automatische Helligkeit, Nachtmodus und Farbanpassungen.",
    "fr": "Ouvrez les paramètres d’affichage ou les réglages rapides et choisissez une luminosité fixe. Désactivez si possible la luminosité automatique, le mode nuit et l’ajustement des couleurs.",
    "es": "Abre los ajustes de pantalla o los ajustes rápidos y elige un brillo fijo. Desactiva el brillo automático, el modo nocturno y el ajuste de color si es posible.",
    "nl": "Open de scherminstellingen of snelle instellingen en kies een vaste helderheid. Schakel automatische helderheid, nachtmodus en kleuraanpassingen uit als dat kan.",
    "it": "Apri le impostazioni dello schermo o quelle rapide e scegli una luminosità fissa. Disattiva luminosità automatica, modalità notturna e regolazione dei colori, se possibile.",
    "pt": "Abre as definições de ecrã ou as definições rápidas e escolhe um brilho fixo. Desativa o brilho automático, o modo noturno e os ajustes de cor, se possível.",
    "da": "Åbn skærmindstillinger eller hurtigindstillinger, og vælg en fast lysstyrke. Slå automatisk lysstyrke, nattilstand og farvetilpasning fra, hvis det er muligt.",
    "pl": "Otwórz ustawienia ekranu lub szybkie ustawienia i wybierz stałą jasność. Jeśli to możliwe, wyłącz automatyczną jasność, tryb nocny i dopasowanie kolorów.",
    "ro": "Deschide setările ecranului sau setările rapide și alege o luminozitate fixă. Dezactivează, dacă este posibil, luminozitatea automată, modul nocturn și ajustările de culoare."
  },
  "windows": {
    "ru": "Windows 10/11: Параметры → Система → Дисплей → Яркость или клавиши Fn. Отключите «Ночной свет». На внешнем мониторе используйте кнопки самого монитора.",
    "nl": "Windows 10/11: Instellingen → Systeem → Beeldscherm → Helderheid, of gebruik de Fn-toetsen. Schakel Nachtlamp uit. Pas een externe monitor aan via de knoppen op het scherm.",
    "it": "Windows 10/11: Impostazioni → Sistema → Schermo → Luminosità, oppure usa i tasti Fn. Disattiva Luce notturna. Per un monitor esterno usa i comandi del monitor.",
    "pt": "Windows 10/11: Definições → Sistema → Ecrã → Brilho, ou utiliza as teclas Fn. Desativa a luz noturna. Num monitor externo, usa os comandos do monitor.",
    "da": "Windows 10/11: Indstillinger → System → Skærm → Lysstyrke, eller brug Fn-tasterne. Slå natlys fra. Brug skærmens egne knapper på en ekstern skærm.",
    "pl": "Windows 10/11: Ustawienia → System → Ekran → Jasność lub klawisze Fn. Wyłącz filtr światła niebieskiego. Monitor zewnętrzny reguluj przyciskami monitora.",
    "ro": "Windows 10/11: Setări → Sistem → Afișaj → Luminozitate sau tastele Fn. Dezactivează lumina de noapte. Pentru un monitor extern folosește butoanele monitorului."
  },
  "macos": {
    "ru": "macOS: Пункт управления → Дисплей / Яркость или Системные настройки → Дисплеи. Отключите True Tone, Night Shift и автоматическую яркость.",
    "nl": "macOS: Bedieningspaneel → Beeldscherm / Helderheid of Systeeminstellingen → Beeldschermen. Schakel True Tone, Night Shift en automatische helderheid uit.",
    "it": "macOS: Centro di Controllo → Schermo / Luminosità oppure Impostazioni di Sistema → Schermi. Disattiva True Tone, Night Shift e luminosità automatica.",
    "pt": "macOS: Central de Controlo → Ecrã / Brilho ou Definições do Sistema → Monitores. Desativa True Tone, Night Shift e brilho automático.",
    "da": "macOS: Kontrolcenter → Skærm / Lysstyrke eller Systemindstillinger → Skærme. Slå True Tone, Night Shift og automatisk lysstyrke fra.",
    "pl": "macOS: Centrum sterowania → Ekran / Jasność lub Ustawienia systemowe → Monitory. Wyłącz True Tone, Night Shift i automatyczną jasność.",
    "ro": "macOS: Centru de control → Ecran / Luminozitate sau Configurări sistem → Monitoare. Dezactivează True Tone, Night Shift și luminozitatea automată."
  },
  "linux": {
    "ru": "Linux: Используйте настройки экрана или питания рабочего окружения (GNOME/KDE) либо клавиши регулировки яркости. Отключите ночной режим. Внешний монитор настраивается его кнопками.",
    "nl": "Linux: Gebruik de scherm- of energie-instellingen van je bureaubladomgeving (GNOME/KDE) of de helderheidstoetsen. Schakel nachtmodus uit. Stel een externe monitor in met de knoppen op de monitor.",
    "it": "Linux: Usa le impostazioni dello schermo o dell'energia del desktop (GNOME/KDE) oppure i tasti della luminosità. Disattiva la modalità notturna. Regola i monitor esterni tramite i loro pulsanti.",
    "pt": "Linux: Usa as definições de ecrã ou energia do ambiente de trabalho (GNOME/KDE) ou as teclas de brilho. Desativa o modo noturno. Nos monitores externos, utiliza os botões do monitor.",
    "da": "Linux: Brug skrivebordsmiljøets skærm- eller strømindstillinger (GNOME/KDE) eller lysstyrketasterne. Slå nattilstand fra. Brug skærmens egne knapper på eksterne skærme.",
    "pl": "Linux: Użyj ustawień ekranu lub zasilania środowiska GNOME/KDE albo klawiszy jasności. Wyłącz tryb nocny. Jasność monitora zewnętrznego ustaw jego przyciskami.",
    "ro": "Linux: Folosește setările de ecran sau alimentare ale mediului desktop (GNOME/KDE) ori tastele de luminozitate. Dezactivează modul nocturn. Reglează monitoarele externe din butoanele lor."
  },
  "ios": {
    "ru": "iPhone/iPad: Пункт управления → Яркость. Отключите Night Shift и True Tone в Настройки → Экран и яркость. Автоматическая яркость находится в Универсальном доступе.",
    "nl": "iPhone/iPad: Bedieningspaneel → Helderheid. Schakel Night Shift en True Tone uit via Instellingen → Scherm en helderheid. Automatische helderheid staat bij Toegankelijkheid.",
    "it": "iPhone/iPad: Centro di Controllo → Luminosità. Disattiva Night Shift e True Tone in Impostazioni → Schermo e luminosità. Luminosità automatica si trova in Accessibilità.",
    "pt": "iPhone/iPad: Central de Controlo → Brilho. Desativa Night Shift e True Tone em Definições → Ecrã e Brilho. O brilho automático está em Acessibilidade.",
    "da": "iPhone/iPad: Kontrolcenter → Lysstyrke. Slå Night Shift og True Tone fra under Indstillinger → Skærm og lysstyrke. Automatisk lysstyrke findes under Tilgængelighed.",
    "pl": "iPhone/iPad: Centrum sterowania → Jasność. Wyłącz Night Shift i True Tone w Ustawienia → Ekran i jasność. Automatyczna jasność znajduje się w Dostępności.",
    "ro": "iPhone/iPad: Centru de control → Luminozitate. Dezactivează Night Shift și True Tone în Configurări → Afișaj și luminozitate. Luminozitatea automată se află în Accesibilitate."
  },
  "android": {
    "ru": "Android: Проведите вниз, чтобы открыть быстрые настройки → Яркость. В настройках экрана отключите адаптивную яркость и ночной режим / защиту зрения.",
    "nl": "Android: Veeg omlaag naar Snelle instellingen → Helderheid. Schakel adaptieve helderheid en Nachtlamp/oogcomfort uit bij de scherminstellingen.",
    "it": "Android: Scorri verso il basso per aprire Impostazioni rapide → Luminosità. Disattiva la luminosità adattiva e Luce notturna/Protezione occhi nelle impostazioni dello schermo.",
    "pt": "Android: Desliza para baixo para abrir as Definições rápidas → Brilho. Desativa o brilho adaptativo e a luz noturna/conforto ocular nas definições de ecrã.",
    "da": "Android: Stryg ned til Hurtigindstillinger → Lysstyrke. Slå adaptiv lysstyrke og natlys/øjenkomfort fra i skærmindstillingerne.",
    "pl": "Android: Przesuń palcem w dół do Szybkich ustawień → Jasność. Wyłącz jasność adaptacyjną i tryb nocny/ochronę oczu w ustawieniach ekranu.",
    "ro": "Android: Glisează în jos spre Setări rapide → Luminozitate. Dezactivează luminozitatea adaptivă și lumina de noapte/confortul ocular din setările ecranului."
  },
  "external": {
    "ru": "Внешний монитор / телевизор: настройте яркость физическими кнопками или через экранное меню (OSD). Отключите динамическую контрастность, автоматическую яркость и корректировку цвета.",
    "nl": "Externe monitor/tv: Stel de helderheid in met de fysieke knoppen of het schermmenu (OSD). Schakel dynamisch contrast, automatische helderheid en kleuraanpassingen uit.",
    "it": "Monitor esterno/TV: Usa i pulsanti fisici o il menu sullo schermo (OSD) per regolare la luminosità. Disattiva contrasto dinamico, luminosità adattiva e regolazioni dei colori.",
    "pt": "Monitor externo/TV: Usa os botões físicos ou o menu no ecrã (OSD) para ajustar o brilho. Desativa contraste dinâmico, brilho adaptativo e ajustes de cor.",
    "da": "Ekstern skærm/tv: Brug de fysiske knapper eller skærmmenuen (OSD) til lysstyrke. Slå dynamisk kontrast, automatisk lysstyrke og farvetilpasning fra.",
    "pl": "Monitor zewnętrzny/telewizor: Ustaw jasność za pomocą przycisków lub menu ekranowego (OSD). Wyłącz kontrast dynamiczny, jasność adaptacyjną i regulację kolorów.",
    "ro": "Monitor extern/TV: Folosește butoanele fizice sau meniul afișat pe ecran (OSD) pentru luminozitate. Dezactivează contrastul dinamic, luminozitatea adaptivă și ajustările de culoare."
  }
};
