"""
Portfolio Optimization Service for SIGMORA.
Calculates optimal asset allocations (Min Variance, Max Sharpe),
generates Markowitz Efficient Frontier curves, and compares candidate allocations.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from analytics.optimization import (
    optimize_minimum_variance, optimize_maximum_sharpe, generate_efficient_frontier
)
from analytics.covariance import calculate_covariance_matrix
from config import DEFAULT_RISK_FREE_RATE, DEFAULT_TRADING_DAYS


class OptimizationService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.market_data_service = MarketDataService(db)

    def optimize_portfolio(
        self,
        portfolio_id: int,
        max_position_weight: float = 0.40,
        min_position_weight: float = 0.0,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    ) -> Dict[str, Any]:
        """
        Runs optimization suite:
        - Current portfolio metrics
        - Minimum Variance Portfolio
        - Maximum Sharpe Ratio Portfolio
        - Efficient Frontier curve points
        """
        holdings = self.portfolio_service.get_holdings_summary(portfolio_id)
        if holdings.empty:
            raise ValueError("Portfolio has no active holdings.")

        symbols = holdings["symbol"].tolist()
        if len(symbols) < 2:
            raise ValueError("Optimization requires at least two distinct assets.")

        current_weights = holdings.set_index("symbol")["weight"]
        returns_df = self.market_data_service.get_return_matrix(symbols)

        if returns_df.empty or len(returns_df) < 20:
            raise ValueError("Insufficient historical observations to estimate covariance matrix.")

        # Annualized parameters
        mean_daily = returns_df.mean()
        mean_annual = (1.0 + mean_daily) ** DEFAULT_TRADING_DAYS - 1.0
        cov_annual = calculate_covariance_matrix(returns_df, annualize=True, trading_days=DEFAULT_TRADING_DAYS)

        # Current portfolio statistics
        curr_w = current_weights[symbols].values
        curr_exp_ret = float(curr_w @ mean_annual[symbols].values)
        curr_vol = float(np.sqrt(curr_w.T @ cov_annual.loc[symbols, symbols].values @ curr_w))
        curr_sharpe = (curr_exp_ret - risk_free_rate) / curr_vol if curr_vol > 0 else 0.0

        current_profile = {
            "name": "Current Portfolio",
            "weights": current_weights,
            "expected_return": curr_exp_ret,
            "volatility": curr_vol,
            "sharpe_ratio": curr_sharpe,
        }

        # Min Variance
        min_var_res = optimize_minimum_variance(
            mean_returns=mean_annual,
            cov_matrix=cov_annual,
            max_weight=max_position_weight,
            min_weight=min_position_weight
        )

        # Max Sharpe
        max_sharpe_res = optimize_maximum_sharpe(
            mean_returns=mean_annual,
            cov_matrix=cov_annual,
            risk_free_rate=risk_free_rate,
            max_weight=max_position_weight,
            min_weight=min_position_weight
        )

        # Efficient frontier points
        frontier_df = generate_efficient_frontier(
            mean_returns=mean_annual,
            cov_matrix=cov_annual,
            num_points=25,
            max_weight=max_position_weight,
            min_weight=min_position_weight
        )

        return {
            "current": current_profile,
            "min_variance": min_var_res,
            "max_sharpe": max_sharpe_res,
            "efficient_frontier": frontier_df,
            "symbols": symbols,
            "asset_means": mean_annual,
            "cov_matrix": cov_annual,
            "assumptions": {
                "max_weight": max_position_weight,
                "min_weight": min_position_weight,
                "risk_free_rate": risk_free_rate,
                "method": "Markowitz Mean-Variance (SLSQP)",
                "note": "Estimates are sensitive to historical inputs and do not guarantee future returns."
            }
        }
