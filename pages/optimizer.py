"""
Screen 07 — Portfolio Optimizer for SIGMORA.
Calculates optimal Markowitz capital allocations (Minimum Variance, Maximum Sharpe),
traces the Efficient Frontier, and compares candidate allocations against current weights.
"""

import streamlit as st
import pandas as pd
import numpy as np
from services.portfolio_service import PortfolioService
from services.optimization_service import OptimizationService
from components.metric_display import render_metric_card
from components.chart_components import plot_efficient_frontier
from components.what_if_rebalancer import render_what_if_sandbox
from config import COLORS, DEFAULT_RISK_FREE_RATE


def render_optimizer_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)
    opt_service = OptimizationService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    holdings = portfolio_service.get_holdings_summary(portfolio_id)
    if holdings.empty or len(holdings) < 2:
        st.warning("Portfolio optimization requires at least two distinct holdings.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Portfolio Allocation Optimizer & Efficient Frontier</h2>",
        unsafe_allow_html=True
    )

    tab_frontier, tab_sandbox = st.tabs([
        "Markowitz Efficient Frontier & Target Weights",
        "Interactive 'What If?' Rebalancing Sandbox"
    ])

    with tab_frontier:
        # Optimization Parameter Controls
        with st.expander("Optimization Constraints & Risk Parameters", expanded=True):
            col_o1, col_o2, col_o3 = st.columns(3)
            with col_o1:
                max_weight = st.slider("Maximum Position Limit (w_max)", min_value=0.15, max_value=1.0, value=0.40, step=0.05, help="Prevents excessive single-stock concentration.")
            with col_o2:
                min_weight = st.slider("Minimum Position Floor (w_min)", min_value=0.0, max_value=0.15, value=0.0, step=0.01, help="Ensures broad participation across assets.")
            with col_o3:
                rf_rate = st.number_input("Risk-Free Benchmark (Rf)", min_value=0.0, max_value=0.15, value=DEFAULT_RISK_FREE_RATE, step=0.005)

        with st.spinner("Solving constrained quadratic programming optimization..."):
            try:
                opt_data = opt_service.optimize_portfolio(
                    portfolio_id=portfolio_id,
                    max_position_weight=max_weight,
                    min_position_weight=min_weight,
                    risk_free_rate=rf_rate
                )
            except Exception as e:
                st.error(f"Optimization error: {str(e)}")
                return

        curr = opt_data["current"]
        min_var = opt_data["min_variance"]
        max_sharpe = opt_data["max_sharpe"]

        # Comparative Metrics (3 Cards)
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(render_metric_card(
                label="Current Portfolio",
                value=f"Sharpe: {curr['sharpe_ratio']:.2f}",
                subvalue=f"Vol: {curr['volatility']*100:.1f}% | Exp Ret: {curr['expected_return']*100:.1f}%"
            ), unsafe_allow_html=True)

        with c2:
            st.markdown(render_metric_card(
                label="Minimum Variance Allocation",
                value=f"Vol: {min_var['volatility']*100:.1f}%",
                delta=f"{(min_var['volatility'] - curr['volatility'])*100:.1f}% vol",
                delta_positive=(min_var['volatility'] < curr['volatility']),
                subvalue=f"Sharpe: {min_var['sharpe_ratio']:.2f} | Exp Ret: {min_var['expected_return']*100:.1f}%"
            ), unsafe_allow_html=True)

        with c3:
            st.markdown(render_metric_card(
                label="Maximum Sharpe Allocation",
                value=f"Sharpe: {max_sharpe['sharpe_ratio']:.2f}",
                delta=f"{max_sharpe['sharpe_ratio'] - curr['sharpe_ratio']:+.2f}",
                delta_positive=(max_sharpe['sharpe_ratio'] >= curr['sharpe_ratio']),
                subvalue=f"Vol: {max_sharpe['volatility']*100:.1f}% | Exp Ret: {max_sharpe['expected_return']*100:.1f}%"
            ), unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

        # Efficient Frontier Chart
        fig_frontier = plot_efficient_frontier(
            frontier_df=opt_data["efficient_frontier"],
            current_profile=curr,
            min_var=min_var,
            max_sharpe=max_sharpe
        )
        st.plotly_chart(fig_frontier, use_container_width=True)

        # Weight Comparison Table
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 6px;'>Asset Allocation Comparison Matrix</h3>", unsafe_allow_html=True)

        symbols = opt_data["symbols"]
        comp_rows = []
        for s in symbols:
            c_wt = curr["weights"].get(s, 0.0)
            mv_wt = min_var["weights"].get(s, 0.0)
            ms_wt = max_sharpe["weights"].get(s, 0.0)
            comp_rows.append({
                "Symbol": s,
                "Current Weight": f"{c_wt * 100:.2f}%",
                "Min Variance Weight": f"{mv_wt * 100:.2f}%",
                "Max Sharpe Weight": f"{ms_wt * 100:.2f}%",
                "Sharpe Delta (vs Current)": f"{(ms_wt - c_wt) * 100:+.2f}%",
            })

        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        # Model Limitations & Explicit Action Warning
        warn_html = (
            f'<div style="background:{COLORS["warm_paper"]};border-left:3px solid {COLORS["amber"]};padding:10px 14px;margin-top:18px;border-radius:4px;">'
            f'<div style="font-size:11px;font-weight:700;color:{COLORS["graphite"]};text-transform:uppercase;margin-bottom:2px;">'
            f'Mathematical Sensitivity & Estimation Risk Warning</div>'
            f'<div style="font-size:11.5px;color:{COLORS["secondary_text"]};line-height:1.4;">'
            f'Markowitz mean-variance optimization is famously sensitive to input assumptions (the "error-maximizer" property). '
            f'Historical sample returns and covariances contain estimation error. SIGMORA presents these candidate allocations '
            f'purely for analytical exploration and will never automatically modify your live portfolio weights without explicit manual execution.'
            f'</div>'
            f'</div>'
        )
        st.markdown(warn_html, unsafe_allow_html=True)

    with tab_sandbox:
        render_what_if_sandbox(db, portfolio_id)
