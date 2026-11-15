"""
Stress Testing Analytics Module for VARLYTIX.
Calculates portfolio and asset-level impacts under predefined, sector-specific,
historical, and custom shock scenarios.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def apply_uniform_shock(
    positions_df: pd.DataFrame,
    shock_pct: float
) -> Dict[str, Any]:
    """
    Applies a uniform market-wide percentage shock to all assets.
    positions_df must contain: ['symbol', 'current_value', 'weight']
    """
    if positions_df.empty:
        return {}

    df = positions_df.copy()
    original_value = df["current_value"].sum()
    df["shock_pct"] = shock_pct
    df["stressed_value"] = df["current_value"] * (1.0 + shock_pct)
    df["value_loss"] = df["stressed_value"] - df["current_value"]

    stressed_total = df["stressed_value"].sum()
    portfolio_return = (stressed_total / original_value) - 1.0 if original_value > 0 else 0.0

    df["new_weight"] = df["stressed_value"] / stressed_total if stressed_total > 0 else 0.0
    df["loss_contribution_pct"] = df["value_loss"] / (stressed_total - original_value) if (stressed_total - original_value) != 0 else 0.0

    return {
        "scenario_type": "Uniform Shock",
        "original_value": float(original_value),
        "stressed_value": float(stressed_total),
        "portfolio_loss": float(stressed_total - original_value),
        "portfolio_return": float(portfolio_return),
        "asset_breakdown": df,
    }


def apply_sector_shock(
    positions_df: pd.DataFrame,
    sector_shocks: Dict[str, float],
    default_shock: float = -0.05
) -> Dict[str, Any]:
    """
    Applies sector-specific percentage shocks.
    positions_df must contain: ['symbol', 'current_value', 'sector', 'weight']
    """
    if positions_df.empty:
        return {}

    df = positions_df.copy()
    original_value = df["current_value"].sum()

    # Map shocks by sector
    shocks = []
    for _, row in df.iterrows():
        sec = row.get("sector", "Other")
        shocks.append(sector_shocks.get(sec, default_shock))

    df["shock_pct"] = shocks
    df["stressed_value"] = df["current_value"] * (1.0 + df["shock_pct"])
    df["value_loss"] = df["stressed_value"] - df["current_value"]

    stressed_total = df["stressed_value"].sum()
    portfolio_return = (stressed_total / original_value) - 1.0 if original_value > 0 else 0.0

    df["new_weight"] = df["stressed_value"] / stressed_total if stressed_total > 0 else 0.0
    total_loss = stressed_total - original_value
    df["loss_contribution_pct"] = df["value_loss"] / total_loss if total_loss != 0 else 0.0

    return {
        "scenario_type": "Sector Shock",
        "original_value": float(original_value),
        "stressed_value": float(stressed_total),
        "portfolio_loss": float(total_loss),
        "portfolio_return": float(portfolio_return),
        "asset_breakdown": df,
    }


def apply_custom_shocks(
    positions_df: pd.DataFrame,
    custom_shocks: Dict[str, float]
) -> Dict[str, Any]:
    """
    Applies user-defined percentage shocks per individual holding.
    custom_shocks maps symbol -> shock_pct (e.g. {'RELIANCE': -0.15})
    """
    if positions_df.empty:
        return {}

    df = positions_df.copy()
    original_value = df["current_value"].sum()

    shocks = [custom_shocks.get(sym, 0.0) for sym in df["symbol"]]
    df["shock_pct"] = shocks
    df["stressed_value"] = df["current_value"] * (1.0 + df["shock_pct"])
    df["value_loss"] = df["stressed_value"] - df["current_value"]

    stressed_total = df["stressed_value"].sum()
    portfolio_return = (stressed_total / original_value) - 1.0 if original_value > 0 else 0.0

    df["new_weight"] = df["stressed_value"] / stressed_total if stressed_total > 0 else 0.0
    total_loss = stressed_total - original_value
    df["loss_contribution_pct"] = df["value_loss"] / total_loss if total_loss != 0 else 0.0

    return {
        "scenario_type": "Custom Scenario",
        "original_value": float(original_value),
        "stressed_value": float(stressed_total),
        "portfolio_loss": float(total_loss),
        "portfolio_return": float(portfolio_return),
        "asset_breakdown": df,
    }


def replay_historical_period(
    prices_df: pd.DataFrame,
    quantities: pd.Series,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Replays exact historical price trajectory during a specific crisis period.
    Calculates actual historical asset returns and portfolio value path.
    """
    clean_prices = prices_df.loc[start_date:end_date]
    if clean_prices.empty or len(clean_prices) < 2:
        return {"error": "Insufficient historical data for selected date range."}

    common_assets = [a for a in clean_prices.columns if a in quantities.index]
    if not common_assets:
        return {"error": "None of the portfolio assets exist in the historical series."}

    sub_prices = clean_prices[common_assets]
    sub_qty = quantities[common_assets]

    # Portfolio value series
    val_series = sub_prices.dot(sub_qty)
    start_val = float(val_series.iloc[0])
    end_val = float(val_series.iloc[-1])
    min_val = float(val_series.min())

    max_dd = (val_series / val_series.cummax() - 1.0).min()

    # Asset-level returns over the period
    asset_start = sub_prices.iloc[0]
    asset_end = sub_prices.iloc[-1]
    asset_returns = (asset_end / asset_start) - 1.0

    return {
        "scenario_type": "Historical Replay",
        "start_date": str(clean_prices.index[0]),
        "end_date": str(clean_prices.index[-1]),
        "starting_value": start_val,
        "ending_value": end_val,
        "lowest_value": min_val,
        "period_return": float((end_val / start_val) - 1.0) if start_val > 0 else 0.0,
        "max_drawdown": float(max_dd),
        "asset_returns": asset_returns,
        "portfolio_path": val_series,
    }
