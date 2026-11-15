"""
Screen 03 — Risk Lab for VARLYTIX.
Core quantitative risk research laboratory computing annualized volatility,
drawdown severity, tail risk (VaR/CVaR), and Euler component risk contributions.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from services.risk_service import RiskService
from services.portfolio_service import PortfolioService
from components.metric_display import render_metric_card
from components.chart_components import (
    plot_risk_contribution_bars, plot_drawdown_curve,
    plot_rolling_volatility, _apply_varlytix_layout
)
from config import COLORS, DEFAULT_RISK_FREE_RATE, DEFAULT_TRADING_DAYS


def render_risk_lab_page(db, portfolio_id: int):
    risk_service = RiskService(db)
    portfolio_service = PortfolioService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Risk Laboratory & Volatility Attribution</h2>",
        unsafe_allow_html=True
    )

    # Risk Controls
    col_c1, col_c2, col_c3 = st.columns([4, 4, 4])
    with col_c1:
        rf_rate = st.number_input("Risk-Free Rate (Rf)", min_value=0.0, max_value=0.20, value=DEFAULT_RISK_FREE_RATE, step=0.005, format="%.3f")
        st.caption("Benchmark: 10-Year Indian Government Sovereign Bond yield")
    with col_c2:
        trading_days = st.selectbox("Annualization Trading Days", [250, 252, 260], index=1)
        st.caption("NSE / BSE active trading sessions per calendar year")
    with col_c3:
        rolling_window = st.slider("Rolling Volatility Window", min_value=10, max_value=126, value=21, step=5)
        st.caption("Trading days in moving volatility estimation window")

    with st.spinner("Computing quantitative risk metrics and covariance decomposition..."):
        risk_data = risk_service.analyze_portfolio_risk(
            portfolio_id=portfolio_id,
            risk_free_rate=rf_rate
        )

    if "error" in risk_data:
        st.warning(risk_data["error"])
        return

    # Section 1: 10 Comprehensive Risk Metrics
    st.markdown(f"<h3 style='font-size: 14px; font-weight: 800; color: {COLORS['graphite']}; margin: 12px 0 8px 0;'>1. Core Quantitative Risk Metrics</h3>", unsafe_allow_html=True)

    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        st.markdown(render_metric_card(
            label="Annualized Volatility (σ)",
            value=f"{risk_data['annualized_volatility'] * 100:.2f}%",
            subvalue=f"Daily: {risk_data['annualized_volatility'] / (trading_days**0.5) * 100:.2f}%",
            help_text="Standard deviation of returns annualized via sqrt(252)"
        ), unsafe_allow_html=True)
    with r2:
        st.markdown(render_metric_card(
            label="Sharpe Ratio",
            value=f"{risk_data['sharpe_ratio']:.2f}",
            subvalue=f"CAGR: {risk_data['annualized_return'] * 100:.1f}%",
            help_text="Excess return over Rf divided by total annualized volatility"
        ), unsafe_allow_html=True)
    with r3:
        st.markdown(render_metric_card(
            label="Sortino Ratio",
            value=f"{risk_data['sortino_ratio']:.2f}",
            subvalue=f"Downside Dev: {risk_data['downside_deviation'] * 100:.1f}%",
            help_text="Penalizes only harmful negative volatility below the target rate"
        ), unsafe_allow_html=True)
    with r4:
        st.markdown(render_metric_card(
            label="Maximum Drawdown",
            value=f"{risk_data['max_drawdown'] * 100:.2f}%",
            subvalue=f"Avg Drawdown: {risk_data['average_drawdown'] * 100:.2f}%",
            help_text="Largest percentage capital contraction from historical peak"
        ), unsafe_allow_html=True)
    with r5:
        st.markdown(render_metric_card(
            label="Calmar Ratio",
            value=f"{risk_data['calmar_ratio']:.2f}",
            subvalue="CAGR / |MDD|",
            help_text="Annualized compound return divided by maximum drawdown"
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    r6, r7, r8, r9, r10 = st.columns(5)
    with r6:
        st.markdown(render_metric_card(
            label="Market Beta (β)",
            value=f"{risk_data['beta']:.2f}",
            subvalue="vs NIFTY 50",
            help_text="Covariance with market benchmark divided by benchmark variance"
        ), unsafe_allow_html=True)
    with r7:
        st.markdown(render_metric_card(
            label="VaR (95% 1-Day)",
            value=f"{risk_data['var_95'] * 100:.2f}%",
            subvalue=f"₹ {risk_data['current_value'] * risk_data['var_95']:,.0f}",
            help_text="Historical 95% quantile loss over a 1-day horizon"
        ), unsafe_allow_html=True)
    with r8:
        st.markdown(render_metric_card(
            label="CVaR (95% Expected Shortfall)",
            value=f"{risk_data['cvar_95'] * 100:.2f}%",
            subvalue=f"₹ {risk_data['current_value'] * risk_data['cvar_95']:,.0f}",
            help_text="Expected average loss conditional on falling into the 5% tail"
        ), unsafe_allow_html=True)
    with r9:
        st.markdown(render_metric_card(
            label="VaR (99% 1-Day)",
            value=f"{risk_data['var_99'] * 100:.2f}%",
            subvalue=f"₹ {risk_data['current_value'] * risk_data['var_99']:,.0f}",
            help_text="Extreme 99% quantile loss over 1-day horizon"
        ), unsafe_allow_html=True)
    with r10:
        st.markdown(render_metric_card(
            label="CVaR (99% Extreme Tail)",
            value=f"{risk_data['cvar_99'] * 100:.2f}%",
            subvalue=f"₹ {risk_data['current_value'] * risk_data['cvar_99']:,.0f}",
            help_text="Mean loss beyond the 1% extreme catastrophe threshold"
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

    # Section 2: Component Risk Contribution (Euler Allocation)
    st.markdown(f"<h3 style='font-size: 14px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 4px;'>2. Euler Volatility Decomposition & Risk Contribution</h3>", unsafe_allow_html=True)
    st.caption(
        f"Mathematical Identity: Total Portfolio Volatility (σ_p = {risk_data['annualized_volatility']*100:.3f}%) strictly equals the sum of component risk contributions (Σ RC_i = {risk_data['sum_rc_identity']*100:.3f}%). Discrepancy: {risk_data['identity_discrepancy']:.2e}."
    )

    col_rc_chart, col_rc_table = st.columns([6, 6])

    rc_df = risk_data["risk_contributions"]
    with col_rc_chart:
        fig_rc = plot_risk_contribution_bars(rc_df)
        st.plotly_chart(fig_rc, use_container_width=True)

    with col_rc_table:
        rc_display = rc_df.copy()
        rc_display["weight"] = rc_display["weight"].apply(lambda w: f"{w * 100:.2f}%")
        rc_display["marginal_risk"] = rc_display["marginal_risk"].apply(lambda m: f"{m * 100:.2f}%")
        rc_display["component_risk"] = rc_display["component_risk"].apply(lambda c: f"{c * 100:.2f}%")
        rc_display["percentage_risk_contribution"] = rc_display["percentage_risk_contribution"].apply(lambda p: f"{p * 100:.2f}%")
        rc_display.columns = ["Capital Weight (w_i)", "Marginal Risk (MRC)", "Component Risk (RC_i)", "Volatility Contribution (%)"]
        st.dataframe(rc_display, use_container_width=True)

    # Section 3: Volatility & Drawdown Dynamics
    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-size: 14px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 6px;'>3. Dynamic Volatility & Tail Curves</h3>", unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        fig_rvol = plot_rolling_volatility(risk_data["rolling_volatility"])
        st.plotly_chart(fig_rvol, use_container_width=True)

    with col_v2:
        # Risk-Return Scatter Plot
        returns_df = risk_service.market_data_service.get_return_matrix(risk_data["holdings"]["symbol"].tolist())
        if not returns_df.empty:
            asset_vols = returns_df.std(ddof=1) * np.sqrt(trading_days) * 100.0
            asset_rets = ((1.0 + returns_df.mean()) ** trading_days - 1.0) * 100.0

            fig_scat = go.Figure()
            # Individual Assets
            fig_scat.add_trace(go.Scatter(
                x=asset_vols,
                y=asset_rets,
                mode="markers+text",
                text=asset_vols.index,
                textposition="top center",
                name="Holdings",
                marker=dict(color=COLORS["deep_teal"], size=9)
            ))
            # Portfolio Marker
            fig_scat.add_trace(go.Scatter(
                x=[risk_data["annualized_volatility"] * 100.0],
                y=[risk_data["annualized_return"] * 100.0],
                mode="markers+text",
                text=["PORTFOLIO"],
                textposition="bottom right",
                name="Portfolio",
                marker=dict(color=COLORS["amber"], size=13, symbol="diamond")
            ))
            fig_scat = _apply_varlytix_layout(fig_scat, title="Risk-Return Scatter (Individual Assets vs Portfolio)", height=280)
            fig_scat.update_layout(
                xaxis_title="Annualized Volatility (%)",
                yaxis_title="Annualized Return (%)",
                margin=dict(l=40, r=20, t=40, b=40)
            )
            st.plotly_chart(fig_scat, use_container_width=True)
