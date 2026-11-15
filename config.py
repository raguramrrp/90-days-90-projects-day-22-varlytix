"""
SIGMORA Configuration Module
Brand Identity, Design Palette, Financial Constants, and System Settings.
"""

from pathlib import Path
import os

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "sigmora.db"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
CACHE_DIR = DATA_DIR / "cache"
IMPORTS_DIR = DATA_DIR / "imports"
DOCS_DIR = BASE_DIR / "docs"

# Ensure directories exist
for folder in [DATA_DIR, DATABASE_DIR, SAMPLE_DATA_DIR, CACHE_DIR, IMPORTS_DIR, DOCS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Database URI
DATABASE_URL = os.getenv("SIGMORA_DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")

# Brand Identity
BRAND_NAME = "SIGMORA"
BRAND_DESCRIPTOR = "Portfolio Risk Intelligence"
BRAND_TAGLINE = "Understand your exposure. Measure uncertainty. Explore possible outcomes."
MARKET_FOCUS = "Indian Equities & ETFs"
BASE_CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"

# Design System Colour Palette — Modern Stock Market App Theme (Midnight Pro)
COLORS = {
    # Core Stock Market Pro Palette
    "application_background": "#0B0F19",  # Deep Midnight Slate Canvas
    "primary_surface": "#121826",         # Elevated Pro Card Surface
    "primary_text": "#F8FAFC",            # Crisp White Typography
    "secondary_text": "#94A3B8",          # Cool Slate for Labels, Subvalues & Units
    "primary_accent": "#2563EB",          # Electric Cobalt / Royal Blue (Primary Brand & Action)
    "secondary_accent": "#38BDF8",        # Tech Sky Cyan (Secondary Analytical Series)
    "muted_highlight": "#F59E0B",         # Market Amber / Gold (Uncertainty & Notices)
    "border": "#1E293B",                  # Crisp Dark Slate Divider Border
    "positive": "#00D26A",                # Stock Market Bull Green (Gains / Profits)
    "negative": "#F43F5E",                # Stock Market Bear Crimson (Losses / Drawdowns)
    "warning": "#F59E0B",                 # Warning Gold
    "neutral": "#64748B",                 # Benchmark Neutral Slate

    # Backwards-compatible aliases for components
    "graphite": "#F8FAFC",                # Primary Crisp White Text
    "warm_paper": "#0B0F19",              # Deep Canvas
    "white": "#121826",                   # Elevated Card Surface
    "deep_teal": "#2563EB",               # Primary Brand Accent (Cobalt)
    "muted_teal": "#38BDF8",              # Secondary Accent (Sky Cyan)
    "amber": "#F59E0B",                   # Warning / Amber
    "slate": "#64748B",                   # Neutral Slate
    "card_bg": "#121826",                 # Card Surface
    "surface_tint": "#182234",            # Elevated Input Background
}

# Financial Conventions & Defaults
DEFAULT_RISK_FREE_RATE = 0.065  # 6.5% Indian 10-Year G-Sec benchmark rate
DEFAULT_TRADING_DAYS = 252      # Trading days per year in India
DEFAULT_BENCHMARK_SYMBOL = "DEMO_INDEX_NIFTY50"
REAL_BENCHMARK_SYMBOL = "^NSEI"  # NIFTY 50 Yahoo symbol

# Simulation Settings
SIMULATION_HORIZONS = {
    "1 Month (21 days)": 21,
    "3 Months (63 days)": 63,
    "6 Months (126 days)": 126,
    "1 Year (252 days)": 252,
    "3 Years (756 days)": 756,
    "5 Years (1260 days)": 1260,
}
DEFAULT_SIMULATION_COUNT = 1000
MAX_SIMULATION_COUNT = 10000
DEFAULT_RANDOM_SEED = 42

# Risk Confidence Levels
VAR_CONFIDENCE_LEVELS = [0.90, 0.95, 0.99]
DEFAULT_CONFIDENCE_LEVEL = 0.95

# Stress Scenarios
PRESET_STRESS_SCENARIOS = {
    "broad_market_decline": {
        "name": "Broad Market Decline",
        "description": "Systemic equity market drop of 15% across all asset classes",
        "shock_pct": -0.15,
        "type": "uniform",
    },
    "moderate_correction": {
        "name": "Moderate Equity Correction",
        "description": "Standard market pullback of 10% after an extended rally",
        "shock_pct": -0.10,
        "type": "uniform",
    },
    "severe_equity_shock": {
        "name": "Severe Equity Shock (Liquidity Crunch)",
        "description": "High-volatility panic drop of 25% similar to major liquidity crises",
        "shock_pct": -0.25,
        "type": "uniform",
    },
    "tech_sector_decline": {
        "name": "Technology Sector Decline",
        "description": "Sector-specific 20% drawdown in Technology stocks, 5% spillover to others",
        "sector_shocks": {"Technology": -0.20, "Other": -0.05},
        "type": "sector",
    },
    "financial_sector_decline": {
        "name": "Financial & Banking Shock",
        "description": "Sector-specific 20% credit/NPA shock to Banking/Financials, 6% spillover",
        "sector_shocks": {"Financial Services": -0.20, "Banking": -0.20, "Other": -0.06},
        "type": "sector",
    },
}
