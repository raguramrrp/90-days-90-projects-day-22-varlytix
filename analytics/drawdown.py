"""
Drawdown Analytics Module for SIGMORA.
Calculates running peak, underwater drawdown series, maximum drawdown,
average drawdown, and Calmar ratio.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd


def calculate_drawdown_series(values_or_cumulative: pd.Series) -> pd.DataFrame:
    """
    Computes running peak, underwater drawdown percentage, and recovery state:
    Peak_t = max_{s <= t} (Value_s)
    Drawdown_t = (Value_t / Peak_t) - 1.0
    Returns a DataFrame with columns: ['value', 'peak', 'drawdown'].
    """
    clean = values_or_cumulative.dropna()
    if clean.empty:
        return pd.DataFrame(columns=["value", "peak", "drawdown"])

    peak = clean.cummax()
    drawdown = (clean / peak) - 1.0

    return pd.DataFrame({
        "value": clean,
        "peak": peak,
        "drawdown": drawdown,
    })


def calculate_max_drawdown(drawdown_series: pd.Series) -> float:
    """
    Returns the minimum drawdown (maximum loss from peak, expressed as negative float):
    MDD = min(Drawdown_t)
    """
    clean = drawdown_series.dropna()
    if clean.empty:
        return 0.0
    return float(clean.min())


def calculate_average_drawdown(drawdown_series: pd.Series) -> float:
    """
    Calculates the mean depth of underwater drawdown periods (excluding 0 drawdown periods).
    """
    clean = drawdown_series.dropna()
    negative_dds = clean[clean < 0]
    if negative_dds.empty:
        return 0.0
    return float(negative_dds.mean())


def calculate_calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
    """
    Calculates Calmar ratio:
    Calmar = Annualized Return / |Max Drawdown|
    """
    abs_mdd = abs(max_drawdown)
    if abs_mdd <= 1e-9:
        return 0.0
    return float(annualized_return / abs_mdd)


def find_drawdown_peaks_and_troughs(df_drawdown: pd.DataFrame) -> Dict[str, Any]:
    """
    Identifies maximum drawdown peak date, trough date, and duration.
    """
    if df_drawdown.empty or "drawdown" not in df_drawdown.columns:
        return {"trough_date": None, "trough_value": 0.0, "peak_date": None}

    mdd = df_drawdown["drawdown"].min()
    if mdd >= 0:
        return {"trough_date": None, "trough_value": 0.0, "peak_date": None}

    trough_date = df_drawdown["drawdown"].idxmin()
    # Find peak before trough
    sub_df = df_drawdown.loc[:trough_date]
    peak_date = sub_df["value"].idxmax()

    return {
        "trough_date": trough_date,
        "trough_value": float(mdd),
        "peak_date": peak_date,
    }
