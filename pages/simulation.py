"""
Screen 05 — Monte Carlo Simulation Lab for SIGMORA.
Signature quantitative simulation suite featuring:
- Joint Historical Bootstrap (Vector resampling preserving empirical fat tails & co-movement)
- Multivariate Parametric Simulation (Correlated normal returns with positive semi-definite covariance)
- High-fidelity Fan Chart, Ending Value Histograms, and Tail Loss Probabilities.
"""

import streamlit as st
import pandas as pd
import numpy as np
from services.portfolio_service import PortfolioService
from services.simulation_service import SimulationService
from components.metric_display import render_metric_card
from components.chart_components import (
    plot_monte_carlo_fan_chart, plot_simulation_distribution
)
from config import (
    COLORS, SIMULATION_HORIZONS, DEFAULT_SIMULATION_COUNT,
    DEFAULT_RANDOM_SEED
)


def render_simulation_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)
    sim_service = SimulationService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    holdings = portfolio_service.get_holdings_summary(portfolio_id)
    if holdings.empty:
        st.warning("Portfolio has no active holdings to simulate.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Monte Carlo Simulation Laboratory</h2>",
        unsafe_allow_html=True
    )

    # Simulation Parameter Controls
    with st.expander("Simulation Parameters & Modeling Assumptions", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            method = st.selectbox(
                "Simulation Method",
                ["Historical Bootstrap", "Multivariate Parametric"],
                index=0,
                help="Bootstrap resamples joint empirical return vectors; Parametric draws from a multivariate normal distribution parameterized by historical mean and covariance."
            )
        with c2:
            horizon_label = st.selectbox("Forecast Horizon", list(SIMULATION_HORIZONS.keys()), index=3)
            horizon_days = SIMULATION_HORIZONS[horizon_label]
        with c3:
            num_sims = st.selectbox("Path Iterations", [1000, 5000, 10000], index=0)
        with c4:
            seed = st.number_input("Deterministic Random Seed", min_value=1, max_value=999999, value=DEFAULT_RANDOM_SEED)

        c_block, c_sip, c_goal = st.columns([4, 4, 4])
        with c_block:
            block_size = 1
            if method == "Historical Bootstrap":
                block_size = st.slider("Block Bootstrap Size (Days)", min_value=1, max_value=21, value=1, help="Values > 1 resample contiguous time blocks to retain short-term serial autocorrelation.")
        with c_sip:
            monthly_sip = st.number_input("Monthly SIP Inflow (₹)", min_value=0, max_value=1000000, value=0, step=5000, help="Simulates recurring monthly cash contributions compounding into the portfolio.")
        with c_goal:
            goal_target = st.number_input("Financial Goal Target (₹)", min_value=0, max_value=500000000, value=0, step=250000, help="Specify a wealth target to calculate the mathematical probability P(V_T >= Goal).")

        run_btn = st.button("Execute Monte Carlo Simulation", type="primary", use_container_width=True)

    # Simulation execution
    method_key = "BOOTSTRAP" if method == "Historical Bootstrap" else "PARAMETRIC"
    goal_val = float(goal_target) if goal_target > 0 else None
    sim_cache_key = f"sim_{portfolio_id}_{method_key}_{horizon_days}_{num_sims}_{seed}_{block_size}_{monthly_sip}_{goal_val}"

    if run_btn or sim_cache_key not in st.session_state:
        with st.spinner(f"Simulating {num_sims:,} portfolio paths over {horizon_days} trading days using {method}..."):
            try:
                sim_res = sim_service.run_simulation(
                    portfolio_id=portfolio_id,
                    method=method_key,
                    horizon_days=horizon_days,
                    num_simulations=num_sims,
                    random_seed=seed,
                    block_size=block_size,
                    monthly_sip=float(monthly_sip),
                    goal_target_value=goal_val
                )
                st.session_state[sim_cache_key] = sim_res
            except Exception as e:
                st.error(f"Simulation failed: {str(e)}")
                return

    sim_data = st.session_state[sim_cache_key]

    # Goal & SIP Highlights Bar (if active)
    total_inv = sim_data.get("total_invested", sim_data["initial_value"])
    goal_prob = sim_data.get("goal_probability")
    if monthly_sip > 0 or goal_prob is not None:
        c_sip_h, c_goal_h, c_loss_h = st.columns(3)
        with c_sip_h:
            st.markdown(render_metric_card(
                label="Total Invested Capital",
                value=f"₹ {total_inv:,.0f}",
                subvalue=f"Initial ₹ {sim_data['initial_value']:,.0f} + SIP ₹ {total_inv - sim_data['initial_value']:,.0f}",
                help_text="Starting portfolio capital plus accumulated monthly SIP inflows."
            ), unsafe_allow_html=True)
        with c_goal_h:
            if goal_prob is not None:
                prob_pct = goal_prob * 100.0
                st.markdown(render_metric_card(
                    label=f"Goal Probability (Target: ₹ {goal_val:,.0f})",
                    value=f"{prob_pct:.1f}%",
                    delta="Likely" if prob_pct >= 70 else ("Moderate" if prob_pct >= 40 else "Challenging"),
                    delta_positive=(prob_pct >= 50),
                    subvalue=f"Based on {num_sims:,} simulated market paths"
                ), unsafe_allow_html=True)
            else:
                st.markdown(render_metric_card(
                    label="Median Wealth Multiple",
                    value=f"{sim_data['summary_percentiles'][50] / total_inv:.2f}x",
                    subvalue=f"Median Ending: ₹ {sim_data['summary_percentiles'][50]:,.0f}"
                ), unsafe_allow_html=True)
        with c_loss_h:
            st.markdown(render_metric_card(
                label="Probability of Capital Loss",
                value=f"{sim_data['loss_probability']*100:.1f}%",
                delta="Low" if sim_data['loss_probability'] < 0.15 else "Elevated",
                delta_positive=(sim_data['loss_probability'] < 0.15),
                subvalue="P(Ending Value < Invested Capital)"
            ), unsafe_allow_html=True)

    # Summary Output KPI Metrics
    initial_val = sim_data["initial_value"]
    pcts = sim_data["summary_percentiles"]

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.markdown(render_metric_card(
            label="5th %ile (Severe Bear)",
            value=f"₹ {pcts[5]:,.0f}",
            delta=f"{(pcts[5]/initial_val - 1)*100:+.1f}%",
            delta_positive=(pcts[5] >= initial_val),
            subvalue="Left tail threshold"
        ), unsafe_allow_html=True)

    with m2:
        st.markdown(render_metric_card(
            label="25th %ile (Conservative)",
            value=f"₹ {pcts[25]:,.0f}",
            delta=f"{(pcts[25]/initial_val - 1)*100:+.1f}%",
            delta_positive=(pcts[25] >= initial_val),
            subvalue="Lower quartile"
        ), unsafe_allow_html=True)

    with m3:
        st.markdown(render_metric_card(
            label="50th %ile (Median Path)",
            value=f"₹ {pcts[50]:,.0f}",
            delta=f"{(pcts[50]/initial_val - 1)*100:+.1f}%",
            delta_positive=(pcts[50] >= initial_val),
            subvalue="Central expectation"
        ), unsafe_allow_html=True)

    with m4:
        st.markdown(render_metric_card(
            label="75th %ile (Favorable)",
            value=f"₹ {pcts[75]:,.0f}",
            delta=f"{(pcts[75]/initial_val - 1)*100:+.1f}%",
            delta_positive=(pcts[75] >= initial_val),
            subvalue="Upper quartile"
        ), unsafe_allow_html=True)

    with m5:
        st.markdown(render_metric_card(
            label="95th %ile (Strong Bull)",
            value=f"₹ {pcts[95]:,.0f}",
            delta=f"{(pcts[95]/initial_val - 1)*100:+.1f}%",
            delta_positive=(pcts[95] >= initial_val),
            subvalue="Right tail expansion"
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Secondary probability metrics
    p_loss = sim_data["loss_probability"] * 100.0
    sim_stats_html = (
        f'<div style="background:{COLORS["white"]};border:1px solid {COLORS["border"]};border-radius:6px;padding:10px 18px;display:flex;justify-content:space-between;align-items:center;">'
        f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Probability of Capital Loss</span>'
        f'<div style="font-size:18px;font-weight:800;color:{COLORS["negative"] if p_loss > 30 else COLORS["graphite"]};">{p_loss:.1f}%</div></div>'
        f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Median Simulated Drawdown</span>'
        f'<div style="font-size:18px;font-weight:800;color:{COLORS["negative"]};">{sim_data["median_max_drawdown"]*100:.1f}%</div></div>'
        f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Worst Simulated Drawdown</span>'
        f'<div style="font-size:18px;font-weight:800;color:{COLORS["negative"]};">{sim_data["worst_max_drawdown"]*100:.1f}%</div></div>'
        f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Active Seed</span>'
        f'<div style="font-size:14px;font-weight:700;color:{COLORS["slate"]};font-family:monospace;">#{seed}</div></div>'
        f'</div>'
    )
    st.markdown(sim_stats_html, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # Fan Chart
    fig_fan = plot_monte_carlo_fan_chart(sim_data)
    st.plotly_chart(fig_fan, use_container_width=True)

    # Distribution Histogram
    fig_dist = plot_simulation_distribution(sim_data)
    st.plotly_chart(fig_dist, use_container_width=True)

    # Regulatory Disclaimer Banner
    disclaimer_html = (
        f'<div style="background:{COLORS["warm_paper"]};border-left:3px solid {COLORS["amber"]};padding:8px 14px;margin-top:16px;border-radius:4px;">'
        f'<span style="font-size:11px;color:{COLORS["graphite"]};font-style:italic;"><b>Hypothetical Simulation Disclaimer:</b> {sim_data["disclaimer"]}</span>'
        f'</div>'
    )
    st.markdown(disclaimer_html, unsafe_allow_html=True)
