"""
Portfolio Optimization Analytics Module for VARLYTIX.
Uses SciPy SLSQP optimization to compute:
- Minimum Variance Portfolio
- Maximum Sharpe Ratio Portfolio
- Target Volatility Portfolio
- Efficient Frontier curve
Enforces long-only constraints (w_i >= 0), sum(w) = 1, and optional position limits.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def optimize_minimum_variance(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    max_weight: float = 1.0,
    min_weight: float = 0.0
) -> Dict[str, Any]:
    """
    Finds weights that minimize annualized portfolio variance:
    min_w w^T * Sigma * w
    subject to sum(w) = 1, min_weight <= w_i <= max_weight.
    """
    assets = list(cov_matrix.columns)
    n = len(assets)
    sigma = cov_matrix.values
    mu = mean_returns[assets].values

    w0 = np.ones(n) / n
    bounds = tuple((min_weight, max_weight) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})

    def objective(w):
        return w.T @ sigma @ w

    res = minimize(
        objective,
        w0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )

    if not res.success:
        return {"success": False, "message": res.message}

    opt_weights = pd.Series(res.x, index=assets)
    # Clean tiny numerical noise
    opt_weights = opt_weights.clip(lower=0.0)
    opt_weights = opt_weights / opt_weights.sum()

    exp_return = float(opt_weights.values @ mu)
    exp_vol = float(np.sqrt(opt_weights.values @ sigma @ opt_weights.values))

    return {
        "success": True,
        "objective": "Minimum Variance",
        "weights": opt_weights,
        "expected_return": exp_return,
        "volatility": exp_vol,
        "sharpe_ratio": (exp_return - 0.065) / exp_vol if exp_vol > 0 else 0.0,
    }


def optimize_maximum_sharpe(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.065,
    max_weight: float = 1.0,
    min_weight: float = 0.0
) -> Dict[str, Any]:
    """
    Finds weights that maximize the Sharpe ratio:
    max_w (w^T * mu - Rf) / sqrt(w^T * Sigma * w)
    subject to sum(w) = 1, min_weight <= w_i <= max_weight.
    """
    assets = list(cov_matrix.columns)
    n = len(assets)
    sigma = cov_matrix.values
    mu = mean_returns[assets].values

    w0 = np.ones(n) / n
    bounds = tuple((min_weight, max_weight) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})

    def neg_sharpe(w):
        port_ret = w.T @ mu
        port_vol = np.sqrt(w.T @ sigma @ w)
        if port_vol <= 1e-9:
            return 0.0
        return -(port_ret - risk_free_rate) / port_vol

    res = minimize(
        neg_sharpe,
        w0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )

    if not res.success:
        # Fall back to min variance
        return optimize_minimum_variance(mean_returns, cov_matrix, max_weight, min_weight)

    opt_weights = pd.Series(res.x, index=assets)
    opt_weights = opt_weights.clip(lower=0.0)
    opt_weights = opt_weights / opt_weights.sum()

    exp_return = float(opt_weights.values @ mu)
    exp_vol = float(np.sqrt(opt_weights.values @ sigma @ opt_weights.values))
    sharpe = float((exp_return - risk_free_rate) / exp_vol) if exp_vol > 0 else 0.0

    return {
        "success": True,
        "objective": "Maximum Sharpe Ratio",
        "weights": opt_weights,
        "expected_return": exp_return,
        "volatility": exp_vol,
        "sharpe_ratio": sharpe,
    }


def generate_efficient_frontier(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    num_points: int = 25,
    max_weight: float = 1.0,
    min_weight: float = 0.0
) -> pd.DataFrame:
    """
    Generates the Markowitz Efficient Frontier curve.
    Returns DataFrame of points with ['return', 'volatility', 'sharpe'].
    """
    assets = list(cov_matrix.columns)
    n = len(assets)
    sigma = cov_matrix.values
    mu = mean_returns[assets].values

    # Find min and max target returns from individual assets
    min_ret = float(mu.min())
    max_ret = float(mu.max())

    if abs(max_ret - min_ret) < 1e-6:
        return pd.DataFrame()

    target_returns = np.linspace(min_ret, max_ret, num_points)
    frontier_points = []

    w0 = np.ones(n) / n
    bounds = tuple((min_weight, max_weight) for _ in range(n))

    for target in target_returns:
        constraints = (
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
            {'type': 'eq', 'fun': lambda w, t=target: (w.T @ mu) - t}
        )

        res = minimize(
            lambda w: w.T @ sigma @ w,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 300, 'ftol': 1e-7}
        )

        if res.success:
            vol = float(np.sqrt(res.fun))
            sharpe = (target - 0.065) / vol if vol > 0 else 0.0
            frontier_points.append({
                "return": target,
                "volatility": vol,
                "sharpe": sharpe,
            })

    return pd.DataFrame(frontier_points)
