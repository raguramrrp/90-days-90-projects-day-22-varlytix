"""
Screen 02 — Portfolio Management for VARLYTIX.
Enables creating/renaming/deleting portfolios, logging transactions (Buy/Sell)
with weighted-average cost basis accounting, and editing holdings.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService
from services.broker_import_service import (
    BrokerImportService, SAMPLE_ZERODHA_DATA, SAMPLE_GROWW_DATA,
    SAMPLE_ANGEL_ONE_DATA, SAMPLE_UPSTOX_DATA
)
from config import COLORS, CURRENCY_SYMBOL, BASE_CURRENCY


def render_portfolio_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)
    market_service = MarketDataService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Portfolio Architecture & Transactions</h2>",
        unsafe_allow_html=True
    )

    tab_holdings, tab_tx, tab_import, tab_manage = st.tabs([
        "Active Holdings",
        "Log Transaction (Buy/Sell)",
        "One-Click Broker Import",
        "Portfolio Configuration"
    ])

    # 1. Active Holdings Tab
    with tab_holdings:
        holdings = portfolio_service.get_holdings_summary(portfolio_id)

        c_search, c_export = st.columns([8, 4])
        with c_search:
            search_query = st.text_input("Filter Holdings", placeholder="Search by symbol, company, or sector...", label_visibility="collapsed")
        with c_export:
            if not holdings.empty:
                csv_data = holdings.to_csv(index=False)
                st.download_button(
                    label="Download Holdings CSV",
                    data=csv_data,
                    file_name=f"{portfolio.portfolio_name.replace(' ', '_')}_holdings.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        if holdings.empty:
            st.info("No active holdings in this portfolio yet. Use the 'Log Transaction' tab to add your first position.")
        else:
            filtered_df = holdings.copy()
            if search_query:
                q = search_query.upper()
                filtered_df = filtered_df[
                    filtered_df["symbol"].str.contains(q, na=False) |
                    filtered_df["name"].str.upper().str.contains(q, na=False) |
                    filtered_df["sector"].str.upper().str.contains(q, na=False)
                ]

            total_invested = filtered_df["invested_value"].sum()
            total_current = filtered_df["current_value"].sum()
            total_pnl = total_current - total_invested
            overall_ret = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

            summary_bar_html = (
                f'<div style="background:{COLORS["white"]};border:1px solid {COLORS["border"]};border-radius:6px;padding:10px 16px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">'
                f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Total Invested</span>'
                f'<div style="font-size:16px;font-weight:700;color:{COLORS["graphite"]};">₹ {total_invested:,.0f}</div></div>'
                f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Current Value</span>'
                f'<div style="font-size:16px;font-weight:700;color:{COLORS["deep_teal"]};">₹ {total_current:,.0f}</div></div>'
                f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Total Unrealized P&L</span>'
                f'<div style="font-size:16px;font-weight:700;color:{COLORS["positive"] if total_pnl >= 0 else COLORS["negative"]};">₹ {total_pnl:+,.0f} ({overall_ret:+.2f}%)</div></div>'
                f'<div><span style="font-size:11px;font-weight:700;color:{COLORS["secondary_text"]};text-transform:uppercase;">Cost Method</span>'
                f'<div style="font-size:13px;font-weight:600;color:{COLORS["slate"]};">Weighted Average Cost</div></div>'
                f'</div>'
            )
            st.markdown(summary_bar_html, unsafe_allow_html=True)

            disp_df = filtered_df[["symbol", "name", "sector", "exchange", "quantity", "average_cost", "latest_price", "invested_value", "current_value", "weight", "return_pct"]].copy()
            disp_df["quantity"] = disp_df["quantity"].apply(lambda q: f"{q:,.0f}")
            disp_df["average_cost"] = disp_df["average_cost"].apply(lambda c: f"₹ {c:,.2f}")
            disp_df["latest_price"] = disp_df["latest_price"].apply(lambda p: f"₹ {p:,.2f}")
            disp_df["invested_value"] = disp_df["invested_value"].apply(lambda v: f"₹ {v:,.0f}")
            disp_df["current_value"] = disp_df["current_value"].apply(lambda v: f"₹ {v:,.0f}")
            disp_df["weight"] = disp_df["weight"].apply(lambda w: f"{w * 100:.2f}%")
            disp_df["return_pct"] = disp_df["return_pct"].apply(lambda r: f"{r * 100:+.2f}%")

            disp_df.columns = ["Symbol", "Asset Name", "Sector", "Exchange", "Qty", "Avg Cost", "Latest Price", "Invested (₹)", "Current (₹)", "Weight (%)", "Return (%)"]
            st.dataframe(disp_df, use_container_width=True, hide_index=True)

    # 2. Log Transaction Tab
    with tab_tx:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 8px;'>Record Position Execution</h3>", unsafe_allow_html=True)
        st.caption("Transactions update positions using Weighted Average Cost accounting: New Cost = (Old Val + New Cost + Fees) / Total Qty.")

        with st.form("tx_form", clear_on_submit=True):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                tx_type = st.selectbox("Action", ["BUY", "SELL"])
                symbol = st.text_input("Asset Symbol", placeholder="e.g. RELIANCE, TCS, DEMO_TECH_TCS").upper().strip()
            with col_t2:
                qty = st.number_input("Quantity", min_value=1.0, value=100.0, step=1.0)
                price = st.number_input("Execution Price (₹)", min_value=0.05, value=1000.0, step=1.0)
            with col_t3:
                tx_date = st.date_input("Transaction Date", value=datetime.now().date())
                fees = st.number_input("Brokerage & Exchange Fees (₹)", min_value=0.0, value=20.0, step=5.0)

            notes = st.text_input("Transaction Notes / Strategy", placeholder="e.g. Core long allocation")
            submit_tx = st.form_submit_button("Record Transaction", type="primary")

            if submit_tx:
                if not symbol:
                    st.error("Please enter a valid stock symbol.")
                else:
                    try:
                        tx = portfolio_service.record_transaction(
                            portfolio_id=portfolio_id,
                            symbol=symbol,
                            transaction_type=tx_type,
                            quantity=qty,
                            price=price,
                            fees=fees,
                            tx_date=tx_date,
                            notes=notes
                        )
                        # Sync prices if needed
                        asset = portfolio_service.get_or_create_asset(symbol)
                        market_service.sync_asset_prices(asset)
                        st.success(f"Recorded {tx_type} transaction for {qty} shares of {symbol} at ₹{price:,.2f}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transaction failed: {str(e)}")

    # 3. One-Click Broker Import Tab
    with tab_import:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 10px;'>Instant Indian Broker Statement Import</h3>", unsafe_allow_html=True)

        broker_service = BrokerImportService(db)

        # 1-Click Sample Testing Buttons
        st.markdown(f"<div style='font-size: 11px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 6px;'>TEST DRIVE IMMEDIATELY WITH SAMPLE BROKER STATEMENTS:</div>", unsafe_allow_html=True)
        b_c1, b_c2, b_c3, b_c4 = st.columns(4)
        sample_to_load = None
        sample_name = None

        with b_c1:
            if st.button("Load Zerodha Kite CSV", use_container_width=True):
                sample_to_load = SAMPLE_ZERODHA_DATA.encode("utf-8")
                sample_name = "zerodha_holdings.csv"
        with b_c2:
            if st.button("Load Groww CSV", use_container_width=True):
                sample_to_load = SAMPLE_GROWW_DATA.encode("utf-8")
                sample_name = "groww_holdings.csv"
        with b_c3:
            if st.button("Load Angel One CSV", use_container_width=True):
                sample_to_load = SAMPLE_ANGEL_ONE_DATA.encode("utf-8")
                sample_name = "angel_one_holdings.csv"
        with b_c4:
            if st.button("Load Upstox CSV", use_container_width=True):
                sample_to_load = SAMPLE_UPSTOX_DATA.encode("utf-8")
                sample_name = "upstox_holdings.csv"

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Or Upload Custom File (.csv, .xlsx, .xls)", type=["csv", "xlsx", "xls"], key="broker_file_uploader")

        # Handle file source
        active_content = None
        active_fname = None
        if uploaded_file is not None:
            active_content = uploaded_file.read()
            active_fname = uploaded_file.name
        elif sample_to_load is not None:
            active_content = sample_to_load
            active_fname = sample_name
            st.session_state["cached_broker_content"] = active_content
            st.session_state["cached_broker_fname"] = active_fname
        elif "cached_broker_content" in st.session_state:
            active_content = st.session_state["cached_broker_content"]
            active_fname = st.session_state["cached_broker_fname"]

        if active_content:
            try:
                detected_broker, parsed_df = broker_service.parse_statement(active_content, active_fname)
                st.success(f"Detected Format: **{detected_broker}** | Successfully parsed {len(parsed_df)} holdings.")

                # Preview Table
                preview_disp = parsed_df[["raw_symbol", "name", "sector", "quantity", "avg_cost", "invested_value"]].copy()
                preview_disp["quantity"] = preview_disp["quantity"].apply(lambda q: f"{q:,.0f}")
                preview_disp["avg_cost"] = preview_disp["avg_cost"].apply(lambda c: f"₹ {c:,.2f}")
                preview_disp["invested_value"] = preview_disp["invested_value"].apply(lambda v: f"₹ {v:,.0f}")
                preview_disp.columns = ["Symbol", "Asset Name", "Sector", "Quantity", "Avg Cost (₹)", "Total Investment (₹)"]
                st.dataframe(preview_disp, use_container_width=True, hide_index=True)

                # Destination controls
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    dest_choice = st.radio(
                        "Import Destination",
                        ["Merge into Currently Active Portfolio", "Create a New Standalone Portfolio"],
                        key="broker_dest_radio"
                    )
                with col_d2:
                    new_port_name = st.text_input("New Portfolio Name (if creating)", value=f"{detected_broker} Imported Portfolio")

                if st.button("Confirm and Import Holdings", type="primary"):
                    with st.spinner("Recording positions and syncing price histories..."):
                        if "Create" in dest_choice:
                            target_p = portfolio_service.create_portfolio(
                                name=new_port_name or f"{detected_broker} Portfolio",
                                description=f"Imported from {detected_broker} statement ({len(parsed_df)} holdings)"
                            )
                            target_id = target_p.id
                            st.session_state["current_portfolio_id"] = target_id
                        else:
                            target_id = portfolio_id

                        count = broker_service.import_parsed_holdings(
                            portfolio_id=target_id,
                            holdings_df=parsed_df,
                            notes=f"Auto-imported from {detected_broker}"
                        )
                        st.session_state.pop("cached_broker_content", None)
                        st.session_state.pop("cached_broker_fname", None)
                        st.success(f"Successfully imported {count} holdings into portfolio!")
                        st.rerun()

            except Exception as e:
                st.error(f"Failed to parse broker statement: {str(e)}")

    # 4. Portfolio Configuration Tab
    with tab_manage:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 8px;'>Portfolio Settings & Management</h3>", unsafe_allow_html=True)

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            st.markdown("#### Rename Active Portfolio")
            new_name = st.text_input("New Portfolio Name", value=portfolio.portfolio_name)
            if st.button("Save New Name"):
                if new_name.strip():
                    portfolio_service.rename_portfolio(portfolio_id, new_name)
                    st.success("Portfolio renamed successfully.")
                    st.rerun()

        with col_cfg2:
            st.markdown("#### Create New Portfolio")
            create_name = st.text_input("Create New Portfolio Name", placeholder="e.g. Momentum Tech Portfolio")
            create_desc = st.text_input("Description", placeholder="Optional investment thesis...")
            if st.button("Create Portfolio", type="primary"):
                if create_name.strip():
                    new_p = portfolio_service.create_portfolio(create_name, create_desc)
                    st.session_state["current_portfolio_id"] = new_p.id
                    st.success(f"Created portfolio: {new_p.portfolio_name}")
                    st.rerun()

        st.markdown(f"<hr style='border: 0.5px solid {COLORS['border']}; margin: 20px 0;'>", unsafe_allow_html=True)

        st.markdown("#### Delete Portfolio")
        st.warning("Deleting a portfolio removes all its positions, transactions, and simulation records permanently.")
        if st.button("Delete This Portfolio", type="secondary"):
            if portfolio_service.delete_portfolio(portfolio_id):
                st.session_state.pop("current_portfolio_id", None)
                st.success("Portfolio deleted.")
                st.rerun()
