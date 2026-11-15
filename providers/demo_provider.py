"""
Deterministic Synthetic Market Data Provider for VARLYTIX.
Generates reproducible daily historical market series for Indian equities & ETFs
using multivariate geometric Brownian motion with realistic sector covariances.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from providers.base_provider import BaseMarketDataProvider

# Pre-defined Synthetic Assets for the Indian Market Demo
DEMO_ASSETS = {
    "DEMO_BANK_HDFC": {
        "name": "HDFC Bank (Demo Synthetic)",
        "sector": "Financial Services",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 1580.0,
        "annual_drift": 0.12,
        "annual_vol": 0.19,
    },
    "DEMO_BANK_ICICI": {
        "name": "ICICI Bank (Demo Synthetic)",
        "sector": "Financial Services",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 1050.0,
        "annual_drift": 0.15,
        "annual_vol": 0.23,
    },
    "DEMO_TECH_TCS": {
        "name": "Tata Consultancy Services (Demo Synthetic)",
        "sector": "Technology",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 3850.0,
        "annual_drift": 0.11,
        "annual_vol": 0.18,
    },
    "DEMO_TECH_INFY": {
        "name": "Infosys (Demo Synthetic)",
        "sector": "Technology",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 1620.0,
        "annual_drift": 0.13,
        "annual_vol": 0.22,
    },
    "DEMO_CONSUMER_RELIANCE": {
        "name": "Reliance Industries (Demo Synthetic)",
        "sector": "Conglomerate / Energy",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 2840.0,
        "annual_drift": 0.14,
        "annual_vol": 0.21,
    },
    "DEMO_CONSUMER_ITC": {
        "name": "ITC Ltd (Demo Synthetic)",
        "sector": "Consumer Defensive",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 435.0,
        "annual_drift": 0.09,
        "annual_vol": 0.15,
    },
    "DEMO_AUTO_TATAMOTORS": {
        "name": "Tata Motors (Demo Synthetic)",
        "sector": "Automobile",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 960.0,
        "annual_drift": 0.16,
        "annual_vol": 0.28,
    },
    "DEMO_PHARMA_SUN": {
        "name": "Sun Pharma (Demo Synthetic)",
        "sector": "Healthcare",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 1540.0,
        "annual_drift": 0.13,
        "annual_vol": 0.17,
    },
    "DEMO_ENERGY_NTPC": {
        "name": "NTPC Ltd (Demo Synthetic)",
        "sector": "Utilities / Power",
        "exchange": "NSE",
        "type": "EQUITY",
        "base_price": 360.0,
        "annual_drift": 0.15,
        "annual_vol": 0.20,
    },
    "DEMO_COMMODITY_GOLDBEES": {
        "name": "Nippon India ETF Gold BeES",
        "sector": "Commodity / Gold ETF",
        "exchange": "NSE",
        "type": "COMMODITY",
        "base_price": 65.50,
        "annual_drift": 0.10,
        "annual_vol": 0.12,
    },
    "DEMO_DEBT_LIQUIDBEES": {
        "name": "Nippon India ETF Liquid BeES",
        "sector": "Debt / Cash Alternative",
        "exchange": "NSE",
        "type": "DEBT",
        "base_price": 1000.0,
        "annual_drift": 0.068,
        "annual_vol": 0.005,
    },
    "DEMO_INDEX_NIFTY50": {
        "name": "NIFTY 50 Benchmark (Demo Synthetic)",
        "sector": "Benchmark Index",
        "exchange": "NSE",
        "type": "INDEX",
        "base_price": 22400.0,
        "annual_drift": 0.12,
        "annual_vol": 0.14,
    },
}


class DemoSyntheticProvider(BaseMarketDataProvider):
    """
    Deterministic Synthetic Market Data Provider.
    Generates realistic, mathematically consistent Indian stock price histories.
    """

    def __init__(self, seed: int = 42, num_trading_days: int = 650):
        self._seed = seed
        self._num_trading_days = num_trading_days
        self._cache = {}
        self._generate_synthetic_universe()

    @property
    def provider_name(self) -> str:
        return "DEMO_SYNTHETIC"

    def is_available(self) -> bool:
        return True

    def _generate_synthetic_universe(self):
        """Generates correlated price series for all demo instruments."""
        np.random.seed(self._seed)

        symbols = list(DEMO_ASSETS.keys())
        n = len(symbols)

        # Build realistic correlation matrix
        corr = np.eye(n)
        for i, s1 in enumerate(symbols):
            for j, s2 in enumerate(symbols):
                if i == j:
                    continue
                sec1 = DEMO_ASSETS[s1]["sector"]
                sec2 = DEMO_ASSETS[s2]["sector"]
                # Sector correlation rules
                if sec1 == sec2:
                    corr[i, j] = 0.70  # Strong intra-sector correlation
                elif "Debt / Cash" in sec1 or "Debt / Cash" in sec2:
                    corr[i, j] = 0.00  # Cash/debt has virtually zero equity correlation
                elif "Gold ETF" in sec1 or "Gold ETF" in sec2:
                    corr[i, j] = 0.02  # Gold provides genuine hedge with low/uncorrelated behavior
                elif "Benchmark" in sec1 or "Benchmark" in sec2:
                    corr[i, j] = 0.65  # Benchmark correlation
                elif "Healthcare" in [sec1, sec2] or "Consumer Defensive" in [sec1, sec2]:
                    corr[i, j] = 0.25  # Defensive lower correlation
                else:
                    corr[i, j] = 0.40  # Moderate inter-sector correlation

        # Nearest PSD correction if needed
        eigvals, eigvecs = np.linalg.eigh(corr)
        eigvals = np.maximum(eigvals, 1e-4)
        corr_psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
        d = np.sqrt(np.diag(corr_psd))
        corr_psd = corr_psd / np.outer(d, d)

        # Cholesky factor
        L = np.linalg.cholesky(corr_psd)

        # Generate trading dates (excluding weekends)
        end_date = datetime.now().date()
        dates = []
        cur_date = end_date
        while len(dates) < self._num_trading_days:
            if cur_date.weekday() < 5:  # Monday to Friday
                dates.append(cur_date)
            cur_date -= timedelta(days=1)
        dates.reverse()

        # Daily dt
        dt = 1.0 / 252.0

        # Simulate correlated daily returns
        z = np.random.standard_normal((self._num_trading_days, n))
        correlated_z = z @ L.T

        price_series = {}
        for i, sym in enumerate(symbols):
            cfg = DEMO_ASSETS[sym]
            mu = cfg["annual_drift"]
            sigma = cfg["annual_vol"]
            p0 = cfg["base_price"]

            # Geometric Brownian Motion step: S_t = S_{t-1} * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
            drift = (mu - 0.5 * (sigma ** 2)) * dt
            diffusion = sigma * np.sqrt(dt) * correlated_z[:, i]
            log_returns = drift + diffusion
            daily_returns = np.exp(log_returns) - 1.0

            # Price path
            prices = np.zeros(self._num_trading_days)
            prices[0] = p0
            for t in range(1, self._num_trading_days):
                prices[t] = prices[t - 1] * (1.0 + daily_returns[t])

            # Create realistic Open, High, Low, Volume
            df_sym = pd.DataFrame(index=pd.to_datetime(dates))
            df_sym.index.name = "date"
            df_sym["close"] = np.round(prices, 2)
            df_sym["adjusted_close"] = df_sym["close"]
            # Intra-day volatility
            noise = np.random.uniform(0.002, 0.015, size=self._num_trading_days)
            df_sym["open"] = np.round(df_sym["close"].shift(1).fillna(df_sym["close"].iloc[0]), 2)
            df_sym["high"] = np.round(np.maximum(df_sym["open"], df_sym["close"]) * (1.0 + noise), 2)
            df_sym["low"] = np.round(np.minimum(df_sym["open"], df_sym["close"]) * (1.0 - noise), 2)
            df_sym["volume"] = np.random.randint(100000, 2500000, size=self._num_trading_days)

            price_series[sym] = df_sym

        self._cache = price_series

    def search_asset(self, query: str) -> List[Dict[str, Any]]:
        q = query.upper()
        results = []
        for sym, meta in DEMO_ASSETS.items():
            if q in sym or q in meta["name"].upper() or q in meta["sector"].upper():
                results.append({
                    "symbol": sym,
                    "name": meta["name"],
                    "exchange": meta["exchange"],
                    "sector": meta["sector"],
                    "type": meta["type"],
                    "provider": self.provider_name,
                })
        return results

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        if symbol not in self._cache:
            return pd.DataFrame()

        df = self._cache[symbol].copy()
        if start_date:
            df = df.loc[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df.loc[df.index <= pd.to_datetime(end_date)]
        return df

    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        if symbol not in self._cache:
            return None
        df = self._cache[symbol]
        last_row = df.iloc[-1]
        return {
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "price": float(last_row["close"]),
            "adjusted_close": float(last_row["adjusted_close"]),
            "currency": "INR",
        }

    def get_asset_metadata(self, symbol: str) -> Dict[str, Any]:
        meta = DEMO_ASSETS.get(symbol, {
            "name": symbol,
            "sector": "General",
            "exchange": "NSE",
            "type": "EQUITY",
        })
        return {
            "symbol": symbol,
            "name": meta["name"],
            "sector": meta["sector"],
            "exchange": meta["exchange"],
            "type": meta["type"],
            "currency": "INR",
            "country": "India",
        }
