"""
Unit Tests for Covariance, Correlation, and Component Risk Contributions.
Validates Euler risk decomposition identity sum(RC_i) == sigma_p.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.covariance import (
    calculate_covariance_matrix, calculate_portfolio_variance_and_volatility,
    calculate_risk_contributions
)


def test_covariance_and_correlation():
    np.random.seed(42)
    t = 100
    r1 = np.random.normal(0, 0.02, t)
    r2 = 0.8 * r1 + np.random.normal(0, 0.01, t)  # High positive correlation
    r3 = -0.9 * r1 + np.random.normal(0, 0.005, t) # Negative correlation

    df = pd.DataFrame({"A": r1, "B": r2, "C": r3})
    corr = df.corr()

    assert corr.loc["A", "B"] > 0.70
    assert corr.loc["A", "C"] < -0.80
    assert pytest.approx(corr.loc["A", "A"], 1e-6) == 1.0


def test_euler_risk_contribution_identity():
    """
    CRITICAL QUANT TEST:
    For any weights w and covariance matrix Sigma:
    sum(Component Risk_i) must strictly equal total portfolio volatility sigma_p.
    """
    np.random.seed(123)
    n_assets = 4
    n_days = 250

    # Random returns
    returns = np.random.normal(0.0005, 0.015, (n_days, n_assets))
    df_returns = pd.DataFrame(returns, columns=["A", "B", "C", "D"])

    cov_matrix = calculate_covariance_matrix(df_returns, annualize=True, trading_days=252)

    # Unequal portfolio weights
    weights = pd.Series({"A": 0.40, "B": 0.30, "C": 0.20, "D": 0.10})

    port_var, port_vol = calculate_portfolio_variance_and_volatility(weights, cov_matrix)
    assert port_vol > 0.0

    rc_df = calculate_risk_contributions(weights, cov_matrix)

    # 1. Check sum of component risk equals total portfolio volatility
    sum_rc = rc_df["component_risk"].sum()
    assert pytest.approx(sum_rc, 1e-6) == port_vol

    # 2. Check sum of percentage risk contribution equals 1.0 (100%)
    sum_prc = rc_df["percentage_risk_contribution"].sum()
    assert pytest.approx(sum_prc, 1e-6) == 1.0

    # 3. Check all assets present in result
    assert list(rc_df.index) == ["A", "B", "C", "D"]
