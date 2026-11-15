"""
Quantitative Return Analytics Module for VARLYTIX.
Calculates simple returns, log returns, cumulative returns,
geometric annualized returns, and buy-and-hold vs rebalanced portfolio trajectories.
"""

from typing import Union, List, Optional
import numpy as np
import pandas as pd


def calculate_simple_returns(prices: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculates percentage simple returns:
    r_t = (P_t / P_{t-1}) - 1
    First observation is dropped (NaN).
    """
    if prices is None or len(prices) < 2:
        return pd.Series(dtype=float) if isinstance(prices, pd.Series) else pd.DataFrame()
    return prices.pct_change().dropna()


def calculate_log_returns(prices: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculates continuously compounded log returns:
    r_t = ln(P_t / P_{t-1})
    """
    if prices is None or len(prices) < 2:
        return pd.Series(dtype=float) if isinstance(prices, pd.Series) else pd.DataFrame()
    return np.log(prices / prices.shift(1)).dropna()


def calculate_cumulative_returns(returns: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculates cumulative wealth index starting at 1.0 (or 0% gain):
    W_t = prod(1 + r_i) - 1
    """
    if returns is None or len(returns) == 0:
        return pd.Series(dtype=float) if isinstance(returns, pd.Series) else pd.DataFrame()
    return (1.0 + returns).cumprod() - 1.0


def calculate_annualized_return(
    ending_value: float,
    starting_value: float,
    num_days: int,
    trading_days: int = 252
) -> float:
    """
    Calculates compound geometric annualized return (CAGR):
    CAGR = (Ending Value / Starting Value) ** (252 / N) - 1
    """
    if starting_value <= 0 or ending_value <= 0 or num_days <= 0:
        return 0.0
    return float((ending_value / starting_value) ** (trading_days / num_days) - 1.0)


def calculate_buy_and_hold_portfolio(
    prices_df: pd.DataFrame,
    quantities: pd.Series
) -> pd.DataFrame:
    """
    Calculates buy-and-hold portfolio value where weights naturally drift
    with changing asset market prices (no daily rebalancing):
    V_t = sum(q_i * P_{i,t})
    Returns a DataFrame with total portfolio value, daily return, and weight series.
    """
    if prices_df.empty or quantities.empty:
        return pd.DataFrame()

    # Align assets
    common_assets = [col for col in prices_df.columns if col in quantities.index]
    if not common_assets:
        return pd.DataFrame()

    aligned_prices = prices_df[common_assets]
    aligned_qty = quantities[common_assets]

    # Position value matrix: Date x Asset
    position_values = aligned_prices.mul(aligned_qty, axis=1)
    total_value = position_values.sum(axis=1)

    # Weights drift
    weights = position_values.div(total_value, axis=0)

    # Daily portfolio returns
    daily_returns = total_value.pct_change().dropna()

    result = pd.DataFrame({
        "portfolio_value": total_value,
        "daily_return": total_value.pct_change(),
    })
    return result.dropna()


def calculate_rebalanced_portfolio(
    returns_df: pd.DataFrame,
    target_weights: pd.Series
) -> pd.Series:
    """
    Calculates daily rebalanced portfolio returns:
    r_{p,t} = sum(w_i * r_{i,t})
    Weights are held constant through daily rebalancing.
    """
    if returns_df.empty or target_weights.empty:
        return pd.Series(dtype=float)

    common_assets = [col for col in returns_df.columns if col in target_weights.index]
    if not common_assets:
        return pd.Series(dtype=float)

    norm_weights = target_weights[common_assets] / target_weights[common_assets].sum()
    portfolio_returns = returns_df[common_assets].dot(norm_weights)
    return portfolio_returns
