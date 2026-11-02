import {useEffect,useRef,useState} from 'react';
import {Check,ChevronDown,Globe2,Search,X} from 'lucide-react';
import {LANGUAGE_NAMES} from './i18n';
import type {Language} from './i18n';

const ENGLISH:Record<Language,string>={nb:'Norwegian',en:'English',sv:'Swedish',da:'Danish',nl:'Dutch',de:'German',fr:'French',es:'Spanish',it:'Italian',pt:'Portuguese',pl:'Polish',ro:'Romanian'};
const ORDER:Language[]=['nb','en','sv','da','nl','de','fr','es','it','pt','pl','ro'];
const UI:Record<Language,[string,string,string]>={
nb:['Søk etter språk','Ingen språk funnet','Velg språk'],
en:['Search languages','No matching languages','Choose language'],
sv:['Sök språk','Inga språk hittades','Välj språk'],
da:['Søg efter sprog','Ingen sprog fundet','Vælg sprog'],
nl:['Zoek een taal','Geen talen gevonden','Kies een taal'],
de:['Sprachen suchen','Keine Sprachen gefunden','Sprache wählen'],
fr:['Rechercher une langue','Aucune langue trouvée','Choisir une langue'],
es:['Buscar idiomas','No se encontraron idiomas','Elegir idioma'],
it:['Cerca una lingua','Nessuna lingua trovata','Scegli la lingua'],
pt:['Pesquisar idiomas','Nenhum idioma encontrado','Escolher idioma'],
pl:['Szukaj języka','Nie znaleziono języków','Wybierz język'],
ro:['Caută o limbă','Nu s-au găsit limbi','Alege limba'],
};
const fold=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();

export default function LanguagePicker({lang,onChange,id,compact=false,dark=false,disabled=false}:{
 lang:Language;onChange:(next:Language)=>void;id:string;compact?:boolean;dark?:boolean;disabled?:boolean;
}){
 const [open,setOpen]=useState(false);
 const [query,setQuery]=useState('');
 const root=useRef<HTMLDivElement>(null);
 const search=useRef<HTMLInputElement>(null);
 const trigger=useRef<HTMLButtonElement>(null);
 const close=()=>{setOpen(false);setQuery('');trigger.current?.focus();};
 useEffect(()=>{
   if(!open)return;
   search.current?.focus();
   const outside=(ev:PointerEvent)=>{if(root.current&&!root.current.contains(ev.target as Node)){setOpen(false);setQuery('');}};
   const key=(ev:KeyboardEvent)=>{if(ev.key==='Escape'){ev.preventDefault();close();}};
   document.addEventListener('pointerdown',outside);
   document.addEventListener('keydown',key);
   return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',key)};
 },[open]);
 const options=ORDER.filter(code=>fold([code,LANGUAGE_NAMES[code],ENGLISH[code]].join(' ')).includes(fold(query.trim())));
 const hints=UI[lang];
 return <div ref={root} className={`lang-picker ${compact?'lang-picker-compact':''} ${dark?'lang-picker-dark':''}`}>
    <button id={id} ref={trigger} type="button" className="lang-picker-trigger"
      aria-label={hints[2]} aria-haspopup="dialog" aria-expanded={open}
      aria-controls={open?`${id}-panel`:undefined}
      disabled={disabled} onClick={()=>open?close():setOpen(true)}>
      <Globe2 size={17} aria-hidden="true"/><span>{LANGUAGE_NAMES[lang]}</span><ChevronDown size={16} aria-hidden="true"/>
    </button>
    {open&&<div className="lang-picker-panel" id={`${id}-panel`} role="dialog" aria-label={hints[2]}>
      <div className="lang-picker-search">
        <Search size={17} aria-hidden="true"/>
        <input ref={search} type="search" value={query} placeholder={hints[0]} aria-label={hints[0]}
          onChange={ev=>setQuery(ev.target.value)}/>
        {query&&<button type="button" aria-label={hints[0]} onClick={()=>setQuery('')}><X size={16}/></button>}
      </div>
      <div className="lang-picker-options">
        {options.map(code=><button key={code} type="button" aria-pressed={lang===code}
          className={`lang-picker-option ${lang===code?'lang-picker-selected':''}`}
          onClick={()=>{onChange(code);close();}}>
          <span className="lang-option-code">{code.toUpperCase()}</span>
          <span className="lang-option-names"><strong lang={code}>{LANGUAGE_NAMES[code]}</strong><small>{ENGLISH[code]}</small></span>
          {lang===code&&<Check size={17} aria-hidden="true"/>}
        </button>)}
        {options.length===0&&<p className="lang-picker-empty">{hints[1]}</p>}
      </div>
    </div>}
 </div>;
}
