"""
Covariance and Risk Contribution Analytics Module for VARLYTIX.
Calculates sample covariance matrices, portfolio variance/volatility,
marginal risk contribution (MRC), component risk contribution (RC),
and percentage risk contribution (PRC).
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd


def calculate_covariance_matrix(
    returns_df: pd.DataFrame,
    annualize: bool = True,
    trading_days: int = 252,
    ddof: int = 1
) -> pd.DataFrame:
    """
    Calculates sample covariance matrix of asset returns.
    If annualize=True, scales daily covariance by trading_days.
    """
    clean_returns = returns_df.dropna()
    if clean_returns.shape[0] < 2:
        return pd.DataFrame()

    cov_matrix = clean_returns.cov(ddof=ddof)
    if annualize:
        cov_matrix = cov_matrix * trading_days
    return cov_matrix


def calculate_portfolio_variance_and_volatility(
    weights: pd.Series,
    cov_matrix: pd.DataFrame
) -> Tuple[float, float]:
    """
    Calculates portfolio variance and volatility:
    sigma_p^2 = w^T * Sigma * w
    sigma_p = sqrt(sigma_p^2)
    """
    common_assets = [a for a in cov_matrix.columns if a in weights.index]
    if not common_assets:
        return 0.0, 0.0

    w = weights[common_assets].values
    total_w = w.sum()
    if abs(total_w) > 1e-9:
        w = w / total_w
    else:
        return 0.0, 0.0

    sigma = cov_matrix.loc[common_assets, common_assets].values

    port_var = float(w.T @ sigma @ w)
    if port_var < 0:
        port_var = 0.0
    port_vol = float(np.sqrt(port_var))
    return port_var, port_vol


def calculate_risk_contributions(
    weights: pd.Series,
    cov_matrix: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculates Component and Percentage Risk Contribution:
    sigma_p = sqrt(w^T * Sigma * w)
    MRC = Sigma * w / sigma_p
    RC_i = w_i * (Sigma * w)_i / sigma_p
    PRC_i = RC_i / sigma_p

    Identity check: sum(RC_i) == sigma_p
    """
    common_assets = [a for a in cov_matrix.columns if a in weights.index]
    if not common_assets:
        return pd.DataFrame()

    # Normalize weights
    w_series = weights[common_assets].copy()
    sum_w = w_series.sum()
    if abs(sum_w) > 1e-9:
        w_series = w_series / sum_w
    else:
        return pd.DataFrame()

    w = w_series.values
    sigma = cov_matrix.loc[common_assets, common_assets].values

    # Portfolio volatility
    port_var = float(w.T @ sigma @ w)
    if port_var <= 1e-12:
        return pd.DataFrame({
            "asset": common_assets,
            "weight": w,
            "marginal_risk": np.zeros(len(common_assets)),
            "component_risk": np.zeros(len(common_assets)),
            "percentage_risk_contribution": np.zeros(len(common_assets)),
        }).set_index("asset")

    port_vol = np.sqrt(port_var)

    # Marginal risk contribution
    sigma_w = sigma @ w
    mrc = sigma_w / port_vol

    # Component risk contribution
    rc = w * mrc

    # Percentage risk contribution
    prc = rc / port_vol

    df_contrib = pd.DataFrame({
        "asset": common_assets,
        "weight": w,
        "marginal_risk": mrc,
        "component_risk": rc,
        "percentage_risk_contribution": prc,
    }).set_index("asset")

    return df_contrib
