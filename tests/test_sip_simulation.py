"""
Unit Tests for VARLYTIX Monte Carlo Monthly SIP & Goal Probability.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.monte_carlo import (
    run_historical_bootstrap_simulation,
    run_parametric_monte_carlo_simulation
)


def test_monte_carlo_monthly_sip_accumulation():
    # Synthetic return series
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100)
    rets = pd.DataFrame({
        "A": np.random.normal(0.0005, 0.01, 100),
        "B": np.random.normal(0.0004, 0.008, 100),
    }, index=dates)
    weights = pd.Series({"A": 0.5, "B": 0.5})

    initial_val = 100000.0
    monthly_sip = 10000.0
    horizon_days = 63  # Approx 3 months (3 SIP injections: day 21, 42, 63)
    goal_target = 140000.0

    res = run_historical_bootstrap_simulation(
        returns_df=rets,
        weights=weights,
        initial_value=initial_val,
        horizon_days=horizon_days,
        num_simulations=200,
        random_seed=42,
        monthly_sip=monthly_sip,
        goal_target_value=goal_target
    )

    # 3 SIP injections of 10,000 -> total invested = 100,000 + 30,000 = 130,000
    expected_invested = initial_val + (3 * monthly_sip)
    assert res["total_invested"] == expected_invested
    assert res["monthly_sip"] == monthly_sip
    assert res["goal_target_value"] == goal_target
    assert res["goal_probability"] is not None
    assert 0.0 <= res["goal_probability"] <= 1.0
    assert 0.0 <= res["loss_probability"] <= 1.0


def test_parametric_monte_carlo_sip_and_goal():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100)
    rets = pd.DataFrame({
        "A": np.random.normal(0.0006, 0.01, 100),
        "B": np.random.normal(0.0004, 0.009, 100),
    }, index=dates)
    weights = pd.Series({"A": 0.6, "B": 0.4})

    initial_val = 200000.0
    monthly_sip = 25000.0
    horizon_days = 42  # 2 SIP injections: day 21 and 42
    goal_target = 270000.0

    res = run_parametric_monte_carlo_simulation(
        returns_df=rets,
        weights=weights,
        initial_value=initial_val,
        horizon_days=horizon_days,
        num_simulations=200,
        random_seed=42,
        monthly_sip=monthly_sip,
        goal_target_value=goal_target
    )

    expected_invested = initial_val + (2 * monthly_sip)
    assert res["total_invested"] == expected_invested
    assert res["goal_probability"] is not None
    assert 0.0 <= res["goal_probability"] <= 1.0
