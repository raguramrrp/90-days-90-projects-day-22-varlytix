"""
Unit Tests for Portfolio Optimization and Efficient Frontier Analytics.
Validates constraints, weight sum identities, solver convergence, and volatility minimization.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.optimization import (
    optimize_minimum_variance, optimize_maximum_sharpe, generate_efficient_frontier
)


@pytest.fixture
def optimization_data():
    mean_returns = pd.Series({"A": 0.12, "B": 0.18, "C": 0.08})
    # Covariance matrix with distinct variances and positive correlations
    cov_matrix = pd.DataFrame([
        [0.04, 0.015, 0.005],
        [0.015, 0.09, 0.01],
        [0.005, 0.01, 0.02]
    ], index=["A", "B", "C"], columns=["A", "B", "C"])
    return mean_returns, cov_matrix


def test_minimum_variance_optimization(optimization_data):
    mean_returns, cov_matrix = optimization_data

    res = optimize_minimum_variance(mean_returns, cov_matrix, max_weight=0.60)

    assert res["success"] is True
    weights = res["weights"]

    # Sum of weights must equal 1.0
    assert pytest.approx(weights.sum(), 1e-5) == 1.0

    # Upper bound of 0.60 must be respected
    assert (weights <= 0.60001).all()

    # Long-only constraint (non-negative)
    assert (weights >= -1e-6).all()

    # Min variance volatility must be <= equal weight portfolio volatility
    eq_w = np.array([1/3, 1/3, 1/3])
    eq_vol = np.sqrt(eq_w.T @ cov_matrix.values @ eq_w)
    assert res["volatility"] <= eq_vol + 1e-6


def test_maximum_sharpe_optimization(optimization_data):
    mean_returns, cov_matrix = optimization_data

    res = optimize_maximum_sharpe(mean_returns, cov_matrix, risk_free_rate=0.065, max_weight=0.70)

    assert res["success"] is True
    weights = res["weights"]
    assert pytest.approx(weights.sum(), 1e-5) == 1.0
    assert (weights <= 0.70001).all()
    assert (weights >= -1e-6).all()
    assert res["sharpe_ratio"] > 0.0


def test_efficient_frontier_generation(optimization_data):
    mean_returns, cov_matrix = optimization_data

    frontier = generate_efficient_frontier(mean_returns, cov_matrix, num_points=15)
    assert not frontier.empty
    assert "return" in frontier.columns
    assert "volatility" in frontier.columns
    assert len(frontier) >= 10
