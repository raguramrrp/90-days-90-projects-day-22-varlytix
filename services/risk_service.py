"""
Risk Analytics Service for SIGMORA.
Aggregates quantitative risk metrics, component risk contributions,
benchmark beta, drawdown series, and automated risk observations.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from models.database import Portfolio, RiskMetric
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from analytics.returns import calculate_buy_and_hold_portfolio, calculate_annualized_return
from analytics.volatility import (
    calculate_annualized_volatility, calculate_downside_deviation,
    calculate_sharpe_ratio, calculate_sortino_ratio, calculate_rolling_volatility
)
from analytics.drawdown import (
    calculate_drawdown_series, calculate_max_drawdown,
    calculate_average_drawdown, calculate_calmar_ratio
)
from analytics.covariance import (
    calculate_covariance_matrix, calculate_portfolio_variance_and_volatility,
    calculate_risk_contributions
)
from analytics.var_cvar import (
    calculate_historical_var, calculate_historical_cvar, calculate_beta
)
from config import DEFAULT_RISK_FREE_RATE, DEFAULT_TRADING_DAYS, DEFAULT_BENCHMARK_SYMBOL


class RiskService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.market_data_service = MarketDataService(db)

    def analyze_portfolio_risk(
        self,
        portfolio_id: int,
        benchmark_symbol: str = DEFAULT_BENCHMARK_SYMBOL,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Executes full portfolio risk analytics pipeline.
        Returns comprehensive dictionary of metrics, tables, and risk observations.
        """
        holdings = self.portfolio_service.get_holdings_summary(portfolio_id)
        if holdings.empty:
            return {"error": "Portfolio has no active holdings."}

        symbols = holdings["symbol"].tolist()
        quantities = holdings.set_index("symbol")["quantity"]
        weights = holdings.set_index("symbol")["weight"]

        # Fetch aligned price matrix
        prices_df = self.market_data_service.get_price_matrix(symbols, start_date, end_date)
        if prices_df.empty or len(prices_df) < 5:
            return {"error": "Insufficient historical price data for portfolio assets."}

        # Calculate buy-and-hold portfolio value trajectory
        port_eval = calculate_buy_and_hold_portfolio(prices_df, quantities)
        if port_eval.empty:
            return {"error": "Unable to calculate portfolio performance trajectory."}

        port_values = port_eval["portfolio_value"]
        port_returns = port_eval["daily_return"].dropna()

        # Returns and performance
        starting_val = float(port_values.iloc[0])
        ending_val = float(port_values.iloc[-1])
        total_pnl = ending_val - starting_val
        cum_return = (ending_val / starting_val) - 1.0 if starting_val > 0 else 0.0

        n_days = len(port_returns)
        cagr = calculate_annualized_return(ending_val, starting_val, n_days, DEFAULT_TRADING_DAYS)

        # Volatility
        ann_vol = calculate_annualized_volatility(port_returns, DEFAULT_TRADING_DAYS)
        downside_dev = calculate_downside_deviation(port_returns, risk_free_rate, DEFAULT_TRADING_DAYS)

        # Risk-adjusted ratios
        sharpe = calculate_sharpe_ratio(cagr, ann_vol, risk_free_rate)
        sortino = calculate_sortino_ratio(cagr, downside_dev, risk_free_rate)

        # Drawdowns
        dd_df = calculate_drawdown_series(port_values)
        mdd = calculate_max_drawdown(dd_df["drawdown"])
        avg_dd = calculate_average_drawdown(dd_df["drawdown"])
        calmar = calculate_calmar_ratio(cagr, mdd)

        # Benchmark Beta
        bench_prices = self.market_data_service.get_price_matrix([benchmark_symbol], start_date, end_date)
        if not bench_prices.empty and len(bench_prices) > 5:
            bench_ret = bench_prices[benchmark_symbol].pct_change().dropna()
            beta = calculate_beta(port_returns, bench_ret)
        else:
            beta = 1.0

        # VaR & CVaR (Historical)
        var_95 = calculate_historical_var(port_returns, 0.95)
        cvar_95 = calculate_historical_cvar(port_returns, 0.95)
        var_99 = calculate_historical_var(port_returns, 0.99)
        cvar_99 = calculate_historical_cvar(port_returns, 0.99)

        # Covariance matrix & Risk Contributions
        returns_df = self.market_data_service.get_return_matrix(symbols, start_date, end_date)
        ann_cov = calculate_covariance_matrix(returns_df, annualize=True, trading_days=DEFAULT_TRADING_DAYS)
        risk_contrib_df = calculate_risk_contributions(weights, ann_cov)

        # Verify identity: sum of component risks equals portfolio volatility
        sum_rc = float(risk_contrib_df["component_risk"].sum()) if not risk_contrib_df.empty else 0.0
        identity_discrepancy = abs(sum_rc - ann_vol)

        # Rolling volatility (21 days)
        rolling_vol = calculate_rolling_volatility(port_returns, window=21, trading_days=DEFAULT_TRADING_DAYS)

        # Correlation matrix
        corr_matrix = returns_df.corr() if not returns_df.empty else pd.DataFrame()

        # Generate automated risk observations
        observations = self._generate_risk_observations(
            holdings=holdings,
            risk_contrib_df=risk_contrib_df,
            corr_matrix=corr_matrix,
            ann_vol=ann_vol,
            mdd=mdd,
            sharpe=sharpe,
            beta=beta
        )

        # Persist summary risk metric to database
        self._save_risk_metric_record(
            portfolio_id=portfolio_id,
            start_d=prices_df.index[0].date(),
            end_d=prices_df.index[-1].date(),
            vol=ann_vol,
            ret=cagr,
            mdd=mdd,
            avg_dd=avg_dd,
            sharpe=sharpe,
            sortino=sortino,
            beta=beta,
            var95=var_95,
            cvar95=cvar_95,
            calmar=calmar,
        )

        return {
            "portfolio_id": portfolio_id,
            "period_start": prices_df.index[0].date(),
            "period_end": prices_df.index[-1].date(),
            "observation_days": n_days,
            "starting_value": starting_val,
            "current_value": ending_val,
            "total_pnl": total_pnl,
            "cumulative_return": cum_return,
            "annualized_return": cagr,
            "annualized_volatility": ann_vol,
            "downside_deviation": downside_dev,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "max_drawdown": mdd,
            "average_drawdown": avg_dd,
            "beta": beta,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "var_99": var_99,
            "cvar_99": cvar_99,
            "port_values": port_values,
            "port_returns": port_returns,
            "drawdown_df": dd_df,
            "rolling_volatility": rolling_vol,
            "covariance_matrix": ann_cov,
            "correlation_matrix": corr_matrix,
            "risk_contributions": risk_contrib_df,
            "sum_rc_identity": sum_rc,
            "identity_discrepancy": identity_discrepancy,
            "holdings": holdings,
            "observations": observations,
            "benchmark_prices": bench_prices,
        }

    def _generate_risk_observations(
        self,
        holdings: pd.DataFrame,
        risk_contrib_df: pd.DataFrame,
        corr_matrix: pd.DataFrame,
        ann_vol: float,
        mdd: float,
        sharpe: float,
        beta: float
    ) -> List[Dict[str, str]]:
        """
        Produces data-grounded observations without hand-waving or hallucination.
        """
        obs = []

        # 1. Concentration Risk
        if not holdings.empty:
            top_holding = holdings.iloc[0]
            if top_holding["weight"] > 0.30:
                obs.append({
                    "type": "Concentration Warning",
                    "level": "warning",
                    "text": f"High concentration in {top_holding['symbol']} ({top_holding['weight'] * 100:.1f}% of portfolio). A sharp move in this position will dominate overall portfolio variance."
                })

        # 2. Disproportionate Risk Contribution
        if not risk_contrib_df.empty:
            max_prc_row = risk_contrib_df.sort_values(by="percentage_risk_contribution", ascending=False).iloc[0]
            max_sym = max_prc_row.name
            max_prc = max_prc_row["percentage_risk_contribution"]
            max_wt = max_prc_row["weight"]
            if max_prc > max_wt * 1.5 and max_prc > 0.25:
                obs.append({
                    "type": "Elevated Risk Contribution",
                    "level": "warning",
                    "text": f"{max_sym} contributes {max_prc * 100:.1f}% of total portfolio volatility while accounting for only {max_wt * 100:.1f}% of invested capital."
                })

        # 3. High Correlation Cluster
        if not corr_matrix.empty and len(corr_matrix) > 1:
            high_corr_pairs = []
            cols = list(corr_matrix.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = corr_matrix.iloc[i, j]
                    if val >= 0.70:
                        high_corr_pairs.append((cols[i], cols[j], val))

            if high_corr_pairs:
                pair_strs = [f"{p[0]} & {p[1]} (r = {p[2]:.2f})" for p in high_corr_pairs[:2]]
                obs.append({
                    "type": "Correlated Exposure",
                    "level": "info",
                    "text": f"Strong co-movement detected between {', '.join(pair_strs)}. These assets offer limited diversification benefit during downturns."
                })

        # 4. Drawdown Depth
        if abs(mdd) > 0.20:
            obs.append({
                "type": "Downside Severity",
                "level": "warning",
                "text": f"Historical maximum drawdown of {abs(mdd) * 100:.1f}% indicates significant vulnerability to market contractions."
            })
        elif abs(mdd) < 0.10:
            obs.append({
                "type": "Resilient Drawdown Profile",
                "level": "positive",
                "text": f"Historical maximum drawdown is contained at {abs(mdd) * 100:.1f}%, reflecting defensive structural characteristics."
            })

        # 5. Beta Sensitivity
        if beta > 1.20:
            obs.append({
                "type": "High Market Beta",
                "level": "info",
                "text": f"Portfolio beta of {beta:.2f} indicates heightened cyclical sensitivity; expect swings ~{((beta - 1.0)*100):.0f}% larger than the NIFTY 50."
            })
        elif beta < 0.80:
            obs.append({
                "type": "Defensive Beta",
                "level": "positive",
                "text": f"Portfolio beta of {beta:.2f} confirms lower sensitivity to broad benchmark volatility."
            })

        return obs

    def _save_risk_metric_record(
        self,
        portfolio_id: int,
        start_d: date,
        end_d: date,
        vol: float,
        ret: float,
        mdd: float,
        avg_dd: float,
        sharpe: float,
        sortino: float,
        beta: float,
        var95: float,
        cvar95: float,
        calmar: float
    ):
        """Persists snapshot into risk_metrics table."""
        rec = RiskMetric(
            portfolio_id=portfolio_id,
            calculation_date=datetime.utcnow(),
            period_start=start_d,
            period_end=end_d,
            volatility=vol,
            annualized_return=ret,
            maximum_drawdown=mdd,
            average_drawdown=avg_dd,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            beta=beta,
            var_95=var95,
            cvar_95=cvar95,
            calmar_ratio=calmar,
        )
        self.db.add(rec)
        self.db.commit()
