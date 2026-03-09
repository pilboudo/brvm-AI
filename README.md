# BRVM AI Investment Tool

An AI-powered weekly investment analysis tool for the BRVM stock exchange.
Built with Streamlit + Claude (Anthropic API).

---

## Features

- **Upload your weekly CSV** → get instant AI-scored rankings
- **Composite score** = AI momentum (45%) + entry timing / peak avoidance (35%) + macro sector (20%)
- **Peak avoidance** — flags stocks at 52W highs or overbought RSI so you don't buy at tops
- **Macro context** — BCEAO rate environment, WAEMU GDP, commodity prices baked in
- **AI Assistant** — ask questions about any stock, get explanations, give trading instructions
- **Notes & Results** — log your trades; the AI remembers and factors them in
- **Weekly Briefing** — one-click AI-written market summary with top buys/sells

---

## Deploying to Streamlit Cloud (Free)

### Step 1 — Create a GitHub repo

1. Go to [github.com](https://github.com) and create a **new repository** (e.g. `brvm-tool`)
2. Upload these two files to the repo:
   - `app.py`
   - `requirements.txt`

### Step 2 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository (`brvm-tool`), branch (`main`), and file (`app.py`)
5. Click **Deploy** — it will be live in ~2 minutes at a URL like:
   `https://your-app-name.streamlit.app`

### Step 3 — Add your Anthropic API key (secure)

**Option A — via Streamlit Secrets (recommended):**
1. In Streamlit Cloud dashboard → your app → **Settings → Secrets**
2. Add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
3. The app will automatically pick this up — you won't need to enter it in the UI

**Option B — enter in the sidebar:**
- Just paste your key into the "API Key" field in the sidebar each session

Get your API key at: [console.anthropic.com](https://console.anthropic.com)

---

## Using the Tool Each Week

### Updating with new data
1. Export your latest BRVM data as a CSV (same format as your historical file)
2. Open the tool → sidebar → **Upload CSV** → click **Run Analysis**
3. The tool re-runs the full model on all available history + new data

### CSV Format Expected
```
symbol,date,open,high,low,close,volume,ric,avg,trade_value,sector
SNTS.sn,2026-02-01,26500,27000,26400,26950,1200,SNTS,26700,32040000,public
...
```
The file can be your full historical file (recommended) or just recent data appended to history.

### Logging trades & notes
- Go to **Notes & Results** tab
- Log every trade with ticker, date, price
- Add instructions like "ignore agriculture until cocoa recovers"
- The AI assistant reads all your notes in real time

### Getting a briefing
- Go to **Weekly Briefing** tab → click **Generate Weekly Briefing**
- Download it as a .txt file to keep records

---

## Score Methodology

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| AI Momentum Score | 45% | GradientBoosting model trained on 2017–2023 data predicting >10% gain in 12 months |
| Entry / Valuation Score | 35% | Distance from 52W high, ATH, RSI headroom, recent drawdown |
| Macro Sector Score | 20% | Sector-level macro adjustment (BCEAO rates, commodity prices) |

**Entry signals:**
- 🚀 **STRONG BUY** — Composite >0.60 AND >15% below 52W high
- ✅ **BUY ON DIPS** — Composite >0.52 AND >8% below 52W high
- 👀 **WATCH** — Good composite but entry not yet optimal
- ⚠️ **NEAR/AT PEAK** — Within 5% of 52W high (avoid buying)

---

## Updating Macro Data

To update macro figures (e.g. new BCEAO rate decision), edit the `MACRO` dictionary
at the top of `app.py`:

```python
MACRO = {
    "BCEAO_rate": 3.00,          # Update after each BCEAO meeting
    "WAEMU_GDP_2025": 6.7,
    "WAEMU_inflation": -0.8,
    "BRVM_CI_YTD": 6.91,         # Update weekly
    "cocoa_drop_yoy": -43.9,     # Update monthly
    ...
}
```

To update dividend data, edit the `DIVIDENDS` dictionary similarly.

---

## Local Development (optional)

```bash
pip install streamlit pandas numpy scikit-learn anthropic
streamlit run app.py
```

---

## Notes

- The model is retrained from scratch on each new CSV upload (uses data up to 2024 for training, scores current snapshot)
- Liquidity filter: only stocks with average daily trade value > 100,000 XOF are shown
- All analysis is for informational purposes only — not financial advice
