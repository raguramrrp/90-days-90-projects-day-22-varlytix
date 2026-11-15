"""
Quantitative Volatility and Risk-Adjusted Ratios for VARLYTIX.
Calculates annualized volatility, downside deviation, rolling volatility,
Sharpe ratio, and Sortino ratio.
"""

from typing import Union
import numpy as np
import pandas as pd


def calculate_daily_volatility(returns: pd.Series) -> float:
    """
    Calculates sample standard deviation of daily returns:
    s = sqrt( 1/(N-1) * sum((r_i - mean)^2) )
    """
    clean = returns.dropna()
    if len(clean) < 2:
        return 0.0
    return float(clean.std(ddof=1))


def calculate_annualized_volatility(returns: pd.Series, trading_days: int = 252) -> float:
    """
    Annualizes daily standard deviation:
    sigma_ann = sigma_daily * sqrt(252)
    """
    daily_vol = calculate_daily_volatility(returns)
    return float(daily_vol * np.sqrt(trading_days))


def calculate_downside_deviation(
    returns: pd.Series,
    target_rate: float = 0.0,
    trading_days: int = 252
) -> float:
    """
    Calculates annualized downside deviation (semi-deviation below target):
    DD = sqrt( 1/N * sum( min(r_t - target, 0)^2 ) ) * sqrt(252)
    """
    clean = returns.dropna()
    if len(clean) == 0:
        return 0.0

    daily_target = target_rate / trading_days
    downside_diff = np.minimum(clean - daily_target, 0.0)
    downside_variance = np.mean(downside_diff ** 2)
    daily_downside_dev = np.sqrt(downside_variance)
    return float(daily_downside_dev * np.sqrt(trading_days))


def calculate_rolling_volatility(
    returns: pd.Series,
    window: int = 21,
    trading_days: int = 252
) -> pd.Series:
    """
    Calculates rolling annualized volatility over a moving window (default 21 trading days):
    rolling_sigma = rolling_std * sqrt(252)
    """
    clean = returns.dropna()
    if len(clean) < window:
        return pd.Series(dtype=float)
    return (clean.rolling(window=window).std(ddof=1) * np.sqrt(trading_days)).dropna()


def calculate_sharpe_ratio(
    annualized_return: float,
    annualized_volatility: float,
    risk_free_rate: float = 0.065
) -> float:
    """
    Calculates Sharpe Ratio:
    Sharpe = (Annualized Return - Risk Free Rate) / Annualized Volatility
    """
    if annualized_volatility <= 1e-9:
        return 0.0
    return float((annualized_return - risk_free_rate) / annualized_volatility)


def calculate_sortino_ratio(
    annualized_return: float,
    downside_deviation: float,
    risk_free_rate: float = 0.065
) -> float:
    """
    Calculates Sortino Ratio:
    Sortino = (Annualized Return - Risk Free Rate) / Downside Deviation
    """
    if downside_deviation <= 1e-9:
        return 0.0
    return float((annualized_return - risk_free_rate) / downside_deviation)
