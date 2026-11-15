"""
Market Data Service for SIGMORA.
Orchestrates market data providers (Demo, Yahoo, CSV), manages database sync,
aligns multi-asset price and return matrices, and tracks data quality/freshness.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from models.database import Asset, HistoricalPrice, DailyReturn, DataRefreshLog, BenchmarkData
from providers.demo_provider import DemoSyntheticProvider, DEMO_ASSETS
from providers.yahoo_compatible_provider import YahooCompatibleProvider
from providers.csv_provider import CSVMarketDataProvider
from analytics.returns import calculate_simple_returns, calculate_log_returns


class MarketDataService:
    def __init__(self, db: Session):
        self.db = db
        self.demo_provider = DemoSyntheticProvider()
        self.yahoo_provider = YahooCompatibleProvider()
        self.csv_provider = CSVMarketDataProvider()

    def get_provider(self, provider_name: str = "DEMO_SYNTHETIC"):
        p = provider_name.upper()
        if "YAHOO" in p:
            return self.yahoo_provider
        elif "CSV" in p:
            return self.csv_provider
        return self.demo_provider

    def sync_asset_prices(
        self,
        asset: Asset,
        provider_name: str = "DEMO_SYNTHETIC",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        Fetches historical price series from selected provider, saves to historical_prices,
        and generates daily returns.
        """
        provider = self.get_provider(provider_name)
        log = DataRefreshLog(
            asset_id=asset.id,
            provider=provider.provider_name,
            refresh_started_at=datetime.utcnow(),
            refresh_status="RUNNING"
        )
        self.db.add(log)
        self.db.commit()

        try:
            df = provider.get_historical_prices(asset.symbol, start_date=start_date, end_date=end_date)
            if df.empty:
                log.refresh_status = "FAILED"
                log.error_message = f"No price observations returned for symbol '{asset.symbol}'."
                log.refresh_completed_at = datetime.utcnow()
                self.db.commit()
                return 0

            # Upsert into historical_prices
            records_count = 0
            for dt, row in df.iterrows():
                p_date = dt.date() if isinstance(dt, (datetime, pd.Timestamp)) else dt
                existing = self.db.query(HistoricalPrice).filter(
                    HistoricalPrice.asset_id == asset.id,
                    HistoricalPrice.price_date == p_date
                ).first()

                close_p = float(row["close"])
                adj_close_p = float(row.get("adjusted_close", close_p))

                if not existing:
                    price_rec = HistoricalPrice(
                        asset_id=asset.id,
                        price_date=p_date,
                        open_price=float(row.get("open", close_p)),
                        high_price=float(row.get("high", close_p)),
                        low_price=float(row.get("low", close_p)),
                        close_price=close_p,
                        adjusted_close=adj_close_p,
                        volume=float(row.get("volume", 0.0)),
                        data_source=provider.provider_name,
                    )
                    self.db.add(price_rec)
                    records_count += 1
                else:
                    existing.close_price = close_p
                    existing.adjusted_close = adj_close_p
                    existing.data_source = provider.provider_name

            self.db.commit()

            # Calculate and store daily returns
            self._sync_daily_returns(asset.id)

            log.refresh_status = "SUCCESS"
            log.records_received = records_count
            log.refresh_completed_at = datetime.utcnow()
            self.db.commit()
            return records_count

        except Exception as e:
            self.db.rollback()
            log.refresh_status = "FAILED"
            log.error_message = str(e)
            log.refresh_completed_at = datetime.utcnow()
            self.db.commit()
            return 0

    def _sync_daily_returns(self, asset_id: int):
        """Calculates and persists simple and log returns for an asset."""
        prices = self.db.query(HistoricalPrice).filter(
            HistoricalPrice.asset_id == asset_id
        ).order_by(HistoricalPrice.price_date.asc()).all()

        if len(prices) < 2:
            return

        dates = [p.price_date for p in prices]
        adj_closes = pd.Series([p.adjusted_close for p in prices], index=dates)

        simple_ret = calculate_simple_returns(adj_closes)
        log_ret = calculate_log_returns(adj_closes)

        for d, s_r in simple_ret.items():
            l_r = log_ret.get(d, 0.0)
            existing = self.db.query(DailyReturn).filter(
                DailyReturn.asset_id == asset_id,
                DailyReturn.return_date == d
            ).first()

            if not existing:
                ret_rec = DailyReturn(
                    asset_id=asset_id,
                    return_date=d,
                    simple_return=float(s_r),
                    log_return=float(l_r),
                )
                self.db.add(ret_rec)
            else:
                existing.simple_return = float(s_r)
                existing.log_return = float(l_r)

        self.db.commit()

    def get_price_matrix(
        self,
        symbols: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Retrieves aligned Date x Asset Price DataFrame for the requested symbols.
        Dates with missing values are strictly aligned via inner join or dropped.
        """
        if not symbols:
            return pd.DataFrame()

        series_dict = {}
        for sym in symbols:
            asset = self.db.query(Asset).filter(Asset.symbol == sym).first()
            if not asset:
                continue

            query = self.db.query(HistoricalPrice).filter(HistoricalPrice.asset_id == asset.id)
            if start_date:
                query = query.filter(HistoricalPrice.price_date >= start_date)
            if end_date:
                query = query.filter(HistoricalPrice.price_date <= end_date)

            prices = query.order_by(HistoricalPrice.price_date.asc()).all()
            if prices:
                s = pd.Series(
                    [p.adjusted_close for p in prices],
                    index=pd.to_datetime([p.price_date for p in prices]),
                    name=sym
                )
                series_dict[sym] = s

        if not series_dict:
            return pd.DataFrame()

        df = pd.DataFrame(series_dict)
        return df.dropna()

    def get_return_matrix(
        self,
        symbols: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Retrieves aligned Date x Asset Daily Returns DataFrame.
        """
        price_matrix = self.get_price_matrix(symbols, start_date, end_date)
        if price_matrix.empty or len(price_matrix) < 2:
            return pd.DataFrame()
        return calculate_simple_returns(price_matrix)
