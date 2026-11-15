"""
Data Quality and Health Inspection Service for VARLYTIX.
Audits historical price coverage, gaps, freshness, and duplicate observations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from models.database import Asset, HistoricalPrice, DataRefreshLog


class DataQualityService:
    def __init__(self, db: Session):
        self.db = db

    def audit_asset_data(self, asset_id: int) -> Dict[str, Any]:
        """Performs a comprehensive data quality check on a specific asset's history."""
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return {"error": "Asset not found."}

        prices = self.db.query(HistoricalPrice).filter(
            HistoricalPrice.asset_id == asset_id
        ).order_by(HistoricalPrice.price_date.asc()).all()

        if not prices:
            return {
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "name": asset.asset_name,
                "status": "NO_DATA",
                "observations": 0,
                "first_date": None,
                "last_date": None,
                "missing_rate": 1.0,
                "duplicate_dates": 0,
                "latest_source": "NONE",
            }

        dates = [p.price_date for p in prices]
        df = pd.DataFrame({
            "date": pd.to_datetime(dates),
            "close": [p.close_price for p in prices],
            "adj_close": [p.adjusted_close for p in prices],
            "volume": [p.volume for p in prices],
            "source": [p.data_source for p in prices],
        }).set_index("date")

        first_d = df.index[0].date()
        last_d = df.index[-1].date()
        n_obs = len(df)

        # Duplicate check
        dup_count = int(df.index.duplicated().sum())

        # Gaps check (business days without prices)
        all_bdays = pd.bdate_range(start=first_d, end=last_d)
        expected_bdays = len(all_bdays)
        missing_bdays = max(0, expected_bdays - n_obs)
        missing_rate = missing_bdays / expected_bdays if expected_bdays > 0 else 0.0

        # Freshness evaluation
        days_stale = (datetime.now().date() - last_d).days
        if days_stale <= 4:
            freshness = "Current"
        elif days_stale <= 14:
            freshness = "Delayed"
        else:
            freshness = "Stale"

        # Quality scoring
        if missing_rate < 0.08 and dup_count == 0 and n_obs >= 250:
            quality = "EXCELLENT"
        elif missing_rate < 0.20 and dup_count == 0:
            quality = "GOOD"
        else:
            quality = "ATTENTION_NEEDED"

        # Check last refresh log
        last_log = self.db.query(DataRefreshLog).filter(
            DataRefreshLog.asset_id == asset_id
        ).order_by(DataRefreshLog.refresh_started_at.desc()).first()

        return {
            "asset_id": asset.id,
            "symbol": asset.symbol,
            "name": asset.asset_name,
            "exchange": asset.exchange,
            "sector": asset.sector,
            "first_date": first_d,
            "last_date": last_d,
            "observations": n_obs,
            "expected_business_days": expected_bdays,
            "missing_business_days": missing_bdays,
            "missing_rate": missing_rate,
            "duplicate_dates": dup_count,
            "freshness": freshness,
            "quality_status": quality,
            "data_source": prices[-1].data_source,
            "last_refreshed": last_log.refresh_started_at if last_log else None,
            "last_refresh_status": last_log.refresh_status if last_log else "OK",
        }

    def audit_all_assets(self) -> List[Dict[str, Any]]:
        """Returns quality audit reports for all registered assets."""
        assets = self.db.query(Asset).all()
        return [self.audit_asset_data(a.id) for a in assets]
