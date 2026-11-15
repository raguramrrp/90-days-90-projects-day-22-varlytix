"""
Screen 04 — Correlation Intelligence for VARLYTIX.
Calculates Pearson co-movements across return frequencies (daily, weekly, monthly),
visualizes annotated diverging heatmaps, identifies high/low correlation clusters,
and tracks dynamic rolling correlation pairs.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from components.chart_components import plot_correlation_heatmap, _apply_varlytix_layout
from config import COLORS


def render_correlation_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)
    market_service = MarketDataService(db)

    holdings = portfolio_service.get_holdings_summary(portfolio_id)
    if holdings.empty:
        st.warning("Portfolio has no active holdings.")
        return

    symbols = holdings["symbol"].tolist()
    if len(symbols) < 2:
        st.info("Correlation analysis requires at least two distinct assets in the portfolio.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Correlation Intelligence & Co-Movement Matrix</h2>",
        unsafe_allow_html=True
    )

    # Controls row
    c_freq, c_win, c_info = st.columns([4, 4, 4])
    with c_freq:
        freq = st.selectbox("Return Aggregation Frequency", ["Daily Returns", "Weekly Returns (W-FRI)", "Monthly Returns (M)"])
    with c_win:
        roll_window = st.slider("Rolling Correlation Window (Days)", min_value=15, max_value=126, value=63, step=5)
    with c_info:
        st.caption("<b>Statistical Note:</b> Low historical correlation reduces portfolio variance under normal market regimes, but cross-asset correlations frequently spike toward 1.0 during severe liquidity shocks.", unsafe_allow_html=True)

    # Fetch aligned price matrix
    prices_df = market_service.get_price_matrix(symbols)
    if prices_df.empty or len(prices_df) < 10:
        st.error("Insufficient historical price data available to compute returns.")
        return

    # Aggregate returns based on selected frequency
    if "Weekly" in freq:
        resampled_prices = prices_df.resample("W-FRI").last().dropna()
        returns_df = resampled_prices.pct_change().dropna()
    elif "Monthly" in freq:
        resampled_prices = prices_df.resample("ME").last().dropna()
        returns_df = resampled_prices.pct_change().dropna()
    else:
        returns_df = prices_df.pct_change().dropna()

    corr_matrix = returns_df.corr()

    # Heatmap & Automated Cluster Analysis
    col_heat, col_clusters = st.columns([7, 5])

    with col_heat:
        fig_heat = plot_correlation_heatmap(corr_matrix)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_clusters:
        st.markdown(f"<h3 style='font-size: 13px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 8px;'>CORRELATION RANKING & OBSERVATIONS</h3>", unsafe_allow_html=True)

        # Extract pairwise correlations
        pairs = []
        n = len(symbols)
        for i in range(n):
            for j in range(i + 1, n):
                s1, s2 = symbols[i], symbols[j]
                r_val = corr_matrix.loc[s1, s2]
                pairs.append({"Asset A": s1, "Asset B": s2, "Correlation": r_val})

        df_pairs = pd.DataFrame(pairs).sort_values(by="Correlation", ascending=False)

        if not df_pairs.empty:
            top_corr = df_pairs.iloc[0]
            low_corr = df_pairs.iloc[-1]

            corr_summary_html = (
                f'<div style="background:{COLORS["white"]};border:1px solid {COLORS["border"]};border-radius:6px;padding:10px 14px;margin-bottom:8px;">'
                f'<div style="font-size:11px;font-weight:700;color:{COLORS["negative"]};text-transform:uppercase;">Highest Positive Co-Movement</div>'
                f'<div style="font-size:14px;font-weight:700;color:{COLORS["graphite"]};margin:2px 0;">{top_corr["Asset A"]} & {top_corr["Asset B"]}</div>'
                f'<div style="font-size:12px;color:{COLORS["secondary_text"]};">Pearson r = <b>{top_corr["Correlation"]:.3f}</b> — Limited diversification</div>'
                f'</div>'
                f'<div style="background:{COLORS["white"]};border:1px solid {COLORS["border"]};border-radius:6px;padding:10px 14px;margin-bottom:12px;">'
                f'<div style="font-size:11px;font-weight:700;color:{COLORS["positive"]};text-transform:uppercase;">Lowest / Negative Co-Movement</div>'
                f'<div style="font-size:14px;font-weight:700;color:{COLORS["graphite"]};margin:2px 0;">{low_corr["Asset A"]} & {low_corr["Asset B"]}</div>'
                f'<div style="font-size:12px;color:{COLORS["secondary_text"]};">Pearson r = <b>{low_corr["Correlation"]:.3f}</b> — High diversification benefit</div>'
                f'</div>'
            )
            st.markdown(corr_summary_html, unsafe_allow_html=True)

            # Display ranking table
            df_display_pairs = df_pairs.copy()
            df_display_pairs["Correlation"] = df_display_pairs["Correlation"].apply(lambda r: f"{r:+.3f}")
            st.dataframe(df_display_pairs, use_container_width=True, hide_index=True)

    # Dynamic Rolling Correlation Section
    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-size: 14px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 6px;'>Rolling Pairwise Correlation Over Time</h3>", unsafe_allow_html=True)

    col_pair_sel, col_scatter_sel = st.columns([6, 6])
    with col_pair_sel:
        pair_options = [f"{p['Asset A']} vs {p['Asset B']}" for _, p in df_pairs.iterrows()]
        selected_pair = st.selectbox("Select Asset Pair to Track", pair_options)

    s1, s2 = selected_pair.split(" vs ")

    # Calculate rolling correlation
    daily_rets = prices_df[[s1, s2]].pct_change().dropna()
    rolling_corr = daily_rets[s1].rolling(window=roll_window).corr(daily_rets[s2]).dropna()

    fig_roll = go.Figure()
    fig_roll.add_trace(go.Scatter(
        x=rolling_corr.index,
        y=rolling_corr.values,
        mode="lines",
        name=f"Rolling r ({s1}, {s2})",
        line=dict(color=COLORS["deep_teal"], width=2.0)
    ))
    fig_roll.add_hline(y=0.0, line_dash="dash", line_color=COLORS["slate"], line_width=1.0)
    fig_roll = _apply_varlytix_layout(fig_roll, title=f"{roll_window}-Day Moving Correlation: {s1} vs {s2}", height=300)
    fig_roll.update_layout(
        yaxis_title="Pearson Correlation (r)",
        yaxis=dict(range=[-1.05, 1.05], gridcolor=COLORS["border"]),
        margin=dict(l=40, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_roll, use_container_width=True)
