import { useCallback, useEffect, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import {
  ArrowRight, Brain, Check, CheckCircle2, Clock3, Eye,
  Focus, Lightbulb, LockKeyhole, Monitor, Moon, RefreshCw,
  ShieldCheck, Sparkles, Sun, ThermometerSun,
} from 'lucide-react';
import { api, COLORS } from './api';
import type { Condition, Language, Pair, Registration, StudyState } from './api';

const PARTICIPANT_KEY = 'lm_v2_participant';
const LANGUAGE_KEY = 'lm_v2_language';
const CALIBRATED_KEY = 'lm_v2_calibrated';
const LABELS: Record<Condition, { nb: string; en: string; descriptionNb: string; descriptionEn: string }> = {
  WARM: { nb: 'Varmt lys', en: 'Warm light', descriptionNb: 'Varm skjermfarge', descriptionEn: 'Warm screen color' },
  COOL: { nb: 'Kaldt lys', en: 'Cool light', descriptionNb: 'Kald skjermfarge', descriptionEn: 'Cool screen color' },
  DARK: { nb: 'Mørkt miljø', en: 'Dark environment', descriptionNb: 'Nesten svart skjermbakgrunn', descriptionEn: 'Near-black screen background' },
};
const draftKey = (id: string, index: number) => `lm_v2_draft_${id}_${index}`;
const hiddenKey = (id: string, index: number) => `lm_v2_hidden_${id}_${index}`;

type View = 'loading' | 'intro' | 'calibration' | 'study' | 'complete';

function Brand({ light = false }: { light?: boolean }) {
  return <div className={`brand ${light ? 'brand-light' : ''}`}>
    <div className="brand-mark"><Brain size={20} strokeWidth={2} /></div>
    <div className="brand-copy"><b>HUKOMMELSE<span>LM</span></b><small>LIGHT & MEMORY RESEARCH</small></div>
  </div>;
}

function Header({ lang, page }: { lang: Language; page?: string }) {
  return <header className="topbar">
    <Brand />
    <div className="topbar-right">
      <span className="research-label"><span className="status-dot" /> {lang === 'nb' ? 'Forskningsprosjekt' : 'Research study'}</span>
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
  { lang: Language; setLang: (l: Language) => void; onRegister: (input: Registration) => void; busy: boolean; error: string | null }) {
  const [age, setAge] = useState('16_17');
  const [gender, setGender] = useState('prefer_not');
  const [consent, setConsent] = useState(false);
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  return <div className="site-shell">
    <Header lang={lang} />
    <main className="intro-layout">
      <div className="intro-main">
        <div className="eyebrow"><Sparkles size={15} /> {t('DIGITALT FORSKNINGSFORSØK', 'A DIGITAL RESEARCH EXPERIMENT')}</div>
        <h1>{t('Kan fargene rundt oss', 'Can the colors around us')}<br /><em>{t('påvirke hukommelsen?', 'affect our memory?')}</em></h1>
        <p className="hero-sub">{t('Bli med på et kort forskningsforsøk der vi undersøker om varme, kalde og mørke skjermmiljøer påvirker hvor lett vi lærer nye ord.',
          'Join a short research study exploring whether warm, cool and dark screen environments affect how easily we learn new words.')}</p>
        <div className="stats-strip">
          <div><Clock3 size={21}/><strong>10–15</strong><span>{t('minutter', 'minutes')}</span></div>
          <div><LayersIcon/><strong>3</strong><span>{t('runder', 'rounds')}</span></div>
          <div><LockKeyhole size={21}/><strong>{t('Ingen navn', 'No names')}</strong><span>{t('registreres', 'recorded')}</span></div>
        </div>
        <div className="process-preview">
          <div className="section-kicker">{t('SLIK FUNGERER DET', 'HOW IT WORKS')}</div>
          <div className="process-row"><span className="process-num">01</span><div><b>{t('Juster skjermen', 'Prepare your screen')}</b><small>{t('En enkel sjekkliste før forsøket starter', 'A simple checklist before beginning')}</small></div><Monitor size={19}/></div>
          <div className="process-row"><span className="process-num">02</span><div><b>{t('Lær 10 ordpar', 'Learn 10 word pairs')}</b><small>{t('Du får 60 sekunder til å memorere', 'You have 60 seconds to memorize')}</small></div><Brain size={19}/></div>
          <div className="process-row"><span className="process-num">03</span><div><b>{t('Test hukommelsen', 'Test your memory')}</b><small>{t('En kort distraksjon før du skriver svarene', 'A short distraction before you recall the answers')}</small></div><CheckCircle2 size={19}/></div>
        </div>
      </div>
      <aside className="enroll-card">
        <div className="enroll-head"><div className="enroll-icon"><Lightbulb size={22}/></div><div><span className="section-kicker">{t('DELTA I STUDIEN', 'PARTICIPATE')}</span><h2>{t('La oss begynne', 'Get started')}</h2></div></div>
        <p className="form-intro">{t('Svar på noen korte spørsmål før vi starter. Du kan når som helst trekke samtykket og slette dataene dine.',
          'Answer a few brief questions before starting. You may withdraw consent and delete your data at any time.')}</p>
        <label className="field"><span>{t('Språk', 'Language')}</span><div className="segmented">
          <button type="button" className={lang === 'nb' ? 'selected' : ''} onClick={() => setLang('nb')}>Norsk</button>
          <button type="button" className={lang === 'en' ? 'selected' : ''} onClick={() => setLang('en')}>English</button>
        </div></label>
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
        <label className="consent-control"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)}/>
          <span>{t('Jeg deltar frivillig og samtykker til at aldersgruppe, eventuelt kjønn, språk og testresultater lagres med en tilfeldig deltaker-ID for forskning. Ingen navn eller e-postadresser samles inn.',
            'I participate voluntarily and agree that my age range, optional gender, language and test results are stored under a random participant ID for research. No names or email addresses are collected.')}</span>
        </label>
        <p className="privacy-notice"><ShieldCheck size={15}/>{t('Deltakere under 18 år: krav til samtykke må avklares med prosjektansvarlig.', 'Under 18: consent requirements must be confirmed with the study organizer.')}</p>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <Button disabled={!consent || busy} className="fullwidth" onClick={() => onRegister({ language: lang, age_band: age, gender, consent: true })}>
          {busy ? t('Registrerer …', 'Registering…') : t('Start forsøket', 'Begin experiment')} <ArrowRight size={18}/>
        </Button>
        <div className="enroll-footer"><span className="status-dot" /> {t('Tar omtrent 10–15 minutter', 'Approximately 10–15 minutes')}</div>
      </aside>
    </main>
    <Footer lang={lang}/>
  </div>;
}

function LayersIcon() { return <div className="layers-icon"><span/><span/><span/></div>; }
function Footer({ lang }: { lang: Language }) {
  return <footer className="site-footer"><span>© HUKOMMELSE LM</span><span>{lang === 'nb' ? 'En studie av skjermfarger og ordhukommelse' : 'A study of screen color and word memory'}</span><span>RESEARCH EDITION 2.0</span></footer>;
}

function Calibration({ lang, onNext }: { lang: Language; onNext: () => void }) {
  const [checks, setChecks] = useState([false, false, false]);
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  const toggle = (i: number) => setChecks(old => old.map((v,j) => i === j ? !v : v));
  return <div className="site-shell"><Header lang={lang} page={t('Forberedelser', 'Preparation')}/>
    <main className="calibration-layout">
      <div className="eyebrow"><Monitor size={16}/>{t('TRINN 1 AV 2', 'STEP 1 OF 2')}</div>
      <h1 className="page-title">{t('Gjør skjermen klar', 'Prepare your screen')}</h1>
      <p className="page-description">{t('For at forsøket skal bli så sammenlignbart som mulig, bør alle bruke samme innstillinger gjennom de tre rundene.',
        'To make results as comparable as possible, keep the same settings throughout all three rounds.')}</p>
      <div className="calibration-grid">
        <div className="calibration-checklist">
          {[
            [t('Sitt i et mørkt eller svakt opplyst rom', 'Use a dark or dimly lit room'), t('Behold den samme rombelysningen gjennom hele forsøket.', 'Keep room lighting unchanged throughout the study.')],
            [t('Slå av automatisk farge og lysstyrke', 'Turn off automatic color and brightness'), t('Deaktiver nattmodus, True Tone, Night Shift og automatisk lysstyrke.', 'Disable night mode, True Tone, Night Shift, and automatic brightness.')],
            [t('Velg fast skjermlysstyrke', 'Set a fixed screen brightness'), t('Bruk omtrent 70 % dersom det er behagelig. Ikke endre den underveis.', 'Aim for around 70% if comfortable. Do not change it later.')],
          ].map(([title, desc], i) => <button type="button" className={`check-tile ${checks[i] ? 'checked' : ''}`} onClick={() => toggle(i)} key={title}>
            <span className="check-square">{checks[i] && <Check size={17}/>}</span><span><b>{title}</b><small>{desc}</small></span>
          </button>)}
          <Button onClick={() => document.documentElement.requestFullscreen?.().catch(() => undefined)} secondary><Monitor size={17}/> {t('Prøv fullskjerm', 'Try fullscreen')}</Button>
        </div>
        <div className="calibration-visual">
          <div className="section-kicker">{t('KONTRASTKONTROLL', 'CONTRAST CHECK')}</div>
          <h3>{t('Ser du begge symbolene?', 'Can you see both symbols?')}</h3>
          <p>{t('Kontroller at du kan se figurene tydelig uten å myse. Dette er ikke en måling av faktisk lysstyrke.',
            'Make sure both symbols are clearly visible without squinting. This does not measure actual brightness.')}</p>
          <div className="swatch-row"><div className="swatch-light"><span className="shape-dark">✦</span></div><div className="swatch-dark"><span className="shape-light">✦</span></div></div>
          <div className="calibration-hint"><Eye size={17}/>{t('La skjermen ha samme lysstyrke under alle rundene.', 'Keep the brightness unchanged for all rounds.')}</div>
        </div>
      </div>
      <div className="calibration-action"><span>{checks.filter(Boolean).length}/3 {t('punkter fullført', 'checks completed')}</span>
        <Button onClick={onNext} disabled={!checks.every(Boolean)}>{t('Jeg er klar', 'I am ready')} <ArrowRight size={18}/></Button></div>
    </main><Footer lang={lang}/>
  </div>;
}

function ConditionIcon({ condition, size = 21 }: { condition: Condition; size?: number }) {
  return condition === 'WARM' ? <ThermometerSun size={size}/> : condition === 'COOL' ? <Sun size={size}/> : <Moon size={size}/>;
}

function ConditionDots({ current }: { current: number }) {
  return <div className="step-dots">{[0,1,2].map(i => <span key={i} className={i < current ? 'complete' : i === current ? 'active' : ''}/>)}</div>;
}

function timeRemaining(deadline: number | null | undefined, offsetSeconds: number): number {
  if (!deadline) return 0;
  return Math.max(0, Math.ceil(deadline - (Date.now() / 1000 + offsetSeconds)));
}

function useCountdown(deadline: number | null | undefined, offsetSeconds: number): number {
  const [seconds, setSeconds] = useState(() => timeRemaining(deadline, offsetSeconds));
  useEffect(() => {
    const update = () => setSeconds(timeRemaining(deadline, offsetSeconds));
    update();
    const timer = window.setInterval(update, 200);
    return () => window.clearInterval(timer);
  }, [deadline, offsetSeconds]);
  return seconds;
}

function Clock({ seconds, total, lang }: { seconds: number; total: number; lang: Language }) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remain = (seconds % 60).toString().padStart(2, '0');
  const pct = Math.min(100, Math.max(0, seconds / total * 100));
  return <div className="clock"><div className="clock-heading"><span><Clock3 size={17}/> {lang === 'nb' ? 'Tid igjen' : 'Time remaining'}</span><b className={seconds <= 10 ? 'urgent' : ''}>{minutes}:{remain}</b></div>
    <div className="progress-track"><div className="progress-fill" style={{width: `${pct}%`}}/></div>
  </div>;
}

function Setup({ condition, index, lang, onStart, busy }: {
  condition: Condition; index: number; lang: Language; onStart: () => Promise<void>; busy: boolean;
}) {
  const [countTo, setCountTo] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const called = useRef(false);
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  useEffect(() => {
    if (!countTo) return;
    const timer = window.setInterval(() => setNow(Date.now()), 150);
    return () => window.clearInterval(timer);
  }, [countTo]);
  const seconds = countTo ? Math.max(0, Math.ceil((countTo - now) / 1000)) : 15;
  useEffect(() => {
    if (countTo && seconds === 0 && !called.current) {
      called.current = true;
      onStart().catch(() => { called.current = false; setCountTo(null); });
    }
  }, [countTo, seconds, onStart]);
  const label = LABELS[condition];
  return <div className="study-center study-setup">
    <div className="pill"><ConditionIcon condition={condition} size={16}/>{t('RUNDE', 'ROUND')} {index + 1} / 3</div>
    <div className={`light-orb light-orb-${condition.toLowerCase()}`}><ConditionIcon condition={condition} size={38}/></div>
    <h1>{t(label.nb, label.en)}</h1>
    <p>{t(label.descriptionNb, label.descriptionEn)} · {COLORS[condition]}</p>
    <div className="instruction-card"><div className="instruction-icon"><Focus size={22}/></div><div>
      <b>{t('Se på skjermen og tilpass deg lysmiljøet', 'Look at the screen and adapt to the color')}</b>
      <span>{t('Når du starter, får du 15 sekunder tilvenning før ordparene vises. Ikke endre skjermens lysstyrke.',
        'After starting, allow 15 seconds to adapt before the word pairs appear. Do not adjust screen brightness.')}</span>
    </div></div>
    {countTo ? <div className="ready-timer"><div className="count-number">{seconds}</div><span>{t('Tilvenning før memorering', 'Adaptation before memorizing')}</span>
      <div className="mini-track"><div style={{width: `${seconds / 15 * 100}%`}}/></div></div> :
      <Button disabled={busy} onClick={() => { called.current = false; setCountTo(Date.now() + 15_000); }}>
        {t('Start denne runden', 'Start this round')} <ArrowRight size={18}/>
      </Button>}
  </div>;
}

function Learning({ pairs, seconds, lang }: { pairs: Pair[]; seconds: number; lang: Language }) {
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  return <div className="phase-main"><div className="phase-tag"><Brain size={16}/>{t('MEMORERING', 'MEMORIZATION')}</div>
    <h1>{t('Husk disse ordparene', 'Remember these word pairs')}</h1>
    <p>{t('Du har 60 sekunder. Prøv å huske hvilket objekt hvert kunstig ord betyr.',
      'You have 60 seconds. Try to remember which object each invented word represents.')}</p>
    <div className="pairs-grid">{pairs.map((pair, idx) => <div className="pair-tile" key={pair.word}>
      <span className="pair-number">{String(idx + 1).padStart(2,'0')}</span><b>{pair.word}</b><span className="pair-arrow">→</span><span>{pair.meaning}</span>
    </div>)}</div>
    <div className="no-notes"><Eye size={17}/>{t('Unngå å skrive ned eller ta bilde av ordene.', 'Do not write down or photograph the word pairs.')}</div>
    <Clock seconds={seconds} total={60} lang={lang}/>
  </div>;
}

type Problem = { a: number; b: number; correct: number };
function newProblem(): Problem {
  const a = 12 + Math.floor(Math.random() * 34);
  const b = 8 + Math.floor(Math.random() * 27);
  return { a, b, correct: a + b };
}
function Distraction({ seconds, lang }: { seconds: number; lang: Language }) {
  const [question, setQuestion] = useState<Problem>(newProblem);
  const [value, setValue] = useState('');
  const [correct, setCorrect] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  const answer = () => {
    if (!value.trim()) return;
    setAttempts(v => v + 1);
    if (Number(value) === question.correct) setCorrect(v => v + 1);
    setQuestion(newProblem()); setValue('');
  };
  return <div className="phase-main distraction-main"><div className="phase-tag"><Focus size={16}/>{t('DISTRAKSJONSOPPGAVE', 'DISTRACTION TASK')}</div>
    <h1>{t('En liten mental pause', 'A quick mental reset')}</h1>
    <p>{t('Løs regnestykkene. Ikke repeter ordparene mens du venter.', 'Solve the arithmetic problems. Do not rehearse the word pairs while waiting.')}</p>
    <div className="math-card"><span>{t('HVA BLIR SUMMEN?', 'WHAT IS THE SUM?')}</span>
      <div className="math-expression">{question.a} <small>+</small> {question.b} <small>=</small> <span>?</span></div>
      <form onSubmit={event => {event.preventDefault(); answer();}} className="math-form">
        <input aria-label={t('Svaret ditt', 'Your answer')} type="number" inputMode="numeric" value={value} onChange={event=>setValue(event.target.value)} placeholder={t('Ditt svar','Your answer')}/>
        <Button type="submit">{t('Svar', 'Submit')} <ArrowRight size={17}/></Button>
      </form><small>{t('Oppgaver besvart', 'Problems attempted')}: {attempts} · {t('Riktig', 'Correct')}: {correct}</small>
    </div><Clock seconds={seconds} total={30} lang={lang}/>
  </div>;
}

function Recall({ state, seconds, lang, id, onSubmit, busy, error }: {
  state: StudyState; seconds: number; lang: Language; id: string;
  onSubmit: (answers: string[], hiddenCount: number) => Promise<void>;
  busy: boolean; error: string | null;
}) {
  const index = state.round_index ?? 0;
  const words = state.words ?? [];
  const [answers, setAnswers] = useState<string[]>(() => {
    try {
      const old = JSON.parse(localStorage.getItem(draftKey(id,index)) || 'null');
      return Array.isArray(old) && old.length === 10 ? old : Array(10).fill('');
    } catch { return Array(10).fill(''); }
  });
  const submitted = useRef(false);
  const autoAttempted = useRef(false);
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  useEffect(() => { localStorage.setItem(draftKey(id,index), JSON.stringify(answers)); }, [answers, id, index]);
  const submit = useCallback(async () => {
    if (submitted.current || busy || words.length !== 10) return;
    submitted.current = true;
    try { await onSubmit(answers, Number(localStorage.getItem(hiddenKey(id,index)) || '0')); }
    catch { submitted.current = false; }
  }, [busy, answers, onSubmit, words.length, id, index]);
  useEffect(() => {
    if (seconds === 0 && !autoAttempted.current && !submitted.current && !busy && words.length === 10) {
      autoAttempted.current = true; void submit();
    }
  }, [seconds, busy, submit, words.length]);
  return <div className="phase-main recall-main"><div className="phase-tag"><CheckCircle2 size={16}/>{t('HUKOMMELSESTEST', 'RECALL TEST')}</div>
    <h1>{t('Hva betyr ordene?', 'What do these words mean?')}</h1>
    <p>{t('Skriv objektet du husker for hvert ord. Hvis du ikke husker, lar du feltet stå tomt.',
      'Type the object you remember for each word. Leave an answer blank if you do not remember.')}</p>
    <div className="answers-grid">{words.map((word,i) => <label className="answer-field" key={word}>
      <span><small>{String(i+1).padStart(2,'0')}</small><b>{word}</b></span>
      <input maxLength={80} autoComplete="off" spellCheck={false} value={answers[i] || ''}
        placeholder={t('Objekt …', 'Object…')} onChange={event => {
          const val=event.target.value; setAnswers(old => old.map((a,j)=>i===j ? val : a));
        }} />
    </label>)}</div>
    {error && <div className="error-banner" role="alert">{error}</div>}
    <div className="recall-footer"><div className="recall-clock"><Clock seconds={seconds} total={120} lang={lang}/></div>
      <Button disabled={busy || words.length !== 10} onClick={() => void submit()}>
        {busy ? t('Lagrer …', 'Saving…') : t('Lever svarene', 'Submit answers')} <ArrowRight size={17}/>
      </Button>
    </div><p className="submit-note">{t('Svarene sendes automatisk når tiden går ut.', 'Answers are submitted automatically when time runs out.')}</p>
  </div>;
}

function Study({ state, offsetSeconds, lang, onStart, onRefresh, onSubmit, onWithdraw, busy, error }: {
  state: StudyState; offsetSeconds: number; lang: Language;
  onStart: () => Promise<void>; onRefresh: () => Promise<void>;
  onSubmit: (answers: string[], hiddenCount: number) => Promise<void>; onWithdraw: () => Promise<void>; busy: boolean; error: string | null;
}) {
  const condition = state.condition ?? 'DARK';
  const phase = state.phase ?? 'setup';
  const seconds = useCountdown(state.phase_end_at, offsetSeconds);
  const index = state.round_index ?? 0;
  const phasePollInFlight = useRef(false);
  useEffect(() => {
    if (phase !== 'learning' && phase !== 'distraction') return;
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
    const onVisibility = () => {
      if (document.hidden && (phase === 'learning' || phase === 'distraction' || phase === 'recall')) {
        const key = hiddenKey(state.participant_id,index);
        localStorage.setItem(key, String(Number(localStorage.getItem(key) || '0') + 1));
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [state.participant_id, index, phase]);
  const label = LABELS[condition];
  return <div className="ambient" style={{'--ambient-color': COLORS[condition]} as CSSProperties}>
    <div className="ambient-overlay">
      <header className="study-header"><Brand light/>
        <div className="study-header-right"><div className="condition-chip"><ConditionIcon condition={condition} size={17}/>{lang === 'nb' ? label.nb : label.en}</div>
          <div className="round-chip">{lang === 'nb' ? 'RUNDE' : 'ROUND'} {index + 1}/3</div></div>
      </header>
      <div className="ambient-content">
        <div className="study-card"><div className="study-card-top"><div className="research-index">LM / RESEARCH PROTOCOL 002</div><ConditionDots current={index}/></div>
          {phase === 'setup' ? <Setup key={index} condition={condition} index={index} lang={lang} onStart={onStart} busy={busy}/> :
           phase === 'learning' ? <Learning pairs={state.pairs ?? []} seconds={seconds} lang={lang}/> :
           phase === 'distraction' ? <Distraction key={index} seconds={seconds} lang={lang}/> :
           <Recall key={index} id={state.participant_id} state={state} seconds={seconds} lang={lang} onSubmit={onSubmit} busy={busy} error={error}/>}
          {error && phase !== 'recall' && <div className="error-banner" role="alert">{error}<button onClick={()=>void onRefresh()}><RefreshCw size={15}/> {lang==='nb'?'Prøv igjen':'Retry'}</button></div>}
        </div>
        <div className="study-under"><span><ShieldCheck size={15}/>{lang === 'nb' ? 'Pseudonym deltaker' : 'Pseudonymous study'}</span>
          <span>{lang === 'nb' ? 'Ikke endre skjerminnstillingene underveis' : 'Keep screen settings unchanged'}</span>
          <span><button type="button" className="withdraw-link study-withdraw" onClick={() => void onWithdraw()}>{lang==='nb'?'Trekk samtykke':'Withdraw'}</button></span>
        </div>
      </div>
    </div>
  </div>;
}

function Complete({ lang, onWithdraw, error }: { lang: Language; onWithdraw: () => Promise<void>; error: string | null }) {
  const t = (nb: string, en: string) => lang === 'nb' ? nb : en;
  return <div className="site-shell"><Header lang={lang}/>
    <main className="complete-wrap"><div className="complete-icon"><Check size={40}/></div>
      <div className="eyebrow"><Sparkles size={15}/>{t('FORSØK FULLFØRT', 'STUDY COMPLETED')}</div>
      <h1>{t('Takk for at du deltok!', 'Thank you for participating!')}</h1>
      <p>{t('Du har fullført alle tre rundene. Svarene dine er lagret og bidrar til prosjektets datagrunnlag.',
        'You have completed all three rounds. Your answers have been saved and contribute to this study.')}</p>
      <div className="complete-stats"><div><strong>3/3</strong><span>{t('Fullførte runder', 'Rounds completed')}</span></div><div><strong>30</strong><span>{t('Ordassosiasjoner', 'Word associations')}</span></div></div>
      <div className="thankyou-note"><ShieldCheck size={19}/>{t('Ingen navn eller e-postadresser ble samlet inn. Du kan lukke denne siden.',
        'No names or email addresses were collected. You can close this page.')}</div>
      {error && <div className="error-banner" role="alert">{error}</div>}
      <button type="button" className="withdraw-link" onClick={() => void onWithdraw()}>{t('Trekk samtykke og slett mine data', 'Withdraw consent and delete my data')}</button>
    </main><Footer lang={lang}/></div>;
}

export default function App() {
  const [lang, setLangState] = useState<Language>(() => localStorage.getItem(LANGUAGE_KEY) === 'en' ? 'en' : 'nb');
  const [id, setId] = useState<string | null>(() => localStorage.getItem(PARTICIPANT_KEY));
  const [view, setView] = useState<View>(() => localStorage.getItem(PARTICIPANT_KEY) ? 'loading' : 'intro');
  const [state, setState] = useState<StudyState | null>(null);
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setLang = (next: Language) => { setLangState(next); localStorage.setItem(LANGUAGE_KEY, next); };

  const getState = useCallback(async (participantID: string) => {
    const data = await api.next(participantID);
    setOffset(data.server_now - Date.now() / 1000);
    setState(data);
    setLangState(data.language);
    if (data.finished) setView('complete');
    else if (localStorage.getItem(CALIBRATED_KEY) !== participantID) setView('calibration');
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
    setBusy(true); setError(null);
    try {
      const result = await api.register(input);
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

  const submit = useCallback(async (answers: string[], hidden: number) => {
    if (!id || !state || busy || state.round_index === undefined) return;
    const round = state.round_index;
    setBusy(true); setError(null);
    try {
      await api.submit(id, round, answers, hidden);
      localStorage.removeItem(draftKey(id,round));
      localStorage.removeItem(hiddenKey(id,round));
      await getState(id);
    } catch(err) { setError(err instanceof Error ? err.message : 'Unable to save'); throw err; }
    finally { setBusy(false); }
  }, [id, state, busy, getState]);

  const withdraw = async () => {
    if (!id) return;
    const okay = window.confirm(lang === 'nb'
      ? 'Vil du trekke samtykket? Alle data som er registrert for denne deltaker-ID-en, slettes permanent.'
      : 'Withdraw consent? All data associated with this participant ID will be permanently deleted.');
    if (!okay) return;
    try {
      await api.withdraw(id);
      for (let index=0; index<3; index++) {
        localStorage.removeItem(draftKey(id,index));
        localStorage.removeItem(hiddenKey(id,index));
      }
      localStorage.removeItem(PARTICIPANT_KEY);
      localStorage.removeItem(CALIBRATED_KEY);
      setId(null); setState(null); setError(null); setView('intro');
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to withdraw'); }
  };

  if (view === 'loading') return <div className="loading-page"><Brand/><div className="loading-spinner"/>
    <p>{lang === 'nb' ? 'Kobler til forsøket …' : 'Connecting to study…'}</p>
    {error && <><div className="error-banner">{error}</div><Button onClick={() => { if(id) void getState(id).catch(() => undefined); }} secondary>
      <RefreshCw size={17}/>{lang === 'nb' ? 'Prøv igjen' : 'Retry'}</Button></>}
  </div>;
  if (view === 'intro') return <Intro lang={lang} setLang={setLang} onRegister={register} busy={busy} error={error}/>;
  if (view === 'calibration') return <Calibration lang={lang} onNext={() => {
    if(id) {localStorage.setItem(CALIBRATED_KEY,id); setView('study'); }
  }}/>
  if (view === 'complete') return <Complete lang={lang} onWithdraw={withdraw} error={error}/>;
  if (!state || !id) return null;
  return <Study state={state} lang={lang} offsetSeconds={offset} onStart={start} onRefresh={refresh} onSubmit={submit} onWithdraw={withdraw} busy={busy} error={error}/>;
}
