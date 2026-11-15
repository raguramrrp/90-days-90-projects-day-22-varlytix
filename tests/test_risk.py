"""
Unit Tests for Quantitative Risk Metrics.
Validates Annualized Volatility, Drawdown, Sharpe, Sortino, VaR, CVaR, and Beta.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.volatility import (
    calculate_daily_volatility, calculate_annualized_volatility,
    calculate_sharpe_ratio, calculate_sortino_ratio, calculate_downside_deviation
)
from analytics.drawdown import (
    calculate_drawdown_series, calculate_max_drawdown, calculate_calmar_ratio
)
from analytics.var_cvar import (
    calculate_historical_var, calculate_historical_cvar, calculate_beta
)


def test_volatility_and_sharpe():
    # Known series with std ~ 0.01 (1%)
    np.random.seed(42)
    daily_rets = pd.Series(np.random.normal(0.0008, 0.01, 252))

    daily_vol = calculate_daily_volatility(daily_rets)
    ann_vol = calculate_annualized_volatility(daily_rets, trading_days=252)

    assert pytest.approx(daily_vol, abs=0.002) == 0.01
    assert pytest.approx(ann_vol, 1e-4) == daily_vol * np.sqrt(252)

    # Sharpe ratio with 15% return and 6.5% risk free
    sharpe = calculate_sharpe_ratio(annualized_return=0.15, annualized_volatility=ann_vol, risk_free_rate=0.065)
    expected_sharpe = (0.15 - 0.065) / ann_vol
    assert pytest.approx(sharpe, 1e-4) == expected_sharpe


def test_drawdown_and_calmar():
    # Price path: 100 -> 120 -> 90 -> 110 -> 80
    prices = pd.Series([100.0, 120.0, 90.0, 110.0, 80.0])
    dd_df = calculate_drawdown_series(prices)

    # Peak: 100, 120, 120, 120, 120
    # DD: (100/100-1)=0, (120/120-1)=0, (90/120-1)=-0.25, (110/120-1)=-0.0833, (80/120-1)=-0.3333
    mdd = calculate_max_drawdown(dd_df["drawdown"])
    assert pytest.approx(mdd, 1e-4) == -0.333333

    calmar = calculate_calmar_ratio(annualized_return=0.10, max_drawdown=mdd)
    assert pytest.approx(calmar, 1e-3) == 0.10 / 0.333333


def test_historical_var_and_cvar():
    # Create 100 returns sorted: -0.10, -0.09, ..., 0.0
    rets = pd.Series(np.linspace(-0.10, 0.08, 100))

    # At 95% confidence, alpha = 5%. 5th percentile is around -0.09
    var_95 = calculate_historical_var(rets, confidence_level=0.95)
    assert var_95 > 0.08  # Positive loss threshold

    # CVaR is mean of values <= -var
    cvar_95 = calculate_historical_cvar(rets, confidence_level=0.95)
    assert cvar_95 >= var_95  # Tail loss is always >= VaR


def test_benchmark_beta():
    np.random.seed(42)
    bench_rets = pd.Series(np.random.normal(0.0005, 0.012, 100))
    # Portfolio is exactly 1.5x benchmark + noise
    noise = np.random.normal(0, 0.002, 100)
    port_rets = 1.5 * bench_rets + noise

    beta = calculate_beta(port_rets, bench_rets)
    assert pytest.approx(beta, 0.05) == 1.5
