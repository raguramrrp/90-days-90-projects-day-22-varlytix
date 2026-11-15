"""
Yahoo-Compatible Market Data Provider Adapter for VARLYTIX.
Supports retrieving Indian listed equities and indices via Yahoo Finance API conventions.
Symbols for NSE are suffixed with .NS, BSE with .BO.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from providers.base_provider import BaseMarketDataProvider


class YahooCompatibleProvider(BaseMarketDataProvider):
    """Market data provider using yfinance / public Yahoo Finance endpoints."""

    def __init__(self):
        self._yf = None
        try:
            import yfinance as yf
            self._yf = yf
        except ImportError:
            self._yf = None

    @property
    def provider_name(self) -> str:
        return "YAHOO_FINANCE"

    def is_available(self) -> bool:
        return self._yf is not None

    def _format_indian_symbol(self, symbol: str, exchange: str = "NSE") -> str:
        """Appends appropriate exchange suffix if not already present."""
        clean = symbol.strip().upper()
        if clean.startswith("^"):
            return clean  # Index
        if "." in clean:
            return clean
        if exchange.upper() == "BSE":
            return f"{clean}.BO"
        return f"{clean}.NS"

    def search_asset(self, query: str) -> List[Dict[str, Any]]:
        """Simple symbol resolver for common Indian symbols."""
        if not self.is_available():
            return []
        sym = query.strip().upper()
        return [{
            "symbol": sym,
            "provider_symbol": self._format_indian_symbol(sym),
            "exchange": "NSE",
            "name": f"{sym} (NSE Listed)",
            "type": "EQUITY",
            "provider": self.provider_name,
        }]

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        if not self.is_available():
            return pd.DataFrame()

        provider_symbol = self._format_indian_symbol(symbol)
        try:
            ticker = self._yf.Ticker(provider_symbol)
            # Default to 3 years if not specified
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                return pd.DataFrame()

            # Standardize columns
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.index.name = "date"

            if "adj_close" in df.columns:
                df["adjusted_close"] = df["adj_close"]
            elif "close" in df.columns:
                df["adjusted_close"] = df["close"]

            return df[["open", "high", "low", "close", "adjusted_close", "volume"]]
        except Exception as e:
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        df = self.get_historical_prices(symbol)
        if df.empty:
            return None
        last_row = df.iloc[-1]
        return {
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "price": float(last_row["close"]),
            "adjusted_close": float(last_row["adjusted_close"]),
            "currency": "INR",
        }

    def get_asset_metadata(self, symbol: str) -> Dict[str, Any]:
        if not self.is_available():
            return {"symbol": symbol, "name": symbol, "exchange": "NSE", "currency": "INR"}
        try:
            ticker = self._yf.Ticker(self._format_indian_symbol(symbol))
            info = ticker.fast_info
            return {
                "symbol": symbol,
                "provider_symbol": self._format_indian_symbol(symbol),
                "name": symbol,
                "currency": getattr(info, "currency", "INR"),
                "exchange": "NSE",
                "sector": "Indian Equities",
            }
        except Exception:
            return {"symbol": symbol, "name": symbol, "exchange": "NSE", "currency": "INR"}
