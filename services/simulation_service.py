"""
Simulation Service for VARLYTIX.
Orchestrates Monte Carlo runs, records simulation meta and percentiles in the database,
and formats fan chart curves and probability distributions.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import pandas as pd
from sqlalchemy.orm import Session
from models.database import SimulationRun, SimulationResult
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from analytics.monte_carlo import (
    run_historical_bootstrap_simulation,
    run_parametric_monte_carlo_simulation
)


class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.market_data_service = MarketDataService(db)

    def run_simulation(
        self,
        portfolio_id: int,
        method: str = "BOOTSTRAP",  # BOOTSTRAP or PARAMETRIC
        horizon_days: int = 252,
        num_simulations: int = 1000,
        random_seed: int = 42,
        block_size: int = 1,
        monthly_sip: float = 0.0,
        goal_target_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes Monte Carlo simulation for current portfolio holdings
        with optional recurring monthly SIP and financial goal probability.
        """
        holdings = self.portfolio_service.get_holdings_summary(portfolio_id)
        if holdings.empty:
            raise ValueError("Portfolio has no active holdings to simulate.")

        symbols = holdings["symbol"].tolist()
        weights = holdings.set_index("symbol")["weight"]
        initial_value = float(holdings["current_value"].sum())

        returns_df = self.market_data_service.get_return_matrix(symbols)
        if returns_df.empty or len(returns_df) < 20:
            raise ValueError("Insufficient historical observations for simulation.")

        # Run chosen simulation method
        if method.upper() == "BOOTSTRAP":
            sim_res = run_historical_bootstrap_simulation(
                returns_df=returns_df,
                weights=weights,
                initial_value=initial_value,
                horizon_days=horizon_days,
                num_simulations=num_simulations,
                block_size=block_size,
                random_seed=random_seed,
                monthly_sip=monthly_sip,
                goal_target_value=goal_target_value
            )
        else:
            sim_res = run_parametric_monte_carlo_simulation(
                returns_df=returns_df,
                weights=weights,
                initial_value=initial_value,
                horizon_days=horizon_days,
                num_simulations=num_simulations,
                random_seed=random_seed,
                monthly_sip=monthly_sip,
                goal_target_value=goal_target_value
            )

        # Persist run meta and summary results
        run_rec = SimulationRun(
            portfolio_id=portfolio_id,
            simulation_method=method.upper(),
            initial_value=initial_value,
            simulation_count=num_simulations,
            horizon_days=horizon_days,
            random_seed=random_seed,
            assumptions=json.dumps({
                "method": method.upper(),
                "block_size": block_size,
                "assets": symbols,
                "monthly_sip": monthly_sip,
                "goal_target_value": goal_target_value
            }),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(run_rec)
        self.db.commit()
        self.db.refresh(run_rec)

        # Store percentiles
        for p_val, val in sim_res["summary_percentiles"].items():
            res_rec = SimulationResult(
                simulation_id=run_rec.id,
                percentile=float(p_val) / 100.0,
                ending_value=float(val),
                ending_return=float((val / initial_value) - 1.0) if initial_value > 0 else 0.0
            )
            self.db.add(res_rec)

        self.db.commit()
        sim_res["simulation_run_id"] = run_rec.id
        return sim_res
