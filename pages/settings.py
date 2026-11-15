"""
Screen 11 — System Settings & Quantitative Preferences for VARLYTIX.
Allows configuring risk-free rates, annualization factors, benchmark assets,
and re-seeding the demo dataset.
"""

import streamlit as st
from config import (
    COLORS, DEFAULT_RISK_FREE_RATE, DEFAULT_TRADING_DAYS,
    DEFAULT_BENCHMARK_SYMBOL
)
from services.portfolio_service import PortfolioService
from scripts.seed_demo_data import seed_all


def render_settings_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>System Settings & Quantitative Preferences</h2>",
        unsafe_allow_html=True
    )

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown(f"### Quantitative Benchmarks")
        new_rf = st.number_input("Global Risk-Free Rate (Rf)", min_value=0.0, max_value=0.15, value=DEFAULT_RISK_FREE_RATE, step=0.005, format="%.3f")
        st.caption("Used as hurdle rate for Sharpe and Sortino ratio calculations.")

        new_days = st.selectbox("Annualization Factor (Trading Days / Year)", [250, 252, 260], index=1)
        st.caption("Standard for Indian equities on National Stock Exchange is 252.")

        cost_method = st.selectbox("Cost Basis Accounting Method", ["Weighted Average Cost", "First-In First-Out (FIFO)"], index=0)
        st.caption("Current engine applies documented Weighted Average Cost for all partial liquidations.")

    with col_s2:
        st.markdown(f"### Demo Workspace & Data Management")
        st.info("Need to reset your testing environment or reload clean synthetic market histories?")

        if st.button("Reload Complete Demo Dataset", type="primary", use_container_width=True):
            with st.spinner("Seeding demo assets, historical prices, and 3 model portfolios..."):
                seed_all()
                st.success("Demo dataset re-seeded successfully!")
                st.rerun()

        st.markdown(f"<hr style='border: 0.5px solid {COLORS['border']}; margin: 18px 0;'>", unsafe_allow_html=True)
        st.markdown("### Software Architecture & License")
        st.markdown("""
        - **Product:** VARLYTIX — Portfolio Risk Intelligence
        - **Engine:** Python 3.12, NumPy, SciPy, Pandas, Plotly, SQLAlchemy, SQLite, ReportLab
        - **Market Focus:** Indian Listed Equities & ETFs (NSE/BSE)
        - **Status:** Day 22 of 90 Days – 90 Projects
        """)
