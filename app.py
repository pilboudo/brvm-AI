import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
# MARKET INTELLIGENCE  —  Live web-search powered research
# ══════════════════════════════════════════════════════════════════════════════

# Ticker → full company name for better search queries
TICKER_NAMES = {
    "SNTS": "Sonatel Sénégal BRVM",
    "ONTBF": "ONATEL Burkina Faso BRVM",
    "CBIBF": "Coris Bank International Burkina Faso BRVM",
    "NSIAC": "NSIA Côte d'Ivoire assurance BRVM",
    "TTLS": "Total Energies Sénégal BRVM",
    "PALC": "Palm CI huile de palme BRVM",
    "ORIV": "Orange Côte d'Ivoire BRVM",
    "BIIC": "Banque Internationale pour l'Industrie et le Commerce BRVM",
    "SGBC": "Société Générale Côte d'Ivoire BRVM",
    "BOABF": "Bank of Africa Burkina Faso BRVM",
    "SIBC": "Société Ivoirienne de Banque BRVM",
    "ETIT": "Ecobank Transnational BRVM",
    "FTSC": "Filtisac Côte d'Ivoire BRVM",
    "STAC": "SAPH caoutchouc Côte d'Ivoire BRVM",
    "BNBC": "Bernabé CI BRVM",
    "CFAC": "CFAO Motors Côte d'Ivoire BRVM",
    "SEMC": "Crown Siem Côte d'Ivoire BRVM",
    "SICC": "SICOGI Côte d'Ivoire BRVM",
    "UNLC": "Unilever Côte d'Ivoire BRVM",
    "TTLC": "TotalEnergies Marketing Côte d'Ivoire BRVM",
    "STBC": "Société des Transports Abidjanais BRVM",
    "SCRC": "SUCRIVOIRE Côte d'Ivoire BRVM",
}

# Dividend history for income profile (3 years)
DIVIDEND_HISTORY_3Y = {
    "SNTS":  {"2022": 1556, "2023": 1667, "2024": 1750, "growth": "+6.3%", "yield_3y_avg": "6.1%", "payout_consistent": True},
    "SGBC":  {"2022": 1100, "2023": 1200, "2024": 1300, "growth": "+8.7%", "yield_3y_avg": "4.2%", "payout_consistent": True},
    "BOABF": {"2022": 600,  "2023": 650,  "2024": 700,  "growth": "+8.3%", "yield_3y_avg": "5.8%", "payout_consistent": True},
    "CBIBF": {"2022": 650,  "2023": 790,  "2024": 850,  "growth": "+14.3%","yield_3y_avg": "6.2%", "payout_consistent": True},
    "SIBC":  {"2022": 400,  "2023": 450,  "2024": 500,  "growth": "+11.8%","yield_3y_avg": "3.8%", "payout_consistent": True},
    "PALC":  {"2022": 800,  "2023": 900,  "2024": None,  "growth": "+12.5%","yield_3y_avg": "8.1%", "payout_consistent": False},
    "ETIT":  {"2022": 1.2,  "2023": 1.5,  "2024": 1.8,  "growth": "+22.5%","yield_3y_avg": "2.1%", "payout_consistent": True},
    "TTLC":  {"2022": 350,  "2023": 420,  "2024": 500,  "growth": "+19.5%","yield_3y_avg": "4.5%", "payout_consistent": True},
    "ONTBF": {"2022": 700,  "2023": 750,  "2024": None,  "growth": "+7.1%", "yield_3y_avg": "17.5%","payout_consistent": False},
    "TTLS":  {"2022": 220,  "2023": 260,  "2024": 300,  "growth": "+16.9%","yield_3y_avg": "7.8%", "payout_consistent": True},
    "UNLC":  {"2022": 1200, "2023": 1300, "2024": None,  "growth": "+8.3%", "yield_3y_avg": "5.2%", "payout_consistent": False},
    "SCRC":  {"2022": 500,  "2023": 550,  "2024": None,  "growth": "+10.0%","yield_3y_avg": "3.9%", "payout_consistent": False},
    "STBC":  {"2022": 350,  "2023": 400,  "2024": None,  "growth": "+14.3%","yield_3y_avg": "5.7%", "payout_consistent": False},
}

def fetch_market_intelligence(tickers: list, api_key: str, progress_callback=None) -> dict:
    """
    Use Claude with web_search tool to fetch live market intelligence
    for a list of BRVM tickers. Returns dict: {ric -> intel_dict}
    """
    if not api_key:
        return {}

    client = anthropic.Anthropic(api_key=api_key)
    results = {}

    for i, ric in enumerate(tickers):
        if progress_callback:
            progress_callback(i, len(tickers), ric)

        company_name = TICKER_NAMES.get(ric, f"{ric} BRVM")
        div_hist = DIVIDEND_HISTORY_3Y.get(ric, {})
        div_context = ""
        if div_hist:
            yrs = [f"{y}: {v} XOF" for y, v in div_hist.items() if y.isdigit() and v]
            div_context = f"Known dividend history: {', '.join(yrs)}. Avg yield: {div_hist.get('yield_3y_avg','N/A')}."

        prompt = f"""You are a BRVM (West African stock exchange) equity research analyst.
Research this stock: {ric} ({company_name})

{div_context}

Search for the MOST RECENT information available on:
1. brvm.org or sikafinance.com or richbourse.com — recent price action and volume trends for {ric}
2. Recent news about {company_name} — earnings, dividends, corporate actions, management changes
3. amf-uemoa.org — any recent regulatory filings, press releases, or sanctions for this company
4. Macro/sector catalysts specifically relevant to this stock (WAEMU, BCEAO, sector trends)

Return ONLY a JSON object (no markdown, no preamble) with these exact keys:
{{
  "sentiment": "bullish" | "neutral" | "bearish",
  "sentiment_score": 0.0-1.0,
  "volume_trend": "increasing" | "stable" | "decreasing" | "unknown",
  "volume_comment": "one sentence about recent volume",
  "catalyst_positive": ["list", "of", "upcoming", "positive", "catalysts"],
  "catalyst_negative": ["list", "of", "risk", "factors"],
  "dividend_comment": "one sentence about dividend outlook based on what you found",
  "dividend_consistency": "consistent" | "irregular" | "suspended" | "unknown",
  "analyst_note": "2-3 sentence summary of key finding from your research",
  "data_sources": ["source1", "source2"],
  "last_updated": "March 2026"
}}"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}]
            )
            # Extract the final text block
            text_blocks = [b for b in response.content if hasattr(b, 'text')]
            if text_blocks:
                raw = text_blocks[-1].text.strip()
                raw = raw.replace("```json","").replace("```","").strip()
                try:
                    intel = json.loads(raw)
                    intel['ric'] = ric
                    results[ric] = intel
                except json.JSONDecodeError:
                    results[ric] = _default_intel(ric, "JSON parse error")
            else:
                results[ric] = _default_intel(ric, "No text response")
        except Exception as e:
            results[ric] = _default_intel(ric, str(e))

    return results


def _default_intel(ric: str, error: str = "") -> dict:
    return {
        "ric": ric, "sentiment": "neutral", "sentiment_score": 0.5,
        "volume_trend": "unknown", "volume_comment": "No data available.",
        "catalyst_positive": [], "catalyst_negative": [],
        "dividend_comment": "No recent data found.",
        "dividend_consistency": "unknown",
        "analyst_note": f"Research unavailable. {error}",
        "data_sources": [], "last_updated": "N/A"
    }


def generate_deep_dive(ric: str, scored_row: dict, intel: dict,
                       portfolio_position: dict, api_key: str) -> str:
    """Generate a comprehensive per-ticker equity research note."""
    if not api_key:
        return "⚠️ API key required."
    client = anthropic.Anthropic(api_key=api_key)

    pos_text = "Not currently held."
    if portfolio_position:
        p = portfolio_position
        pos_text = (
            f"HELD: {p.get('qty',0):.0f} shares @ avg cost {p.get('avg_cost',0):,.0f} XOF | "
            f"Current P&L: {p.get('unrealised_pct',0):+.1%} | "
            f"Dividends received: {p.get('div_received',0):,.0f} XOF"
        )

    div_hist = DIVIDEND_HISTORY_3Y.get(ric, {})
    div_text = ""
    if div_hist:
        yrs = [f"{y}: {v} XOF" for y, v in div_hist.items() if y.isdigit() and v]
        div_text = f"3Y dividends: {', '.join(yrs)} | Growth: {div_hist.get('growth','N/A')} | Consistency: {'Yes' if div_hist.get('payout_consistent') else 'Irregular'}"

    prompt = f"""You are a senior BRVM equity research analyst writing a formal stock note.

TICKER: {ric} ({TICKER_NAMES.get(ric, ric)})
SECTOR: {scored_row.get('sector','N/A')}

QUANTITATIVE DATA:
- Price: {scored_row.get('last_price',0):,.0f} XOF
- vs 52W High: {scored_row.get('pct_from_hi52',0):+.1%}
- vs ATH: {scored_row.get('pct_from_ath',0):+.1%}
- 1Y Return: {scored_row.get('ret_1y',0):+.1%}
- RSI(14): {scored_row.get('rsi14',50):.0f}
- MACD hist: {scored_row.get('macd_hist',0):+.1f}
- Div yield: {scored_row.get('div_yield',0):.1%}
- AI composite score: {scored_row.get('composite',0):.2f}/1.0
- Entry signal: {scored_row.get('entry_signal','N/A')}

LIVE INTELLIGENCE (from web research):
- Market sentiment: {intel.get('sentiment','N/A')} (score: {intel.get('sentiment_score',0.5):.2f})
- Volume trend: {intel.get('volume_trend','N/A')}
- Volume comment: {intel.get('volume_comment','N/A')}
- Positive catalysts: {', '.join(intel.get('catalyst_positive',[]) or ['None identified'])}
- Risk factors: {', '.join(intel.get('catalyst_negative',[]) or ['None identified'])}
- Dividend outlook: {intel.get('dividend_comment','N/A')}
- Analyst note: {intel.get('analyst_note','N/A')}
- Sources: {', '.join(intel.get('data_sources',[]) or ['N/A'])}

INCOME PROFILE (3-year):
{div_text if div_text else 'No dividend history available.'}

PORTFOLIO INTEGRATION:
{pos_text}

MACRO (March 2026): BCEAO 3.00% (easing) | WAEMU GDP 6.7% | BRVM YTD +6.9%

Write a structured research note with these sections:
## Investment Thesis (2-3 sentences, buy/hold/sell recommendation)
## Market Sentiment & Volume Analysis
## Catalyst Watch (next 3-6 months)
## Income Profile & Dividend Analysis
## Portfolio Recommendation (specific action for this investor)
## Key Risks
## Price Target Indication (qualitative range vs current price)

Be specific, data-driven, professional. Max 450 words."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Error generating deep dive: {e}"


def generate_rebalance_report(scored: pd.DataFrame, portfolio_data: dict,
                               market_intel: dict, api_key: str) -> str:
    """Generate a full portfolio rebalance recommendation integrating live intel."""
    if not api_key:
        return "⚠️ API key required."
    client = anthropic.Anthropic(api_key=api_key)

    if portfolio_data is None:
        pos_text = "No portfolio data loaded."
    else:
        pos = portfolio_data['positions']
        lines = []
        for _, r in pos.iterrows():
            intel = market_intel.get(r['ric'], {})
            lines.append(
                f"  {r['ric']} | Qty:{r['qty']:.0f} | AvgCost:{r['avg_cost']:,.0f} | "
                f"CMP:{r['current_price']:,.0f} | P&L:{r['unrealised_pct']:+.1%} | "
                f"Total return:{r['total_return_pct']:+.1%} | Divs:{r['div_received']:,.0f} XOF | "
                f"AI signal:{r['ai_signal']} | Sentiment:{intel.get('sentiment','N/A')} | "
                f"Catalysts:{'; '.join(intel.get('catalyst_positive',[])[:2] or ['none'])} | "
                f"Risks:{'; '.join(intel.get('catalyst_negative',[])[:2] or ['none'])}"
            )
        pos_text = "\n".join(lines)
        summary = (
            f"Total value: {portfolio_data['total_current_val']:,.0f} XOF | "
            f"Cost basis: {portfolio_data['total_cost_basis']:,.0f} XOF | "
            f"Unrealised P&L: {portfolio_data['total_pl_pct']:+.1%} | "
            f"Total return (incl divs): {portfolio_data['total_return_pct']:+.1%} | "
            f"Cash balance: {portfolio_data['cash_balance']:,.0f} XOF"
        )

    # Top buy candidates with intel
    top_buys = scored.head(10)
    buy_lines = []
    for _, r in top_buys.iterrows():
        intel = market_intel.get(r['ric'], {})
        buy_lines.append(
            f"  #{r['rank']} {r['ric']} | Score:{r['composite']:.2f} | {r['entry_signal']} | "
            f"Sentiment:{intel.get('sentiment','N/A')} | "
            f"Catalysts:{'; '.join(intel.get('catalyst_positive',[])[:2] or ['none'])}"
        )
    buys_text = "\n".join(buy_lines)

    prompt = f"""You are a senior BRVM portfolio strategist. Produce a comprehensive rebalance report.

PORTFOLIO SUMMARY:
{summary if portfolio_data else 'No portfolio loaded.'}

CURRENT HOLDINGS (with live intelligence):
{pos_text}

TOP-RANKED OPPORTUNITIES (model + live intel):
{buys_text}

MACRO (March 2026): BCEAO rate 3.00% easing | WAEMU GDP 6.7% | BRVM YTD +6.9% | Cocoa -43.9% | Rubber -23.5%

Produce a structured REBALANCE REPORT:

## Executive Summary (3 sentences: overall portfolio health, market context, key action)

## Holdings Review — Action per Position
For each holding, give: HOLD / ADD / TRIM / EXIT with specific reasoning integrating P&L, AI signal, sentiment, and catalysts.

## New Positions to Initiate
Top 2-3 stocks from the opportunity list not currently held, with rationale and suggested entry sizing.

## Income Optimisation
Dividend calendar review — which positions to reinforce for income, any upcoming ex-dates to act before.

## Risk & Concentration
Flag any sector concentration, geopolitical exposure, or overleveraged positions.

## Priority Action Plan (numbered, top 5 actions in order of urgency)

Be direct, specific with prices and percentages. Professional tone. Max 600 words."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Error: {e}"


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
        "transactions": [],          # ledger of all transactions
        "portfolio_analysis": None,  # cached AI assessment text
        "port_data_v2": None,        # computed portfolio analytics
        "market_intel": {},          # {ric -> intel_dict} from live web research
        "deep_dive_cache": {},       # {ric -> research_text}
        "rebalance_report": None,    # cached rebalance report
        "intel_last_run": None,      # timestamp of last research run
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

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
# PORTFOLIO HELPERS  —  Transaction-ledger based
# ══════════════════════════════════════════════════════════════════════════════

# Transaction schema:
#   id, date, type (BUY|SELL|DIVIDEND|DIV_REINVEST), ric, qty, price, cash_flow, notes
#   cash_flow: negative = cash out (buy), positive = cash in (sell/div)


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
        sentiment_s=0.5  # default neutral; overridden post-hoc by recalculate_with_intel()
        composite=(row['ai_score']*0.40+val_score*0.30+(0.5+macro_adj)*0.15+sentiment_s*0.15)

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
            'macro_adj':macro_adj,'sentiment_score':sentiment_s,'composite':composite,
            'entry_signal':entry_signal,'entry_color':entry_color,
        })

    scored=pd.DataFrame(rows).sort_values('composite',ascending=False).reset_index(drop=True)
    scored['rank']=range(1,len(scored)+1)
    return scored

def recalculate_with_intel(scored: 'pd.DataFrame', market_intel: dict) -> 'pd.DataFrame':
    """Re-score the scored dataframe incorporating live sentiment scores."""
    if scored is None or not market_intel:
        return scored
    df = scored.copy()
    for i, row in df.iterrows():
        ric = row['ric']
        intel = market_intel.get(ric, {})
        sentiment_s = float(intel.get('sentiment_score', 0.5))
        macro_adj = row['macro_adj']
        # Updated composite: 40% AI + 30% entry + 15% macro + 15% sentiment
        new_composite = (row['ai_score']*0.40 + row['val_score']*0.30 +
                         (0.5+macro_adj)*0.15 + sentiment_s*0.15)
        df.at[i, 'sentiment_score'] = sentiment_s
        df.at[i, 'composite'] = new_composite
        # Re-derive entry signal from new composite
        pct_from_hi52 = row['pct_from_hi52']
        rsi_v = row['rsi14']
        if pct_from_hi52 > -0.03 and rsi_v > 72:
            df.at[i, 'entry_signal'] = "⚠️ AT PEAK — WAIT"
            df.at[i, 'entry_color'] = "red"
        elif pct_from_hi52 > -0.05:
            df.at[i, 'entry_signal'] = "⚠️ NEAR PEAK — WAIT"
            df.at[i, 'entry_color'] = "orange"
        elif new_composite > 0.60 and pct_from_hi52 < -0.15:
            df.at[i, 'entry_signal'] = "🚀 STRONG BUY"
            df.at[i, 'entry_color'] = "green"
        elif new_composite > 0.52 and pct_from_hi52 < -0.08:
            df.at[i, 'entry_signal'] = "✅ BUY ON DIPS"
            df.at[i, 'entry_color'] = "green"
        elif new_composite > 0.48:
            df.at[i, 'entry_signal'] = "👀 WATCH"
            df.at[i, 'entry_color'] = "blue"
        else:
            df.at[i, 'entry_signal'] = "📊 NEUTRAL"
            df.at[i, 'entry_color'] = "grey"
    df = df.sort_values('composite', ascending=False).reset_index(drop=True)
    df['rank'] = range(1, len(df)+1)
    return df


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
# SIDEBAR
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

def ledger_to_positions(transactions: list) -> pd.DataFrame:
    """Derive current open positions from transaction ledger."""
    if not transactions:
        return pd.DataFrame(columns=['ric','qty','avg_cost','total_cost','sector'])

    rows = []
    for t in transactions:
        if t['type'] in ('BUY', 'DIV_REINVEST'):
            rows.append({'ric': t['ric'], 'qty': float(t['qty']),
                         'cost': float(t['qty']) * float(t['price']),
                         'sector': t.get('sector','')})
        elif t['type'] == 'SELL':
            rows.append({'ric': t['ric'], 'qty': -float(t['qty']),
                         'cost': -float(t['qty']) * float(t['price']),
                         'sector': t.get('sector','')})

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=['ric','qty','avg_cost','total_cost','sector'])

    pos = df.groupby('ric').agg(
        qty=('qty','sum'),
        total_cost=('cost','sum'),
        sector=('sector','last')
    ).reset_index()
    pos = pos[pos['qty'] > 0.001].copy()
    pos['avg_cost'] = pos['total_cost'] / pos['qty']
    return pos


def ledger_cash_balance(transactions: list) -> float:
    """Sum all cash flows from the ledger."""
    return sum(float(t.get('cash_flow', 0)) for t in transactions)


def compute_portfolio_v2(transactions: list, df_market: pd.DataFrame,
                         scored: pd.DataFrame) -> dict:
    """Full portfolio analytics from transaction ledger."""
    if not transactions or df_market is None:
        return None

    positions = ledger_to_positions(transactions)
    if positions.empty:
        return None

    # ── BRVM Composite baseline ─────────────────────────────────────────────
    all_dates   = df_market['date'].sort_values().unique()
    earliest_tx = min(pd.to_datetime(t['date']) for t in transactions)
    idx_data    = (df_market.groupby(['date','symbol'])['close']
                   .last().unstack().ffill())
    idx_slice   = idx_data[idx_data.index >= earliest_tx].dropna(how='all')
    if len(idx_slice) > 1:
        base          = idx_slice.iloc[0].replace(0, np.nan)
        brvm_composite = (idx_slice / base * 100).mean(axis=1)
    else:
        brvm_composite = pd.Series(dtype=float)

    # ── Per-position analytics ──────────────────────────────────────────────
    results        = []
    port_val_series = {}
    total_cost_basis = 0
    total_current_val = 0

    for _, pos in positions.iterrows():
        ric       = pos['ric'].upper().strip()
        qty       = float(pos['qty'])
        avg_cost  = float(pos['avg_cost'])
        sector    = pos.get('sector', '')
        cost_b    = qty * avg_cost

        # Market data for this ticker
        sym_rows = df_market[df_market['ric'].str.upper() == ric]
        if sym_rows.empty:
            sym_rows = df_market[df_market['symbol'].str.upper().str.startswith(ric)]

        if sym_rows.empty:
            current_price = avg_cost
            price_hist    = pd.Series(dtype=float)
        else:
            sym_sorted    = sym_rows.sort_values('date')
            current_price = sym_sorted.iloc[-1]['close']
            price_hist    = sym_sorted.set_index('date')['close']

        current_val   = qty * current_price
        unrealised_pl = current_val - cost_b
        unrealised_pct= unrealised_pl / cost_b if cost_b > 0 else 0

        total_cost_basis  += cost_b
        total_current_val += current_val

        # Realised P&L from sells of this ticker
        sell_txs = [t for t in transactions if t['ric'].upper()==ric and t['type']=='SELL']
        realised_pl = sum(
            (float(t['price']) - _avg_cost_at(transactions, ric, t['date'])) * float(t['qty'])
            for t in sell_txs
        )

        # Dividends actually received (from ledger)
        div_received = sum(
            float(t.get('cash_flow',0))
            for t in transactions
            if t['ric'].upper()==ric and t['type']=='DIVIDEND'
        )
        div_reinvested = sum(
            float(t['qty'])*float(t['price'])
            for t in transactions
            if t['ric'].upper()==ric and t['type']=='DIV_REINVEST'
        )

        # Upcoming dividends from DIVIDENDS dict
        max_date    = df_market['date'].max()
        upcoming_div= None
        if ric in DIVIDENDS:
            divs = pd.DataFrame(DIVIDENDS[ric], columns=['ex_date','dividend'])
            divs['ex_date'] = pd.to_datetime(divs['ex_date'])
            future = divs[divs['ex_date'] > max_date].sort_values('ex_date')
            if not future.empty:
                nxt = future.iloc[0]
                upcoming_div = {
                    'date':   nxt['ex_date'],
                    'per_share': nxt['dividend'],
                    'amount': nxt['dividend'] * qty,
                }

        total_return_xof = unrealised_pl + realised_pl + div_received
        total_return_pct = total_return_xof / cost_b if cost_b > 0 else 0

        # AI signal
        ai_signal = "No data"; ai_score = None; composite = None
        if scored is not None:
            match = scored[scored['ric'].str.upper() == ric]
            if not match.empty:
                ai_signal = match.iloc[0]['entry_signal']
                ai_score  = match.iloc[0]['ai_score']
                composite = match.iloc[0]['composite']

        # Recommendation
        if unrealised_pct > 0.40 and (composite or 0) < 0.50:
            rec, rec_col = "✂️ TRIM — strong gain, weakening signal", "orange"
        elif unrealised_pct > 0.60:
            rec, rec_col = "✂️ TRIM — take profit", "orange"
        elif unrealised_pct < -0.25 and (composite or 0) > 0.55:
            rec, rec_col = "➕ ADD — down sharply, model still bullish", "green"
        elif unrealised_pct < -0.35:
            rec, rec_col = "🔄 REVIEW — large loss, reassess thesis", "red"
        elif (composite or 0) > 0.58:
            rec, rec_col = "✅ HOLD & CONSIDER ADDING", "green"
        else:
            rec, rec_col = "🤝 HOLD", "blue"

        # Price series for chart
        if len(price_hist) > 0:
            first_buy = min(
                pd.to_datetime(t['date'])
                for t in transactions
                if t['ric'].upper()==ric and t['type'] in ('BUY','DIV_REINVEST')
            )
            ph = price_hist[price_hist.index >= first_buy]
            # Build value series respecting partial sells
            val_s = _build_value_series(transactions, ric, price_hist)
            if val_s is not None:
                port_val_series[ric] = val_s

        results.append({
            'ric': ric, 'sector': sector,
            'qty': qty, 'avg_cost': avg_cost,
            'current_price': current_price,
            'cost_basis': cost_b,
            'current_val': current_val,
            'unrealised_pl': unrealised_pl,
            'unrealised_pct': unrealised_pct,
            'realised_pl': realised_pl,
            'div_received': div_received,
            'div_reinvested': div_reinvested,
            'total_return_xof': total_return_xof,
            'total_return_pct': total_return_pct,
            'upcoming_div': upcoming_div,
            'ai_signal': ai_signal,
            'ai_score': ai_score,
            'composite': composite,
            'recommendation': rec,
            'rec_color': rec_col,
        })

    pos_df = pd.DataFrame(results)

    # ── Portfolio-level totals ───────────────────────────────────────────────
    total_pl        = total_current_val - total_cost_basis
    total_pl_pct    = total_pl / total_cost_basis if total_cost_basis > 0 else 0
    total_divs      = pos_df['div_received'].sum()
    total_realised  = pos_df['realised_pl'].sum()
    total_return_abs= total_pl + total_divs + total_realised
    total_return_pct= total_return_abs / total_cost_basis if total_cost_basis > 0 else 0
    cash_balance    = ledger_cash_balance(transactions)

    # ── Portfolio daily value series ────────────────────────────────────────
    if port_val_series:
        port_series = (pd.concat(port_val_series.values(), axis=1)
                       .sum(axis=1).sort_index())
        port_series = port_series[port_series > 0]
    else:
        port_series = pd.Series(dtype=float)

    # Align BRVM composite to portfolio start value
    if len(brvm_composite) > 1 and len(port_series) > 1:
        start_val     = port_series.iloc[0]
        brvm_aligned  = brvm_composite / brvm_composite.iloc[0] * start_val
    else:
        brvm_aligned  = pd.Series(dtype=float)

    # ── Sector allocation ───────────────────────────────────────────────────
    sec_alloc     = pos_df.groupby('sector')['current_val'].sum()
    sec_alloc_pct = (sec_alloc / total_current_val * 100).round(1) if total_current_val > 0 else sec_alloc

    # ── Upcoming dividends (all positions) ──────────────────────────────────
    upcoming_divs = sorted(
        [{'ric': r['ric'], **r['upcoming_div']}
         for _, r in pos_df.iterrows() if r['upcoming_div']],
        key=lambda x: x['date']
    )

    return {
        'positions':        pos_df,
        'total_cost_basis': total_cost_basis,
        'total_current_val':total_current_val,
        'total_pl':         total_pl,
        'total_pl_pct':     total_pl_pct,
        'total_divs':       total_divs,
        'total_realised':   total_realised,
        'total_return_abs': total_return_abs,
        'total_return_pct': total_return_pct,
        'cash_balance':     cash_balance,
        'port_series':      port_series,
        'brvm_aligned':     brvm_aligned,
        'sec_alloc_pct':    sec_alloc_pct,
        'upcoming_divs':    upcoming_divs,
        'transactions':     transactions,
    }


def _avg_cost_at(transactions: list, ric: str, before_date: str) -> float:
    """Compute average cost of a position just before a given date."""
    bd   = pd.to_datetime(before_date)
    buys = [t for t in transactions
            if t['ric'].upper()==ric.upper()
            and t['type'] in ('BUY','DIV_REINVEST')
            and pd.to_datetime(t['date']) < bd]
    sells= [t for t in transactions
            if t['ric'].upper()==ric.upper()
            and t['type']=='SELL'
            and pd.to_datetime(t['date']) < bd]
    total_qty  = sum(float(t['qty']) for t in buys) - sum(float(t['qty']) for t in sells)
    total_cost = sum(float(t['qty'])*float(t['price']) for t in buys)
    return total_cost / total_qty if total_qty > 0 else 0


def _build_value_series(transactions: list, ric: str,
                        price_hist: pd.Series) -> pd.Series:
    """Build daily portfolio value series for one ticker, respecting partial sells."""
    buy_txs  = sorted(
        [t for t in transactions
         if t['ric'].upper()==ric.upper() and t['type'] in ('BUY','DIV_REINVEST')],
        key=lambda x: x['date']
    )
    if not buy_txs:
        return None

    first_date = pd.to_datetime(buy_txs[0]['date'])
    ph         = price_hist[price_hist.index >= first_date].copy()
    if len(ph) < 2:
        return None

    # Build running qty series
    qty_changes = {}
    for t in transactions:
        if t['ric'].upper() != ric.upper():
            continue
        d = pd.to_datetime(t['date'])
        if t['type'] in ('BUY','DIV_REINVEST'):
            qty_changes[d] = qty_changes.get(d, 0) + float(t['qty'])
        elif t['type'] == 'SELL':
            qty_changes[d] = qty_changes.get(d, 0) - float(t['qty'])

    qty_series = pd.Series(qty_changes).sort_index().reindex(ph.index).fillna(0).cumsum().ffill()
    qty_series = qty_series.clip(lower=0)
    return (ph * qty_series).dropna()


def generate_portfolio_ai_analysis(portfolio_data: dict) -> str:
    """Ask Claude for a full portfolio assessment."""
    client = get_ai_client()
    if not client:
        return "⚠️ Please enter your Anthropic API key in the sidebar."

    pos = portfolio_data['positions']
    txns = portfolio_data.get('transactions', [])

    positions_text = "\n".join([
        f"  {r['ric']} ({r['sector']}) | Qty: {r['qty']:.0f} | "
        f"Avg cost: {r['avg_cost']:,.0f} | Current: {r['current_price']:,.0f} | "
        f"Unrealised P&L: {r['unrealised_pct']:+.1%} | "
        f"Realised P&L: {r['realised_pl']:+,.0f} XOF | "
        f"Divs received: {r['div_received']:,.0f} XOF | "
        f"Total return: {r['total_return_pct']:+.1%} | "
        f"AI signal: {r['ai_signal']} | Composite: {r['composite'] if r['composite'] else 'N/A'}"
        for _, r in pos.iterrows()
    ])
    sector_text = "\n".join(
        f"  {s}: {v:.1f}%" for s, v in portfolio_data['sec_alloc_pct'].items()
    )
    recent_txns = sorted(txns, key=lambda x: x['date'], reverse=True)[:10]
    txn_text = "\n".join(
        f"  {t['date']} | {t['type']} | {t['ric']} | "
        f"qty:{t['qty']} @ {float(t['price']):,.0f} XOF"
        for t in recent_txns
    )

    prompt = f"""You are an expert BRVM investment analyst. Analyse this investor's portfolio and provide sharp, actionable advice.

PORTFOLIO SUMMARY:
  Cost basis:        {portfolio_data['total_cost_basis']:,.0f} XOF
  Current value:     {portfolio_data['total_current_val']:,.0f} XOF
  Unrealised P&L:    {portfolio_data['total_pl']:+,.0f} XOF ({portfolio_data['total_pl_pct']:+.1%})
  Realised P&L:      {portfolio_data['total_realised']:+,.0f} XOF
  Dividends earned:  {portfolio_data['total_divs']:,.0f} XOF
  Total return:      {portfolio_data['total_return_abs']:+,.0f} XOF ({portfolio_data['total_return_pct']:+.1%})
  Cash balance:      {portfolio_data['cash_balance']:,.0f} XOF

OPEN POSITIONS:
{positions_text}

SECTOR ALLOCATION:
{sector_text}

RECENT TRANSACTIONS:
{txn_text}

MACRO (March 2026):
  BCEAO rate 3.00% (easing) | WAEMU GDP 6.7% | Inflation -0.8%
  BRVM YTD +6.9% | Cocoa -43.9% | Rubber -23.5%

Provide:
1. **Overall Assessment** — total return vs BRVM benchmark (+6.9% YTD), are they beating the market?
2. **Position Advice** — for each open position: hold / add / trim / exit with specific reasoning
3. **Risk Flags** — concentration, sector exposure, overextended positions
4. **Dividend Outlook** — income quality, what to expect next
5. **Top Action This Week** — the single most impactful move right now

Be direct, specific with numbers. Under 500 words."""

    try:
        response = get_ai_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role":"user","content":prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

with st.sidebar:
    st.markdown("## 📈 BRVM AI Tool")
    st.markdown("---")

    # ── API Key ────────────────────────────────────────────────────────────
    st.markdown("### 🔑 API Key")
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.get("api_key", ""),
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input
        st.markdown('<span class="badge badge-green">✓ Key Set</span>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Data Upload ────────────────────────────────────────────────────────
    st.markdown("### 📂 Upload Market Data")
    uploaded = st.file_uploader(
        "Upload BRVM CSV (weekly update)",
        type=["csv"],
        help="Columns: symbol, date, open, high, low, close, volume, ric, avg, trade_value, sector"
    )

    if uploaded:
        if st.button("▶ Run Analysis", use_container_width=True):
            with st.spinner("Running full analysis…"):
                csv_bytes = uploaded.read()
                # Store raw market df for portfolio price lookups
                raw = pd.read_csv(io.BytesIO(csv_bytes), low_memory=False)
                raw = raw[raw['symbol'] != 'symbol']
                for _c in ['open','high','low','close','volume','avg','trade_value']:
                    raw[_c] = pd.to_numeric(raw[_c], errors='coerce')
                raw['date'] = pd.to_datetime(raw['date'], errors='coerce')
                raw = raw.dropna(subset=['date','close','symbol'])
                raw = raw[raw['close'] > 0].sort_values(['symbol','date']).reset_index(drop=True)
                st.session_state.raw_df = raw
                instr_list = parse_instructions_to_filters(st.session_state.instructions)
                scored = run_analysis(csv_bytes, json.dumps(instr_list))
                st.session_state.scored = scored
                st.session_state.last_upload = datetime.now().strftime("%d %b %Y %H:%M")
                st.session_state.weekly_briefing = None
                st.session_state.port_data_v2    = None
                st.success(f"✅ Analysed {len(scored)} stocks")

    if st.session_state.last_upload:
        st.markdown(
            f'<div style="font-size:0.78rem;color:#8b949e">Last run: {st.session_state.last_upload}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Quick Filters / Instructions ───────────────────────────────────────
    st.markdown("### ⚙️ Quick Filters")
    new_instr = st.text_input("Add instruction", placeholder="e.g. ignore agriculture")
    if st.button("Add", key="add_instr") and new_instr.strip():
        st.session_state.instructions.append({
            "date":   datetime.now().strftime("%d %b"),
            "text":   new_instr.strip(),
            "active": True,
        })
        run_analysis.clear()
        st.rerun()

    if st.session_state.instructions:
        for i, instr in enumerate(st.session_state.instructions):
            cols = st.columns([0.75, 0.25])
            with cols[0]:
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#e6edf3">{instr["text"]}</div>',
                    unsafe_allow_html=True
                )
            with cols[1]:
                if st.button("✕", key=f"del_instr_{i}"):
                    st.session_state.instructions.pop(i)
                    run_analysis.clear()
                    st.rerun()

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.75rem;color:#8b949e;text-align:center">'
        'Not financial advice.<br>Data: BRVM • Macro: BCEAO/WAEMU</div>',
        unsafe_allow_html=True
    )

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "🏆 Rankings",
    "💼 My Portfolio",
    "💬 AI Assistant",
    "📓 Notes & Results",
    "📰 Weekly Briefing",
    "🔍 Deep Research"
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
            # Sentiment badge if live intel available
            intel_r = st.session_state.market_intel.get(r['ric'], {})
            sent_str = intel_r.get('sentiment','') if intel_r else ''
            sent_badge = ''
            if sent_str == 'bullish':
                sent_badge = color_badge('🟢 Bullish', 'green')
            elif sent_str == 'bearish':
                sent_badge = color_badge('🔴 Bearish', 'red')
            elif sent_str == 'neutral':
                sent_badge = color_badge('⚪ Neutral', 'blue')
            catalyst_html = ''
            if intel_r.get('catalyst_positive'):
                cats = ' · '.join((intel_r['catalyst_positive'] or [])[:2])
                catalyst_html = f'<div style="font-size:0.77rem;color:#2ea043;margin-top:4px">✅ {cats}</div>'
            if intel_r.get('catalyst_negative'):
                risks = ' · '.join((intel_r['catalyst_negative'] or [])[:2])
                catalyst_html += f'<div style="font-size:0.77rem;color:#f85149;margin-top:2px">⚠️ {risks}</div>'

            st.markdown(f"""
            <div class="card card-{card_c}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <span style="color:#8b949e;font-size:0.9rem">#{r['rank']}</span>
                  <span class="stock-ticker" style="margin-left:8px">{r['ric']}</span>
                  <span style="color:#8b949e;font-size:0.85rem;margin-left:8px">{str(r['sector']).capitalize()}</span>
                </div>
                <div>{signal_badge} {rsi_badge} {color_badge(f"Composite {r['composite']:.2f}", "gold")} {sent_badge}</div>
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
              {catalyst_html}
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PORTFOLIO
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 💼 My Portfolio")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PORTFOLIO  (transaction-ledger based)
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 💼 My Portfolio")
    st.markdown(
        '<div style="color:#8b949e;font-size:0.88rem;margin-bottom:16px">'
        'Full transaction ledger — buy, sell, dividends, reinvestments. '
        'Positions and P&L are derived automatically.</div>',
        unsafe_allow_html=True
    )

    scored_now = st.session_state.scored

    # ── TOP BAR: Add Transaction + Upload ─────────────────────────────────
    input_mode = st.radio("Add transactions via:", ["Manual entry", "Upload CSV"], horizontal=True)

    if input_mode == "Upload CSV":
        st.markdown("""<div class="note-box">
          <strong>CSV columns:</strong> date, type, ric, qty, price, sector, notes<br>
          <strong>type values:</strong> BUY · SELL · DIVIDEND · DIV_REINVEST<br>
          <strong>Example:</strong><br>
          <code>2024-06-01, BUY, SNTS, 10, 25000, public, Initial buy</code><br>
          <code>2025-05-20, DIVIDEND, SNTS, 0, 1839, public, Annual dividend</code><br>
          <code>2025-08-01, SELL, SNTS, 3, 28000, public, Partial trim</code>
        </div>""", unsafe_allow_html=True)
        txn_csv = st.file_uploader("Upload transactions CSV", type=["csv"], key="txn_csv")
        if txn_csv and st.button("📥 Load Transactions", key="load_txn_csv"):
            try:
                tdf = pd.read_csv(txn_csv)
                tdf.columns = [c.strip().lower() for c in tdf.columns]
                new_txns = []
                for i, row in tdf.iterrows():
                    txn_type = str(row.get('type','')).strip().upper()
                    ric_val  = str(row.get('ric','')).strip().upper()
                    qty_val  = float(row.get('qty', 0))
                    price_val= float(row.get('price', 0))
                    # cash_flow: BUY/DIV_REINVEST = negative (cash out), SELL/DIVIDEND = positive
                    if txn_type in ('BUY','DIV_REINVEST'):
                        cf = -(qty_val * price_val)
                    elif txn_type == 'SELL':
                        cf = qty_val * price_val
                    elif txn_type == 'DIVIDEND':
                        cf = price_val  # price = total dividend cash received
                    else:
                        cf = 0
                    new_txns.append({
                        'id':       i,
                        'date':     str(row.get('date','')).strip(),
                        'type':     txn_type,
                        'ric':      ric_val,
                        'qty':      qty_val,
                        'price':    price_val,
                        'cash_flow':cf,
                        'sector':   str(row.get('sector','')).strip().lower(),
                        'notes':    str(row.get('notes','')).strip(),
                    })
                st.session_state.transactions = new_txns
                st.session_state.portfolio_analysis = None
                st.session_state.port_data_v2 = None
                st.success(f"✅ Loaded {len(new_txns)} transactions")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    else:  # Manual entry
        with st.expander("➕ Add Transaction", expanded=len(st.session_state.get('transactions',[])) == 0):
            tc1, tc2, tc3, tc4, tc5 = st.columns(5)
            with tc1:
                t_type = st.selectbox("Type", ["BUY","SELL","DIVIDEND","DIV_REINVEST"], key="t_type")
            with tc2:
                t_ric  = st.text_input("Ticker (RIC)", placeholder="e.g. SNTS", key="t_ric").upper().strip()
            with tc3:
                t_qty  = st.number_input(
                    "Qty / Shares" if t_type != "DIVIDEND" else "Qty (0 for cash div)",
                    min_value=0.0, value=10.0, step=1.0, key="t_qty"
                )
            with tc4:
                t_price= st.number_input(
                    "Price per share (XOF)" if t_type != "DIVIDEND" else "Total dividend (XOF)",
                    min_value=0.0, value=25000.0, step=100.0, key="t_price"
                )
            with tc5:
                t_sector = st.selectbox("Sector", [
                    "finance","agriculture","industry",
                    "distribution","public","transportation","other"
                ], key="t_sector")

            tc6, tc7 = st.columns([3,1])
            with tc6:
                t_date  = st.date_input("Date", value=datetime.today(), key="t_date")
                t_notes = st.text_input("Notes (optional)", placeholder="e.g. Q4 dividend received", key="t_notes")
            with tc7:
                # Show computed cash flow
                if t_type in ('BUY','DIV_REINVEST'):
                    cf_display = -(t_qty * t_price)
                    cf_label   = "Cash out"
                    cf_color   = "#f85149"
                elif t_type == 'SELL':
                    cf_display = t_qty * t_price
                    cf_label   = "Cash in"
                    cf_color   = "#2ea043"
                elif t_type == 'DIVIDEND':
                    cf_display = t_price
                    cf_label   = "Cash in (div)"
                    cf_color   = "#e3b341"
                else:
                    cf_display = 0; cf_label = ""; cf_color = "#8b949e"

                st.markdown(f"""
                <div style="text-align:center;padding:8px;background:#161b22;
                     border-radius:6px;border:1px solid #21262d;margin-top:22px">
                  <div style="font-size:0.72rem;color:#8b949e">{cf_label}</div>
                  <div style="font-size:1.1rem;font-weight:800;color:{cf_color}">
                    {cf_display:+,.0f} XOF
                  </div>
                </div>""", unsafe_allow_html=True)

            if st.button("➕ Add Transaction", key="add_txn"):
                if t_ric:
                    if 'transactions' not in st.session_state:
                        st.session_state.transactions = []
                    cf = cf_display
                    st.session_state.transactions.append({
                        'id':       len(st.session_state.transactions),
                        'date':     str(t_date),
                        'type':     t_type,
                        'ric':      t_ric,
                        'qty':      t_qty,
                        'price':    t_price,
                        'cash_flow':cf,
                        'sector':   t_sector,
                        'notes':    t_notes,
                    })
                    st.session_state.portfolio_analysis = None
                    st.session_state.port_data_v2       = None
                    st.success(f"✅ Added {t_type} {t_ric}")
                    st.rerun()
                else:
                    st.warning("Enter a ticker symbol.")

    # ── TRANSACTION LEDGER ─────────────────────────────────────────────────
    txns = st.session_state.get('transactions', [])

    if txns:
        # Run / clear buttons
        rb1, rb2, rb3 = st.columns([0.3, 0.3, 0.4])
        with rb1:
            if st.button("📊 Analyse Portfolio", use_container_width=True, key="run_port_v2"):
                raw_df = st.session_state.get("raw_df")
                if raw_df is None:
                    st.warning("⚠️ Upload your market data CSV in the sidebar first.")
                else:
                    with st.spinner("Computing…"):
                        pd_ = compute_portfolio_v2(txns, raw_df, scored_now)
                    st.session_state.port_data_v2 = pd_
                    st.session_state.portfolio_analysis = None
        with rb2:
            if st.button("🗑 Clear All Transactions", use_container_width=True, key="clear_txns"):
                st.session_state.transactions      = []
                st.session_state.port_data_v2      = None
                st.session_state.portfolio_analysis= None
                st.rerun()

        # ── LEDGER TABLE ───────────────────────────────────────────────────
        with st.expander(f"📒 Transaction Ledger ({len(txns)} entries)", expanded=False):
            type_colors = {
                'BUY':'#58a6ff','SELL':'#f85149',
                'DIVIDEND':'#e3b341','DIV_REINVEST':'#2ea043'
            }
            # Header
            st.markdown("""
            <div style="display:grid;grid-template-columns:0.8fr 1.2fr 0.8fr 0.7fr 1fr 1fr 1fr 1.5fr 0.5fr;
                 gap:6px;padding:6px 10px;background:#21262d;border-radius:6px;
                 font-size:0.72rem;color:#8b949e;font-weight:700;text-transform:uppercase;margin-bottom:4px">
              <div>Date</div><div>Type</div><div>Ticker</div><div>Qty</div>
              <div>Price</div><div>Cash Flow</div><div>Sector</div><div>Notes</div><div></div>
            </div>""", unsafe_allow_html=True)

            for i, t in enumerate(sorted(txns, key=lambda x: x['date'], reverse=True)):
                tc = type_colors.get(t['type'], '#8b949e')
                cf = float(t.get('cash_flow', 0))
                cf_col = '#2ea043' if cf > 0 else '#f85149'
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:0.8fr 1.2fr 0.8fr 0.7fr 1fr 1fr 1fr 1.5fr 0.5fr;
                     gap:6px;padding:7px 10px;background:#161b22;border-radius:6px;
                     border:1px solid #21262d;margin-bottom:3px;font-size:0.83rem;align-items:center">
                  <div style="color:#8b949e">{t['date']}</div>
                  <div><span style="color:{tc};font-weight:700">{t['type']}</span></div>
                  <div style="font-weight:700;color:#e6edf3">{t['ric']}</div>
                  <div>{float(t['qty']):,.0f}</div>
                  <div>{float(t['price']):,.0f}</div>
                  <div style="color:{cf_col};font-weight:700">{cf:+,.0f}</div>
                  <div style="color:#8b949e">{t.get('sector','').capitalize()}</div>
                  <div style="color:#8b949e;font-size:0.78rem">{t.get('notes','')}</div>
                </div>""", unsafe_allow_html=True)
                # Delete button per row
                if st.button("✕", key=f"del_txn_{i}_{t['id']}"):
                    orig_idx = next(
                        (j for j,tx in enumerate(st.session_state.transactions)
                         if tx['id']==t['id']), None
                    )
                    if orig_idx is not None:
                        st.session_state.transactions.pop(orig_idx)
                        st.session_state.port_data_v2 = None
                        st.rerun()

        # ── PORTFOLIO RESULTS ──────────────────────────────────────────────
        pd2 = st.session_state.get("port_data_v2")
        if pd2:
            st.markdown("---")

            # Summary metrics row
            st.markdown('<div class="section-title">📈 Portfolio Summary</div>', unsafe_allow_html=True)
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            tpl  = pd2['total_pl_pct']
            trp  = pd2['total_return_pct']
            bench= 0.0691  # BRVM YTD

            with m1: st.markdown(metric_card("COST BASIS",    f"{pd2['total_cost_basis']/1e6:.2f}M XOF","blue"), unsafe_allow_html=True)
            with m2: st.markdown(metric_card("MARKET VALUE",  f"{pd2['total_current_val']/1e6:.2f}M XOF","blue"), unsafe_allow_html=True)
            with m3: st.markdown(metric_card("UNREALISED P&L",f"{tpl:+.1%}","green" if tpl>=0 else "red", f"{pd2['total_pl']:+,.0f} XOF"), unsafe_allow_html=True)
            with m4: st.markdown(metric_card("REALISED P&L",  f"{pd2['total_realised']:+,.0f}","green" if pd2['total_realised']>=0 else "red","from closed positions"), unsafe_allow_html=True)
            with m5: st.markdown(metric_card("DIVIDENDS",     f"{pd2['total_divs']/1e3:.1f}K XOF","gold","received"), unsafe_allow_html=True)
            with m6:
                alpha = trp - bench
                st.markdown(metric_card(
                    "TOTAL RETURN",
                    f"{trp:+.1%}",
                    "green" if trp >= bench else "red",
                    f"α {alpha:+.1%} vs BRVM"
                ), unsafe_allow_html=True)

            st.markdown("---")

            # ── CHART: Portfolio vs BRVM ───────────────────────────────────
            st.markdown('<div class="section-title">📊 Portfolio vs BRVM Composite</div>', unsafe_allow_html=True)
            port_s = pd2['port_series']
            brvm_s = pd2['brvm_aligned']

            if len(port_s) > 1:
                BG_C="#0d1117"; CARD_C="#161b22"; GRN_C="#2ea043"
                BLU_C="#58a6ff"; GRY_C="#8b949e"; WHT_C="#e6edf3"

                fig, ax = plt.subplots(figsize=(14,4.5), facecolor=BG_C)
                ax.set_facecolor(CARD_C)

                ax.plot(port_s.index, port_s.values, color=GRN_C, lw=2.2,
                        label="My Portfolio", zorder=3)

                brvm_reindexed = (brvm_s.reindex(port_s.index).ffill()
                                  if len(brvm_s)>1 else pd.Series(index=port_s.index, dtype=float))

                if len(brvm_reindexed.dropna()) > 1:
                    ax.plot(brvm_reindexed.index, brvm_reindexed.values,
                            color=BLU_C, lw=1.5, ls='--', alpha=0.8,
                            label="BRVM Composite (rebased)")
                    ax.fill_between(port_s.index, port_s.values, brvm_reindexed.values,
                                    where=(port_s.values >= brvm_reindexed.values),
                                    alpha=0.12, color=GRN_C, label="Outperformance")
                    ax.fill_between(port_s.index, port_s.values, brvm_reindexed.values,
                                    where=(port_s.values < brvm_reindexed.values),
                                    alpha=0.12, color="#f85149", label="Underperformance")

                # Mark sell events on chart
                sell_txns = [t for t in txns if t['type']=='SELL']
                for st_ in sell_txns:
                    sd = pd.to_datetime(st_['date'])
                    if sd in port_s.index:
                        ax.axvline(sd, color="#f85149", lw=1, ls=':', alpha=0.6)

                # Mark dividend events
                div_txns = [t for t in txns if t['type'] in ('DIVIDEND','DIV_REINVEST')]
                for dt_ in div_txns:
                    dd = pd.to_datetime(dt_['date'])
                    if dd in port_s.index:
                        ax.axvline(dd, color="#e3b341", lw=1, ls=':', alpha=0.5)

                ax.legend(fontsize=9, framealpha=0.2, labelcolor=WHT_C, loc='upper left')
                ax.set_title("Portfolio Value vs BRVM Composite  |  🔴 dotted = sell  |  🟡 dotted = dividend",
                             fontsize=11, color=WHT_C, pad=8)
                ax.grid(alpha=0.12); ax.tick_params(colors=GRY_C)
                ax.yaxis.set_major_formatter(
                    mticker.FuncFormatter(lambda x,_: f"{x/1e6:.2f}M" if x>=1e6 else f"{x:,.0f}")
                )
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=BG_C)
                buf.seek(0)
                st.image(buf, use_container_width=True)
                plt.close()
            else:
                st.info("Not enough price history to render chart.")

            st.markdown("---")

            # ── OPEN POSITIONS ─────────────────────────────────────────────
            st.markdown('<div class="section-title">📋 Open Positions</div>', unsafe_allow_html=True)
            pos_df = pd2['positions'].sort_values('unrealised_pct', ascending=False)

            for _, r in pos_df.iterrows():
                cc = ("green" if r['rec_color']=="green"
                      else "red" if r['rec_color']=="red"
                      else "orange" if r['rec_color']=="orange"
                      else "blue")
                pl_c  = '#2ea043' if r['unrealised_pl'] >= 0 else '#f85149'
                ai_b  = color_badge(r['ai_signal'],
                                    "green" if "BUY" in r['ai_signal']
                                    else "red" if "PEAK" in r['ai_signal'] else "blue")
                rec_b = color_badge(r['recommendation'],
                                    r['rec_color'] if r['rec_color']!="orange" else "gold")

                div_info = ""
                if r['div_received'] > 0:
                    div_info += f'<span style="color:#e3b341;margin-right:12px">÷ {r["div_received"]:,.0f} XOF received</span>'
                if r['div_reinvested'] > 0:
                    div_info += f'<span style="color:#2ea043;margin-right:12px">↺ {r["div_reinvested"]:,.0f} XOF reinvested</span>'
                if r['upcoming_div']:
                    ud = r['upcoming_div']
                    div_info += (f'<span style="color:#58a6ff">📅 Next div: '
                                 f'{ud["amount"]:,.0f} XOF on {ud["date"].strftime("%d %b %Y")}</span>')

                st.markdown(f"""
                <div class="card card-{cc}">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                      <span class="stock-ticker">{r['ric']}</span>
                      <span style="color:#8b949e;font-size:0.85rem;margin-left:8px">{str(r['sector']).capitalize()}</span>
                    </div>
                    <div>{ai_b} {rec_b}</div>
                  </div>
                  <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:10px;font-size:0.84rem">
                    <div><div class="metric-lbl">Qty held</div><b>{r['qty']:,.0f}</b></div>
                    <div><div class="metric-lbl">Avg cost</div><b>{r['avg_cost']:,.0f}</b></div>
                    <div><div class="metric-lbl">Current price</div><b>{r['current_price']:,.0f}</b></div>
                    <div><div class="metric-lbl">Unrealised P&L</div>
                      <b style="color:{pl_c}">{r['unrealised_pct']:+.1%}</b>
                      <span style="font-size:0.77rem;color:#8b949e"> ({r['unrealised_pl']:+,.0f})</span>
                    </div>
                    <div><div class="metric-lbl">Realised P&L</div>
                      <b style="color:{'#2ea043' if r['realised_pl']>=0 else '#f85149'}">{r['realised_pl']:+,.0f}</b>
                    </div>
                    <div><div class="metric-lbl">Total return</div>
                      <b style="color:{'#2ea043' if r['total_return_pct']>=0 else '#f85149'}">{r['total_return_pct']:+.1%}</b>
                    </div>
                    <div><div class="metric-lbl">Market value</div><b>{r['current_val']:,.0f}</b></div>
                  </div>
                  <div style="margin-top:8px;font-size:0.82rem">{div_info}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")

            # ── SECTOR + BEST/WORST ────────────────────────────────────────
            sec_col, bw_col = st.columns(2)

            with sec_col:
                st.markdown('<div class="section-title">🥧 Sector Allocation</div>', unsafe_allow_html=True)
                sec_colors_map = {
                    "finance":"#58a6ff","agriculture":"#2ea043","industry":"#e3b341",
                    "distribution":"#ff7b2b","public":"#a371f7","transportation":"#f85149","other":"#8b949e"
                }
                for sector, pct in pd2['sec_alloc_pct'].sort_values(ascending=False).items():
                    clr = sec_colors_map.get(sector.lower(),"#8b949e")
                    st.markdown(f"""
                    <div style="margin:5px 0">
                      <div style="display:flex;justify-content:space-between;margin-bottom:2px">
                        <span style="font-size:0.88rem;color:#e6edf3">{sector.capitalize()}</span>
                        <span style="font-size:0.88rem;font-weight:700;color:{clr}">{pct:.1f}%</span>
                      </div>
                      <div style="background:#21262d;border-radius:4px;height:8px">
                        <div style="background:{clr};width:{min(pct,100):.0f}%;height:8px;border-radius:4px"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                # Risk flags
                max_sec     = pd2['sec_alloc_pct'].idxmax() if len(pd2['sec_alloc_pct'])>0 else ""
                max_sec_pct = pd2['sec_alloc_pct'].max() if len(pd2['sec_alloc_pct'])>0 else 0
                agri_pct    = pd2['sec_alloc_pct'].get('agriculture',0)
                n_pos       = len(pos_df)
                flags       = []
                if max_sec_pct > 50:
                    flags.append(f'⚠️ {max_sec_pct:.0f}% in {max_sec} — concentrated')
                if agri_pct > 20:
                    flags.append(f'⚠️ {agri_pct:.0f}% in agriculture — cocoa/rubber risk')
                if n_pos < 4:
                    flags.append(f'⚠️ Only {n_pos} positions — consider diversifying')
                if flags:
                    st.markdown(f"""<div class="card card-orange" style="margin-top:10px">
                      {'<br>'.join(flags)}</div>""", unsafe_allow_html=True)

            with bw_col:
                st.markdown('<div class="section-title">🏆 Best &amp; Worst Performers</div>', unsafe_allow_html=True)
                best  = pos_df.nlargest(3,'total_return_pct')
                worst = pos_df.nsmallest(3,'total_return_pct')
                for _, r in best.iterrows():
                    st.markdown(f"""<div class="card card-green" style="padding:10px 14px;margin-bottom:6px">
                      <span style="font-weight:800">{r['ric']}</span>
                      <span style="float:right;color:#2ea043;font-weight:800">{r['total_return_pct']:+.1%}</span>
                      <div style="font-size:0.8rem;color:#8b949e">{r['avg_cost']:,.0f} → {r['current_price']:,.0f}
                      {f" + {r['div_received']:,.0f} div" if r['div_received']>0 else ""}</div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
                for _, r in worst.iterrows():
                    st.markdown(f"""<div class="card card-red" style="padding:10px 14px;margin-bottom:6px">
                      <span style="font-weight:800">{r['ric']}</span>
                      <span style="float:right;color:#f85149;font-weight:800">{r['total_return_pct']:+.1%}</span>
                      <div style="font-size:0.8rem;color:#8b949e">{r['avg_cost']:,.0f} → {r['current_price']:,.0f}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("---")

            # ── UPCOMING DIVIDENDS ─────────────────────────────────────────
            if pd2['upcoming_divs']:
                st.markdown('<div class="section-title">📅 Upcoming Dividends</div>', unsafe_allow_html=True)
                ud_cols = st.columns(min(len(pd2['upcoming_divs']),4))
                for col, div in zip(ud_cols, pd2['upcoming_divs']):
                    with col:
                        st.markdown(f"""
                        <div class="card card-gold" style="text-align:center;padding:14px">
                          <div style="font-weight:800;font-size:1.1rem;color:#58a6ff">{div['ric']}</div>
                          <div style="font-size:1.3rem;font-weight:800;color:#e3b341">{div['amount']:,.0f} XOF</div>
                          <div style="font-size:0.78rem;color:#8b949e">{div['per_share']:,.0f}/share</div>
                          <div style="font-size:0.8rem;color:#8b949e">{div['date'].strftime('%d %b %Y')}</div>
                        </div>""", unsafe_allow_html=True)
                st.markdown("---")

            # ── AI ASSESSMENT ──────────────────────────────────────────────
            st.markdown('<div class="section-title">🤖 AI Portfolio Assessment</div>', unsafe_allow_html=True)
            if st.session_state.portfolio_analysis:
                st.markdown(f"""
                <div class="card card-gold">
                  <div style="font-size:0.8rem;color:#8b949e;margin-bottom:8px">🤖 AI Analysis</div>
                  <div style="font-size:0.93rem;line-height:1.75;color:#e6edf3;white-space:pre-wrap">{st.session_state.portfolio_analysis}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("🔄 Refresh", key="refresh_ai_v2"):
                    with st.spinner("Analysing…"):
                        st.session_state.portfolio_analysis = generate_portfolio_ai_analysis(pd2)
                    st.rerun()
            else:
                if st.button("🤖 Generate AI Assessment", key="gen_ai_v2"):
                    with st.spinner("Analysing your portfolio…"):
                        st.session_state.portfolio_analysis = generate_portfolio_ai_analysis(pd2)
                    st.rerun()

    else:
        st.markdown("""
        <div class="card card-blue" style="text-align:center;padding:40px">
          <div style="font-size:2rem">💼</div>
          <div style="font-size:1.1rem;font-weight:700;margin:12px 0">No transactions yet</div>
          <div style="color:#8b949e">Add transactions manually above or upload a CSV.<br>
          Every buy, sell, dividend and reinvestment is recorded here.</div>
        </div>""", unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
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
# TAB 5 — NOTES & RESULTS
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
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
# TAB 6 — WEEKLY BRIEFING
# ─────────────────────────────────────────────────────────────────────────────
with tab6:
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

# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 — DEEP RESEARCH & REBALANCE
# ─────────────────────────────────────────────────────────────────────────────
with tab7:
    st.markdown("### 🔍 Deep Research & Portfolio Rebalance")
    st.markdown(
        '<div style="color:#8b949e;font-size:0.88rem;margin-bottom:16px">'
        'AI-powered live research from BRVM.org, Sikafinance, Richbourse, AMF-UEMOA. '
        'Sentiment, catalysts, income profile — then a full rebalance recommendation.</div>',
        unsafe_allow_html=True
    )

    scored_r = st.session_state.scored
    api_key_r = st.session_state.get("api_key","") or os.environ.get("ANTHROPIC_API_KEY","")

    if scored_r is None:
        st.info("📂 Upload and analyse your BRVM CSV first (sidebar), then run deep research here.")
    elif not api_key_r:
        st.warning("🔑 Please enter your Anthropic API key in the sidebar to enable live research.")
    else:
        # ── RESEARCH CONTROLS ─────────────────────────────────────────────
        st.markdown('<div class="section-title">📡 Live Market Intelligence</div>', unsafe_allow_html=True)

        r_col1, r_col2, r_col3 = st.columns([0.4, 0.3, 0.3])

        with r_col1:
            research_scope = st.selectbox(
                "Research scope",
                ["Top 10 ranked stocks", "My portfolio holdings only",
                 "Top 10 + portfolio holdings", "Custom selection"],
                key="research_scope"
            )

        with r_col2:
            if research_scope == "Custom selection" and scored_r is not None:
                custom_tickers = st.multiselect(
                    "Select tickers",
                    options=sorted(scored_r['ric'].tolist()),
                    default=scored_r.head(5)['ric'].tolist(),
                    key="custom_tickers"
                )
            else:
                custom_tickers = []

        with r_col3:
            if st.session_state.intel_last_run:
                st.markdown(
                    f'<div style="font-size:0.8rem;color:#8b949e;padding-top:28px">'
                    f'Last run: {st.session_state.intel_last_run}</div>',
                    unsafe_allow_html=True
                )

        # Determine tickers to research
        def get_research_tickers():
            port_tickers = []
            if st.session_state.get("port_data_v2"):
                port_tickers = st.session_state.port_data_v2['positions']['ric'].str.upper().tolist()
            elif st.session_state.get("transactions"):
                from collections import Counter
                port_tickers = list({t['ric'].upper() for t in st.session_state.transactions
                                     if t['type'] in ('BUY','DIV_REINVEST')})

            if research_scope == "Top 10 ranked stocks":
                return scored_r.head(10)['ric'].tolist()
            elif research_scope == "My portfolio holdings only":
                return port_tickers if port_tickers else scored_r.head(5)['ric'].tolist()
            elif research_scope == "Top 10 + portfolio holdings":
                combined = scored_r.head(10)['ric'].tolist()
                for t in port_tickers:
                    if t not in combined:
                        combined.append(t)
                return combined[:15]
            else:
                return custom_tickers

        run_intel_col, clear_intel_col = st.columns([0.5, 0.5])
        with run_intel_col:
            run_research = st.button(
                "🔎 Run Live Research",
                use_container_width=True,
                help="Fetches real-time data from BRVM, Sikafinance, Richbourse, AMF-UEMOA using AI web search"
            )
        with clear_intel_col:
            if st.button("🗑 Clear Research Cache", use_container_width=True, key="clear_intel"):
                st.session_state.market_intel = {}
                st.session_state.deep_dive_cache = {}
                st.session_state.rebalance_report = None
                st.session_state.intel_last_run = None
                st.rerun()

        if run_research:
            tickers_to_research = get_research_tickers()
            if not tickers_to_research:
                st.warning("No tickers selected.")
            else:
                progress_bar = st.progress(0)
                status_text  = st.empty()

                def update_progress(i, total, ric):
                    progress_bar.progress((i + 1) / total)
                    status_text.markdown(
                        f'<div style="color:#8b949e;font-size:0.85rem">🔍 Researching {ric} ({i+1}/{total})…</div>',
                        unsafe_allow_html=True
                    )

                with st.spinner(f"Running live research on {len(tickers_to_research)} tickers…"):
                    intel = fetch_market_intelligence(
                        tickers_to_research, api_key_r, update_progress
                    )
                    st.session_state.market_intel = intel
                    st.session_state.intel_last_run = datetime.now().strftime("%d %b %Y %H:%M")
                    # Re-score with sentiment
                    updated_scored = recalculate_with_intel(scored_r, intel)
                    st.session_state.scored = updated_scored
                    st.session_state.rebalance_report = None
                    st.session_state.deep_dive_cache = {}

                progress_bar.empty()
                status_text.empty()
                st.success(f"✅ Research complete for {len(intel)} tickers. Rankings updated with sentiment scores.")
                st.rerun()

        # ── INTELLIGENCE DASHBOARD ────────────────────────────────────────
        market_intel = st.session_state.market_intel
        if market_intel:
            st.markdown("---")
            st.markdown('<div class="section-title">📊 Market Intelligence Summary</div>', unsafe_allow_html=True)

            # Summary cards grid
            sentiment_map = {"bullish": ("green","🟢"), "bearish": ("red","🔴"), "neutral": ("blue","⚪")}
            volume_map    = {"increasing": "⬆️", "decreasing": "⬇️", "stable": "➡️", "unknown": "❓"}

            intel_items = list(market_intel.items())
            cols_per_row = 3
            for row_start in range(0, len(intel_items), cols_per_row):
                row_items = intel_items[row_start:row_start+cols_per_row]
                cols = st.columns(len(row_items))
                for col, (ric, intel) in zip(cols, row_items):
                    s_color, s_icon = sentiment_map.get(intel.get("sentiment","neutral"), ("blue","⚪"))
                    v_icon = volume_map.get(intel.get("volume_trend","unknown"), "❓")
                    cats_pos = intel.get("catalyst_positive",[]) or []
                    cats_neg = intel.get("catalyst_negative",[]) or []

                    scored_row = scored_r[scored_r['ric']==ric]
                    comp_str = f"{scored_row.iloc[0]['composite']:.2f}" if not scored_row.empty else "N/A"

                    with col:
                        st.markdown(f"""
                        <div class="card card-{s_color}" style="min-height:180px">
                          <div style="display:flex;justify-content:space-between;align-items:center">
                            <span class="stock-ticker" style="font-size:1.1rem">{ric}</span>
                            <span style="font-size:0.75rem;color:#8b949e">Score {comp_str}</span>
                          </div>
                          <div style="margin:6px 0">
                            {color_badge(f"{s_icon} {intel.get('sentiment','N/A').upper()}", s_color)}
                            <span style="font-size:0.8rem;color:#8b949e;margin-left:6px">{v_icon} Vol: {intel.get('volume_trend','N/A')}</span>
                          </div>
                          <div style="font-size:0.8rem;color:#8b949e;margin:4px 0">{intel.get('volume_comment','')[:80]}…</div>
                          {'<div style="font-size:0.78rem;color:#2ea043;margin-top:4px">✅ ' + ' · '.join(cats_pos[:2]) + '</div>' if cats_pos else ''}
                          {'<div style="font-size:0.78rem;color:#f85149;margin-top:2px">⚠️ ' + ' · '.join(cats_neg[:2]) + '</div>' if cats_neg else ''}
                          <div style="font-size:0.78rem;color:#8b949e;margin-top:6px;border-top:1px solid #21262d;padding-top:4px">{intel.get('analyst_note','')[:120]}…</div>
                        </div>
                        """, unsafe_allow_html=True)

            # ── FULL INTELLIGENCE TABLE ───────────────────────────────────
            with st.expander("📋 Full Intelligence Table", expanded=False):
                rows_intel = []
                for ric, intel in market_intel.items():
                    srow = scored_r[scored_r['ric']==ric]
                    rows_intel.append({
                        "Ticker": ric,
                        "Sentiment": intel.get("sentiment","N/A").capitalize(),
                        "Sent. Score": f"{intel.get('sentiment_score',0.5):.2f}",
                        "Volume": intel.get("volume_trend","N/A").capitalize(),
                        "Pos. Catalysts": " · ".join((intel.get("catalyst_positive",[]) or [])[:2]),
                        "Neg. Risks": " · ".join((intel.get("catalyst_negative",[]) or [])[:2]),
                        "Div. Outlook": intel.get("dividend_comment","N/A")[:60],
                        "Composite": f"{srow.iloc[0]['composite']:.2f}" if not srow.empty else "N/A",
                        "Sources": ", ".join(intel.get("data_sources",[]) or [])[:40],
                    })
                if rows_intel:
                    st.dataframe(pd.DataFrame(rows_intel), use_container_width=True, hide_index=True)

            st.markdown("---")

            # ── PER-TICKER DEEP DIVE ──────────────────────────────────────
            st.markdown('<div class="section-title">🔬 Per-Ticker Deep Dive Research</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="color:#8b949e;font-size:0.85rem;margin-bottom:12px">'
                'Generate a full equity research note for any researched ticker.</div>',
                unsafe_allow_html=True
            )

            dd_ric = st.selectbox(
                "Select ticker for deep dive",
                options=list(market_intel.keys()),
                key="dd_ric_select"
            )

            if dd_ric:
                portfolio_position = None
                if st.session_state.get("port_data_v2"):
                    pos_df = st.session_state.port_data_v2['positions']
                    match = pos_df[pos_df['ric'].str.upper() == dd_ric.upper()]
                    if not match.empty:
                        portfolio_position = match.iloc[0].to_dict()

                scored_match = scored_r[scored_r['ric'] == dd_ric]
                scored_dict  = scored_match.iloc[0].to_dict() if not scored_match.empty else {}

                dd_col1, dd_col2 = st.columns([0.5, 0.5])
                with dd_col1:
                    gen_dd = st.button(f"📝 Generate Deep Dive: {dd_ric}", use_container_width=True, key="gen_dd")
                with dd_col2:
                    if dd_ric in st.session_state.deep_dive_cache:
                        st.markdown(
                            f'<div style="font-size:0.8rem;color:#2ea043;padding-top:10px">✅ Report cached — regenerate to refresh</div>',
                            unsafe_allow_html=True
                        )

                if gen_dd:
                    with st.spinner(f"Writing equity research note for {dd_ric}…"):
                        note = generate_deep_dive(
                            dd_ric, scored_dict,
                            market_intel.get(dd_ric, _default_intel(dd_ric)),
                            portfolio_position, api_key_r
                        )
                        st.session_state.deep_dive_cache[dd_ric] = note
                    st.rerun()

                if dd_ric in st.session_state.deep_dive_cache:
                    report_text = st.session_state.deep_dive_cache[dd_ric]
                    st.markdown(f"""
                    <div class="card card-blue">
                      <div style="font-size:0.8rem;color:#8b949e;margin-bottom:10px">
                        📊 Equity Research Note — {dd_ric} | Generated {datetime.now().strftime('%d %b %Y')}
                      </div>
                      <div style="font-size:0.92rem;line-height:1.75;color:#e6edf3;white-space:pre-wrap">{report_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.download_button(
                        f"⬇ Download {dd_ric} Research Note (.txt)",
                        data=report_text,
                        file_name=f"BRVM_{dd_ric}_research_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        key=f"dl_dd_{dd_ric}"
                    )

            st.markdown("---")

            # ── PORTFOLIO REBALANCE REPORT ────────────────────────────────
            st.markdown('<div class="section-title">⚖️ Portfolio Rebalance Report</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="color:#8b949e;font-size:0.85rem;margin-bottom:12px">'
                'Integrates your holdings, live sentiment, catalysts, and model rankings into a single rebalance plan.</div>',
                unsafe_allow_html=True
            )

            rb_col1, rb_col2 = st.columns([0.5, 0.5])
            with rb_col1:
                gen_rebalance = st.button("⚖️ Generate Rebalance Report", use_container_width=True, key="gen_rebalance")
            with rb_col2:
                if st.session_state.rebalance_report:
                    st.markdown('<div style="font-size:0.8rem;color:#2ea043;padding-top:10px">✅ Report ready — regenerate to refresh</div>', unsafe_allow_html=True)

            if gen_rebalance:
                port_data = st.session_state.get("port_data_v2")
                if port_data is None and st.session_state.get("transactions"):
                    raw_df = st.session_state.get("raw_df")
                    if raw_df is not None:
                        with st.spinner("Computing portfolio…"):
                            port_data = compute_portfolio_v2(
                                st.session_state.transactions, raw_df,
                                st.session_state.scored
                            )
                        st.session_state.port_data_v2 = port_data

                with st.spinner("Generating rebalance report…"):
                    report = generate_rebalance_report(
                        st.session_state.scored or scored_r,
                        port_data, market_intel, api_key_r
                    )
                    st.session_state.rebalance_report = report
                st.rerun()

            if st.session_state.rebalance_report:
                st.markdown(f"""
                <div class="card card-gold">
                  <div style="font-size:0.8rem;color:#8b949e;margin-bottom:10px">
                    ⚖️ Portfolio Rebalance Report | Generated {datetime.now().strftime('%d %b %Y, %H:%M')}
                  </div>
                  <div style="font-size:0.93rem;line-height:1.75;color:#e6edf3;white-space:pre-wrap">{st.session_state.rebalance_report}</div>
                </div>
                """, unsafe_allow_html=True)
                st.download_button(
                    "⬇ Download Rebalance Report (.txt)",
                    data=st.session_state.rebalance_report,
                    file_name=f"BRVM_rebalance_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    key="dl_rebalance"
                )

        else:
            # No intel yet — show dividend income profile as static fallback
            st.markdown("---")
            st.markdown('<div class="section-title">📅 3-Year Dividend Income Profile (Offline Data)</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="color:#8b949e;font-size:0.85rem;margin-bottom:12px">'
                'Run live research above to enrich with real-time data. '
                'Showing static 3-year dividend profile in the meantime.</div>',
                unsafe_allow_html=True
            )

            div_rows = []
            for ric, d in DIVIDEND_HISTORY_3Y.items():
                div_rows.append({
                    "Ticker": ric,
                    "2022 (XOF)": d.get("2022","—"),
                    "2023 (XOF)": d.get("2023","—"),
                    "2024 (XOF)": d.get("2024","—"),
                    "3Y Growth": d.get("growth","N/A"),
                    "Avg Yield": d.get("yield_3y_avg","N/A"),
                    "Consistent?": "✅ Yes" if d.get("payout_consistent") else "⚠️ Irregular",
                })
            st.dataframe(pd.DataFrame(div_rows), use_container_width=True, hide_index=True)

            st.markdown("""
            <div class="card card-blue" style="text-align:center;padding:30px;margin-top:20px">
              <div style="font-size:1.5rem">🔎</div>
              <div style="font-size:1rem;font-weight:700;margin:10px 0">Run Live Research to unlock full intelligence</div>
              <div style="color:#8b949e;font-size:0.88rem">
                Click <strong>Run Live Research</strong> above to fetch real-time sentiment, catalysts,
                analyst notes, and volume trends from BRVM.org, Sikafinance, Richbourse, and AMF-UEMOA.<br><br>
                Research updates the composite scores with live sentiment (+15% weight) and enables
                per-ticker deep dives and portfolio rebalance reports.
              </div>
            </div>
            """, unsafe_allow_html=True)
