"""
Base Market Data Provider Interface for VARLYTIX.
Defines abstract contracts for asset searching, historical price retrieval,
metadata discovery, and provider health verification.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class BaseMarketDataProvider(ABC):
    """Abstract base class for all market data adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the human-readable provider identifier."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider endpoint or data source is accessible."""
        pass

    @abstractmethod
    def search_asset(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches available instruments matching the query string.
        Returns a list of dicts with: symbol, name, exchange, type.
        """
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieves daily historical price observations.
        Returns a DataFrame indexed by Date with columns:
        ['open', 'high', 'low', 'close', 'adjusted_close', 'volume']
        """
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest available close observation.
        Returns dict with: ['date', 'price', 'adjusted_close', 'currency'].
        """
        pass

    @abstractmethod
    def get_asset_metadata(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieves metadata such as sector, exchange, country, asset_type.
        """
        pass
