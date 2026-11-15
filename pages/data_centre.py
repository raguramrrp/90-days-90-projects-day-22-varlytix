"""
Screen 09 — Data Centre for VARLYTIX.
Audits historical market data freshness, gaps, and quality metrics across all registered assets.
Supports custom CSV price imports with schema validation and preview.
"""

import streamlit as st
import pandas as pd
from services.data_quality_service import DataQualityService
from services.market_data_service import MarketDataService
from services.portfolio_service import PortfolioService
from providers.csv_provider import CSVMarketDataProvider
from config import COLORS


def render_data_centre_page(db, portfolio_id: int):
    dq_service = DataQualityService(db)
    market_service = MarketDataService(db)
    portfolio_service = PortfolioService(db)

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Market Data Centre & Data Quality Audit</h2>",
        unsafe_allow_html=True
    )

    tab_audit, tab_import = st.tabs(["Data Quality & Observation Audit", "Import Custom CSV Price Series"])

    # 1. Audit Tab
    with tab_audit:
        audits = dq_service.audit_all_assets()
        if not audits:
            st.info("No registered assets found in the database.")
        else:
            df_audit = pd.DataFrame(audits)

            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total Tracked Instruments", len(df_audit))
            with col_stat2:
                total_obs = df_audit["observations"].sum()
                st.metric("Total Historical Observations", f"{total_obs:,}")
            with col_stat3:
                excellent_count = (df_audit["quality_status"] == "EXCELLENT").sum()
                st.metric("Data Quality Rating", f"{excellent_count}/{len(df_audit)} Instruments Tier 1")

            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

            disp_audit = df_audit[["symbol", "name", "exchange", "observations", "first_date", "last_date", "missing_business_days", "duplicate_dates", "freshness", "quality_status", "data_source"]].copy()
            disp_audit.columns = ["Symbol", "Name", "Exchange", "Observations", "Earliest Date", "Latest Date", "Missing B-Days", "Duplicates", "Freshness", "Audit Status", "Source Provider"]

            st.dataframe(disp_audit, use_container_width=True, hide_index=True)

    # 2. CSV Import Tab
    with tab_import:
        st.markdown(f"<h3 style='font-size: 14px; font-weight: 700; color: {COLORS['graphite']}; margin-bottom: 8px;'>Upload Historical Price Series (CSV)</h3>", unsafe_allow_html=True)
        st.caption("Upload an end-of-day price CSV. Required headers: Date, Close (or Adjusted Close). Optional: Open, High, Low, Volume.")

        col_up, col_preview = st.columns([5, 7])
        with col_up:
            target_symbol = st.text_input("Map to Instrument Symbol", placeholder="e.g. RELIANCE, HDFCBANK").strip().upper()
            uploaded_file = st.file_uploader("Select Price History CSV", type=["csv"])

        csv_provider = CSVMarketDataProvider()
        if uploaded_file is not None and target_symbol:
            valid, msg, df_parsed = csv_provider.validate_and_parse_csv(uploaded_file)
            if not valid:
                st.error(f"Validation Rejected: {msg}")
            else:
                st.success(f"Validation Passed: {msg}")
                with col_preview:
                    st.markdown("<b>Parsed Observations Preview (First 5 Rows):</b>", unsafe_allow_html=True)
                    st.dataframe(df_parsed.head(5), use_container_width=True)

                if st.button("Confirm and Import into Database", type="primary"):
                    # Register asset and prices
                    asset = portfolio_service.get_or_create_asset(target_symbol)
                    count = 0
                    for dt, row in df_parsed.iterrows():
                        p_date = dt.date()
                        # Upsert price record
                        from models.database import HistoricalPrice
                        existing = db.query(HistoricalPrice).filter(
                            HistoricalPrice.asset_id == asset.id,
                            HistoricalPrice.price_date == p_date
                        ).first()
                        if not existing:
                            rec = HistoricalPrice(
                                asset_id=asset.id,
                                price_date=p_date,
                                open_price=float(row["open"]),
                                high_price=float(row["high"]),
                                low_price=float(row["low"]),
                                close_price=float(row["close"]),
                                adjusted_close=float(row["adjusted_close"]),
                                volume=float(row["volume"]),
                                data_source="MANUAL_CSV_IMPORT",
                            )
                            db.add(rec)
                            count += 1
                        else:
                            existing.close_price = float(row["close"])
                            existing.adjusted_close = float(row["adjusted_close"])
                    db.commit()
                    # Recompute returns
                    market_service._sync_daily_returns(asset.id)
                    st.success(f"Successfully imported and indexed {count} historical price records for {target_symbol}.")
                    st.rerun()
