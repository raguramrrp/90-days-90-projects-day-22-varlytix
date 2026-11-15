"""
Unit Tests for Quantitative Return Calculations.
Validates simple returns, log returns, cumulative compounding, CAGR, and buy-and-hold logic.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.returns import (
    calculate_simple_returns, calculate_log_returns,
    calculate_cumulative_returns, calculate_annualized_return,
    calculate_buy_and_hold_portfolio, calculate_rebalanced_portfolio
)


def test_simple_and_log_returns():
    prices = pd.Series([100.0, 110.0, 104.5, 114.95])

    simple_ret = calculate_simple_returns(prices)
    assert len(simple_ret) == 3
    assert pytest.approx(simple_ret.iloc[0], 1e-4) == 0.10     # (110 - 100)/100
    assert pytest.approx(simple_ret.iloc[1], 1e-4) == -0.05    # (104.5 - 110)/110
    assert pytest.approx(simple_ret.iloc[2], 1e-4) == 0.10     # (114.95 - 104.5)/104.5

    log_ret = calculate_log_returns(prices)
    assert len(log_ret) == 3
    assert pytest.approx(log_ret.iloc[0], 1e-4) == np.log(1.10)


def test_cumulative_returns():
    returns = pd.Series([0.10, -0.05, 0.10])
    cum_ret = calculate_cumulative_returns(returns)
    # (1 + 0.10) * (1 - 0.05) * (1 + 0.10) - 1 = 1.10 * 0.95 * 1.10 - 1 = 1.1495 - 1 = 0.1495
    assert pytest.approx(cum_ret.iloc[-1], 1e-4) == 0.1495


def test_annualized_cagr_calculation():
    # Double money in 252 trading days (1 year) -> CAGR = 100%
    cagr_1yr = calculate_annualized_return(ending_value=200.0, starting_value=100.0, num_days=252)
    assert pytest.approx(cagr_1yr, 1e-4) == 1.0

    # 44% gain in 504 trading days (2 years) -> (1.44)**(1/2) - 1 = 1.20 - 1 = 20%
    cagr_2yr = calculate_annualized_return(ending_value=144.0, starting_value=100.0, num_days=504)
    assert pytest.approx(cagr_2yr, 1e-4) == 0.20


def test_buy_and_hold_vs_rebalanced():
    # 2 assets over 3 days
    prices = pd.DataFrame({
        "A": [100.0, 120.0, 150.0],
        "B": [100.0, 80.0, 70.0],
    }, index=pd.date_range("2024-01-01", periods=3))

    quantities = pd.Series({"A": 10.0, "B": 10.0})

    # Day 0: Val = 10*100 + 10*100 = 2000
    # Day 1: Val = 10*120 + 10*80 = 2000 (0% return)
    # Day 2: Val = 10*150 + 10*70 = 2200 (+10% return)
    bh = calculate_buy_and_hold_portfolio(prices, quantities)
    assert len(bh) == 2
    assert pytest.approx(bh["daily_return"].iloc[0], 1e-4) == 0.0
    assert pytest.approx(bh["daily_return"].iloc[1], 1e-4) == 0.10
