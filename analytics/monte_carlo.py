"""
Monte Carlo Simulation Engine for VARLYTIX.
Supports:
1. Method A: Historical Bootstrap (joint cross-asset vector resampling with optional block bootstrap)
2. Method B: Multivariate Parametric Simulation (correlated Gaussian returns with nearest PSD covariance)
Computes percentile trajectories, ending value distributions, loss probabilities,
recurring monthly SIP (Systematic Investment Plan) cash flows, goal target probabilities,
and maximum simulated drawdown distributions.
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd


def ensure_positive_semidefinite(matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """
    Ensures a symmetric covariance matrix is positive semi-definite (PSD)
    by clipping negative eigenvalues (Higham projection approximation).
    """
    sym_matrix = (matrix + matrix.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(sym_matrix)
    if np.all(eigenvalues >= 0):
        return sym_matrix

    clipped_eigenvalues = np.maximum(eigenvalues, epsilon)
    psd_matrix = eigenvectors @ np.diag(clipped_eigenvalues) @ eigenvectors.T
    return (psd_matrix + psd_matrix.T) / 2.0


def _simulate_path_compounding(
    daily_port_returns: np.ndarray,
    initial_value: float,
    horizon_days: int,
    monthly_sip: float = 0.0
) -> Tuple[np.ndarray, float]:
    """
    Compounds portfolio daily returns over time, incorporating recurring monthly
    Systematic Investment Plan (SIP) cash inflows every 21 trading days.
    """
    num_sims = daily_port_returns.shape[0]
    paths = np.zeros((num_sims, horizon_days + 1))
    paths[:, 0] = initial_value

    if monthly_sip <= 0.0:
        paths[:, 1:] = initial_value * np.cumprod(1.0 + daily_port_returns, axis=1)
        total_invested = initial_value
    else:
        num_sip_payments = 0
        for t in range(1, horizon_days + 1):
            r_t = daily_port_returns[:, t - 1]
            new_val = paths[:, t - 1] * (1.0 + r_t)
            # Add monthly SIP on 21-day cycle (approx 1 market month)
            if t % 21 == 0:
                new_val += monthly_sip
                num_sip_payments += 1
            paths[:, t] = new_val
        total_invested = initial_value + (num_sip_payments * monthly_sip)

    return paths, total_invested


def run_historical_bootstrap_simulation(
    returns_df: pd.DataFrame,
    weights: pd.Series,
    initial_value: float,
    horizon_days: int = 252,
    num_simulations: int = 1000,
    block_size: int = 1,
    random_seed: Optional[int] = 42,
    monthly_sip: float = 0.0,
    goal_target_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Historical Bootstrap Simulation:
    Resamples complete daily joint return vectors from historical data to preserve
    empirical cross-asset correlations and fat-tailed characteristics.
    Supports recurring monthly SIP cash inflows and target goal tracking.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    common_assets = [a for a in returns_df.columns if a in weights.index]
    clean_returns = returns_df[common_assets].dropna()
    num_historical_days = len(clean_returns)

    if num_historical_days < 20:
        raise ValueError("Insufficient historical observations for bootstrap simulation (minimum 20 required).")

    # Normalize weights
    w = (weights[common_assets] / weights[common_assets].sum()).values
    historical_matrix = clean_returns.values  # Shape: (T_hist, N_assets)

    if block_size <= 1:
        # Standard joint i.i.d vector bootstrap
        idx = np.random.randint(0, num_historical_days, size=(num_simulations, horizon_days))
        resampled_asset_returns = historical_matrix[idx]
        daily_port_returns = np.dot(resampled_asset_returns, w)
    else:
        # Block bootstrap to preserve serial correlation
        daily_port_returns = np.zeros((num_simulations, horizon_days))
        num_blocks = int(np.ceil(horizon_days / block_size))
        for s in range(num_simulations):
            sampled_series = []
            for _ in range(num_blocks):
                start_idx = np.random.randint(0, num_historical_days - block_size + 1)
                sampled_series.append(historical_matrix[start_idx : start_idx + block_size])
            block_data = np.vstack(sampled_series)[:horizon_days]
            daily_port_returns[s] = np.dot(block_data, w)

    # Compound paths with optional monthly SIP
    paths, total_invested = _simulate_path_compounding(
        daily_port_returns=daily_port_returns,
        initial_value=initial_value,
        horizon_days=horizon_days,
        monthly_sip=monthly_sip
    )

    return _compute_simulation_statistics(
        paths=paths,
        initial_value=initial_value,
        total_invested=total_invested,
        monthly_sip=monthly_sip,
        horizon_days=horizon_days,
        method_name="Historical Bootstrap",
        goal_target_value=goal_target_value
    )


def run_parametric_monte_carlo_simulation(
    returns_df: pd.DataFrame,
    weights: pd.Series,
    initial_value: float,
    horizon_days: int = 252,
    num_simulations: int = 1000,
    random_seed: Optional[int] = 42,
    monthly_sip: float = 0.0,
    goal_target_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Multivariate Parametric Monte Carlo Simulation:
    Estimates historical mean vector and covariance matrix,
    generates correlated normal return vectors, and compounds portfolio value
    with optional recurring monthly SIP cash inflows and goal target tracking.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    common_assets = [a for a in returns_df.columns if a in weights.index]
    clean_returns = returns_df[common_assets].dropna()

    if len(clean_returns) < 20:
        raise ValueError("Insufficient historical observations for parametric simulation.")

    w = (weights[common_assets] / weights[common_assets].sum()).values
    mean_vec = clean_returns.mean().values
    cov_mat = clean_returns.cov().values

    # Ensure covariance matrix is positive semi-definite
    psd_cov = ensure_positive_semidefinite(cov_mat)

    # Cholesky decomposition: Sigma = L * L^T
    try:
        L = np.linalg.cholesky(psd_cov)
    except np.linalg.LinAlgError:
        eigvals, eigvecs = np.linalg.eigh(psd_cov)
        eigvals = np.maximum(eigvals, 1e-8)
        L = eigvecs @ np.diag(np.sqrt(eigvals))

    # Generate standard normal random variates: (num_simulations, horizon_days, num_assets)
    n_assets = len(common_assets)
    z = np.random.standard_normal((num_simulations, horizon_days, n_assets))

    # Correlated returns: z @ L.T + mean
    correlated_returns = np.einsum("ijk,lk->ijl", z, L) + mean_vec

    # Daily portfolio returns: (num_simulations, horizon_days)
    daily_port_returns = np.dot(correlated_returns, w)

    # Compound paths with optional monthly SIP
    paths, total_invested = _simulate_path_compounding(
        daily_port_returns=daily_port_returns,
        initial_value=initial_value,
        horizon_days=horizon_days,
        monthly_sip=monthly_sip
    )

    return _compute_simulation_statistics(
        paths=paths,
        initial_value=initial_value,
        total_invested=total_invested,
        monthly_sip=monthly_sip,
        horizon_days=horizon_days,
        method_name="Multivariate Parametric",
        goal_target_value=goal_target_value
    )


def _compute_simulation_statistics(
    paths: np.ndarray,
    initial_value: float,
    total_invested: float,
    monthly_sip: float,
    horizon_days: int,
    method_name: str,
    goal_target_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes summary percentiles, fan chart lines, ending distribution,
    loss probability, goal success probability, and maximum drawdown.
    """
    ending_values = paths[:, -1]
    ending_returns = (ending_values / total_invested) - 1.0

    # Percentiles across time steps (fan chart series)
    percentiles_over_time = {
        "p05": np.percentile(paths, 5, axis=0),
        "p25": np.percentile(paths, 25, axis=0),
        "p50": np.percentile(paths, 50, axis=0),  # Median
        "p75": np.percentile(paths, 75, axis=0),
        "p95": np.percentile(paths, 95, axis=0),
    }

    # Summary ending percentiles
    summary_percentiles = {
        5: float(np.percentile(ending_values, 5)),
        25: float(np.percentile(ending_values, 25)),
        50: float(np.percentile(ending_values, 50)),
        75: float(np.percentile(ending_values, 75)),
        95: float(np.percentile(ending_values, 95)),
    }

    # Loss probability: P(Ending Value < Total Invested Capital)
    loss_prob = float(np.mean(ending_values < total_invested))

    # Goal probability: P(Ending Value >= Goal Target Value)
    goal_prob = None
    if goal_target_value is not None and goal_target_value > 0:
        goal_prob = float(np.mean(ending_values >= goal_target_value))

    # Maximum drawdown for each simulated path
    running_peaks = np.maximum.accumulate(paths, axis=1)
    drawdowns = (paths / running_peaks) - 1.0
    max_drawdowns_per_path = np.min(drawdowns, axis=1)
    median_sim_mdd = float(np.median(max_drawdowns_per_path))
    worst_sim_mdd = float(np.min(max_drawdowns_per_path))

    # Sample paths for overlay display (up to 30 paths)
    sample_indices = np.random.choice(paths.shape[0], size=min(30, paths.shape[0]), replace=False)
    sample_paths = paths[sample_indices]

    return {
        "method": method_name,
        "initial_value": initial_value,
        "total_invested": total_invested,
        "monthly_sip": monthly_sip,
        "goal_target_value": goal_target_value,
        "goal_probability": goal_prob,
        "horizon_days": horizon_days,
        "num_simulations": paths.shape[0],
        "percentiles_over_time": percentiles_over_time,
        "summary_percentiles": summary_percentiles,
        "ending_values": ending_values,
        "ending_returns": ending_returns,
        "median_ending_value": summary_percentiles[50],
        "median_ending_return": float(np.percentile(ending_returns, 50)),
        "loss_probability": loss_prob,
        "median_max_drawdown": median_sim_mdd,
        "worst_max_drawdown": worst_sim_mdd,
        "sample_paths": sample_paths,
        "disclaimer": "These are hypothetical statistical scenarios based on historical data and selected assumptions. They are not forecasts, guarantees or investment recommendations."
    }
