"""
Unit Tests for Monte Carlo Simulation Engine.
Validates Historical Bootstrap, Multivariate Parametric, Percentile Ordering, and Seed Reproducibility.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.monte_carlo import (
    run_historical_bootstrap_simulation,
    run_parametric_monte_carlo_simulation
)


@pytest.fixture
def sample_market_data():
    np.random.seed(42)
    n_days = 200
    r1 = np.random.normal(0.0006, 0.012, n_days)
    r2 = 0.5 * r1 + np.random.normal(0.0004, 0.010, n_days)
    df = pd.DataFrame({"A": r1, "B": r2})
    weights = pd.Series({"A": 0.60, "B": 0.40})
    return df, weights


def test_historical_bootstrap_reproducibility_and_bounds(sample_market_data):
    df_returns, weights = sample_market_data

    res1 = run_historical_bootstrap_simulation(
        returns_df=df_returns,
        weights=weights,
        initial_value=100000.0,
        horizon_days=63,
        num_simulations=500,
        random_seed=777
    )

    res2 = run_historical_bootstrap_simulation(
        returns_df=df_returns,
        weights=weights,
        initial_value=100000.0,
        horizon_days=63,
        num_simulations=500,
        random_seed=777
    )

    # Identical seed must produce bitwise identical summary percentiles
    assert res1["summary_percentiles"] == res2["summary_percentiles"]

    # Monotonic percentile order: 5th <= 25th <= 50th <= 75th <= 95th
    p = res1["summary_percentiles"]
    assert p[5] <= p[25] <= p[50] <= p[75] <= p[95]

    # Non-negative portfolio values
    assert (res1["ending_values"] > 0).all()

    # Loss probability is a valid probability in [0, 1]
    assert 0.0 <= res1["loss_probability"] <= 1.0


def test_parametric_monte_carlo_simulation(sample_market_data):
    df_returns, weights = sample_market_data

    res = run_parametric_monte_carlo_simulation(
        returns_df=df_returns,
        weights=weights,
        initial_value=250000.0,
        horizon_days=126,
        num_simulations=500,
        random_seed=101
    )

    p = res["summary_percentiles"]
    assert p[5] <= p[25] <= p[50] <= p[75] <= p[95]
    assert res["initial_value"] == 250000.0
    assert len(res["percentiles_over_time"]["p50"]) == 127  # t=0 to t=126
