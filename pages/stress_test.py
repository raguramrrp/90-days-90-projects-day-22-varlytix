"""
Screen 06 — Stress Test Lab for SIGMORA.
Evaluates portfolio resilience against systemic market shocks, sector-specific drawdowns,
historical crisis replays, and custom asset-level stress scenarios.
"""

import streamlit as st
import pandas as pd
from services.portfolio_service import PortfolioService
from services.stress_test_service import StressTestService
from services.market_data_service import MarketDataService
from analytics.stress_testing import replay_historical_period
from components.metric_display import render_metric_card
from components.chart_components import plot_stress_comparison
from config import COLORS, PRESET_STRESS_SCENARIOS


def render_stress_test_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)
    stress_service = StressTestService(db)
    market_service = MarketDataService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    holdings = portfolio_service.get_holdings_summary(portfolio_id)
    if holdings.empty:
        st.warning("Portfolio has no active holdings to stress test.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Stress Testing Laboratory</h2>",
        unsafe_allow_html=True
    )

    tab_preset, tab_custom, tab_historical = st.tabs(["Standard Macro Shocks", "Custom Asset Shock Builder", "Historical Event Replay"])

    # 1. Preset Scenarios Tab
    with tab_preset:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 8px;'>Predefined Macroeconomic Stress Scenarios</h3>", unsafe_allow_html=True)
        st.caption("Apply standard regulatory and institutional shock assumptions to test systemic capital impact.")

        preset_results = []
        for key in PRESET_STRESS_SCENARIOS.keys():
            res = stress_service.run_preset_scenario(portfolio_id, key)
            preset_results.append(res)

        # Comparative Bar Chart
        fig_stress = plot_stress_comparison(preset_results)
        st.plotly_chart(fig_stress, use_container_width=True)

        # Scenarios Table
        table_rows = []
        for r in preset_results:
            table_rows.append({
                "Scenario Name": r["scenario_name"],
                "Type": r["scenario_type"],
                "Original Capital": f"₹ {r['original_value']:,.0f}",
                "Stressed Value": f"₹ {r['stressed_value']:,.0f}",
                "Simulated Capital Loss": f"₹ {r['portfolio_loss']:,.0f}",
                "Portfolio Impact (%)": f"{r['portfolio_return'] * 100:+.2f}%",
            })

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        selected_scenario_name = st.selectbox(
            "Inspect Detailed Asset-Level Impact for Scenario:",
            [r["scenario_name"] for r in preset_results]
        )
        matched_res = next(r for r in preset_results if r["scenario_name"] == selected_scenario_name)
        breakdown_df = matched_res["asset_breakdown"].copy()

        disp_breakdown = breakdown_df[["symbol", "sector", "current_value", "shock_pct", "stressed_value", "value_loss", "loss_contribution_pct", "new_weight"]].copy()
        disp_breakdown["current_value"] = disp_breakdown["current_value"].apply(lambda v: f"₹ {v:,.0f}")
        disp_breakdown["shock_pct"] = disp_breakdown["shock_pct"].apply(lambda s: f"{s * 100:+.1f}%")
        disp_breakdown["stressed_value"] = disp_breakdown["stressed_value"].apply(lambda v: f"₹ {v:,.0f}")
        disp_breakdown["value_loss"] = disp_breakdown["value_loss"].apply(lambda l: f"₹ {l:,.0f}")
        disp_breakdown["loss_contribution_pct"] = disp_breakdown["loss_contribution_pct"].apply(lambda c: f"{c * 100:.1f}%")
        disp_breakdown["new_weight"] = disp_breakdown["new_weight"].apply(lambda w: f"{w * 100:.1f}%")

        disp_breakdown.columns = ["Symbol", "Sector", "Pre-Shock Value", "Applied Shock", "Post-Shock Value", "Value Impact", "Loss Contribution (%)", "New Weight (%)"]
        st.dataframe(disp_breakdown, use_container_width=True, hide_index=True)

    # 2. Custom Scenario Builder Tab
    with tab_custom:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 8px;'>Tailored Asset Shock Builder</h3>", unsafe_allow_html=True)
        st.caption("Specify individual asset price movements to simulate idiosyncratic risks (e.g. earnings misses, regulatory fines, leadership changes).")

        custom_shocks = {}
        cols = st.columns(min(4, len(holdings)))
        for i, (_, row) in enumerate(holdings.iterrows()):
            sym = row["symbol"]
            with cols[i % len(cols)]:
                shock_val = st.slider(f"{sym} (%)", min_value=-50, max_value=30, value=-15, step=1, key=f"cust_shock_{sym}")
                custom_shocks[sym] = shock_val / 100.0

        custom_res = stress_service.run_custom_scenario(portfolio_id, custom_shocks)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(render_metric_card("Pre-Shock Portfolio", f"₹ {custom_res['original_value']:,.0f}"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_metric_card("Stressed Portfolio", f"₹ {custom_res['stressed_value']:,.0f}"), unsafe_allow_html=True)
        with m3:
            st.markdown(render_metric_card(
                "Total Capital Impact",
                f"₹ {custom_res['portfolio_loss']:+,.0f}",
                delta=f"{custom_res['portfolio_return']*100:+.2f}%",
                delta_positive=(custom_res['portfolio_loss'] >= 0)
            ), unsafe_allow_html=True)
        with m4:
            st.markdown(render_metric_card("Assets Stressed", f"{len(custom_shocks)} Holdings"), unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        st.dataframe(custom_res["asset_breakdown"][["symbol", "current_value", "shock_pct", "stressed_value", "value_loss", "new_weight"]], use_container_width=True)

    # 3. Historical Replay Tab
    with tab_historical:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 8px;'>Historical Market Shock Replay</h3>", unsafe_allow_html=True)
        st.caption("Replay exact empirical price declines from notable market stress periods.")

        HISTORICAL_EVENTS = {
            "2022 Inflation & Rate Hike Shock": ("2022-01-10", "2022-06-20", "Global central bank rate tightening and energy inflation correction."),
            "2023 Adani-Hindenburg Market Volatility": ("2023-01-23", "2023-03-01", "Banking and infrastructure liquidity shock."),
            "2024 Election Day Volatility Spike": ("2024-06-03", "2024-06-05", "Sharp one-day election result market correction and subsequent recovery."),
        }

        sel_event = st.selectbox("Select Historical Crisis Period to Replay", list(HISTORICAL_EVENTS.keys()))
        s_date, e_date, desc = HISTORICAL_EVENTS[sel_event]
        st.info(f"<b>Period:</b> {s_date} to {e_date} | <i>{desc}</i>", icon="ℹ️")

        symbols = holdings["symbol"].tolist()
        quantities = holdings.set_index("symbol")["quantity"]
        prices_df = market_service.get_price_matrix(symbols)

        if not prices_df.empty:
            replay_res = replay_historical_period(prices_df, quantities, s_date, e_date)
            if "error" in replay_res:
                st.warning(f"Replay Notice: {replay_res['error']} Synthetic data timeframe may differ from calendar crisis dates.")
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Starting Value", f"₹ {replay_res['starting_value']:,.0f}")
                with c2:
                    st.metric("Ending Value", f"₹ {replay_res['ending_value']:,.0f}", delta=f"{replay_res['period_return']*100:+.2f}%")
                with c3:
                    st.metric("Max Drawdown in Period", f"{replay_res['max_drawdown']*100:.2f}%")

                st.line_chart(replay_res["portfolio_path"])
