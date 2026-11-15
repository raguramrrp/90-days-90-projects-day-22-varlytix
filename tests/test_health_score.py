"""
Unit Tests for VARLYTIX Portfolio Health Score & Executive Summary Engine.
"""

import pytest
import pandas as pd
from analytics.health_score import compute_health_score


def test_health_score_balanced_portfolio():
    # Mock realistic healthy portfolio risk profile
    holdings = pd.DataFrame([
        {"symbol": "RELIANCE", "name": "Reliance", "sector": "Energy", "weight": 0.20},
        {"symbol": "TCS", "name": "TCS", "sector": "Technology", "weight": 0.20},
        {"symbol": "HDFC", "name": "HDFC Bank", "sector": "Financials", "weight": 0.20},
        {"symbol": "GOLDBEES", "name": "Gold ETF", "sector": "Commodity / Gold ETF", "weight": 0.20},
        {"symbol": "LIQUIDBEES", "name": "Liquid ETF", "sector": "Debt / Cash Alternative", "weight": 0.20},
    ])

    risk_data = {
        "holdings": holdings,
        "max_drawdown": -0.12,
        "sharpe_ratio": 1.15,
        "cvar_95": -0.018,
        "annualized_volatility": 0.13,
        "current_value": 1500000.0,
        "starting_value": 1200000.0,
        "cumulative_return": 0.25,
    }

    res = compute_health_score(risk_data)

    assert "total_score" in res
    assert 0 <= res["total_score"] <= 100
    assert res["total_score"] >= 75  # Balanced multi-asset should score high
    assert res["grade"] in ["A", "B"]

    # Verify 4 pillars
    pillars = res["pillars"]
    assert "diversification" in pillars
    assert "downside_resilience" in pillars
    assert "risk_efficiency" in pillars
    assert "tail_risk" in pillars

    # Verify 3-bullet executive summary
    exec_summary = res["executive_summary"]
    assert "strength" in exec_summary and len(exec_summary["strength"]) > 10
    assert "blindspot" in exec_summary and len(exec_summary["blindspot"]) > 10
    assert "stress_reality" in exec_summary and len(exec_summary["stress_reality"]) > 10
    assert "₹" in exec_summary["stress_reality"]


def test_health_score_concentrated_risky_portfolio():
    # Mock high-risk, concentrated, high-drawdown portfolio
    holdings = pd.DataFrame([
        {"symbol": "SPECULATIVE", "name": "Speculative Stock", "sector": "Smallcap", "weight": 0.85},
        {"symbol": "OTHER", "name": "Other", "sector": "Tech", "weight": 0.15},
    ])

    risk_data = {
        "holdings": holdings,
        "max_drawdown": -0.45,
        "sharpe_ratio": 0.10,
        "cvar_95": -0.048,
        "annualized_volatility": 0.32,
        "current_value": 500000.0,
        "starting_value": 600000.0,
        "cumulative_return": -0.16,
    }

    res = compute_health_score(risk_data)

    assert res["total_score"] <= 55
    assert res["grade"] in ["C", "D"]
    assert "Single-Stock Concentration" in res["executive_summary"]["blindspot"]
