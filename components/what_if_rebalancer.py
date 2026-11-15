"""
Interactive "What If?" Rebalancing Sandbox for VARLYTIX.
Allows investors to dynamically adjust asset weights via sliders,
add safe-haven assets (Gold / Liquid Debt), and instantly observe real-time
changes to Expected Return, Volatility, Sharpe Ratio, Drawdown, and VaR.
"""

from typing import Dict, Any, List
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from analytics.covariance import calculate_covariance_matrix
from config import COLORS, DEFAULT_RISK_FREE_RATE


def render_what_if_sandbox(db, portfolio_id: int):
    """
    Renders the interactive What If? Rebalancing sandbox UI.
    """
    portfolio_service = PortfolioService(db)
    market_service = MarketDataService(db)

    holdings = portfolio_service.get_holdings_summary(portfolio_id)
    if holdings.empty:
        st.info("No active holdings found in portfolio.")
        return

    st.markdown(
        f"<h3 style='font-size: 15px; font-weight: 800; color: {COLORS['graphite']}; margin-top: 10px; margin-bottom: 4px;'>Interactive Allocation Sandbox</h3>"
        f"<p style='font-size: 12px; color: {COLORS['secondary_text']}; margin-bottom: 14px;'>Adjust allocation weights below to test how adding Gold or re-weighting positions impacts your portfolio's risk-return profile in real time.</p>",
        unsafe_allow_html=True
    )

    symbols = holdings["symbol"].tolist()
    asset_names = {row["symbol"]: row["name"] for _, row in holdings.iterrows()}
    curr_weights = dict(zip(holdings["symbol"], holdings["weight"]))

    # Optional Multi-Asset Hedge Additions
    hedge_symbols = ["DEMO_COMMODITY_GOLDBEES", "DEMO_DEBT_LIQUIDBEES"]
    for hs in hedge_symbols:
        if hs not in symbols:
            asset = portfolio_service.get_asset(hs)
            if asset:
                symbols.append(hs)
                asset_names[hs] = asset.asset_name
                curr_weights[hs] = 0.0

    # Get Return Matrix
    returns_df = market_service.get_return_matrix(symbols)
    if returns_df.empty or len(returns_df) < 20:
        st.warning("Insufficient market data for sandbox analytics.")
        return

    common_syms = [s for s in symbols if s in returns_df.columns]
    clean_rets = returns_df[common_syms].dropna()
    mean_rets = clean_rets.mean() * 252.0  # Annualized
    cov_matrix = calculate_covariance_matrix(clean_rets, annualize=True)

    col_sliders, col_metrics = st.columns([6, 6])

    with col_sliders:
        st.markdown(f"<div style='font-size: 11px; font-weight: 700; color: {COLORS['secondary_text']}; text-transform: uppercase; margin-bottom: 6px;'>SLIDER WEIGHTS (ALLOCATION %):</div>", unsafe_allow_html=True)
        raw_weights = {}

        for sym in common_syms:
            disp_name = asset_names.get(sym, sym)
            default_val = float(curr_weights.get(sym, 0.0) * 100.0)
            is_hedge = "GOLDBEES" in sym or "LIQUIDBEES" in sym
            badge = " [Hedge: Gold]" if "GOLDBEES" in sym else (" [Hedge: Cash/Debt]" if "LIQUIDBEES" in sym else "")

            w_val = st.slider(
                f"{disp_name}{badge}",
                min_value=0.0,
                max_value=100.0,
                value=float(round(default_val, 1)),
                step=1.0,
                key=f"sandbox_w_{sym}"
            )
            raw_weights[sym] = w_val

    # Normalize weights
    total_raw = sum(raw_weights.values())
    if total_raw <= 0.0:
        st.error("Please allocate at least one asset greater than 0%.")
        return

    norm_weights = {sym: raw_weights[sym] / total_raw for sym in common_syms}
    curr_norm_weights = {sym: curr_weights.get(sym, 0.0) for sym in common_syms}
    curr_norm_sum = sum(curr_norm_weights.values())
    if curr_norm_sum > 0:
        curr_norm_weights = {s: curr_norm_weights[s] / curr_norm_sum for s in common_syms}

    # Vector computations
    w_new = np.array([norm_weights[s] for s in common_syms])
    w_curr = np.array([curr_norm_weights[s] for s in common_syms])
    means = mean_rets[common_syms].values
    cov_mat = cov_matrix.loc[common_syms, common_syms].values

    # Analytics for Current
    curr_exp_ret = float(np.dot(w_curr, means))
    curr_vol = float(np.sqrt(np.dot(w_curr, np.dot(cov_mat, w_curr))))
    curr_sharpe = (curr_exp_ret - DEFAULT_RISK_FREE_RATE) / curr_vol if curr_vol > 0 else 0.0
    curr_mdd_est = -min(0.60, curr_vol * 1.85)

    # Analytics for What-If
    new_exp_ret = float(np.dot(w_new, means))
    new_vol = float(np.sqrt(np.dot(w_new, np.dot(cov_mat, w_new))))
    new_sharpe = (new_exp_ret - DEFAULT_RISK_FREE_RATE) / new_vol if new_vol > 0 else 0.0
    new_mdd_est = -min(0.60, new_vol * 1.85)

    with col_metrics:
        st.markdown(f"<div style='font-size: 11px; font-weight: 700; color: {COLORS['secondary_text']}; text-transform: uppercase; margin-bottom: 6px;'>REAL-TIME IMPACT ANALYSIS:</div>", unsafe_allow_html=True)

        # Delta metrics
        d_vol = (new_vol - curr_vol) * 100.0
        d_sharpe = new_sharpe - curr_sharpe
        d_ret = (new_exp_ret - curr_exp_ret) * 100.0
        d_mdd = (new_mdd_est - curr_mdd_est) * 100.0

        comp_html = (
            f'<div style="background:{COLORS["white"]}; border:1px solid {COLORS["border"]}; border-radius:6px; padding:12px 16px; margin-bottom:12px;">'
            f'<table style="width:100%; border-collapse:collapse; font-size:12px;">'
            f'<thead><tr style="border-bottom:1px solid {COLORS["border"]}; text-align:left; color:{COLORS["secondary_text"]}; font-size:10.5px; text-transform:uppercase;">'
            f'<th style="padding:6px 0;">Metric</th><th>Current</th><th>What-If</th><th>Delta Impact</th>'
            f'</tr></thead>'
            f'<tbody>'
            f'<tr style="border-bottom:1px solid {COLORS["border"]};"><td style="padding:8px 0; font-weight:600; color:{COLORS["graphite"]};">Annualized Volatility (σ)</td>'
            f'<td>{curr_vol*100:.1f}%</td><td style="font-weight:700; color:{COLORS["secondary_accent"]};">{new_vol*100:.1f}%</td>'
            f'<td style="font-weight:800; color:{COLORS["positive"] if d_vol <= 0 else COLORS["negative"]};">{d_vol:+.1f}% vol</td></tr>'
            f'<tr style="border-bottom:1px solid {COLORS["border"]};"><td style="padding:8px 0; font-weight:600; color:{COLORS["graphite"]};">Sharpe Ratio (Rf=6.5%)</td>'
            f'<td>{curr_sharpe:.2f}</td><td style="font-weight:700; color:{COLORS["secondary_accent"]};">{new_sharpe:.2f}</td>'
            f'<td style="font-weight:800; color:{COLORS["positive"] if d_sharpe >= 0 else COLORS["negative"]};">{d_sharpe:+.2f}</td></tr>'
            f'<tr style="border-bottom:1px solid {COLORS["border"]};"><td style="padding:8px 0; font-weight:600; color:{COLORS["graphite"]};">Expected Return (CAGR)</td>'
            f'<td>{curr_exp_ret*100:.1f}%</td><td style="font-weight:700; color:{COLORS["secondary_accent"]};">{new_exp_ret*100:.1f}%</td>'
            f'<td style="font-weight:800; color:{COLORS["positive"] if d_ret >= 0 else COLORS["negative"]};">{d_ret:+.1f}%</td></tr>'
            f'<tr><td style="padding:8px 0; font-weight:600; color:{COLORS["graphite"]};">Estimated Max Drawdown</td>'
            f'<td>{curr_mdd_est*100:.1f}%</td><td style="font-weight:700; color:{COLORS["secondary_accent"]};">{new_mdd_est*100:.1f}%</td>'
            f'<td style="font-weight:800; color:{COLORS["positive"] if d_mdd >= 0 else COLORS["negative"]};">{d_mdd:+.1f}%</td></tr>'
            f'</tbody></table>'
            f'</div>'
        )
        st.markdown(comp_html, unsafe_allow_html=True)

        # Plotly comparison bar chart of weights
        fig_bar = go.Figure()
        short_names = [asset_names.get(s, s).replace(" (Demo Synthetic)", "")[:18] for s in common_syms]

        fig_bar.add_trace(go.Bar(
            y=short_names,
            x=[curr_norm_weights[s] * 100.0 for s in common_syms],
            name="Current Allocation",
            orientation="h",
            marker=dict(color=COLORS["secondary_accent"], opacity=0.7)
        ))
        fig_bar.add_trace(go.Bar(
            y=short_names,
            x=[norm_weights[s] * 100.0 for s in common_syms],
            name="What-If Allocation",
            orientation="h",
            marker=dict(color=COLORS["primary_accent"])
        ))
        fig_bar.update_layout(
            template="plotly_white",
            barmode="group",
            height=260,
            margin=dict(l=10, r=10, t=25, b=25),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Weight (%)", gridcolor=COLORS["border"]),
            yaxis=dict(autorange="reversed"),
            paper_bgcolor=COLORS["primary_surface"],
            plot_bgcolor=COLORS["primary_surface"],
            font=dict(family="Inter, sans-serif", size=10.5, color=COLORS["primary_text"])
        )
        st.plotly_chart(fig_bar, use_container_width=True)
