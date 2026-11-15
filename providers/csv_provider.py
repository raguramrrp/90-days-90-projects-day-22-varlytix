"""
CSV Market Data Provider and File Validator for VARLYTIX.
Allows users to upload custom CSV historical price data with strict validation:
date formats, positive prices, duplicate date detection, and column mapping.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from providers.base_provider import BaseMarketDataProvider
from config import IMPORTS_DIR


class CSVMarketDataProvider(BaseMarketDataProvider):
    """Provider for user-imported CSV price files."""

    def __init__(self, imports_dir: Optional[Path] = None):
        self.imports_dir = imports_dir or IMPORTS_DIR

    @property
    def provider_name(self) -> str:
        return "MANUAL_CSV_IMPORT"

    def is_available(self) -> bool:
        return True

    def validate_and_parse_csv(self, file_path_or_buffer) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Validates imported CSV data.
        Expected columns: Date, Close (or Adjusted Close).
        Optional: Open, High, Low, Volume, Symbol.
        """
        try:
            df = pd.read_csv(file_path_or_buffer)
            if df.empty:
                return False, "CSV file is empty.", None

            # Lowercase columns
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            # Find date column
            date_col = None
            for candidate in ["date", "timestamp", "time"]:
                if candidate in df.columns:
                    date_col = candidate
                    break
            if not date_col:
                return False, "Missing mandatory 'Date' column.", None

            # Find close column
            close_col = None
            for candidate in ["close", "close_price", "adj_close", "adjusted_close", "price"]:
                if candidate in df.columns:
                    close_col = candidate
                    break
            if not close_col:
                return False, "Missing mandatory 'Close' or 'Price' column.", None

            # Parse dates
            df["parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
            if df["parsed_date"].isna().any():
                bad_count = df["parsed_date"].isna().sum()
                return False, f"Found {bad_count} unparseable date values in '{date_col}'.", None

            # Check duplicates
            if df["parsed_date"].duplicated().any():
                dup_count = df["parsed_date"].duplicated().sum()
                return False, f"Found {dup_count} duplicate dates in CSV. Dates must be unique.", None

            # Parse numeric prices
            df[close_col] = pd.to_numeric(df[close_col], errors="coerce")
            if df[close_col].isna().any():
                return False, f"Found non-numeric values in '{close_col}'.", None

            if (df[close_col] <= 0).any():
                return False, f"Found non-positive prices (<= 0) in '{close_col}'. Prices must be positive.", None

            # Standardize output DataFrame
            res_df = pd.DataFrame(index=df["parsed_date"])
            res_df.index.name = "date"
            res_df["close"] = df[close_col].values
            res_df["adjusted_close"] = df.get("adjusted_close", df.get("adj_close", df[close_col])).values

            # Optional columns
            for col in ["open", "high", "low", "volume"]:
                if col in df.columns:
                    res_df[col] = pd.to_numeric(df[col], errors="coerce").fillna(res_df["close"])
                else:
                    res_df[col] = res_df["close"] if col != "volume" else 0.0

            res_df = res_df.sort_index()
            return True, f"Successfully validated {len(res_df)} daily observations from {res_df.index[0].date()} to {res_df.index[-1].date()}.", res_df

        except Exception as e:
            return False, f"CSV parsing error: {str(e)}", None

    def search_asset(self, query: str) -> List[Dict[str, Any]]:
        return []

    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        csv_file = self.imports_dir / f"{symbol.upper()}.csv"
        if not csv_file.exists():
            return pd.DataFrame()
        valid, msg, df = self.validate_and_parse_csv(csv_file)
        if not valid or df is None:
            return pd.DataFrame()
        if start_date:
            df = df.loc[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df.loc[df.index <= pd.to_datetime(end_date)]
        return df

    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
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
        return {
            "symbol": symbol,
            "name": f"{symbol} (Custom Import)",
            "sector": "Imported",
            "exchange": "CUSTOM",
            "currency": "INR",
        }
