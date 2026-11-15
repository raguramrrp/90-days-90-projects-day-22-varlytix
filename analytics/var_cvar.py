"""
Value-at-Risk (VaR), Conditional VaR (CVaR), and Beta Analytics for SIGMORA.
Calculates historical quantile-based VaR & CVaR, parametric VaR, and benchmark Beta.
"""

from typing import Union, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def calculate_historical_var(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculates Historical Value at Risk (VaR) as a positive loss threshold:
    VaR = -Quantile(returns, 1 - confidence_level)
    E.g. at 95% confidence, if 5th percentile is -0.024, VaR = +0.024 (2.4% loss).
    """
    clean = returns.dropna()
    if len(clean) < 10:
        return 0.0

    alpha = 1.0 - confidence_level
    var_threshold = -float(np.percentile(clean, alpha * 100))
    return max(0.0, var_threshold)


def calculate_historical_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculates Historical Conditional Value at Risk (CVaR / Expected Shortfall):
    CVaR = -Mean(returns <= -VaR)
    The average expected loss beyond the VaR threshold in the left tail.
    """
    clean = returns.dropna()
    if len(clean) < 10:
        return 0.0

    alpha = 1.0 - confidence_level
    cutoff = np.percentile(clean, alpha * 100)
    tail_returns = clean[clean <= cutoff]

    if len(tail_returns) == 0:
        return max(0.0, -float(cutoff))

    cvar_threshold = -float(tail_returns.mean())
    return max(0.0, cvar_threshold)


def calculate_parametric_var(
    mean_return: float,
    volatility: float,
    confidence_level: float = 0.95
) -> float:
    """
    Calculates Parametric Gaussian Value at Risk:
    VaR = -(mu + z * sigma)
    where z is standard normal quantile for (1 - confidence_level).
    """
    z = stats.norm.ppf(1.0 - confidence_level)
    var_threshold = -(mean_return + z * volatility)
    return max(0.0, float(var_threshold))


def calculate_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series
) -> float:
    """
    Calculates CAPM Beta of portfolio returns against benchmark returns:
    Beta = Covariance(r_p, r_b) / Variance(r_b)
    Dates are strictly aligned.
    """
    aligned = pd.concat([portfolio_returns, benchmark_returns], axis=1, join="inner").dropna()
    if aligned.shape[0] < 10:
        return 1.0

    cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1], ddof=1)
    port_bench_cov = cov_matrix[0, 1]
    bench_var = cov_matrix[1, 1]

    if bench_var <= 1e-12:
        return 1.0

    return float(port_bench_cov / bench_var)
