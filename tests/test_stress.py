"""
Unit Tests for Stress Testing Engine.
Validates uniform market shocks, sector-specific shocks, and custom asset scenarios.
"""

import pytest
import pandas as pd
from analytics.stress_testing import (
    apply_uniform_shock, apply_sector_shock, apply_custom_shocks
)


@pytest.fixture
def sample_positions():
    return pd.DataFrame({
        "symbol": ["HDFC", "TCS", "ITC"],
        "sector": ["Financials", "Technology", "Consumer"],
        "current_value": [50000.0, 30000.0, 20000.0],
        "weight": [0.50, 0.30, 0.20]
    })


def test_uniform_market_shock(sample_positions):
    # Apply -20% uniform market drop
    res = apply_uniform_shock(sample_positions, shock_pct=-0.20)

    assert res["original_value"] == 100000.0
    assert pytest.approx(res["stressed_value"], 1e-4) == 80000.0
    assert pytest.approx(res["portfolio_loss"], 1e-4) == -20000.0
    assert pytest.approx(res["portfolio_return"], 1e-4) == -0.20

    # Total loss contribution should sum to 100%
    assert pytest.approx(res["asset_breakdown"]["loss_contribution_pct"].sum(), 1e-4) == 1.0


def test_sector_shock(sample_positions):
    sector_shocks = {
        "Financials": -0.30,   # HDFC: 50000 * 0.70 = 35000 (loss -15000)
        "Technology": -0.10,   # TCS: 30000 * 0.90 = 27000 (loss -3000)
    }
    # ITC falls back to default -5% -> 20000 * 0.95 = 19000 (loss -1000)
    # Total stressed = 35000 + 27000 + 19000 = 81000 (total loss -19000 = -19%)
    res = apply_sector_shock(sample_positions, sector_shocks=sector_shocks, default_shock=-0.05)

    assert res["original_value"] == 100000.0
    assert pytest.approx(res["stressed_value"], 1e-4) == 81000.0
    assert pytest.approx(res["portfolio_return"], 1e-4) == -0.19


def test_custom_shocks(sample_positions):
    custom = {
        "HDFC": -0.10,
        "TCS": 0.05,
        "ITC": 0.00
    }
    # HDFC: 50k -> 45k (-5k)
    # TCS: 30k -> 31.5k (+1.5k)
    # ITC: 20k -> 20k (0)
    # Stressed total = 96.5k (-3.5k)
    res = apply_custom_shocks(sample_positions, custom)
    assert pytest.approx(res["stressed_value"], 1e-4) == 96500.0
    assert pytest.approx(res["portfolio_loss"], 1e-4) == -3500.0
