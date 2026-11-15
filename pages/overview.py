"""
Screen 01 — Portfolio Overview for SIGMORA.
Refined Editorial Research Workspace answering 4 core investor questions:
1. What is my portfolio worth?
2. How has it performed?
3. How risky is it?
4. Where is the risk concentrated?

Features 4 primary + 4 secondary metric cards, trajectory vs NIFTY 50 benchmark,
allocation treemap, underwater drawdown curve, automated risk observations,
active holdings snapshot table, and contextual methodological explanations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.risk_service import RiskService
from services.portfolio_service import PortfolioService
from components.metric_display import render_metric_card, render_observation_banner
from components.chart_components import (
    plot_portfolio_performance, plot_allocation_treemap,
    plot_drawdown_curve
)
from config import COLORS, CURRENCY_SYMBOL


def render_overview_page(db, portfolio_id: int):
    risk_service = RiskService(db)
    portfolio_service = PortfolioService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    # Header Row: Portfolio Title + Period Selector
    c_title, c_range = st.columns([7, 5])
    with c_title:
        st.markdown(
            f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['primary_text']}; margin: 0; line-height: 1.2;'>{portfolio.portfolio_name}</h2>",
            unsafe_allow_html=True
        )

    with c_range:
        selected_period = st.segmented_control(
            "Period",
            options=["1M", "3M", "6M", "1Y", "3Y", "All"],
            default="All",
            label_visibility="collapsed",
            key="overview_period_segmented"
        )
        if not selected_period:
            selected_period = "All"

    # Date filter calculation
    end_d = datetime.now().date()
    if selected_period == "1M":
        start_d = end_d - timedelta(days=30)
    elif selected_period == "3M":
        start_d = end_d - timedelta(days=90)
    elif selected_period == "6M":
        start_d = end_d - timedelta(days=180)
    elif selected_period == "1Y":
        start_d = end_d - timedelta(days=365)
    elif selected_period == "3Y":
        start_d = end_d - timedelta(days=1095)
    else:
        start_d = None

    # Compute risk analytics
    with st.spinner("Calculating portfolio risk metrics..."):
        risk_data = risk_service.analyze_portfolio_risk(
            portfolio_id=portfolio_id,
            start_date=start_d,
            end_date=end_d
        )

    if "error" in risk_data:
        st.warning(f"Portfolio Status: {risk_data['error']}")
        st.info("Navigate to the **Portfolio** tab to add positions or import historical data.")
        return

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 4 CORE INVESTOR QUESTIONS — PRIMARY METRIC CARDS (ROW 1)
    # -------------------------------------------------------------
    pnl_val = risk_data.get("total_pnl", 0.0)
    pnl_prefix = "+" if pnl_val >= 0 else ""

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(render_metric_card(
            label="1. Portfolio Value",
            value=f"₹ {risk_data['current_value']:,.0f}",
            delta=f"{pnl_prefix}₹ {abs(pnl_val):,.0f}",
            delta_positive=(pnl_val >= 0),
            subvalue=f"Cost Basis: ₹ {risk_data['starting_value']:,.0f}",
            help_text="Current total market value based on latest available closing prices."
        ), unsafe_allow_html=True)

    with m2:
        cum_ret = risk_data['cumulative_return'] * 100.0
        cagr_ret = risk_data['annualized_return'] * 100.0
        st.markdown(render_metric_card(
            label="2. Total Return",
            value=f"{cum_ret:+.2f}%",
            delta=f"CAGR {cagr_ret:+.1f}%",
            delta_positive=(cum_ret >= 0),
            subvalue=f"Window: {risk_data['observation_days']} trading days",
            help_text="Cumulative return over the selected period with compound annualized growth rate."
        ), unsafe_allow_html=True)

    with m3:
        vol_ann = risk_data['annualized_volatility'] * 100.0
        vol_daily = (risk_data['annualized_volatility'] / (252**0.5)) * 100.0
        st.markdown(render_metric_card(
            label="3. Annualized Volatility (σ)",
            value=f"{vol_ann:.2f}%",
            subvalue=f"Daily Volatility: {vol_daily:.2f}%",
            help_text="Annualized standard deviation of daily log returns (252-day Indian market convention)."
        ), unsafe_allow_html=True)

    with m4:
        mdd_pct = risk_data['max_drawdown'] * 100.0
        avg_dd = risk_data.get('average_drawdown', 0.0) * 100.0
        st.markdown(render_metric_card(
            label="4. Maximum Drawdown (MDD)",
            value=f"{mdd_pct:.2f}%",
            subvalue=f"Average Drawdown: {avg_dd:.2f}%",
            help_text="Deepest historical decline from any peak to subsequent trough over the observation window."
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # SECONDARY QUANTITATIVE RISK METRICS (ROW 2)
    # -------------------------------------------------------------
    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.markdown(render_metric_card(
            label="Sharpe Ratio (Rf=6.5%)",
            value=f"{risk_data['sharpe_ratio']:.2f}",
            subvalue=f"Sortino: {risk_data.get('sortino_ratio', 0.0):.2f}",
            help_text="Excess return over 6.5% Indian 10-Year G-Sec benchmark per unit of total volatility."
        ), unsafe_allow_html=True)

    with m6:
        st.markdown(render_metric_card(
            label="Benchmark Beta (β)",
            value=f"{risk_data['beta']:.2f}",
            subvalue="Relative to NIFTY 50",
            help_text="Sensitivity of portfolio returns to market benchmark swings (β > 1 indicates amplified cyclicality)."
        ), unsafe_allow_html=True)

    with m7:
        var_pct = risk_data['var_95'] * 100.0
        cvar_pct = risk_data.get('cvar_95', var_pct * 1.25) * 100.0
        st.markdown(render_metric_card(
            label="Value at Risk (95% 1-Day)",
            value=f"{var_pct:.2f}%",
            subvalue=f"CVaR (Tail Risk): {cvar_pct:.2f}%",
            help_text="Parametric 1-day threshold loss at 95% statistical confidence."
        ), unsafe_allow_html=True)

    with m8:
        holdings_count = len(risk_data["holdings"])
        div_label = "Well Diversified" if holdings_count >= 6 else ("Moderately Concentrated" if holdings_count >= 3 else "High Concentration")
        st.markdown(render_metric_card(
            label="Holdings & Structure",
            value=f"{holdings_count} Positions",
            subvalue=div_label,
            help_text="Total number of active equity and ETF holdings currently composing the portfolio."
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # PRIMARY VISUALIZATIONS ROW (PERFORMANCE & ALLOCATION)
    # -------------------------------------------------------------
    col_chart, col_side = st.columns([7.5, 4.5])

    with col_chart:
        fig_perf = plot_portfolio_performance(
            port_values=risk_data["port_values"],
            benchmark_prices=risk_data.get("benchmark_prices"),
            normalize=True
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    with col_side:
        # Treemap toggle
        treemap_mode = st.segmented_control(
            "Treemap View",
            options=["By Asset", "By Sector"],
            default="By Asset",
            label_visibility="collapsed",
            key="overview_treemap_toggle"
        )
        if not treemap_mode:
            treemap_mode = "By Asset"
        fig_tree = plot_allocation_treemap(risk_data["holdings"], by_sector=(treemap_mode == "By Sector"))
        st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # SECONDARY ROW: UNDERWATER DRAWDOWN & OBSERVATIONS
    # -------------------------------------------------------------
    col_dd, col_obs = st.columns([6.8, 5.2])

    with col_dd:
        fig_dd = plot_drawdown_curve(risk_data["drawdown_df"])
        st.plotly_chart(fig_dd, use_container_width=True)

    with col_obs:
        st.markdown(
            f"<div style='font-size: 13px; font-weight: 700; color: {COLORS['primary_text']}; margin-bottom: 8px;'>Risk & Factor Observations</div>",
            unsafe_allow_html=True
        )
        obs_html = render_observation_banner(risk_data.get("observations", []))
        st.markdown(obs_html, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # ACTIVE HOLDINGS SNAPSHOT TABLE
    # -------------------------------------------------------------
    st.markdown(
        f"<div style='font-size: 13px; font-weight: 700; color: {COLORS['primary_text']}; margin-bottom: 6px;'>Active Holdings Snapshot</div>",
        unsafe_allow_html=True
    )

    h_df = risk_data["holdings"].copy()
    display_h = h_df[["symbol", "name", "sector", "quantity", "average_cost", "latest_price", "current_value", "weight", "return_pct"]].copy()
    display_h["weight"] = display_h["weight"].apply(lambda w: f"{w * 100:.1f}%")
    display_h["return_pct"] = display_h["return_pct"].apply(lambda r: f"{r * 100:+.1f}%")
    display_h["current_value"] = display_h["current_value"].apply(lambda v: f"₹ {v:,.0f}")
    display_h["average_cost"] = display_h["average_cost"].apply(lambda c: f"₹ {c:,.1f}")
    display_h["latest_price"] = display_h["latest_price"].apply(lambda p: f"₹ {p:,.1f}")

    display_h.columns = ["Symbol", "Name", "Sector", "Quantity", "Avg Cost", "Latest Price", "Current Value", "Weight", "P&L Return"]
    st.dataframe(display_h, use_container_width=True, hide_index=True)
