"""
Stress Testing Service for SIGMORA.
Applies predefined, sector, historical, and custom shocks to portfolio holdings
and records scenario results in the database.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import pandas as pd
from sqlalchemy.orm import Session
from models.database import StressTestScenario, StressTestResult
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from analytics.stress_testing import (
    apply_uniform_shock, apply_sector_shock,
    apply_custom_shocks, replay_historical_period
)
from config import PRESET_STRESS_SCENARIOS


class StressTestService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.market_data_service = MarketDataService(db)

    def run_preset_scenario(self, portfolio_id: int, scenario_key: str) -> Dict[str, Any]:
        """Runs one of the built-in standard macro stress scenarios."""
        if scenario_key not in PRESET_STRESS_SCENARIOS:
            raise ValueError(f"Unknown preset scenario: {scenario_key}")

        cfg = PRESET_STRESS_SCENARIOS[scenario_key]
        holdings = self.portfolio_service.get_holdings_summary(portfolio_id)
        if holdings.empty:
            raise ValueError("Portfolio has no active holdings.")

        pos_df = holdings[["symbol", "current_value", "sector", "weight"]].copy()

        if cfg["type"] == "uniform":
            res = apply_uniform_shock(pos_df, cfg["shock_pct"])
        else:
            res = apply_sector_shock(pos_df, cfg["sector_shocks"])

        res["scenario_name"] = cfg["name"]
        res["description"] = cfg["description"]

        # Persist result
        self._save_stress_result(
            portfolio_id=portfolio_id,
            name=cfg["name"],
            orig_val=res["original_value"],
            stress_val=res["stressed_value"],
            port_ret=res["portfolio_return"]
        )

        return res

    def run_custom_scenario(
        self,
        portfolio_id: int,
        custom_shocks: Dict[str, float],
        scenario_name: str = "Custom User Shock"
    ) -> Dict[str, Any]:
        """Runs user-configured asset-level shocks."""
        holdings = self.portfolio_service.get_holdings_summary(portfolio_id)
        if holdings.empty:
            raise ValueError("Portfolio has no active holdings.")

        pos_df = holdings[["symbol", "current_value", "sector", "weight"]].copy()
        res = apply_custom_shocks(pos_df, custom_shocks)
        res["scenario_name"] = scenario_name

        self._save_stress_result(
            portfolio_id=portfolio_id,
            name=scenario_name,
            orig_val=res["original_value"],
            stress_val=res["stressed_value"],
            port_ret=res["portfolio_return"]
        )

        return res

    def _save_stress_result(
        self,
        portfolio_id: int,
        name: str,
        orig_val: float,
        stress_val: float,
        port_ret: float
    ):
        """Persists stress outcome to database."""
        rec = StressTestResult(
            portfolio_id=portfolio_id,
            scenario_name=name,
            original_value=orig_val,
            stressed_value=stress_val,
            portfolio_return=port_ret,
            calculated_at=datetime.utcnow(),
        )
        self.db.add(rec)
        self.db.commit()
