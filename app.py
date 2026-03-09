import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import anthropic

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BRVM AI Investment Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Dark base */
  .stApp { background-color: #0d1117; color: #e6edf3; }
  section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #21262d; }

  /* Cards */
  .card {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 18px 22px; margin-bottom: 14px;
  }
  .card-green  { border-left: 4px solid #2ea043; }
  .card-red    { border-left: 4px solid #f85149; }
  .card-blue   { border-left: 4px solid #58a6ff; }
  .card-gold   { border-left: 4px solid #e3b341; }
  .card-orange { border-left: 4px solid #ff7b2b; }

  /* Score badges */
  .badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:0.78rem; font-weight:700; margin-right:5px;
  }
  .badge-green  { background:#1a3a26; color:#2ea043; border:1px solid #2ea043; }
  .badge-red    { background:#3a1a1a; color:#f85149; border:1px solid #f85149; }
  .badge-blue   { background:#1a2a3a; color:#58a6ff; border:1px solid #58a6ff; }
  .badge-gold   { background:#3a3010; color:#e3b341; border:1px solid #e3b341; }
  .badge-orange { background:#3a2510; color:#ff7b2b; border:1px solid #ff7b2b; }

  /* Section headers */
  .section-title {
    font-size:1.15rem; font-weight:700; color:#e6edf3;
    border-bottom:1px solid #21262d; padding-bottom:8px; margin:18px 0 14px 0;
  }
  .stock-ticker { font-size:1.3rem; font-weight:800; color:#e6edf3; }
  .stock-price  { font-size:1.1rem; color:#8b949e; }
  .metric-val   { font-size:1.6rem; font-weight:800; }
  .metric-lbl   { font-size:0.75rem; color:#8b949e; text-transform:uppercase; letter-spacing:.05em; }

  /* Chat bubbles */
  .chat-user {
    background:#1f2937; border-radius:12px 12px 2px 12px;
    padding:10px 15px; margin:6px 0; max-width:85%; float:right; clear:both;
    color:#e6edf3; font-size:0.92rem;
  }
  .chat-ai {
    background:#161b22; border:1px solid #21262d;
    border-radius:12px 12px 12px 2px;
    padding:10px 15px; margin:6px 0; max-width:90%; float:left; clear:both;
    color:#e6edf3; font-size:0.92rem;
  }
  .chat-wrap { overflow:hidden; margin-bottom:6px; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"]  { background:#161b22; border-radius:8px; gap:4px; }
  .stTabs [data-baseweb="tab"]       { background:#21262d; color:#8b949e; border-radius:6px; }
  .stTabs [aria-selected="true"]     { background:#2ea043 !important; color:#fff !important; }

  /* Tables */
  .stDataFrame { background:#161b22; }

  /* Inputs */
  .stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background:#161b22 !important; color:#e6edf3 !important;
    border:1px solid #21262d !important; border-radius:6px;
  }
  .stSelectbox>div>div { background:#161b22 !important; color:#e6edf3 !important; }

  /* Buttons */
  .stButton>button {
    background:#2ea043; color:#fff; border:none; border-radius:6px;
    font-weight:600; padding:8px 20px;
  }
  .stButton>button:hover { background:#3fb950; }

  /* Scrollable chat */
  #chat-scroll { max-height:480px; overflow-y:auto; padding-right:6px; }

  /* Note boxes */
  .note-box {
    background:#161b22; border:1px solid #21262d; border-radius:8px;
    padding:12px 16px; margin:6px 0; font-size:0.88rem; color:#8b949e;
  }
  .note-box strong { color:#e6edf3; }

  /* Dividers */
  hr { border-color:#21262d; }

  /* Macro pills */
  .macro-pill {
    display:inline-block; background:#161b22; border:1px solid #21262d;
    border-radius:20px; padding:4px 12px; margin:3px; font-size:0.8rem;
  }
  .pill-green { border-color:#2ea043; color:#2ea043; }
  .pill-red   { border-color:#f85149; color:#f85149; }
  .pill-gold  { border-color:#e3b341; color:#e3b341; }
  .pill-blue  { border-color:#58a6ff; color:#58a6ff; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
DIVIDENDS = {
    "SNTS":[("2021-05-12",1361),("2022-05-16",1556),("2023-05-15",1667),("2024-05-15",1750),("2025-05-20",1839)],
    "SGBC":[("2021-06-01",800),("2022-06-01",1100),("2023-06-01",1200),("2024-06-01",1300)],
    "BOABF":[("2021-07-01",450),("2022-07-01",600),("2023-07-01",650),("2024-07-01",700)],
    "CBIBF":[("2021-07-01",500),("2022-07-01",650),("2023-07-01",790),("2024-07-01",850)],
    "SIBC":[("2021-07-01",250),("2022-07-01",400),("2023-07-01",450),("2024-07-01",500)],
    "PALC":[("2021-06-01",500),("2022-06-01",800),("2023-06-01",900)],
    "ETIT":[("2021-06-01",1.0),("2022-06-01",1.2),("2023-06-01",1.5),("2024-06-01",1.8)],
    "TTLC":[("2021-06-01",280),("2022-06-01",350),("2023-06-01",420),("2024-06-01",500)],
    "ONTBF":[("2021-07-01",550),("2022-07-01",700),("2023-07-01",750)],
    "TTLS":[("2021-06-01",180),("2022-06-01",220),("2023-06-01",260),("2024-06-01",300)],
    "UNLC":[("2021-06-01",900),("2022-06-01",1200),("2023-06-01",1300)],
    "SCRC":[("2021-06-01",350),("2022-06-01",500),("2023-06-01",550)],
    "STBC":[("2021-06-01",250),("2022-06-01",350),("2023-06-01",400)],
}

MACRO = {
    "BCEAO_rate": 3.00, "BCEAO_trend": "easing",
    "WAEMU_GDP_2025": 6.7, "WAEMU_GDP_2026f": 6.4,
    "WAEMU_inflation": -0.8, "BRVM_CI_YTD": 6.91,
    "cocoa_drop_yoy": -43.9, "rubber_drop_yoy": -23.5,
}

SECTOR_MACRO = {
    "finance": +0.08, "banking": +0.08,
    "agriculture": -0.10,
    "public": +0.05, "utilities": +0.05,
    "industry": +0.05, "distribution": +0.03,
    "transportation": +0.02, "other": 0.0,
}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "df": None,
        "scored": None,
        "last_upload": None,
        "chat_history": [],          # [{role, content}]
        "notes": [],                 # [{date, type, ticker, text}]
        "instructions": [],          # [{date, text, active}]
        "weekly_briefing": None,
        "active_tab": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def run_analysis(csv_bytes: bytes, instructions_json: str) -> pd.DataFrame:
    import io
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    import warnings; warnings.filterwarnings('ignore')

    instructions = json.loads(instructions_json)

    # ── Load ──────────────────────────────────────────────────────────────
    df = pd.read_csv(io.BytesIO(csv_bytes), low_memory=False)
    df = df[df['symbol'] != 'symbol']
    for c in ['open','high','low','close','volume','avg','trade_value']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date','close','symbol'])
    df = df[df['close'] > 0].sort_values(['symbol','date']).reset_index(drop=True)

    # Apply instruction filters
    excluded_sectors = [i.get('value','').lower() for i in instructions if i.get('type')=='exclude_sector']
    excluded_tickers = [i.get('value','').upper() for i in instructions if i.get('type')=='exclude_ticker']
    if excluded_sectors:
        df = df[~df['sector'].str.lower().isin(excluded_sectors)]
    if excluded_tickers:
        df = df[~df['ric'].str.upper().isin(excluded_tickers)]

    # ── Feature engineering ───────────────────────────────────────────────
    def featurize(grp):
        g = grp.copy().sort_values('date')
        c = g['close']; v = g['volume']
        for d in [5,10,20,60,120,252]:
            g[f'ret_{d}d'] = c.pct_change(d)
        for d in [20,50,200]:
            g[f'ma_{d}'] = c.rolling(d).mean()
            g[f'ma_ratio_{d}'] = c / g[f'ma_{d}']
        dr = c.pct_change()
        for w in [20,60]:
            g[f'vol_{w}d'] = dr.rolling(w).std() * np.sqrt(252)
        delta=c.diff(); gain=delta.clip(lower=0).rolling(14).mean()
        loss=(-delta.clip(upper=0)).rolling(14).mean()
        g['rsi14'] = 100-(100/(1+(gain/(loss+1e-9))))
        ema12=c.ewm(span=12,adjust=False).mean(); ema26=c.ewm(span=26,adjust=False).mean()
        g['macd'] = ema12-ema26
        g['macd_signal'] = g['macd'].ewm(span=9,adjust=False).mean()
        g['macd_hist']   = g['macd']-g['macd_signal']
        ma20=c.rolling(20).mean(); sd20=c.rolling(20).std()
        g['bb_upper']=ma20+2*sd20; g['bb_lower']=ma20-2*sd20
        g['bb_pct']=(c-g['bb_lower'])/(g['bb_upper']-g['bb_lower']+1e-9)
        g['vol_ma20']=v.rolling(20).mean()
        g['vol_ratio']=v/(g['vol_ma20']+1e-9)
        g['trade_val_ma20']=g['trade_value'].rolling(20).mean()
        g['hi52']=c.rolling(252).max(); g['lo52']=c.rolling(252).min()
        g['dist_hi52']=(c-g['hi52'])/(g['hi52']+1e-9)
        g['dist_lo52']=(c-g['lo52'])/(g['lo52']+1e-9)
        g['ath']=c.cummax()
        g['dist_ath']=(c-g['ath'])/(g['ath']+1e-9)
        ric=g['ric'].iloc[0]
        if ric in DIVIDENDS:
            divs=pd.DataFrame(DIVIDENDS[ric],columns=['ex_date','dividend'])
            divs['ex_date']=pd.to_datetime(divs['ex_date'])
            g['div_ttm']=g['date'].apply(lambda d: divs.loc[(divs['ex_date']<=d)&(divs['ex_date']>d-pd.Timedelta(days=365)),'dividend'].sum())
            g['div_yield']=g['div_ttm']/(c+1e-9)
            g['div_growing']=int((divs['dividend'].diff()>0).iloc[-1]) if len(divs)>1 else 0
            g['days_to_div']=g['date'].apply(lambda d: (divs[divs['ex_date']>d]['ex_date'].min()-d).days if len(divs[divs['ex_date']>d])>0 else 365)
        else:
            g['div_ttm']=0; g['div_yield']=0; g['div_growing']=0; g['days_to_div']=999
        g['fwd_ret_12m']=c.pct_change(252).shift(-252)
        g['target']=(g['fwd_ret_12m']>0.10).astype(int)
        return g

    results=[featurize(grp) for _,grp in df.groupby('symbol')]
    df=pd.concat(results).sort_values(['symbol','date']).reset_index(drop=True)

    FEAT=['ret_5d','ret_10d','ret_20d','ret_60d','ret_120d','ret_252d',
          'ma_ratio_20','ma_ratio_50','ma_ratio_200',
          'vol_20d','vol_60d','rsi14','macd_hist','bb_pct','vol_ratio',
          'dist_hi52','dist_lo52','dist_ath',
          'div_yield','div_ttm','div_growing','days_to_div']

    dm=df.dropna(subset=FEAT+['target']).copy()
    dm=dm[dm['date']<pd.Timestamp("2025-01-01")]
    X=dm[FEAT].values; y=dm['target'].values
    train_mask=dm['date']<pd.Timestamp("2024-01-01")
    sc=StandardScaler()
    Xtr=sc.fit_transform(X[train_mask])
    clf=GradientBoostingClassifier(n_estimators=300,learning_rate=0.05,
        max_depth=4,subsample=0.8,min_samples_leaf=20,random_state=42)
    clf.fit(Xtr, y[train_mask])

    # ── Score latest snapshot ──────────────────────────────────────────────
    max_date=df['date'].max()
    latest=(df[df['date']>=max_date-pd.Timedelta(days=90)]
            .sort_values('date').groupby('symbol').last().reset_index())
    has_feat=latest[FEAT].notna().all(axis=1)
    lc=latest[has_feat].copy()
    lc=lc[lc['trade_val_ma20'].fillna(0)>1e5]
    X_now=sc.transform(lc[FEAT].fillna(0).values)
    lc['ai_score']=clf.predict_proba(X_now)[:,1]

    # ── Peak avoidance + macro ─────────────────────────────────────────────
    rows=[]
    for _,row in lc.iterrows():
        sym=row['symbol']
        s=df[df['symbol']==sym].sort_values('date')
        px=s['close']; last_px=px.iloc[-1]
        hi52=px.tail(252).max(); lo52=px.tail(252).min(); ath=px.max()
        ma200=px.rolling(200).mean().iloc[-1]; ma50=px.rolling(50).mean().iloc[-1]
        pct_from_hi52=(last_px-hi52)/hi52
        pct_from_ath=(last_px-ath)/ath
        dd_90d=(last_px-px.tail(90).max())/px.tail(90).max()
        one_yr=s[s['date']<=s['date'].max()-pd.Timedelta(days=252)]
        ret_1y=(last_px/one_yr.iloc[-1]['close']-1) if len(one_yr)>0 else 0
        ret_1m=(last_px/s[s['date']<=s['date'].max()-pd.Timedelta(days=21)].iloc[-1]['close']-1) if len(s)>21 else 0
        rsi_v=row.get('rsi14',50) or 50
        val_score=(
            min(1.0,max(0.0,(-pct_from_hi52)*2))*0.35+
            min(1.0,max(0.0,(-pct_from_ath)*1.5))*0.25+
            min(1.0,max(0.0,(100-rsi_v)/100))*0.25+
            min(1.0,max(0.0,(-dd_90d)*3))*0.15
        )
        sector=str(row.get('sector','')).lower()
        macro_adj=SECTOR_MACRO.get(sector,0.0)
        composite=(row['ai_score']*0.45+val_score*0.35+(0.5+macro_adj)*0.20)

        # Entry signal
        if pct_from_hi52>-0.03 and rsi_v>72:
            entry_signal="⚠️ AT PEAK — WAIT"; entry_color="red"
        elif pct_from_hi52>-0.05:
            entry_signal="⚠️ NEAR PEAK — WAIT"; entry_color="orange"
        elif composite>0.60 and pct_from_hi52<-0.15:
            entry_signal="🚀 STRONG BUY"; entry_color="green"
        elif composite>0.52 and pct_from_hi52<-0.08:
            entry_signal="✅ BUY ON DIPS"; entry_color="green"
        elif composite>0.48:
            entry_signal="👀 WATCH"; entry_color="blue"
        else:
            entry_signal="📊 NEUTRAL"; entry_color="grey"

        rows.append({
            'symbol':sym,'ric':row['ric'],'sector':row.get('sector',''),
            'last_price':last_px,'hi52':hi52,'lo52':lo52,'ath':ath,
            'ma200':ma200,'ma50':ma50,
            'pct_from_hi52':pct_from_hi52,'pct_from_ath':pct_from_ath,
            'dd_90d':dd_90d,'ret_1y':ret_1y,'ret_1m':ret_1m,
            'rsi14':rsi_v,'div_yield':row.get('div_yield',0) or 0,
            'div_ttm':row.get('div_ttm',0) or 0,
            'macd_hist':row.get('macd_hist',0) or 0,
            'bb_pct':row.get('bb_pct',0.5) or 0.5,
            'vol_ratio':row.get('vol_ratio',1) or 1,
            'trade_val_ma20':row.get('trade_val_ma20',0) or 0,
            'ai_score':row['ai_score'],'val_score':val_score,
            'macro_adj':macro_adj,'composite':composite,
            'entry_signal':entry_signal,'entry_color':entry_color,
        })

    scored=pd.DataFrame(rows).sort_values('composite',ascending=False).reset_index(drop=True)
    scored['rank']=range(1,len(scored)+1)
    return scored

# ══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
def get_ai_client():
    api_key = st.session_state.get("api_key","") or os.environ.get("ANTHROPIC_API_KEY","")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)

def build_system_prompt():
    scored = st.session_state.scored
    notes  = st.session_state.notes
    instructions = st.session_state.instructions

    scored_summary = ""
    if scored is not None:
        top = scored.head(15)
        lines = []
        for _,r in top.iterrows():
            lines.append(
                f"  #{r['rank']} {r['ric']} ({r['sector']}) | Price: {r['last_price']:,.0f} XOF | "
                f"Composite: {r['composite']:.2f} | AI: {r['ai_score']:.0%} | "
                f"Entry: {r['val_score']:.2f} | vs52WHi: {r['pct_from_hi52']:+.1%} | "
                f"RSI: {r['rsi14']:.0f} | 1Y ret: {r['ret_1y']:+.1%} | "
                f"DivYield: {r['div_yield']:.1%} | Signal: {r['entry_signal']}"
            )
        scored_summary = "\n".join(lines)

    notes_summary = ""
    if notes:
        notes_summary = "\n".join([
            f"  [{n['date']}] {n['type'].upper()} | {n.get('ticker','')} | {n['text']}"
            for n in notes[-20:]
        ])

    instr_summary = ""
    active_instr = [i for i in instructions if i.get('active', True)]
    if active_instr:
        instr_summary = "\n".join([f"  - {i['text']}" for i in active_instr])

    macro_summary = f"""
  BCEAO Rate: {MACRO['BCEAO_rate']}% (easing cycle)
  WAEMU GDP 2025: {MACRO['WAEMU_GDP_2025']}% | 2026 forecast: {MACRO['WAEMU_GDP_2026f']}%
  WAEMU Inflation: {MACRO['WAEMU_inflation']}% (deflation)
  BRVM YTD: +{MACRO['BRVM_CI_YTD']}%
  Cocoa YoY: {MACRO['cocoa_drop_yoy']}% | Rubber YoY: {MACRO['rubber_drop_yoy']}%
  Sector adjustments: Finance +8% (rate cuts), Agriculture -10% (commodity crash),
    Industry +5%, Utilities/Public +5%, Distribution +3%
"""

    return f"""You are an expert BRVM (Bourse Régionale des Valeurs Mobilières) investment analyst AI assistant.
You have deep knowledge of West African capital markets, WAEMU economics, and the specific stocks listed on the BRVM.
You speak French and English fluently and understand the regional context.

CURRENT ANALYSIS DATA (as of latest upload):
{scored_summary if scored_summary else "No data uploaded yet."}

MACRO CONTEXT:
{macro_summary}

USER'S INVESTMENT NOTES & RESULTS:
{notes_summary if notes_summary else "None recorded yet."}

ACTIVE TRADING INSTRUCTIONS:
{instr_summary if instr_summary else "None set."}

YOUR ROLE:
- Answer questions about specific BRVM stocks with precision and nuance
- Explain the composite score breakdown (AI momentum + entry quality + macro) when asked
- Accept and acknowledge investment results and notes the user shares
- Incorporate active trading instructions into your advice
- Generate weekly briefings when asked
- Flag peak risks clearly — the user is trying to AVOID buying at tops
- Consider WAEMU macro context (rate cuts, commodity prices, GDP, CFA peg) in every answer
- Be honest about uncertainty — BRVM is a frontier market with thin liquidity

Always be specific, data-driven, and concise. Reference actual numbers from the data above.
When asked about entry timing, always reference the val_score, RSI, and % from 52W high.
"""

def chat_with_ai(user_message: str) -> str:
    client = get_ai_client()
    if not client:
        return "⚠️ Please enter your Anthropic API key in the sidebar to enable the AI assistant."

    history = st.session_state.chat_history[-20:]  # keep last 20 turns
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=build_system_prompt(),
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ API error: {str(e)}"

def generate_weekly_briefing() -> str:
    client = get_ai_client()
    if not client:
        return "⚠️ Please enter your Anthropic API key in the sidebar."

    scored = st.session_state.scored
    if scored is None:
        return "⚠️ Please upload data first."

    top5  = scored.head(5)
    sell5 = scored.tail(5)

    prompt = f"""Generate a concise weekly BRVM investment briefing for the week.

TOP 5 BUY CANDIDATES:
{top5[['ric','sector','composite','ai_score','val_score','pct_from_hi52','rsi14','ret_1y','div_yield','entry_signal']].to_string()}

BOTTOM 5 / SELL WATCH:
{sell5[['ric','sector','composite','ai_score','val_score','pct_from_hi52','rsi14','ret_1y','entry_signal']].to_string()}

MACRO CONTEXT: BCEAO cut rate to 3% (easing), WAEMU GDP 6.7%, BRVM up 7% YTD, cocoa -44%, rubber -24%.

Write a professional briefing with:
1. Market overview (2-3 sentences)
2. Top 3 BUY picks with specific reasoning and entry levels to watch
3. Top 2 stocks to AVOID or SELL with reasoning
4. One macro factor to watch this week
5. Overall market tone (bullish/cautious/selective)

Be specific with prices and numbers. Keep it under 400 words."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role":"user","content":prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def color_badge(text, color):
    return f'<span class="badge badge-{color}">{text}</span>'

def metric_card(label, value, color="blue", sub=""):
    sub_html = f'<div style="font-size:0.78rem;color:#8b949e;margin-top:2px">{sub}</div>' if sub else ""
    return f"""
    <div class="card card-{color}" style="text-align:center;padding:14px">
      <div class="metric-lbl">{label}</div>
      <div class="metric-val" style="color:{'#2ea043' if color=='green' else '#f85149' if color=='red' else '#58a6ff' if color=='blue' else '#e3b341'}">{value}</div>
      {sub_html}
    </div>"""

def parse_instructions_to_filters(instructions):
    """Convert plain-text instructions to structured filters."""
    filters = []
    text_lower = " ".join([i['text'].lower() for i in instructions if i.get('active', True)])
    sector_keywords = {
        'agriculture': ['agriculture','agri','cocoa','rubber','farming'],
        'finance': ['finance','bank','banking'],
        'distribution': ['distribution'],
        'industry': ['industry','industrial'],
        'public': ['public','utilities'],
    }
    for sector, keywords in sector_keywords.items():
        for kw in keywords:
            if f'ignore {kw}' in text_lower or f'exclude {kw}' in text_lower or f'avoid {kw}' in text_lower:
                filters.append({'type':'exclude_sector','value':sector})
                break
    return filters

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📈 BRVM AI Tool")
    st.markdown("---")

    # API Key
    st.markdown("### 🔑 API Key")
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.get("api_key",""),
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input
        st.markdown('<span class="badge badge-green">✓ Key Set</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Data Upload
    st.markdown("### 📂 Upload Data")
    uploaded = st.file_uploader(
        "Upload CSV (weekly update)",
        type=["csv"],
        help="Same format as your historical data: symbol, date, open, high, low, close, volume, ric, avg, trade_value, sector"
    )

    if uploaded:
        if st.button("▶ Run Analysis", use_container_width=True):
            with st.spinner("Running full analysis…"):
                csv_bytes = uploaded.read()
                instr_list = parse_instructions_to_filters(st.session_state.instructions)
                scored = run_analysis(csv_bytes, json.dumps(instr_list))
                st.session_state.scored = scored
                st.session_state.last_upload = datetime.now().strftime("%d %b %Y %H:%M")
                st.session_state.weekly_briefing = None  # reset for new data
                st.success(f"✅ Analysed {len(scored)} stocks")

    if st.session_state.last_upload:
        st.markdown(f'<div style="font-size:0.78rem;color:#8b949e">Last run: {st.session_state.last_upload}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Quick instructions
    st.markdown("### ⚙️ Quick Filters")
    new_instr = st.text_input("Add instruction", placeholder="e.g. ignore agriculture")
    if st.button("Add", key="add_instr") and new_instr.strip():
        st.session_state.instructions.append({
            "date": datetime.now().strftime("%d %b"),
            "text": new_instr.strip(),
            "active": True
        })
        run_analysis.clear()
        st.rerun()

    if st.session_state.instructions:
        for i, instr in enumerate(st.session_state.instructions):
            cols = st.columns([0.75, 0.25])
            with cols[0]:
                st.markdown(f'<div style="font-size:0.82rem;color:#e6edf3">{instr["text"]}</div>',
                            unsafe_allow_html=True)
            with cols[1]:
                if st.button("✕", key=f"del_instr_{i}"):
                    st.session_state.instructions.pop(i)
                    run_analysis.clear()
                    st.rerun()

    st.markdown("---")
    st.markdown('<div style="font-size:0.75rem;color:#8b949e;text-align:center">Not financial advice.<br>Data: BRVM • Macro: BCEAO/WAEMU</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🏆 Rankings",
    "💬 AI Assistant",
    "📓 Notes & Results",
    "📰 Weekly Briefing"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    scored = st.session_state.scored

    # Macro pills
    st.markdown("### 🌍 Macro Environment")
    st.markdown(f"""
    <div style="margin-bottom:16px">
      <span class="macro-pill pill-green">🏦 BCEAO {MACRO['BCEAO_rate']}% — Easing</span>
      <span class="macro-pill pill-green">📈 WAEMU GDP {MACRO['WAEMU_GDP_2025']}%</span>
      <span class="macro-pill pill-blue">💰 Inflation {MACRO['WAEMU_inflation']}%</span>
      <span class="macro-pill pill-gold">📊 BRVM YTD +{MACRO['BRVM_CI_YTD']}%</span>
      <span class="macro-pill pill-red">🍫 Cocoa {MACRO['cocoa_drop_yoy']}%</span>
      <span class="macro-pill pill-red">🌿 Rubber {MACRO['rubber_drop_yoy']}%</span>
    </div>
    """, unsafe_allow_html=True)

    if scored is None:
        st.markdown("""
        <div class="card card-blue" style="text-align:center;padding:40px">
          <div style="font-size:2rem">📂</div>
          <div style="font-size:1.1rem;font-weight:700;margin:12px 0">Upload your CSV to get started</div>
          <div style="color:#8b949e">Use the sidebar to upload your weekly BRVM data and click Run Analysis</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary metrics
        n_buys   = len(scored[scored['entry_color']=='green'])
        n_peaks  = len(scored[scored['entry_color'].isin(['red','orange'])])
        n_watch  = len(scored[scored['entry_color']=='blue'])
        top_pick = scored.iloc[0]

        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(metric_card("STOCKS ANALYSED", len(scored), "blue"), unsafe_allow_html=True)
        with c2: st.markdown(metric_card("BUY SIGNALS", n_buys, "green", "Strong buy + buy on dips"), unsafe_allow_html=True)
        with c3: st.markdown(metric_card("AT/NEAR PEAK", n_peaks, "red", "Avoid buying now"), unsafe_allow_html=True)
        with c4: st.markdown(metric_card("TOP PICK", top_pick['ric'], "gold", f"Score {top_pick['composite']:.2f}"), unsafe_allow_html=True)

        st.markdown("---")

        # Top 3 Buys
        st.markdown('<div class="section-title">🚀 Top Buy Opportunities This Week</div>', unsafe_allow_html=True)
        buy_stocks = scored[scored['entry_color']=='green'].head(3)
        if len(buy_stocks) == 0:
            buy_stocks = scored.head(3)

        for _,r in buy_stocks.iterrows():
            hi_pct_str  = f"{r['pct_from_hi52']:+.1%} vs 52W High"
            ath_pct_str = f"{r['pct_from_ath']:+.1%} vs ATH"
            dy_str      = f"{r['div_yield']:.1%} div yield" if r['div_yield']>0.01 else "no dividend data"
            rsi_badge   = color_badge(f"RSI {r['rsi14']:.0f}", "red" if r['rsi14']>70 else ("green" if r['rsi14']<35 else "blue"))
            comp_badge  = color_badge(f"Score {r['composite']:.2f}", "green")
            entry_badge = color_badge(r['entry_signal'], r['entry_color'])

            st.markdown(f"""
            <div class="card card-green">
              <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                  <span class="stock-ticker">{r['ric']}</span>
                  <span style="color:#8b949e;font-size:0.88rem;margin-left:10px">{str(r['sector']).capitalize()}</span>
                </div>
                <div>
                  {comp_badge} {entry_badge} {rsi_badge}
                </div>
              </div>
              <div style="margin-top:10px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
                <div><div class="metric-lbl">Price (XOF)</div><div style="font-size:1.15rem;font-weight:700">{r['last_price']:,.0f}</div></div>
                <div><div class="metric-lbl">1Y Return</div><div style="font-size:1.15rem;font-weight:700;color:{'#2ea043' if r['ret_1y']>0 else '#f85149'}">{r['ret_1y']:+.1%}</div></div>
                <div><div class="metric-lbl">vs 52W High</div><div style="font-size:1.15rem;font-weight:700;color:{'#2ea043' if r['pct_from_hi52']<-0.1 else '#e3b341'}">{hi_pct_str}</div></div>
                <div><div class="metric-lbl">Dividend Yield</div><div style="font-size:1.15rem;font-weight:700;color:#e3b341">{dy_str}</div></div>
              </div>
              <div style="margin-top:8px;font-size:0.82rem;color:#8b949e">
                Entry score: {r['val_score']:.2f}/1.0  ·  {ath_pct_str}  ·  AI momentum: {r['ai_score']:.0%}  ·  MACD hist: {r['macd_hist']:+.0f}
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Stocks at peak — avoid
        st.markdown('<div class="section-title">⚠️ Stocks at or Near Peak — Avoid Buying</div>', unsafe_allow_html=True)
        peak_stocks = scored[scored['entry_color'].isin(['red','orange'])].head(4)

        if len(peak_stocks) > 0:
            cols = st.columns(len(peak_stocks))
            for col, (_, r) in zip(cols, peak_stocks.iterrows()):
                with col:
                    st.markdown(f"""
                    <div class="card card-{'red' if r['entry_color']=='red' else 'orange'}">
                      <div class="stock-ticker">{r['ric']}</div>
                      <div style="color:#8b949e;font-size:0.8rem">{str(r['sector']).capitalize()}</div>
                      <div style="margin:8px 0">
                        {color_badge(r['entry_signal'], r['entry_color'])}
                      </div>
                      <div style="font-size:0.85rem">Price: <b>{r['last_price']:,.0f}</b></div>
                      <div style="font-size:0.82rem;color:#8b949e">vs 52W Hi: <span style="color:#f85149">{r['pct_from_hi52']:+.1%}</span></div>
                      <div style="font-size:0.82rem;color:#8b949e">RSI: <span style="color:#f85149">{r['rsi14']:.0f}</span></div>
                      <div style="font-size:0.82rem;color:#8b949e">1Y return: {r['ret_1y']:+.1%}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#8b949e;font-size:0.9rem">No stocks flagged at peak currently.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — FULL RANKINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    scored = st.session_state.scored
    if scored is None:
        st.info("Upload data and run analysis first.")
    else:
        st.markdown("### 🏆 Full Stock Rankings")

        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            sector_filter = st.selectbox("Filter by sector",
                ["All"] + sorted(scored['sector'].dropna().unique().tolist()))
        with col_f2:
            signal_filter = st.selectbox("Filter by signal",
                ["All", "🚀 Strong Buy", "✅ Buy on Dips", "👀 Watch", "⚠️ Near/At Peak"])
        with col_f3:
            min_score = st.slider("Min composite score", 0.0, 1.0, 0.0, 0.05)

        display = scored.copy()
        if sector_filter != "All":
            display = display[display['sector']==sector_filter]
        if signal_filter != "All":
            sig_map = {"🚀 Strong Buy":"green","✅ Buy on Dips":"green",
                       "👀 Watch":"blue","⚠️ Near/At Peak": "red"}
            if signal_filter in ["🚀 Strong Buy","✅ Buy on Dips"]:
                display = display[display['entry_color']=='green']
            elif signal_filter == "👀 Watch":
                display = display[display['entry_color']=='blue']
            elif signal_filter == "⚠️ Near/At Peak":
                display = display[display['entry_color'].isin(['red','orange'])]
        display = display[display['composite'] >= min_score]

        # Render each row
        for _, r in display.iterrows():
            entry_c = r['entry_color']
            card_c  = "green" if entry_c=="green" else ("red" if entry_c in ["red","orange"] else "blue")
            rsi_badge = color_badge(f"RSI {r['rsi14']:.0f}",
                                    "red" if r['rsi14']>70 else ("green" if r['rsi14']<35 else "blue"))
            signal_badge = color_badge(r['entry_signal'], entry_c if entry_c!="orange" else "gold")

            st.markdown(f"""
            <div class="card card-{card_c}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <span style="color:#8b949e;font-size:0.9rem">#{r['rank']}</span>
                  <span class="stock-ticker" style="margin-left:8px">{r['ric']}</span>
                  <span style="color:#8b949e;font-size:0.85rem;margin-left:8px">{str(r['sector']).capitalize()}</span>
                </div>
                <div>{signal_badge} {rsi_badge} {color_badge(f"Composite {r['composite']:.2f}", "gold")}</div>
              </div>
              <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-top:10px;font-size:0.83rem">
                <div><div class="metric-lbl">Price</div><b>{r['last_price']:,.0f}</b></div>
                <div><div class="metric-lbl">AI Score</div><b>{r['ai_score']:.0%}</b></div>
                <div><div class="metric-lbl">Entry Score</div><b>{r['val_score']:.2f}</b></div>
                <div><div class="metric-lbl">vs 52W Hi</div><b style="color:{'#2ea043' if r['pct_from_hi52']<-0.15 else '#f85149' if r['pct_from_hi52']>-0.05 else '#e6edf3'}">{r['pct_from_hi52']:+.1%}</b></div>
                <div><div class="metric-lbl">vs ATH</div><b>{r['pct_from_ath']:+.1%}</b></div>
                <div><div class="metric-lbl">1Y Return</div><b style="color:{'#2ea043' if r['ret_1y']>0 else '#f85149'}">{r['ret_1y']:+.1%}</b></div>
                <div><div class="metric-lbl">Div Yield</div><b style="color:#e3b341">{r['div_yield']:.1%}</b></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 💬 AI Investment Assistant")
    st.markdown('<div style="color:#8b949e;font-size:0.88rem;margin-bottom:16px">Ask about specific stocks, get explanations of scores, give trading instructions, or explore macro themes.</div>', unsafe_allow_html=True)

    # Suggestion chips
    suggestions = [
        "Why is FTSC ranked #1?",
        "Is SNTS still worth buying at this price?",
        "Explain ONTBF's entry timing",
        "Which finance stocks benefit most from rate cuts?",
        "Generate a portfolio of 5 stocks with good entry points",
        "What's the risk for Burkina Faso-listed stocks?",
    ]
    st.markdown("**Quick questions:**")
    chip_cols = st.columns(3)
    for i, sug in enumerate(suggestions):
        with chip_cols[i % 3]:
            if st.button(sug, key=f"chip_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role":"user","content":sug})
                with st.spinner("Thinking…"):
                    reply = chat_with_ai(sug)
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()

    st.markdown("---")

    # Chat history
    if st.session_state.chat_history:
        chat_html = '<div id="chat-scroll">'
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                chat_html += f'<div class="chat-wrap"><div class="chat-user">{msg["content"]}</div></div>'
            else:
                content = msg['content'].replace('\n','<br>')
                chat_html += f'<div class="chat-wrap"><div class="chat-ai">🤖 {content}</div></div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # Input
    st.markdown("---")
    col_inp, col_btn = st.columns([0.85, 0.15])
    with col_inp:
        user_input = st.text_input("Message", placeholder="Ask anything about BRVM stocks, scores, macro…",
                                   label_visibility="collapsed", key="chat_input")
    with col_btn:
        send = st.button("Send", use_container_width=True)

    if send and user_input.strip():
        st.session_state.chat_history.append({"role":"user","content":user_input.strip()})
        with st.spinner("Thinking…"):
            reply = chat_with_ai(user_input.strip())
        st.session_state.chat_history.append({"role":"assistant","content":reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑 Clear chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — NOTES & RESULTS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### 📓 Investment Notes & Results")
    st.markdown('<div style="color:#8b949e;font-size:0.88rem;margin-bottom:16px">Log your trades, results, and personal observations. The AI assistant reads these notes to give you better advice.</div>', unsafe_allow_html=True)

    # Add note form
    with st.expander("➕ Add Note / Log Result", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            note_type = st.selectbox("Type", ["Trade Result", "Observation", "Research Note", "Instruction"])
            ticker_input = st.text_input("Ticker (optional)", placeholder="e.g. SNTS")
        with c2:
            note_date = st.date_input("Date", value=datetime.today())

        note_text = st.text_area("Note", placeholder=(
            "Examples:\n"
            "• Bought FTSC at 2,155 XOF on 08/03/2026\n"
            "• SNTS sold off after dividend ex-date as expected\n"
            "• Ignore all agriculture stocks until cocoa recovers\n"
            "• CBIBF reported +15% profit growth Q4 2025"
        ), height=100)

        if st.button("💾 Save Note", use_container_width=True):
            if note_text.strip():
                entry = {
                    "date": str(note_date),
                    "type": note_type,
                    "ticker": ticker_input.upper().strip(),
                    "text": note_text.strip(),
                    "active": True,
                }
                st.session_state.notes.append(entry)
                # If it's an instruction, also add to instructions
                if note_type == "Instruction":
                    st.session_state.instructions.append({
                        "date": str(note_date),
                        "text": note_text.strip(),
                        "active": True,
                    })
                st.success("✅ Note saved — the AI assistant will now factor this in")
                st.rerun()

    # Display notes
    if st.session_state.notes:
        st.markdown('<div class="section-title">Recent Notes</div>', unsafe_allow_html=True)
        for i, note in enumerate(reversed(st.session_state.notes)):
            type_color = {
                "Trade Result": "green", "Observation": "blue",
                "Research Note": "gold", "Instruction": "orange"
            }.get(note['type'], 'blue')

            ticker_html = f'<span style="font-weight:700;color:#58a6ff">{note["ticker"]}</span> — ' if note.get('ticker') else ''

            st.markdown(f"""
            <div class="note-box">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                <div>{color_badge(note['type'], type_color)} {ticker_html}<span style="color:#8b949e;font-size:0.8rem">{note['date']}</span></div>
              </div>
              <div style="color:#e6edf3">{note['text']}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑 Clear All Notes"):
            st.session_state.notes = []
            st.rerun()
    else:
        st.markdown('<div style="color:#8b949e;font-size:0.9rem">No notes yet. Log your first trade or observation above.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — WEEKLY BRIEFING
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("### 📰 Weekly Investment Briefing")
    st.markdown('<div style="color:#8b949e;font-size:0.88rem;margin-bottom:16px">Generate a concise AI-written briefing summarising the top buys, sells, and market tone for the week.</div>', unsafe_allow_html=True)

    if st.session_state.scored is None:
        st.info("Upload and analyse data first, then generate your briefing.")
    else:
        col_gen, col_date = st.columns([0.6, 0.4])
        with col_gen:
            if st.button("🗞 Generate Weekly Briefing", use_container_width=True):
                with st.spinner("Writing your briefing…"):
                    briefing = generate_weekly_briefing()
                st.session_state.weekly_briefing = briefing

        if st.session_state.weekly_briefing:
            st.markdown(f"""
            <div class="card card-gold">
              <div style="font-size:0.8rem;color:#8b949e;margin-bottom:10px">
                📅 Generated {datetime.now().strftime('%d %B %Y, %H:%M')}
              </div>
              <div style="font-size:0.95rem;line-height:1.7;color:#e6edf3;white-space:pre-wrap">{st.session_state.weekly_briefing}</div>
            </div>
            """, unsafe_allow_html=True)

            # Download button
            st.download_button(
                "⬇ Download Briefing (.txt)",
                data=st.session_state.weekly_briefing,
                file_name=f"BRVM_briefing_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
