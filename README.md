# VARLYTIX — Portfolio Risk Intelligence & Quantitative Simulator
> **"Understand your exposure. Measure uncertainty. Explore possible outcomes."**
> 
> *Day 22 of 90 Days – 90 Projects*

---

## 1. Project Overview

**VARLYTIX** is a professional quantitative portfolio risk analysis, stress testing, and stochastic simulation platform focused on Indian listed equities and ETFs (NSE/BSE).

Traditional portfolio trackers evaluate investments strictly through the narrow lens of profit and loss (P&L). However, past return alone fails to illuminate underlying systemic fragility, concentration hazards, or market tail risks. 

VARLYTIX provides institutional-grade risk metrics, Euler volatility decomposition, multi-regime stress testing, and Monte Carlo scenario modeling in an editorial research workstation.

### Key Questions Answered by VARLYTIX:
- **How volatile is my portfolio?** (Annualized $\sigma$, daily dispersion, and 21-day moving volatility).
- **Which asset contributes the most to overall portfolio risk?** (Euler component volatility contribution vs invested capital weight).
- **Are my holdings moving in lockstep?** (Pearson correlation heatmaps across daily, weekly, and monthly frequencies).
- **How much could I lose during an acute market shock?** (Uniform, sector-specific, and tailored stress testing).
- **What does severe historical downside look like?** (Maximum drawdown, average underwater duration, and Calmar ratios).
- **What is my tail risk?** (Historical 95% & 99% Value at Risk and Conditional VaR / Expected Shortfall).
- **How uncertain are future portfolio outcomes?** (1,000 to 10,000 path Monte Carlo fan charts and terminal probability distributions).
- **What happens if I change my capital allocation?** (Markowitz Modern Portfolio Theory, Minimum Variance, Maximum Sharpe, and Efficient Frontier tracing).

---

## 2. Visual Identity & Modern Stock Market Theme (Midnight Pro)

VARLYTIX is styled in an authentic, high-end Stock Market App terminal design:

- **Application Canvas (`#0B0F19`):** Deep Midnight Slate canvas for focus and low eye fatigue.
- **Elevated Surfaces (`#121826`):** Sleek dark card surfaces and responsive analytical tables.
- **Primary Typography (`#F8FAFC`):** Crisp white typography with tabular numerals for figures.
- **Secondary Text (`#94A3B8`):** Cool slate for labels, subvalues, and units.
- **Primary Accent (`#2563EB`):** Electric Cobalt / Royal Blue for primary actions and brand presence.
- **Secondary Accent (`#38BDF8`):** Tech Sky Cyan for analytical curves and active highlights.
- **Muted Highlight (`#F59E0B`):** Market Amber / Gold for uncertainty envelopes and alerts.
- **Dividers & Borders (`#1E293B`):** Crisp dark slate dividers and container borders.
- **Stock Market Bull Green (`#00D26A`):** Vivid profit and positive return indicators.
- **Stock Market Bear Crimson (`#F43F5E`):** Vivid loss and historical drawdown indicators.

---

## 3. Workstation Navigation & Architecture

VARLYTIX provides a clean **horizontal workstation navigation bar** with exactly 10 dedicated analytical modules:

1. **Overview:** 
   - **4 Core Investor Questions:** Direct clarity on Portfolio Value, Total Return, Annualized Volatility, and Maximum Drawdown.
   - **8 Quantitative KPI Cards:** Value, Return, Volatility, Max Drawdown, Sharpe Ratio, Benchmark Beta, Value at Risk, and Holdings Structure.
   - **Performance & Asset Allocation:** Normalized trajectory vs NIFTY 50 benchmark, allocation treemap, and underwater drawdown curve.
   - **Contextual Methodology:** Accessible inline explanations of formulas and models without interrupting the analytical flow.
2. **Portfolio:** 
   - Position management with weighted-average cost transaction accounting.
   - **One-Click Indian Broker Statement Import:** Auto-detects and parses statements from **Zerodha (Kite)**, **Groww**, **Angel One**, and **Upstox**.
3. **Risk Lab:** 10 core quantitative metrics and Euler component volatility decomposition with strict mathematical identity verification ($\sum \text{RC}_i = \sigma_p$).
4. **Correlation:** Multi-frequency Pearson correlation heatmaps, co-movement rankings, and moving pairwise rolling correlation across asset pairs.
5. **Simulation:** 
   - Stochastic Monte Carlo simulation (Historical Bootstrap and Multivariate Parametric modes).
   - **Monthly SIP Inflow Simulator:** Compounds recurring monthly SIP contributions into simulated paths.
   - **Goal-Based Target Probability Overlay:** Calculates exact mathematical probability of hitting financial wealth targets.
6. **Stress Test:** Institutional macroeconomic stress testing (uniform market shocks, sector-specific drawdowns, custom idiosyncratic shocks, and historical crisis replays).
7. **Optimizer:** Markowitz Modern Portfolio Theory, Minimum Variance, Maximum Sharpe, and interactive 'What If?' rebalancing sandbox.
8. **Reports:** Publication-quality multi-page PDF risk dossier generation (ReportLab) and raw CSV matrix exports.
9. **Data Centre:** Historical price observation auditing, gap detection, quality rating, and custom CSV end-of-day price uploads.
10. **Settings:** Macro benchmark configuration (Indian 10Y G-Sec hurdle rate, 252-day annualization) and 1-click demo universe reload.
6. **Stress Test:** Standard macro drawdowns (-10%, -15%, -25%), sector contagion shocks, tailored asset sliders, and historical crisis replays.
7. **Optimizer:** 
   - Markowitz mean-variance optimization (Minimum Variance, Maximum Sharpe, Efficient Frontier).
   - **Interactive "What If?" Rebalancing Sandbox:** Real-time slider re-weighting with instant impact delta analysis and multi-asset safe-haven integration (GoldBeES & LiquidBeES).
8. **Reports:** Publication-quality multi-page PDF generation via ReportLab and raw matrix CSV exports.
9. **Data Centre:** Audit inspection of observation density, gap frequency, freshness statuses, and custom CSV historical price imports.
10. **Methodology:** Transparent, educational documentation of all financial formulas, assumptions, and limitations.
11. **Settings:** Global parameters (Rf rate, annualization trading days, cost basis, demo re-seeding).

---

## 4. Folder Structure

```
90-days-90-projects-day-22-varlytix/
├── app.py                     # Main Streamlit workstation entrypoint
├── config.py                  # Global brand constants, palette, financial defaults
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables configuration
├── run.bat                    # One-click Windows launch script
├── setup.bat                  # One-click Windows environment installer
├── test.bat                   # Automated Pytest suite runner
├── README.md                  # Comprehensive product documentation
│
├── pages/                     # Dedicated screen views
│   ├── overview.py            # Screen 01: Portfolio Overview
│   ├── portfolio.py           # Screen 02: Position & Transaction Management
│   ├── risk_lab.py            # Screen 03: Risk Lab & Euler Decomposition
│   ├── correlation.py         # Screen 04: Correlation Intelligence
│   ├── simulation.py          # Screen 05: Monte Carlo Simulation Lab
│   ├── stress_test.py         # Screen 06: Stress Testing Engine
│   ├── optimizer.py           # Screen 07: Portfolio Optimizer & Efficient Frontier
│   ├── reports.py             # Screen 08: PDF & CSV Report Generator
│   ├── data_centre.py         # Screen 09: Data Quality & CSV Import
│   ├── methodology.py         # Screen 10: Quantitative Foundations
│   └── settings.py            # Screen 11: System Settings & Preferences
│
├── components/                # Reusable visual components
│   ├── brand.py               # Custom geometric SVG logo, badges, favicon
│   ├── navigation.py          # Global header & horizontal navbar
│   ├── metric_display.py      # Editorial metric cards & observation banners
│   └── chart_components.py    # Plotly interactive visualizations
│
├── services/                  # Business & orchestration logic
│   ├── portfolio_service.py   # Position CRUD & weighted-average cost accounting
│   ├── market_data_service.py # Multi-asset synchronization & return alignment
│   ├── risk_service.py        # Quantitative risk aggregation & observations
│   ├── simulation_service.py  # Monte Carlo orchestration & persistence
│   ├── stress_test_service.py # Macro and tailored shock execution
│   ├── optimization_service.py# Markowitz solver & frontier tracing
│   ├── report_service.py      # ReportLab PDF & CSV builder
│   └── data_quality_service.py# Gaps, freshness, and audit inspector
│
├── providers/                 # Market data adapter architecture
│   ├── base_provider.py       # Abstract provider contract
│   ├── demo_provider.py       # Deterministic synthetic Indian market universe
│   ├── yahoo_compatible_provider.py # Yahoo Finance API adapter (NSE/BSE)
│   └── csv_provider.py        # Strict CSV import parser & validator
│
├── models/                    # Database models & schemas
│   └── database.py            # SQLAlchemy SQLite schema & session factory
│
├── analytics/                 # Dedicated mathematical calculation modules
│   ├── returns.py             # Simple, log, cumulative, buy-and-hold returns
│   ├── volatility.py          # Volatility, downside deviation, Sharpe, Sortino
│   ├── drawdown.py            # Running peak, underwater series, MDD, Calmar
│   ├── covariance.py          # Covariance matrix & Euler risk contribution
│   ├── var_cvar.py            # Historical VaR, CVaR, benchmark Beta
│   ├── monte_carlo.py         # Bootstrap & parametric simulation engines
│   ├── stress_testing.py      # Uniform, sector, and custom shock models
│   └── optimization.py        # SciPy SLSQP optimization & efficient frontier
│
├── data/                      # Local data folders
│   ├── sample/                # Reference datasets
│   ├── imports/               # Uploaded CSV historical series
│   └── cache/                 # Cached returns & computations
│
├── database/                  # SQLite storage
│   └── varlytix.db             # Persistent SQLite database
│
├── scripts/                   # CLI execution utilities
│   └── seed_demo_data.py      # Seeds 650 days of synthetic prices & 3 portfolios
│
├── tests/                     # Comprehensive unit test suite (Pytest)
│   ├── test_portfolio.py      # Valuation & weighted-average cost tests
│   ├── test_returns.py        # Return compounding & buy-and-hold tests
│   ├── test_risk.py           # Volatility, drawdown, Sharpe, VaR/CVaR, Beta
│   ├── test_correlation.py    # Covariance & Euler identity verification
│   ├── test_simulation.py     # Monte Carlo reproducibility & bounds
│   ├── test_stress.py         # Static & sector shock impact tests
│   └── test_optimization.py   # SLSQP constraints & frontier tests
│
└── docs/                      # Methodological references
    ├── methodology.md         # Detailed mathematical equations & derivations
    ├── data_sources.md        # Market data provider architecture
    └── assumptions.md         # Financial assumptions & model limitations
```

---

## 5. Technology Stack

- **Frontend & Workstation UI:** Streamlit, Custom HTML/CSS
- **Interactive Visualizations:** Plotly Graph Objects & Plotly Express
- **Quantitative Analytics:** NumPy, SciPy (SLSQP optimization), Pandas
- **Persistence & Database:** SQLite 3, SQLAlchemy 2.0
- **Report Generation:** ReportLab 5.1 (PDF), Pandas (CSV)
- **Market Data Adapters:** Public Yahoo Finance convention (NSE/BSE), CSV Import
- **Quality Assurance & Verification:** Pytest, Pytest-cov

---

## 6. Windows Quickstart Setup Guide

### Prerequisites
- Windows 10 or Windows 11
- Python 3.12 (Recommended) installed and available on system PATH

### Automated Quickstart (1-Click)
Double-click `setup.bat` to automatically build the virtual environment, install packages, initialize the database, seed synthetic demo data, and run tests. Then launch with `run.bat`.

### Manual PowerShell Setup
```powershell
# 1. Navigate to project root
cd "d:\90 days\90-days-90-projects-day-22-varlytix"

# 2. Create virtual environment with Python 3.12
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize database & seed deterministic synthetic data
$env:PYTHONPATH = "."
python scripts\seed_demo_data.py

# 6. Run complete unit test suite
pytest tests -v

# 7. Launch VARLYTIX
streamlit run app.py
```

---

## 7. Deterministic Demo Mode Universe

VARLYTIX initializes with a deterministic synthetic market universe representing 10 major Indian equities and the NIFTY 50 benchmark over **650 continuous trading days (~2.5 years)**:

| Symbol | Company Name | Sector | Base Price | Annual Volatility |
| :--- | :--- | :--- | :--- | :--- |
| `DEMO_BANK_HDFC` | HDFC Bank (Demo) | Financial Services | ₹ 1,580 | 19.0% |
| `DEMO_BANK_ICICI` | ICICI Bank (Demo) | Financial Services | ₹ 1,050 | 23.0% |
| `DEMO_TECH_TCS` | Tata Consultancy Services (Demo) | Technology | ₹ 3,850 | 18.0% |
| `DEMO_TECH_INFY` | Infosys (Demo) | Technology | ₹ 1,620 | 22.0% |
| `DEMO_CONSUMER_RELIANCE` | Reliance Industries (Demo) | Conglomerate / Energy | ₹ 2,840 | 21.0% |
| `DEMO_CONSUMER_ITC` | ITC Ltd (Demo) | Consumer Defensive | ₹ 435 | 15.0% |
| `DEMO_AUTO_TATAMOTORS` | Tata Motors (Demo) | Automobile | ₹ 960 | 28.0% |
| `DEMO_PHARMA_SUN` | Sun Pharma (Demo) | Healthcare | ₹ 1,540 | 17.0% |
| `DEMO_ENERGY_NTPC` | NTPC Ltd (Demo) | Utilities / Power | ₹ 360 | 20.0% |
| `DEMO_INDEX_NIFTY50` | NIFTY 50 Benchmark (Demo) | Benchmark Index | ₹ 22,400 | 14.0% |

Three pre-configured sample portfolios are automatically loaded:
1. **Balanced Growth Portfolio:** Core multi-sector allocation across HDFC, TCS, RELIANCE, ITC, SUN PHARMA, and NTPC.
2. **High-Beta Aggressive Portfolio:** Concentrated momentum allocation in TATAMOTORS, INFY, ICICI, and TCS.
3. **Defensive Dividend Portfolio:** Capital preservation allocation in ITC, SUN PHARMA, NTPC, and HDFC.

---

## 8. Verification & Test Suite

Run the full automated test suite verifying mathematical correctness:

```powershell
pytest tests -v
```

All 21 comprehensive quantitative tests verify:
- Weighted-average cost basis after multi-stage purchases and partial liquidations.
- Buy-and-hold portfolio drift vs rebalanced returns.
- Standard annualized volatility scaling ($\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{252}$).
- Underwater drawdown series and maximum drawdown identification.
- Historical quantile VaR & Conditional VaR (Expected Shortfall).
- **Euler risk decomposition identity:** Verifies that $\sum \text{RC}_i$ strictly equals portfolio volatility $\sigma_p$ to numerical precision.
- Monte Carlo reproducibility with seeds and monotonic percentile ordering ($P_5 \le P_{25} \le P_{50} \le P_{75} \le P_{95}$).
- SciPy SLSQP optimization convergence and constraint enforcement ($\sum w_i = 1$, $0 \le w_i \le w_{\text{max}}$).

---

## 9. Regulatory & Financial Disclaimer

VARLYTIX is an analytical portfolio risk exploration platform. All statistics, Sharpe ratios, Value at Risk calculations, stress tests, and Monte Carlo simulations are hypothetical quantitative scenarios based on historical data and mathematical models. 

**This software does not execute trades, guarantee future returns, or provide investment advice.** Historical market behavior and correlation patterns do not guarantee future results.
