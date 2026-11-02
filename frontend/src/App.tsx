import { useCallback, useEffect, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import {
  ArrowLeft, ArrowRight, Brain, Check, CheckCircle2, Clock3, Eye,
  Focus, Lightbulb, LockKeyhole, Monitor, Circle, RefreshCw, Maximize, Minimize, VolumeX,
  ShieldCheck, Sun, ThermometerSun,
} from 'lucide-react';
import { api, COLORS, storeParticipantToken, clearParticipantToken } from './api';
import { LANGUAGE_NAMES, OS_HELP, translate, detectBrowserLanguage, directionForLanguage } from './i18n';
import { currentDeviceGuide } from './device';
import { secondsRemaining, deadlinePassed } from './timing';
import type { Condition, Language, Pair, Registration, StudyState, Perception } from './api';

const PARTICIPANT_KEY = 'lm_v2_participant';
const LANGUAGE_KEY = 'lm_v2_language';
const CALIBRATED_KEY = 'lm_v2_calibrated';
const LABELS: Record<Condition, { nb: string; en: string; descriptionNb: string; descriptionEn: string }> = {
  ORANGE: { nb: 'Oransje', en: 'Orange', descriptionNb: 'Oransje skjermbakgrunn', descriptionEn: 'Orange screen background' },
  BLUE: { nb: 'Blå', en: 'Blue', descriptionNb: 'Blå skjermbakgrunn', descriptionEn: 'Blue screen background' },
  NEUTRAL: { nb: 'Nøytral grå', en: 'Neutral gray', descriptionNb: 'Grå skjermbakgrunn', descriptionEn: 'Gray screen background' },
};
const draftKey = (id: string, index: number) => `lm_v2_draft_${id}_${index}`;
const draftVersionKey = (id: string, index: number) => `lm_v2_draft_revision_${id}_${index}`;
const hiddenKey = (id: string, index: number) => `lm_v2_hidden_${id}_${index}`;
const mathKey = (id: string, index: number) => `lm_v23_math_${id}_${index}`;

type View = 'loading' | 'intro' | 'calibration' | 'study' | 'perception' | 'complete';
type ChangeLanguage = (lang: Language) => void;

function LanguageSwitcher({ lang, onChange, dark = false, disabled = false }: {
  lang: Language; onChange: ChangeLanguage; dark?: boolean; disabled?: boolean;
}) {
  return <div className={`language-switch${dark ? ' language-switch-dark' : ''}`}>
    <label htmlFor={dark ? 'study-language' : 'page-language'}>{translate('Språk', 'Language', lang)}</label>
    <select id={dark ? 'study-language' : 'page-language'} aria-label={translate('Språk', 'Language', lang)}
      disabled={disabled} title={disabled ? translate('Språket er låst etter registrering for å sikre riktig skåring.', 'The study language is fixed after registration to ensure correct scoring.', lang) : undefined}
      value={lang} onChange={event => onChange(event.target.value as Language)}>
      {Object.entries(LANGUAGE_NAMES).map(([code, name]) =>
        <option key={code} value={code}>{name}</option>)}
    </select>
  </div>;
}


function WithdrawControl({ lang, onWithdraw, busy, error }: {
  lang: Language; onWithdraw: () => Promise<void>; busy: boolean; error: string | null;
}) {
  const [confirming, setConfirming] = useState(false);
  const t = (nb: string, en: string) => translate(nb, en, lang);
  useEffect(() => {
    if (!confirming) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !busy) setConfirming(false);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [confirming, busy]);
  return <>
    <button type="button" className="withdraw-access" onClick={() => setConfirming(true)}
      aria-haspopup="dialog" aria-expanded={confirming} disabled={busy}>
      <ShieldCheck size={16}/>{t('Trekk samtykke', 'Withdraw consent')}
    </button>
    {confirming && <div className="withdraw-shade">
      <section role="dialog" aria-modal="true" aria-labelledby="withdraw-title"
        aria-describedby="withdraw-description" className="withdraw-dialog">
        <h2 id="withdraw-title">{t('Trekk samtykke?', 'Withdraw consent?')}</h2>
        <p id="withdraw-description">{t(
          'Vil du avslutte deltakelsen og slette alle data knyttet til deltaker-ID-en din? Dette kan ikke angres.',
          'End your participation and permanently delete all data linked to your participant ID? This cannot be undone.'
        )}</p>
        {error && <p className="withdraw-error" role="alert">{t(
          'Slettingen er ikke bekreftet. Den lokale økten er beholdt. Du kan prøve igjen.',
          'Deletion has not been confirmed. Your local session is retained. You may try again.'
        )} <span>{error}</span></p>}
        <div className="withdraw-actions">
          <button type="button" className="withdraw-keep" autoFocus disabled={busy}
            onClick={() => setConfirming(false)}>{t('Fortsett forsøket', 'Continue the study')}</button>
          <button type="button" className="withdraw-delete" disabled={busy}
            onClick={() => void onWithdraw()}>
            {busy ? t('Sletter …', 'Deleting…') : t('Ja, slett dataene mine', 'Yes, delete my data')}
          </button>
        </div>
      </section>
    </div>}
  </>;
}

function Brand({ light = false }: { light?: boolean }) {
  return <div className={`brand ${light ? 'brand-light' : ''}`} aria-label="Hukommelse LM">
    <div className="brand-mark" aria-hidden="true">h<span>.</span></div>
    <div className="brand-copy"><b>hukommelse<span>lm</span></b></div>
  </div>;
}

function Header({ lang, page, onLanguageChange }: { lang: Language; page?: string; onLanguageChange: ChangeLanguage }) {
  return <header className="topbar">
    <Brand />
    <div className="topbar-right">
      <LanguageSwitcher lang={lang} onChange={onLanguageChange}/>
      <span className="research-label"><span className="status-dot" /> {translate('Forskningsprosjekt', 'Research study', lang)}</span>
      {page && <span className="header-page">{page}</span>}
    </div>
  </header>;
}

function Button({ children, onClick, disabled, secondary = false, className = '', type = 'button' }:
  { children: ReactNode; onClick?: () => void; disabled?: boolean; secondary?: boolean; className?: string; type?: 'button' | 'submit' }) {
  return <button type={type} onClick={onClick} disabled={disabled} className={`btn ${secondary ? 'btn-secondary' : 'btn-primary'} ${className}`}>
    {children}
  </button>;
}

function Intro({ lang, setLang, onRegister, busy, error }:
  { lang: Language; setLang: ChangeLanguage; onRegister: (input: Registration) => void; busy: boolean; error: string | null }) {
  const [age, setAge] = useState('16_17');
  const [gender, setGender] = useState('prefer_not');
  const [consent, setConsent] = useState(false);
  const t = (nb: string, en: string) => translate(nb, en, lang);
  return <div className="site-shell">
    <Header lang={lang} onLanguageChange={setLang}/>
    <main className="intro-layout">
      <div className="intro-main">
        <div className="eyebrow"><span aria-hidden="true">LM / 03</span> {t('DIGITALT FORSKNINGSFORSØK', 'A DIGITAL RESEARCH EXPERIMENT')}</div>
        <h1>{t('Kan fargene rundt oss', 'Can the colors around us')}<br /><em>{t('påvirke hukommelsen?', 'affect our memory?')}</em></h1>
        <p className="hero-sub">{t('Bli med på et kort forskningsforsøk der vi sammenligner oransje, blå og grå skjermbakgrunn og undersøker om fargen påvirker hvor lett vi husker nye ord.',
          'Join a short research study comparing orange, blue and gray screen backgrounds to see whether background color affects word memory.')}</p>
        <div className="stats-strip">
          <div><Clock3 size={21}/><strong>15–18</strong><span>{t('minutter', 'minutes')}</span></div>
          <div><LayersIcon/><strong>3</strong><span>{t('runder', 'rounds')}</span></div>
          <div><LockKeyhole size={21}/><strong>{t('Ingen navn', 'No names')}</strong><span>{t('registreres', 'recorded')}</span></div>
        </div>
        <div className="process-preview">
          <div className="section-kicker">{t('SLIK FUNGERER DET', 'HOW IT WORKS')}</div>
          <div className="process-row"><span className="process-num">01</span><div><b>{t('Juster skjermen', 'Prepare your screen')}</b><small>{t('En enkel sjekkliste før forsøket starter', 'A simple checklist before beginning')}</small></div><Monitor size={19}/></div>
          <div className="process-row"><span className="process-num">02</span><div><b>{t('Lær 8 ordpar', 'Learn 8 word pairs')}</b><small>{t('Du får 75 sekunder til å memorere', 'You have 75 seconds to memorize')}</small></div><Brain size={19}/></div>
          <div className="process-row"><span className="process-num">03</span><div><b>{t('Test hukommelsen', 'Test your memory')}</b><small>{t('En kort distraksjon før du skriver svarene', 'A short distraction before you recall the answers')}</small></div><CheckCircle2 size={19}/></div>
        </div>
      </div>
      <aside className="enroll-card">
        <div className="enroll-head"><div className="enroll-icon"><Lightbulb size={22}/></div><div><span className="section-kicker">{t('DELTA I STUDIEN', 'PARTICIPATE')}</span><h2>{t('La oss begynne', 'Get started')}</h2></div></div>
        <p className="form-intro">{t('Svar på noen korte spørsmål før vi starter. Du kan når som helst trekke samtykket og slette dataene dine.',
          'Answer a few brief questions before starting. You may withdraw consent and delete your data at any time.')}</p>
        <div className="language-preference">
          <label htmlFor="registration-language">{t('Velg språk for forsøket', 'Choose your study language')}</label>
          <select id="registration-language" value={lang} onChange={event => setLang(event.target.value as Language)}>
            {Object.entries(LANGUAGE_NAMES).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
          <p>{t('Foreslått fra nettleserspråket ditt, uten IP-oppslag. Du kan endre det før du starter.',
            'Suggested from your browser language, without an IP lookup. You can change it before starting.')}</p>
        </div>
        <label className="field"><span>{t('Alder', 'Age')}</span><select value={age} onChange={event => setAge(event.target.value)}>
          <option value="16_17">16–17</option><option value="18_24">18–24</option><option value="25_44">25–44</option>
          <option value="45_plus">45+</option><option value="prefer_not">{t('Ønsker ikke å oppgi', 'Prefer not to say')}</option>
        </select></label>
        <label className="field"><span>{t('Kjønn (valgfritt)', 'Gender (optional)')}</span><select value={gender} onChange={event => setGender(event.target.value)}>
          <option value="prefer_not">{t('Ønsker ikke å oppgi', 'Prefer not to say')}</option>
          <option value="woman">{t('Kvinne', 'Woman')}</option><option value="man">{t('Mann', 'Man')}</option>
          <option value="nonbinary">{t('Ikke-binær', 'Non-binary')}</option>
          <option value="other">{t('Annet', 'Other')}</option>
        </select></label>
        {!['nb','en','sv','de','fr','es'].includes(lang) &&
          <p className="locale-disclosure">{t('Språket for ordtesten er valgt. Veiledningen vises foreløpig på engelsk.',
            'Your word-test language is selected. Some instructions currently appear in English.')}</p>}
        <label className="consent-control"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)}/>
          <span>{t('Jeg deltar frivillig og samtykker til at aldersgruppe, eventuelt kjønn, språk, testresultater og valgfrie svar om hvordan fargene opplevdes lagres med en tilfeldig deltaker-ID for forskning. Ingen navn eller e-postadresser samles inn.',
            'I participate voluntarily and agree that my age range, optional gender, language, test results and optional color-perception feedback are stored under a random participant ID for research. No names or email addresses are collected.')}</span>
        </label>
        <p className="privacy-notice"><ShieldCheck size={15}/>{t('Deltakere under 18 år: krav til samtykke må avklares med prosjektansvarlig.', 'Under 18: consent requirements must be confirmed with the study organizer.')}</p>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <Button disabled={!consent || busy} className="fullwidth" onClick={() => onRegister({ language: lang, age_band: age, gender, consent: true })}>
          {busy ? t('Registrerer …', 'Registering…') : t('Start forsøket', 'Begin experiment')} <ArrowRight size={18}/>
        </Button>
        <div className="enroll-footer"><span className="status-dot" /> {t('Tar omtrent 15–18 minutter', 'Approximately 15–18 minutes')}</div>
      </aside>
    </main>
    <Footer lang={lang}/>
  </div>;
}

function LayersIcon() { return <div className="layers-icon"><span/><span/><span/></div>; }
function Footer({ lang }: { lang: Language }) {
  return <footer className="site-footer"><span>© HUKOMMELSE LM</span><span>{translate('En studie av skjermfarger og ordhukommelse', 'A study of screen color and word memory', lang)}</span><span>RESEARCH EDITION 2.7</span></footer>;
}

function FullscreenToggle({ lang }: { lang: Language }) {
  const [fullscreen, setFullscreen] = useState(() => Boolean(document.fullscreenElement));
  const [failure, setFailure] = useState(false);
  const t = (nb: string, en: string) => translate(nb, en, lang);
  const supported = Boolean(document.fullscreenEnabled && document.documentElement.requestFullscreen);
  useEffect(() => {
    const listener = () => { setFullscreen(Boolean(document.fullscreenElement)); setFailure(false); };
    document.addEventListener('fullscreenchange', listener);
    return () => document.removeEventListener('fullscreenchange', listener);
  }, []);
  const toggle = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (document.fullscreenEnabled && document.documentElement.requestFullscreen)
        await document.documentElement.requestFullscreen();
      else setFailure(true);
    } catch { setFailure(true); }
  };
  if (!supported) return null;
  return <div className="fullscreen-control">
    <Button secondary onClick={() => void toggle()}>
      {fullscreen ? <Minimize size={17}/> : <Maximize size={17}/>}
      {fullscreen ? t('Avslutt fullskjerm','Exit fullscreen') : t('Bruk fullskjerm','Try fullscreen')}
    </Button>
    {failure && <span role="status">{t('Fullskjerm støttes ikke her. Prøv nettleserens eget valg.', 'Fullscreen is not supported here. Use the browser’s fullscreen control if available.')}</span>}
  </div>;
}

function Calibration({ lang, onNext, onLanguageChange }: { lang: Language; onNext: () => void; onLanguageChange: ChangeLanguage }) {
  const [checks, setChecks] = useState([false, false, false, false]);
  const [deviceGuide] = useState(currentDeviceGuide);
  const t = (nb: string, en: string) => translate(nb, en, lang);
  const toggle = (i: number) => setChecks(old => old.map((v,j) => i === j ? !v : v));
  return <div className="site-shell"><Header lang={lang} page={t('Forberedelser', 'Preparation')} onLanguageChange={onLanguageChange}/>
    <main className="calibration-layout">
      <div className="eyebrow"><Monitor size={16}/>{t('TRINN 1 AV 2', 'STEP 1 OF 2')}</div>
      <h1 className="page-title">{t('Gjør skjermen klar for forsøket', 'Prepare your screen for the study')}</h1>
      <p className="page-description">{t('For at forsøket skal bli så sammenlignbart som mulig, bør alle bruke samme innstillinger gjennom de tre rundene.',
        'To make results as comparable as possible, keep the same settings throughout all three rounds.')}</p>
      <div className="calibration-grid">
        <div className="calibration-visual">
          <div className="section-kicker">{t('SKJERMSJEKK', 'SCREEN CHECK')}</div>
          <h3>{t('Kan du skille symbolene fra bakgrunnen?', 'Can you distinguish the symbols from their backgrounds?')}</h3>
          <p>{t('Det er normalt å se begge symbolene ved alle lysstyrker på mange mobilskjermer. Ikke prøv å få dem til å forsvinne: Dette er bare en enkel sjekk av svak kontrast.',
            'On many phones, both symbols remain visible at every brightness setting. Do not try to make them disappear: This is only a simple check of low contrast.')}</p>
          <div className="swatch-row" role="img" aria-label="Low-contrast symbols against white and black backgrounds">
            <div className="swatch-light"><span className="shape-on-white" aria-hidden="true">✦</span></div>
            <div className="swatch-dark"><span className="shape-on-black" aria-hidden="true">✦</span></div>
          </div>
          <div className="calibration-hint"><Eye size={17}/>{t('Still lysstyrken omtrent midt på enhetens skyveknapp, så lenge skjermen er lett å lese. Behold innstillingen gjennom alle rundene. Dette gir ikke samme fysiske lysstyrke på ulike skjermer.',
            'Set brightness about halfway on your device slider, provided the screen is easy to read. Keep that setting for all rounds. This does not produce equal physical brightness across devices.')}</div>
          <div className="os-guide">
            <span className="guide-kicker">{t('TIPS FOR ENHETEN DIN', 'HELP FOR YOUR DEVICE')}</span>
            <b>{t('Slik justerer du lysstyrken', 'How to adjust brightness')}</b>
            <p>{OS_HELP[deviceGuide][lang] ?? OS_HELP[deviceGuide].en}</p>
            <details className="external-screen-tip">
              <summary>{t('Bruker du ekstern skjerm eller TV?', 'Using an external monitor or TV?')}</summary>
              <p>{OS_HELP.external[lang] ?? OS_HELP.external.en}</p>
            </details>
          </div>
        </div>
        <div className="calibration-checklist">
          {[
            [t('Sitt i et mørkt eller svakt opplyst rom', 'Use a dark or dimly lit room'), t('Behold den samme rombelysningen gjennom hele forsøket.', 'Keep room lighting unchanged throughout the study.')],
            [t('Slå av automatisk farge og lysstyrke', 'Turn off automatic color and brightness'), t('Deaktiver nattmodus, True Tone, Night Shift og automatisk lysstyrke.', 'Disable night mode, True Tone, Night Shift, and automatic brightness.')],
            [t('Still inn en fast skjermlysstyrke', 'Set a fixed screen brightness'), t('Sett lysstyrken omtrent midt på skyveknappen (ca. 50 %), så lenge teksten er lett å lese. Ikke endre den mellom rundene.', 'Set brightness about halfway on the slider (around 50%), provided text is easy to read. Do not change it between rounds.')],
            [t('Slå av musikk og annen lyd', 'Mute music and other audio'), t('Stopp musikk, video, varslinger og lyd i hodetelefoner under hele forsøket.', 'Turn off music, videos, notifications and headphones with audio during the entire study.')],
          ].map(([title, desc], i) => <button type="button" className={`check-tile ${checks[i] ? 'checked' : ''}`} onClick={() => toggle(i)} key={title} aria-pressed={checks[i]}>
            <span className="check-square">{checks[i] ? <Check size={17}/> : i === 3 ? <VolumeX size={15}/> : null}</span><span><b>{title}</b><small>{desc}</small></span>
          </button>)}
          <FullscreenToggle lang={lang}/>
        </div>
      </div>
      <div className="calibration-action"><span>{checks.filter(Boolean).length}/4 {t('punkter fullført', 'checks completed')}</span>
        <Button onClick={onNext} disabled={!checks.every(Boolean)}>{t('Jeg er klar', 'I am ready')} <ArrowRight size={18}/></Button></div>
    </main><Footer lang={lang}/>
  </div>;
}

function ConditionIcon({ condition, size = 21 }: { condition: Condition; size?: number }) {
  return condition === 'ORANGE' ? <ThermometerSun size={size}/> : condition === 'BLUE' ? <Sun size={size}/> : <Circle size={size}/>;
}

function ConditionDots({ current }: { current: number }) {
  return <div className="step-dots">{[0,1,2].map(i => <span key={i} className={i < current ? 'complete' : i === current ? 'active' : ''}/>)}</div>;
}

function useCountdown(deadline: number | null | undefined, offsetSeconds: number): number {
  // Store only the clock tick, not seconds remaining. If a phase changes,
  // its NEW deadline is used immediately on this same render, so the expired
  // distraction timer cannot accidentally trigger recall auto-submission.
  const [currentUnixSeconds, setCurrentUnixSeconds] = useState(() => Date.now() / 1000);
  useEffect(() => {
    const update = () => setCurrentUnixSeconds(Date.now() / 1000);
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, []);
  return secondsRemaining(deadline, offsetSeconds, currentUnixSeconds);
}

function Clock({ seconds, total, lang }: { seconds: number; total: number; lang: Language }) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remain = (seconds % 60).toString().padStart(2, '0');
  const pct = Math.min(100, Math.max(0, seconds / total * 100));
  return <div className="clock"><div className="clock-heading"><span><Clock3 size={17}/> {translate('Tid igjen', 'Time remaining', lang)}</span><b className={seconds <= 10 ? 'urgent' : ''}>{minutes}:{remain}</b></div>
    <div className="progress-track"><div className="progress-fill" style={{width: `${pct}%`}}/></div>
  </div>;
}

function Setup({ condition, index, lang, onStart, busy, colorReady }: {
  condition: Condition; index: number; lang: Language; onStart: () => Promise<void>; busy: boolean; colorReady: boolean;
}) {
  const t = (nb: string, en: string) => translate(nb, en, lang);
  const label = LABELS[condition];
  return <div className="study-center study-setup">
    <div className="pill"><ConditionIcon condition={condition} size={16}/>{t('RUNDE', 'ROUND')} {index + 1} / 3</div>
    <div className={`light-orb light-orb-${condition.toLowerCase()}`}><ConditionIcon condition={condition} size={38}/></div>
    <h1>{t(label.nb, label.en)}</h1>
    <p>{t(label.descriptionNb, label.descriptionEn)} · {COLORS[condition]}</p>
    {index > 0 && <p className="between-round">{t('Forrige runde er lagret. Takk for innsatsen så langt.', 'Your previous round was saved. Thank you for continuing.')}</p>}
    <div className="instruction-card"><div className="instruction-icon"><Focus size={22}/></div><div>
      <b>{t('Se på skjermen og venn deg til fargen', 'Look at the screen and adapt to the color')}</b>
      <span>{t('I 60 sekunder ser du bare en farge og en nedtelling. Ikke endre skjermens lysstyrke.',
        'You will see only the color and a timer for 60 seconds. Do not change your screen brightness.')}</span>
    </div></div>
    <Button disabled={busy || !colorReady} onClick={() => void onStart()}>
      {colorReady ? t('Start denne runden', 'Start this round') : t('Gjør bakgrunnen klar …', 'Preparing background…')} <ArrowRight size={18}/>
    </Button>
  </div>;
}

function Acclimation({ seconds, condition, lang, onCancel, busy, error }: {
  seconds: number; condition: Condition; lang: Language; onCancel: () => Promise<void>;
  busy: boolean; error: string | null;
}) {
  const [confirmCancel, setConfirmCancel] = useState(false);
  const t = (nb: string, en: string) => translate(nb, en, lang);
  return <main className={`acclimation-screen acclimation-${condition.toLowerCase()}`}
    aria-label="60-second screen color adaptation">
    <div className="acclimation-stack">
      <div className="acclimation-timer" role="timer" aria-live="off" aria-label={`${seconds} seconds remaining`}>
        {String(Math.floor(seconds / 60)).padStart(2,'0')}:{String(seconds % 60).padStart(2,'0')}
      </div>
      <div className="acclimation-actions">
        <p className="acclimation-explanation">{t(
          'Vi venter i 60 sekunder slik at øynene kan venne seg til bakgrunnsfargen. Runden fortsetter automatisk. Du trenger ikke trykke på noe.',
          'The 60-second wait lets your eyes adapt to the background color. The round continues automatically. You do not need to press anything.'
        )}</p>
        {seconds > 0 && (confirmCancel ? <>
          <p className="acclimation-confirm-message" role="status">{t(
            'Vil du avbryte? Da går du tilbake til rundestart, og de 60 sekundene starter på nytt neste gang.',
            'Cancel this wait? You will return to round setup, and the full 60 seconds will restart next time.'
          )}</p>
          <div className="acclimation-buttons">
            <button type="button" className="acclimation-back" disabled={busy}
              onClick={() => setConfirmCancel(false)}>{t('Fortsett å vente', 'Keep waiting')}</button>
            <button type="button" className="acclimation-back acclimation-confirm-button"
              disabled={busy} onClick={() => void onCancel()}>
              <ArrowLeft size={17}/>{busy ? t('Går tilbake …', 'Going back…') : t('Ja, gå tilbake', 'Yes, go back')}
            </button>
          </div>
        </> : <button type="button" className="acclimation-back" disabled={busy}
            onClick={() => setConfirmCancel(true)}>
          <ArrowLeft size={17}/>{t('Tilbake til rundestart', 'Go back to round setup')}
        </button>)}
        {error && <p className="acclimation-error" role="alert">{error}</p>}
      </div>
    </div>
  </main>;
}

function Learning({ pairs, seconds, lang }: { pairs: Pair[]; seconds: number; lang: Language }) {
  const t = (nb: string, en: string) => translate(nb, en, lang);
  return <div className="phase-main"><div className="phase-tag"><Brain size={16}/>{t('MEMORERING', 'MEMORIZATION')}</div>
    <h1>{t('Husk disse ordparene', 'Remember these word pairs')}</h1>
    <p>{t('Du har 75 sekunder til å lære åtte ordpar. Det er helt greit å ikke huske alle. Rekkefølgen blir endret i testen.',
      'You have 75 seconds to learn eight pairs. It is okay not to remember every one. The order will change in the test.')}</p>
    <div className="pairs-grid">{pairs.map((pair, idx) => <div className="pair-tile" key={pair.word}>
      <span className="pair-number">{String(idx + 1).padStart(2,'0')}</span><b>{pair.word}</b><span className="pair-arrow">→</span><span>{pair.meaning}</span>
    </div>)}</div>
    <div className="no-notes"><Eye size={17}/>{t('Unngå å skrive ned eller ta bilde av ordene.', 'Do not write down or photograph the word pairs.')}</div>
    <Clock seconds={seconds} total={75} lang={lang}/>
  </div>;
}

type Problem = { a: number; b: number; correct: number };
function newProblem(): Problem {
  const a = 12 + Math.floor(Math.random() * 34);
  const b = 8 + Math.floor(Math.random() * 27);
  return { a, b, correct: a + b };
}
function Distraction({ seconds, lang, id, index }: { seconds: number; lang: Language; id: string; index: number }) {
  const [question, setQuestion] = useState<Problem>(newProblem);
  const [value, setValue] = useState('');
  const [stats, setStats] = useState<{attempts: number; correct: number}>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(mathKey(id,index)) || '{}');
      const attempts = Number(saved.attempts);
      const correct = Number(saved.correct);
      if (Number.isSafeInteger(attempts) && Number.isSafeInteger(correct) &&
          attempts >= 0 && attempts <= 100 && correct >= 0 && correct <= attempts)
        return {attempts, correct};
    } catch { /* storage is optional */ }
    return {attempts:0, correct:0};
  });
  const t = (nb: string, en: string) => translate(nb, en, lang);
  const answer = () => {
    if (!value.trim()) return;
    const next = {attempts:Math.min(100,stats.attempts + 1),
                  correct:Math.min(100,stats.correct + (Number(value) === question.correct ? 1 : 0))};
    setStats(next);
    localStorage.setItem(mathKey(id,index), JSON.stringify(next));
    setQuestion(newProblem()); setValue('');
  };
  return <div className="phase-main distraction-main"><div className="phase-tag"><Focus size={16}/>{t('DISTRAKSJONSOPPGAVE', 'DISTRACTION TASK')}</div>
    <h1>{t('En liten mental pause', 'A quick mental reset')}</h1>
    <p>{t('Løs regnestykkene. Ikke repeter ordparene mens du venter.', 'Solve the arithmetic problems. Do not rehearse the word pairs while waiting.')}</p>
    <div className="math-card"><span>{t('HVA BLIR SUMMEN?', 'WHAT IS THE SUM?')}</span>
      <div className="math-expression">{question.a} <small>+</small> {question.b} <small>=</small> <span className="math-unknown" aria-label={t('Ukjent svar', 'Unknown answer')}>?</span></div>
      <form onSubmit={event => {event.preventDefault(); answer();}} className="math-form">
        <input aria-label={t('Svaret ditt', 'Your answer')} type="number" inputMode="numeric" value={value} onChange={event=>setValue(event.target.value)} placeholder={t('Ditt svar','Your answer')}/>
        <Button type="submit">{t('Svar', 'Submit')} <ArrowRight size={17}/></Button>
      </form><small>{t('Oppgaver besvart', 'Problems attempted')}: {stats.attempts} · {t('Riktig', 'Correct')}: {stats.correct}</small>
    </div><Clock seconds={seconds} total={30} lang={lang}/>
  </div>;
}

function Recall({ state, seconds, offsetSeconds, lang, id, onSubmit, busy, error }: {
  state: StudyState; seconds: number; offsetSeconds: number; lang: Language; id: string;
  onSubmit: (answers: string[], hiddenCount: number) => Promise<void>;
  busy: boolean; error: string | null;
}) {
  const index = state.round_index ?? 0;
  const words = state.words ?? [];
  const expired = seconds === 0 && deadlinePassed(state.phase_end_at, offsetSeconds, Date.now() / 1000);
  const serverRevision = state.draft_revision ?? 0;
  const storedRevision = Number(localStorage.getItem(draftVersionKey(id,index)) || 0);
  const initialRevision = Number.isSafeInteger(storedRevision) && storedRevision >= 0
    ? Math.max(storedRevision,serverRevision) : serverRevision;
  const [answers, setAnswers] = useState<string[]>(() => {
    const server = state.draft_answers?.length === 8 ? state.draft_answers : Array(8).fill('');
    // Expired sessions must never allow a local unsent edit to count. Only the
    // checkpoint accepted by the server before the deadline can be recovered.
    if (expired) return server;
    try {
      const local = JSON.parse(localStorage.getItem(draftKey(id,index)) || 'null');
      if (Array.isArray(local) && local.length === 8 && local.every(x=>typeof x==='string') &&
          (storedRevision > serverRevision || !serverRevision)) return local;
    } catch { /* server checkpoint is the fallback */ }
    return server;
  });
  const latestAnswers = useRef(answers);
  const revision = useRef(initialRevision);
  const dirty = useRef(!expired && storedRevision > serverRevision);
  const [saveStatus, setSaveStatus] = useState<'idle'|'saving'|'saved'|'offline'>(dirty.current ? 'saving' : serverRevision ? 'saved' : 'idle');
  const submitted = useRef(false);
  const autoAttempted = useRef(false);
  // Freeze answers once the server's deadline is reached. Server-side scoring
  // independently refuses to accept newly supplied late answers.
  const frozenAnswers = useRef<string[] | null>(null);
  const [sendFailed, setSendFailed] = useState(false);
  const t = (nb: string, en: string) => translate(nb, en, lang);

  const flush = useCallback((keepalive = false, force = false) => {
    if (expired || (!dirty.current && !force) || words.length !== 8) return;
    const snapshot = latestAnswers.current.slice();
    const value = revision.current;
    dirty.current = false;
    void api.draft(id, index, value, snapshot, keepalive).then(response => {
      if (revision.current === value) {
        if (response.saved) setSaveStatus('saved');
        else { dirty.current = true; setSaveStatus('saving'); }
      }
    }).catch(() => {
      if (revision.current === value) {
        dirty.current = true;
        setSaveStatus('offline');
      }
    });
  }, [id,index,expired,words.length]);

  useEffect(() => {
    if (expired || !dirty.current) return;
    const debounce = window.setTimeout(() => flush(), 280);
    return () => window.clearTimeout(debounce);
  }, [answers,expired,flush]);
  useEffect(() => {
    if (expired) return;
    // Bounded, periodic retries, not an unbounded request per keystroke.
    const retry = window.setInterval(() => { if (dirty.current) flush(); }, 4000);
    // Even if a debounced save is already in flight, send the latest revision
    // with keepalive during navigation. Duplicate revision writes are safe.
    const visibility = () => { if (document.hidden) flush(true, true); };
    const pagehide = () => flush(true, true);
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('pagehide',pagehide);
    return () => {
      window.clearInterval(retry);
      document.removeEventListener('visibilitychange',visibility);
      window.removeEventListener('pagehide',pagehide);
    };
  }, [expired,flush]);

  const submit = useCallback(async () => {
    if (submitted.current || busy || words.length !== 8) return;
    submitted.current = true;
    setSendFailed(false);
    try { await onSubmit(frozenAnswers.current ?? latestAnswers.current,
                         Number(localStorage.getItem(hiddenKey(id,index)) || '0')); }
    catch { submitted.current = false; setSendFailed(true); }
  }, [busy,onSubmit,words.length,id,index]);
  useEffect(() => {
    if (!expired || words.length !== 8) return;
    if (frozenAnswers.current === null) frozenAnswers.current = answers.slice();
    if (!autoAttempted.current && !submitted.current && !busy) {
      autoAttempted.current = true;
      void submit();
    }
  }, [expired,words.length,busy,submit,answers]);

  return <div className="phase-main recall-main"><div className="phase-tag"><CheckCircle2 size={16}/>{t('HUKOMMELSESTEST', 'RECALL TEST')}</div>
    <h1>{t('Hva betyr ordene?', 'What do these words mean?')}</h1>
    <p>{t('Ordene er stokket om. Skriv det du husker, og la resten stå tomt.',
      'The order is shuffled. Enter what you remember and leave the rest blank.')}</p>
    <div className="answers-grid">{words.map((word,i) => <label className="answer-field" key={word}>
      <span><small>{String(i+1).padStart(2,'0')}</small><b>{word}</b></span>
      <input maxLength={80} autoComplete="off" spellCheck={false} value={answers[i] || ''}
        disabled={expired || busy} placeholder={t('Objekt …', 'Object…')}
        onBlur={() => flush()}
        onChange={event => {
          if (expired) return;
          const val=event.target.value;
          const next = latestAnswers.current.map((a,j)=>i===j ? val : a);
          latestAnswers.current = next;
          setAnswers(next);
          revision.current += 1;
          dirty.current = true;
          setSaveStatus('saving');
          try {
            localStorage.setItem(draftKey(id,index), JSON.stringify(next));
            localStorage.setItem(draftVersionKey(id,index),String(revision.current));
          } catch { /* server checkpoints remain available if storage is blocked */ }
        }} />
    </label>)}</div>
    <p className="checkpoint-status" role="status" aria-live="polite">
      {expired ? t('Svarfristen er nådd. Kun svar lagret innen fristen kan telles.', 'Time is up. Only answers saved before the deadline can count.') :
        saveStatus === 'saved' ? t('Svarene er sikkerhetslagret.', 'Answers backed up to the server.') :
        saveStatus === 'offline' ? t('Forbindelsen er brutt. Svarene er lagret på denne enheten; prøver igjen.', 'Connection interrupted. Answers saved on this device; retrying.') :
        saveStatus === 'saving' ? t('Sikkerhetslagrer …', 'Saving a backup…') :
        t('Svarene sikkerhetslagres automatisk mens du skriver.', 'Answers are backed up as you type.')}
    </p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    <div className="recall-footer"><div className="recall-clock"><Clock seconds={seconds} total={120} lang={lang}/></div>
      <Button disabled={busy || words.length !== 8 || (expired && !sendFailed)} onClick={() => void submit()}>
        {busy ? t('Lagrer …', 'Saving…') : expired && sendFailed ? t('Prøv å lagre igjen', 'Retry saving') : expired ? t('Tiden er ute', 'Time is up') : t('Lever svarene', 'Submit answers')} <ArrowRight size={17}/>
      </Button>
    </div><p className="submit-note" role={expired ? 'status' : undefined}>{expired
      ? (sendFailed ? t('Tiden er ute. Kontroller tilkoblingen og prøv igjen.', 'Time is up. Check your connection and try again.')
        : t('Tiden er ute. Vi lagrer svarene som ble mottatt innen fristen.', 'Time is up. Saving answers received before the deadline.'))
      : t('Du kan levere før fristen. Etter 120 sekunder låses svarene og sendes automatisk.',
           'You may submit early. After 120 seconds, answers lock and submit automatically.')}</p>
  </div>;
}

function Study({ state, offsetSeconds, lang, onLanguageChange, onStart, onCancelAcclimation, onRefresh, onSubmit, busy, error }: {
  state: StudyState; offsetSeconds: number; lang: Language; onLanguageChange: ChangeLanguage;
  onStart: () => Promise<void>; onCancelAcclimation: () => Promise<void>; onRefresh: () => Promise<void>;
  onSubmit: (answers: string[], hiddenCount: number) => Promise<void>; busy: boolean; error: string | null;
}) {
  const condition = state.condition ?? 'NEUTRAL';
  const phase = state.phase ?? 'setup';
  const seconds = useCountdown(state.phase_end_at, offsetSeconds);
  const index = state.round_index ?? 0;
  const phasePollInFlight = useRef(false);
  const [readyFor, setReadyFor] = useState<Condition | null>(null);
  // The background change finishes during SETUP, before the 60s adaptation
  // clock begins. Rapid clicks cannot shorten the adaptation period.
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setReadyFor(condition);
      return;
    }
    const timeout = window.setTimeout(() => setReadyFor(condition), 1900);
    return () => window.clearTimeout(timeout);
  }, [condition]);
  const colorReady = readyFor === condition;
  useEffect(() => {
    if (phase !== 'acclimation' && phase !== 'learning' && phase !== 'distraction') return;
    if (seconds !== 0) return;
    // Retry until server phase advances; tab suspensions do not reset timing.
    const tick = () => {
      if (phasePollInFlight.current) return;
      phasePollInFlight.current = true;
      void onRefresh().catch(() => undefined).finally(() => { phasePollInFlight.current = false; });
    };
    const first = window.setTimeout(tick, 350);
    const interval = window.setInterval(tick, 1500);
    return () => { window.clearTimeout(first); window.clearInterval(interval); };
  }, [phase, seconds, onRefresh]);
  useEffect(() => {
    const onResume = () => { if (!document.hidden && phase !== 'setup' && phase !== 'recall') void onRefresh().catch(() => undefined); };
    document.addEventListener('visibilitychange', onResume);
    return () => document.removeEventListener('visibilitychange', onResume);
  }, [phase, onRefresh]);
  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden && (phase === 'acclimation' || phase === 'learning' || phase === 'distraction' || phase === 'recall')) {
        const key = hiddenKey(state.participant_id,index);
        localStorage.setItem(key, String(Number(localStorage.getItem(key) || '0') + 1));
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [state.participant_id, index, phase]);
  const label = LABELS[condition];
  return <div className={`experiment-surface ${phase === 'acclimation' ? 'is-acclimating' : ''} ${phase === 'setup' && index === 0 ? 'intro-transition' : ''}`}
    style={{ '--ambient-color': COLORS[condition], backgroundColor: COLORS[condition] } as CSSProperties}>
    {phase === 'acclimation' ? <Acclimation key={`${index}-${state.phase_end_at}`} condition={condition} seconds={seconds} lang={lang}
      onCancel={onCancelAcclimation} busy={busy} error={error}/> :
    <div className="ambient">
    <div className="ambient-overlay">
      <header className="study-header"><Brand light/>
        <div className="study-header-right"><LanguageSwitcher lang={lang} onChange={onLanguageChange} disabled dark/><FullscreenToggle lang={lang}/><div className="condition-chip"><ConditionIcon condition={condition} size={17}/>{translate(label.nb, label.en, lang)}</div>
          <div className="round-chip">{translate('RUNDE', 'ROUND', lang)} {index + 1}/3</div></div>
      </header>
      <div className="ambient-content">
        <div className="study-card"><div className="study-card-top"><div className="research-index">{translate('Hukommelsesstudie', 'Memory study', lang)}</div><ConditionDots current={index}/></div>
          {phase === 'setup' ? <Setup key={index} condition={condition} index={index} lang={lang} onStart={onStart} busy={busy} colorReady={colorReady}/> :
           phase === 'learning' ? <Learning pairs={state.pairs ?? []} seconds={seconds} lang={lang}/> :
           phase === 'distraction' ? <Distraction key={index} seconds={seconds} lang={lang} id={state.participant_id} index={index}/> :
           <Recall key={index} id={state.participant_id} state={state} seconds={seconds} offsetSeconds={offsetSeconds} lang={lang} onSubmit={onSubmit} busy={busy} error={error}/>}
          {error && phase !== 'recall' && <div className="error-banner" role="alert">{error}<button onClick={()=>void onRefresh()}><RefreshCw size={15}/> {lang==='nb'?'Prøv igjen':'Retry'}</button></div>}
        </div>
        <div className="study-under"><span><ShieldCheck size={15}/>{translate('Pseudonym deltaker', 'Pseudonymous study', lang)}</span>
          <span>{translate('Ikke endre skjerminnstillingene underveis', 'Keep screen settings unchanged', lang)}</span>
          <span>{translate('Du kan trekke samtykket når som helst', 'You may withdraw consent at any time', lang)}</span>
        </div>
      </div>
    </div>
    </div>}
  </div>;
}

function PerceptionPage({ lang, onLanguageChange, onSubmit, onTimeout, deadline, offsetSeconds, busy, error }: {
  lang: Language; onLanguageChange: ChangeLanguage;
  onSubmit: (payload: Perception) => Promise<void>; onTimeout: () => Promise<void>;
  deadline: number | null | undefined; offsetSeconds: number;
  busy: boolean; error: string | null;
}) {
  const t = (nb: string, en: string) => translate(nb, en, lang);
  const [difference, setDifference] = useState<Perception['perceived_difference'] | ''>('');
  const [easiest, setEasiest] = useState<Perception['perceived_easiest'] | ''>('');
  const remaining = useCountdown(deadline, offsetSeconds);
  const timedOut = remaining === 0;
  useEffect(() => {
    if (!timedOut) return;
    // The server is authoritative. Retry fetching the saved results if offline;
    // do not fabricate a SKIPPED answer or create a synthetic survey response.
    void onTimeout().catch(() => undefined);
    const retry = window.setInterval(() => void onTimeout().catch(() => undefined), 3000);
    return () => window.clearInterval(retry);
  }, [timedOut, onTimeout]);
  const differenceOptions: {value: Perception['perceived_difference']; nb: string; en: string}[] = [
    {value:'NONE',nb:'Ingen forskjell',en:'No difference'},
    {value:'SMALL',nb:'Liten forskjell',en:'Small difference'},
    {value:'MODERATE',nb:'Tydelig forskjell',en:'Noticeable difference'},
    {value:'LARGE',nb:'Stor forskjell',en:'Large difference'},
    {value:'UNSURE',nb:'Usikker',en:'Not sure'},
  ];
  const easiestOptions: {value: Perception['perceived_easiest']; nb: string; en: string}[] = [
    {value:'ORANGE',nb:'Oransje',en:'Orange'},
    {value:'BLUE',nb:'Blå',en:'Blue'},
    {value:'NEUTRAL',nb:'Grå',en:'Gray'},
    {value:'SAME',nb:'Omtrent likt',en:'About the same'},
    {value:'UNSURE',nb:'Usikker',en:'Not sure'},
  ];
  return <div className="site-shell perception-page"><Header lang={lang} onLanguageChange={onLanguageChange}/>
    <main className="perception-main">
      <p className="perception-step">{t('Ferdig med forsøket', 'The study is complete')}</p>
      <h1>{t('Hvordan opplevde du fargene?', 'How did the colors feel?')}</h1>
      <p className="perception-intro">{t(
        'Tre hukommelsesrunder er allerede lagret. Disse to spørsmålene er valgfrie og påvirker ikke poengsummen din.',
        'All three memory rounds are already saved. These two questions are optional and do not affect your scores.')}</p>
      <div className="perception-save-status" role="status">
        <span><CheckCircle2 size={18} aria-hidden="true" /> {t('3 av 3 runder lagret på serveren', '3 of 3 rounds saved on the server')}</span>
        <span className="perception-countdown" aria-label={t('Tid igjen til resultatvisning', 'Time until results appear')}>
          <Clock3 size={16} aria-hidden="true" /> {String(Math.floor(remaining / 60)).padStart(2,'0')}:{String(remaining % 60).padStart(2,'0')}
        </span>
      </div>
      <p className="perception-time-note">{timedOut
        ? t('Tiden er ute. Vi åpner de lagrede resultatene dine. Hvis forbindelsen er brutt, kan du åpne siden på nytt senere.',
            'Time is up. Opening your saved results. If your connection is interrupted, you can return later.')
        : t('Etter 90 sekunder vises resultatene automatisk, selv om du ikke svarer. Du kan også hoppe over spørsmålene.',
            'Your results appear automatically after 90 seconds, even if you do not answer. You may also skip the questions.')}</p>
      <form onSubmit={event => {
        event.preventDefault();
        if (!timedOut && difference && easiest) void onSubmit({perceived_difference:difference, perceived_easiest:easiest});
      }}>
        <fieldset className="perception-question" disabled={busy || timedOut}>
          <legend>{t('Opplevde du noen forskjell i hvor enkelt det var å huske ordene med de ulike bakgrunnsfargene?',
            'Did remembering the words feel different between the background colors?')}</legend>
          <div className="perception-options">{differenceOptions.map(option =>
            <label className={`perception-choice ${difference===option.value?'selected':''}`} key={option.value}>
              <input type="radio" name="difference" value={option.value} checked={difference===option.value}
                onChange={()=>setDifference(option.value)}/>
              <span>{t(option.nb, option.en)}</span>
            </label>)}</div>
        </fieldset>
        <fieldset className="perception-question" disabled={busy || timedOut}>
          <legend>{t('Hvilken bakgrunn opplevde du at det var enklest å huske ord med?',
            'With which background did remembering words feel easiest?')}</legend>
          <div className="perception-options">{easiestOptions.map(option =>
            <label className={`perception-choice ${easiest===option.value?'selected':''}`} key={option.value}>
              <input type="radio" name="easiest" value={option.value} checked={easiest===option.value}
                onChange={()=>setEasiest(option.value)}/>
              <span>{t(option.nb, option.en)}</span>
            </label>)}</div>
        </fieldset>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <div className="perception-actions">
          <Button type="submit" disabled={!difference || !easiest || busy || timedOut}>
            {busy ? t('Lagrer …', 'Saving…') : t('Se resultatene mine', 'See my results')} <ArrowRight size={18}/>
          </Button>
          <button type="button" className="perception-skip" disabled={busy || timedOut}
            onClick={() => void onSubmit({perceived_difference:'SKIPPED',perceived_easiest:'SKIPPED'})}>
            {t('Hopp over disse spørsmålene', 'Skip these questions')}
          </button>
        </div>
      </form>
      <p className="perception-note">{t('Disse vurderingene lagres separat fra hukommelsespoengsummen og brukes bare til å undersøke opplevde forskjeller.',
        'These impressions are stored separately from memory scores and are used only to explore perceived differences.')}</p>
    </main><Footer lang={lang}/></div>;
}

function Complete({ lang, onLanguageChange, error, state }: {
  lang: Language; onLanguageChange: ChangeLanguage;
  error: string | null; state: StudyState | null;
}) {
  const t = (nb: string, en: string) => translate(nb, en, lang);
  const review = state?.review ?? [];
  const recalled = review.reduce((sum, round) => sum + round.score, 0);
  const max = review.reduce((sum, round) => sum + round.max_score, 0);
  const mathCorrect = review.reduce((sum, round) => sum + round.math_correct, 0);
  const mathAttempts = review.reduce((sum, round) => sum + round.math_attempts, 0);
  return <div className="site-shell"><Header lang={lang} onLanguageChange={onLanguageChange}/>
    <main className="results-wrap">
      <div className="results-head">
        <div className="results-topline">{t('Alle rundene er fullført', 'All three rounds are complete')} <CheckCircle2 size={18}/></div>
        <h1>{t('Bra jobbet med å fullføre.', 'Well done for finishing.')}</h1>
        <p>{t('Alle svarene er registrert. Nå kan du se hvordan det gikk – uten at resultatene påvirker de andre rundene.',
          'All your answers have been saved. You can now review your performance without affecting any later rounds.')}</p>
        <p>{t('Forsøket er fullført for denne deltaker-ID-en. Du kan oppdatere nettsiden og se resultatene igjen, men ikke starte en ny gjennomføring med samme økt.',
          'This participant session is complete. You can refresh the page to view your results again, but you cannot start another run in this session.')}</p>
      </div>
      <section className="results-overview" aria-label={t('Oppsummering', 'Summary')}>
        <div><span>{t('Ord du husket', 'Words recalled')}</span><strong>{recalled}<small>/{max || 24}</small></strong></div>
        <div><span>{t('Regnestykker riktig', 'Arithmetic correct')}</span><strong>{mathCorrect}<small>/{mathAttempts}</small></strong></div>
        <div><span>{t('Gjennomførte runder', 'Rounds completed')}</span><strong>3<small>/3</small></strong></div>
      </section>
      <section className="results-review" aria-labelledby="review-title">
        <h2 id="review-title">{t('Se gjennom svarene dine', 'Review your answers')}</h2>
        <p className="review-context">{t('Hver rad viser svaret ditt og hvilket ord som ble godkjent. Resultatene må tolkes som en pilot, ikke en vurdering av evner.',
          'Each row shows your answer and the accepted word. This pilot is not a judgment of your ability.')}</p>
        {review.map(round => <details className="review-round" key={round.round_index}>
          <summary><span className="review-title">{t('Runde', 'Round')} {round.round_index + 1} <small>{translate(LABELS[round.condition].nb,LABELS[round.condition].en,lang)}</small></span>
            <span className="review-score">{round.score}/{round.max_score} <span aria-hidden="true">⌄</span></span></summary>
          <div className="review-inner">
            <p>{t('Regnestykker', 'Arithmetic')}: <b>{round.math_correct}/{round.math_attempts}</b></p>
            <div className="review-labels"><span>{t('Ord', 'Word')}</span><span>{t('Ditt svar', 'Your answer')}</span><span>{t('Fasit', 'Correct answer')}</span></div>
            {round.items.map(item => <div className={`review-item ${item.correct ? 'correct' : 'incorrect'}`} key={item.word}>
              <b>{item.word}</b><span>{item.answer.trim() || t('Ikke besvart','Not answered')}</span>
              <span className="expected"><span className="review-status" aria-label={item.correct ? t('Riktig','Correct') : t('Ikke helt','Not quite')}>
                {item.correct ? <Check size={15}/> : <span aria-hidden="true">•</span>}</span>{item.expected}</span>
            </div>)}
          </div>
        </details>)}
      </section>
      <div className="results-footnote"><ShieldCheck size={18}/><p>{t('Takk for bidraget ditt. Ikke gjenta forsøket for å forbedre poengsummen – et nytt forsøk vil gi misvisende forskningsdata.',
        'Thank you for taking part. Please do not repeat the experiment to improve your score, as retakes would distort the research data.')}</p></div>
      {error && <div className="error-banner" role="alert">{error}</div>}
    </main><Footer lang={lang}/></div>;
}

export default function App() {
  const [lang, setLangState] = useState<Language>(() => {
    const stored = localStorage.getItem(LANGUAGE_KEY);
    return stored && Object.hasOwn(LANGUAGE_NAMES, stored) ? stored as Language : detectBrowserLanguage(navigator.languages?.length ? navigator.languages : [navigator.language]);
  });
  const [id, setId] = useState<string | null>(() => localStorage.getItem(PARTICIPANT_KEY));
  const [view, setView] = useState<View>(() => localStorage.getItem(PARTICIPANT_KEY) ? 'loading' : 'intro');
  const [state, setState] = useState<StudyState | null>(null);
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [withdrawError, setWithdrawError] = useState<string | null>(null);
  const setLang = (next: Language) => { setLangState(next); document.documentElement.lang = next; document.documentElement.dir = directionForLanguage(next); localStorage.setItem(LANGUAGE_KEY, next); };
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = directionForLanguage(lang); }, [lang]);

  // Keep multiple tabs on the same participant. A newer tab must not create
  // another enrollment merely because it was opened before registration.
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== PARTICIPANT_KEY) return;
      setError(null);
      setWithdrawError(null);
      setState(null);
      if (event.newValue) {
        setId(event.newValue);
        setView('loading');
      } else {
        setId(null);
        setView('intro');
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const getState = useCallback(async (participantID: string) => {
    const data = await api.next(participantID);
    // An old request can finish after withdrawal in another tab. Never restore
    // a deleted or replaced session from an out-of-order network response.
    if (localStorage.getItem(PARTICIPANT_KEY) !== participantID) return;
    setOffset(data.server_now - Date.now() / 1000);
    setState(data);
    // Server progress is authoritative. A lost calibration flag must never
    // hide an active timed phase behind a second calibration screen.
    const isInitialSetup = !data.finished && data.phase === 'setup' && data.round_index === 0;
    if (!isInitialSetup) localStorage.setItem(CALIBRATED_KEY, participantID);
    if (data.finished) setView(data.perception_done ? 'complete' : 'perception');
    else if (isInitialSetup && localStorage.getItem(CALIBRATED_KEY) !== participantID) setView('calibration');
    else setView('study');
  }, []);

  useEffect(() => {
    if (!id) return;
    getState(id).catch(err => {
      setError(err instanceof Error ? err.message : 'Unable to load study');
      // Old/invalid participant IDs must not start a new participant silently.
      setView('loading');
    });
  }, [id, getState]);

  const register = async (input: Registration) => {
    if (busy) return;
    // Another tab may already have registered this browser. Reuse that
    // participant instead of creating a duplicate record.
    const existing = localStorage.getItem(PARTICIPANT_KEY) || id;
    if (existing) {
      if (existing !== id) { setId(existing); setView('loading'); }
      return;
    }
    setBusy(true); setError(null);
    try {
      const result = await api.register(input);
      storeParticipantToken(result.access_token);
      localStorage.setItem(PARTICIPANT_KEY, result.participant_id);
      setId(result.participant_id);
    } catch(err) { setError(err instanceof Error ? err.message : 'Registration failed'); }
    finally { setBusy(false); }
  };

  const refresh = useCallback(async () => {
    if (!id) return;
    try { await getState(id); setError(null); }
    catch(err) { setError(err instanceof Error ? err.message : 'Unable to connect'); throw err; }
  }, [getState, id]);

  const start = useCallback(async () => {
    if (!id || busy) return;
    setBusy(true); setError(null);
    try {
      const data = await api.start(id);
      setOffset(data.server_now - Date.now() / 1000);
      setState(data); setView('study');
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to start'); throw err; }
    finally { setBusy(false); }
  }, [id, busy]);

  const cancelAcclimation = useCallback(async () => {
    if (!id || !state || busy || state.phase !== 'acclimation' ||
        state.round_index === undefined || state.phase_end_at == null) return;
    setBusy(true); setError(null);
    try {
      const data = await api.cancelAcclimation(id, state.round_index, state.phase_end_at);
      setOffset(data.server_now - Date.now() / 1000);
      setState(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to return to round setup');
      // If the phase advanced while the request was in flight, re-sync rather
      // than showing a stale acclimation screen or offering a time bypass.
      try { await getState(id); } catch { /* retain the actionable error */ }
    } finally { setBusy(false); }
  }, [id, state, busy, getState]);

  const submit = useCallback(async (answers: string[], hidden: number) => {
    if (!id || !state || busy || state.round_index === undefined) return;
    const round = state.round_index;
    setBusy(true); setError(null);
    try {
      const raw = localStorage.getItem(mathKey(id,round));
      let math = {attempts:0, correct:0};
      try { if (raw) math = JSON.parse(raw); } catch { /* invalid optional stats */ }
      try {
        await api.submit(id, round, answers, hidden, math.attempts, math.correct);
      } catch (err) {
        // A connection may drop after the server committed the result. Check
        // server progress before telling the participant to retry the POST.
        try {
          const latest = await api.next(id);
          if (!latest.finished && latest.round_index === round) throw err;
        } catch (lookupError) {
          // A failed lookup cannot prove that the original submission saved.
          if (lookupError !== err) throw err;
          throw lookupError;
        }
      }
      localStorage.removeItem(mathKey(id,round));
      localStorage.removeItem(draftKey(id,round));
      localStorage.removeItem(draftVersionKey(id,round));
      localStorage.removeItem(hiddenKey(id,round));
      await getState(id);
    } catch(err) { setError(err instanceof Error ? err.message : 'Unable to save'); throw err; }
    finally { setBusy(false); }
  }, [id, state, busy, getState]);

  const submitPerception = async (payload: Perception) => {
    if (!id || busy) return;
    setBusy(true); setError(null);
    try {
      try {
        await api.perception(id, payload);
      } catch (err) {
        // A network interruption may occur after the server saved the response.
        const latest = await api.next(id).catch(() => null);
        if (!latest?.perception_done) throw err;
      }
      await getState(id);
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save'); }
    finally { setBusy(false); }
  };

  const withdraw = async () => {
    if (!id || busy) return;
    setBusy(true); setWithdrawError(null);
    try {
      // Retain the local session until the server confirms deletion.
      await api.withdraw(id);
      for (let index=0; index<3; index++) {
        localStorage.removeItem(draftKey(id,index));
        localStorage.removeItem(draftVersionKey(id,index));
        localStorage.removeItem(hiddenKey(id,index));
        localStorage.removeItem(mathKey(id,index));
      }
      localStorage.removeItem(PARTICIPANT_KEY);
      clearParticipantToken();
      localStorage.removeItem(CALIBRATED_KEY);
      setId(null); setState(null); setError(null); setView('intro');
    } catch (err) {
      setWithdrawError(err instanceof Error ? err.message : 'Unable to withdraw');
    } finally { setBusy(false); }
  };

  const content = (() => {
    if (view === 'loading') return <div className="loading-page"><Brand/><div className="loading-spinner"/>
      <p>{translate('Kobler til forsøket …', 'Connecting to study…', lang)}</p>
      {error && <><div className="error-banner">{error}</div>
        <Button onClick={() => { if (id) void getState(id).catch(() => undefined); }} secondary>
          <RefreshCw size={17}/>{translate('Prøv igjen', 'Retry', lang)}</Button>
      </>}
    </div>;
    if (view === 'intro') return <Intro lang={lang} setLang={setLang} onRegister={register} busy={busy} error={error}/>;
    if (view === 'calibration') return <Calibration lang={lang} onLanguageChange={setLang} onNext={() => {
      if (id) { localStorage.setItem(CALIBRATED_KEY,id); setView('study'); }
    }}/>;
    if (view === 'perception') return <PerceptionPage lang={lang} onLanguageChange={setLang} onSubmit={submitPerception}
      onTimeout={refresh} deadline={state?.perception_deadline_at} offsetSeconds={offset} busy={busy} error={error}/>;
    if (view === 'complete') return <Complete lang={lang} onLanguageChange={setLang} error={error} state={state}/>;
    if (!state || !id) return null;
    return <Study state={state} lang={lang} onLanguageChange={setLang} offsetSeconds={offset}
      onStart={start} onCancelAcclimation={cancelAcclimation} onRefresh={refresh}
      onSubmit={submit} busy={busy} error={error}/>;
  })();
  return <>{content}{id && <WithdrawControl lang={lang} onWithdraw={withdraw} busy={busy} error={withdrawError}/>}</>;
}
