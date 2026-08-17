'use client';

import { useCallback, useEffect, useState } from 'react';
import RealtimeMonitor from './components/RealtimeMonitor';
import VoiceAssistantDock from './components/VoiceAssistantDock';

type Json = Record<string, any>;
type ModuleId = 'overview'|'market'|'council'|'twin'|'memory'|'lab'|'execution'|'audit';

const modules: {id: ModuleId; label: string; icon: string; desc: string}[] = [
  {id:'overview',label:'Command',icon:'⌬',desc:'System-wide intelligence and safety state'},
  {id:'market',label:'Market',icon:'◈',desc:'Real market evidence and data freshness'},
  {id:'council',label:'AI Council',icon:'✦',desc:'Independent reasoning and adversarial challenge'},
  {id:'twin',label:'Market Twin',icon:'◎',desc:'Gated scenario simulation'},
  {id:'memory',label:'Memory',icon:'⌘',desc:'Persistent market memory and similarity retrieval'},
  {id:'lab',label:'Strategy Lab',icon:'⚗',desc:'Research, validation and governance'},
  {id:'execution',label:'Execution',icon:'⇄',desc:'Broker, risk, reconciliation and kill switch'},
  {id:'audit',label:'Audit',icon:'⌁',desc:'Certification evidence, lineage and replay'},
];

const agents = ['Technical','ML','Macro','News','Sentiment','Liquidity','Regime','Risk','Execution'];

function apiBase(){ return (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/,''); }

async function getJson(path:string){
  const r=await fetch(`${apiBase()}${path}`,{cache:'no-store'});
  const body=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(body?.detail || `HTTP ${r.status}`);
  return body;
}

function safeJson(value:any){ try{return JSON.stringify(value,null,2)}catch{return String(value)} }

export default function Home(){
  const [active,setActive]=useState<ModuleId>('overview');
  const [symbol,setSymbol]=useState('BTCUSDT');
  const [health,setHealth]=useState<Json|null>(null);
  const [providers,setProviders]=useState<Json|null>(null);
  const [cert,setCert]=useState<Json|null>(null);
  const [market,setMarket]=useState<Json|null>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [time,setTime]=useState(new Date());

  const refresh=useCallback(async()=>{
    setBusy(true); setError('');
    const results=await Promise.allSettled([
      getJson('/health'),
      getJson('/api/advanced/providers/status'),
      getJson('/api/advanced/certification/plan'),
      getJson(`/api/market/${encodeURIComponent(symbol)}`)
    ]);
    const [h,p,c,m]=results;
    if(h.status==='fulfilled') setHealth(h.value); else setHealth({status:'offline'});
    if(p.status==='fulfilled') setProviders(p.value); else setProviders(null);
    if(c.status==='fulfilled') setCert(c.value); else setCert(null);
    if(m.status==='fulfilled') setMarket(m.value); else setMarket(null);
    if(results.some(x=>x.status==='rejected')) setError('Some real backend evidence is unavailable. The UI will not synthesize replacement market values.');
    setBusy(false);
  },[symbol]);

  useEffect(()=>{refresh(); const t=setInterval(()=>setTime(new Date()),1000); const p=setInterval(refresh,15000); return()=>{clearInterval(t);clearInterval(p)}},[refresh]);

  const online=health?.status==='ok'||health?.status==='healthy';
  const live=Boolean(health?.live_trading);
  const workers=Boolean(health?.workers_enabled);
  const module=modules.find(x=>x.id===active)!;

  return <main className="iq-shell">
    <div className="scanlines"/><div className="ambient ambient-a"/><div className="ambient ambient-b"/>
    <header className="topbar glass">
      <button className="brand" onClick={()=>setActive('overview')} aria-label="IQ200 command">
        <span className="brand-orb"><i/><b>IQ</b></span>
        <span><strong>IQ200</strong><small>ADAPTIVE MARKET INTELLIGENCE</small></span>
      </button>
      <div className="top-status">
        <span className={`status-dot ${online?'online':'offline'}`}/><b>{online?'ONLINE':'OFFLINE'}</b>
        <span className="divider"/><span className="mono">{time.toLocaleTimeString()}</span>
        <button className="icon-btn" onClick={refresh} disabled={busy} aria-label="Refresh">{busy?'…':'↻'}</button>
      </div>
    </header>
    <div className="layout">
      <aside className="sidebar glass">
        <div className="side-label">COMMAND LAYERS</div>
        <nav>{modules.map(m=><button key={m.id} className={`nav-item ${active===m.id?'active':''}`} onClick={()=>setActive(m.id)}><span className="nav-icon">{m.icon}</span><span>{m.label}</span><i/></button>)}</nav>
        <div className="side-bottom">
          <div className="guard-card"><span className="shield">⬡</span><div><b>FAIL-CLOSED</b><small>Risk engine is final authority</small></div></div>
          <div className="mini-runtime"><span>WORKERS</span><b>{workers?'RUNNING':'OFF'}</b></div>
          <div className="mini-runtime"><span>LIVE MONEY</span><b className={live?'danger':''}>{live?'ENABLED':'BLOCKED'}</b></div>
        </div>
      </aside>
      <section className="content">
        <div className="hero-row"><div><div className="eyebrow">AUTONOMOUS TRADING COCKPIT / {module.label.toUpperCase()}</div><h1>{module.label}<span>.</span></h1><p>{module.desc}. <b>Evidence-first:</b> unavailable providers remain visibly unverified.</p></div><div className="hero-actions"><label className="symbol-input"><span>ASSET</span><input value={symbol} onChange={e=>setSymbol(e.target.value.toUpperCase())} onKeyDown={e=>e.key==='Enter'&&refresh()} /></label><span className="hero-chip"><span className="pulse"/> LIVE TELEMETRY</span></div></div>
        {error&&<div className="notice glass">⚠ {error}</div>}
        <div className="metric-grid"><Metric title="RUNTIME" value={online?'ONLINE':'OFFLINE'} state={online?'good':'warn'} sub="GET /health"/><Metric title="LIVE TRADING" value={live?'ENABLED':'BLOCKED'} state={live?'warn':'good'} sub={live?'External money path active':'Fail-closed default'}/><Metric title="PROVIDERS" value={providerCount(providers)} state={providers?'good':'warn'} sub="Real configuration status"/><Metric title="EVIDENCE" value={cert?`${cert.items?.length??0} GATES`:'UNAVAILABLE'} state={cert?'good':'warn'} sub="External certification plan"/></div>
        {active==='overview'&&<Overview health={health} providers={providers} cert={cert} market={market} symbol={symbol}/>} {active==='market'&&<Market market={market} health={health} symbol={symbol}/>} {active==='council'&&<Council symbol={symbol}/>} {active==='twin'&&<Twin/>} {active==='memory'&&<Memory/>} {active==='lab'&&<Lab/>} {active==='execution'&&<Execution health={health} providers={providers}/>} {active==='audit'&&<Audit cert={cert}/>} 
      </section>
    </div>
    <VoiceAssistantDock />
  </main>;
}

function providerCount(p:any){if(!p)return '—';return `${['ai','binance','oanda'].map(k=>p[k]?.configured===true).filter(Boolean).length}/3`;}
function Metric({title,value,sub,state}:{title:string,value:string,sub:string,state:string}){return <div className="metric glass"><div className="metric-head"><span>{title}</span><i className={`metric-state ${state}`}/></div><strong>{value}</strong><small>{sub}</small></div>;}
function Panel({children,className=''}:{children:any,className?:string}){return <section className={`panel glass ${className}`}>{children}</section>}
function Head({kicker,title,badge}:{kicker:string,title:string,badge?:string}){return <div className="panel-head"><div><span className="kicker">{kicker}</span><h2>{title}</h2></div>{badge&&<span className="live-pill"><i/>{badge}</span>}</div>}
function Status({ok,children}:{ok:boolean,children:any}){return <span className={`state ${ok?'ok':'pending'}`}><i/>{children}</span>}
function Overview({health,providers,cert,market,symbol}:{health:any,providers:any,cert:any,market:any,symbol:string}){return <div className="dashboard-grid"><Panel className="hero-panel"><Head kicker="SYSTEM CORE" title="Evidence matrix" badge="REAL INPUTS"/><div className="core-layout"><div className="core-reactor"><div className="reactor-ring r1"/><div className="reactor-ring r2"/><div className="reactor-core"><b>IQ200</b><small>{health?.fail_closed?'FAIL-CLOSED':'VERIFYING'}</small></div></div><div className="evidence-list">{[['API',health?.status==='ok'],['RISK ENGINE',Boolean(health?.risk_engine)],['FAIL-CLOSED',health?.fail_closed===true],['TESTNET',health?.testnet===true],['AI PROVIDER',providers?.ai?.configured===true],['BROKER',Boolean(providers?.binance?.configured||providers?.oanda?.configured)]].map(([n,v])=><div className="evidence-row" key={String(n)}><span>{n}</span><Status ok={Boolean(v)}>{v?'VERIFIED':'UNVERIFIED'}</Status></div>)}</div></div></Panel><Panel><Head kicker="MARKET SNAPSHOT" title={symbol} badge={market?'CONNECTED':'WAITING'}/><DataCards data={market}/></Panel><Panel><Head kicker="PROVIDER MATRIX" title="Connectivity" badge="NO SYNTHETICS"/><ProviderMatrix providers={providers}/></Panel><Panel><Head kicker="CERTIFICATION" title="External evidence gates"/><div className="cert-list">{(cert?.items||[]).slice(0,7).map((x:any,i:number)=><div className="cert-row" key={i}><span>{String(i+1).padStart(2,'0')}</span><b>{x.name||x.title||'Certification gate'}</b><em>{x.status||'REQUIRES EXTERNAL EVIDENCE'}</em></div>)}</div>{!cert&&<Empty text="Certification plan unavailable from backend."/>}</Panel></div>}
function Market({market,health,symbol}:{market:any,health:any,symbol:string}){return <div className="dashboard-grid"><Panel className="wide"><Head kicker="REAL MARKET EVIDENCE" title={symbol} badge={market?'LIVE RESPONSE':'UNVERIFIED'}/><RealtimeMonitor symbol={symbol}/><DataCards data={market}/><div className="signal-strip"><Signal n="REGIME" v={market?.regime}/><Signal n="SPREAD" v={market?.spread}/><Signal n="ORDER FLOW" v={market?.order_flow}/><Signal n="FRESHNESS" v={market?.timestamp||market?.time}/></div><pre className="evidence-json">{market?safeJson(market):'No provider response. No synthetic candles/prices/signals are rendered.'}</pre></Panel><Panel><Head kicker="RUNTIME" title="Backend truth"/><pre className="evidence-json">{safeJson(health||{status:'unavailable'})}</pre></Panel></div>}
function DataCards({data}:{data:any}){const keys=data?Object.keys(data).slice(0,6):[];return <div className="data-cards">{keys.map(k=><div className="data-card" key={k}><span>{k.replace(/_/g,' ').toUpperCase()}</span><b>{typeof data[k]==='object'?'{…}':String(data[k])}</b></div>)}</div>}
function Signal({n,v}:{n:string,v:any}){return <div><span>{n}</span><b>{v==null?'UNVERIFIED':String(v)}</b></div>}
function ProviderMatrix({providers}:{providers:any}){if(!providers)return <Empty text="Provider status endpoint unavailable."/>;return <div className="provider-grid">{['ai','binance','oanda'].map(k=>{const p=providers[k]||{};return <div className="provider-card" key={k}><div><b>{k.toUpperCase()}</b><small>{p.provider||k}</small></div><Status ok={p.configured===true}>{p.configured?'CONFIGURED':'NOT CONFIGURED'}</Status><small>{p.practice===true?'PRACTICE MODE':p.live_enabled===true?'LIVE ENABLED':'LIVE BLOCKED'}</small></div>})}</div>}
function Council({symbol}:{symbol:string}){return <Panel className="full"><Head kicker="MULTI-AGENT COUNCIL" title={`Independent evidence / ${symbol}`} badge="GATED"/><div className="agent-grid">{agents.map(a=><div className="agent" key={a}><div className="agent-avatar">{a[0]}</div><div><b>{a}</b><small>Awaiting real evidence</small></div><span>UNVERIFIED</span></div>)}</div><div className="debate"><div><b>BULL</b><span>Requires real evidence</span></div><div className="vs">VS</div><div><b>BEAR</b><span>Requires real evidence</span></div><div className="challenger"><b>ADVERSARIAL CHALLENGER</b><span>Unsupported conclusions are rejected before risk.</span></div></div></Panel>}
function Twin(){return <div className="dashboard-grid"><Panel className="wide twin"><Head kicker="DIGITAL MARKET TWIN" title="Scenario field" badge="INPUT-GATED"/><div className="twin-orbit"><div className="orbit o1"/><div className="orbit o2"/><div className="orbit o3"/><div className="twin-core"><strong>WAIT</strong><small>NO VERIFIED INPUT</small></div></div><div className="scenario-grid">{['BUY','SELL','WAIT','SKIP'].map(x=><div key={x}><b>{x}</b><span>—</span><small>simulation requires real distribution</small></div>)}</div></Panel></div>}
function Memory(){return <Panel className="full"><Head kicker="PERSISTENT MARKET MEMORY" title="Recall / similarity / outcomes" badge="DATABASE-GATED"/><div className="memory-visual"><div className="memory-node">MEMORY</div>{['REGIMES','FAILURES','SUCCESSES','MACRO','DECISIONS','ASSET BEHAVIOR'].map((x,i)=><div className="memory-chip" style={{['--i' as any]:i}} key={x}>{x}</div>)}</div><Empty text="Similarity retrieval requires populated production memory. The UI intentionally does not invent historical matches." /></Panel>}
function Lab(){return <div className="dashboard-grid"><Panel className="wide"><Head kicker="AUTONOMOUS RESEARCH LAB" title="Discover → validate → govern" badge="FAIL-CLOSED"/><div className="pipeline">{['DATA LINEAGE','PATTERN DISCOVERY','HYPOTHESIS','PURGED TEST','WALK-FORWARD','MONTE CARLO','PAPER TRADE','GOVERNANCE'].map((x,i)=><div className="pipe" key={x}><span>{String(i+1).padStart(2,'0')}</span><b>{x}</b><em>GATED</em></div>)}</div></Panel><Panel><Head kicker="ANTI-OVERFIT" title="Research guardrails"/><ul className="guard-list"><li>No look-ahead</li><li>Chronological validation</li><li>Purged/embargoed tests</li><li>Dataset lineage</li><li>Uncertainty reporting</li><li>No automatic live rule mutation</li></ul></Panel></div>}
function Execution({health,providers}:{health:any,providers:any}){return <div className="dashboard-grid"><Panel className="wide"><Head kicker="EXECUTION CONTROL" title="Broker / risk / reconciliation" badge="FAIL-CLOSED"/><div className="execution-grid"><div className="exec-core"><div className="big-lock">⬡</div><b>LIVE MONEY {health?.live_trading?'ENABLED':'BLOCKED'}</b><small>Risk engine: {health?.risk_engine||'UNVERIFIED'}</small></div><ProviderMatrix providers={providers}/></div><div className="warning-banner">No order controls are rendered as executable trading actions in this dashboard. Execution must pass broker, risk, idempotency and reconciliation gates.</div></Panel></div>}
function Audit({cert}:{cert:any}){return <div className="dashboard-grid"><Panel className="wide"><Head kicker="ZERO-TRUST AUDIT" title="Certification evidence" badge="NO CLAIMS WITHOUT PROOF"/><div className="audit-table">{(cert?.items||[]).map((x:any,i:number)=><div className="audit-row" key={i}><span>{String(i+1).padStart(2,'0')}</span><b>{x.name||x.title||'Evidence gate'}</b><em>{x.status||'EXTERNAL EVIDENCE REQUIRED'}</em></div>)}</div>{!cert&&<Empty text="Certification endpoint unavailable."/>}</Panel><Panel><Head kicker="PRINCIPLE" title="Truth over theatre"/><p className="truth">A futuristic interface must never manufacture a price, PnL, vote, trade, or certification result. IQ200 shows uncertainty explicitly until the real backend proves it.</p></Panel></div>}
function Empty({text}:{text:string}){return <div className="empty"><div className="empty-icon">✦</div><p>{text}</p><span className="blocked">UNVERIFIED / WAITING FOR REAL INPUT</span></div>}
