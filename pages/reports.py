"""
Screen 08 — Reports & Data Export for SIGMORA.
Generates publication-quality PDF Risk Dossiers via ReportLab and
provides structured CSV exports for external quantitative analysis.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from services.portfolio_service import PortfolioService
from services.risk_service import RiskService
from services.report_service import ReportService
from services.simulation_service import SimulationService
from config import COLORS, BRAND_NAME


def render_reports_page(db, portfolio_id: int):
    portfolio_service = PortfolioService(db)
    risk_service = RiskService(db)
    report_service = ReportService()
    sim_service = SimulationService(db)

    portfolio = portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Selected portfolio not found.")
        return

    holdings = portfolio_service.get_holdings_summary(portfolio_id)
    if holdings.empty:
        st.warning("Portfolio has no active holdings to generate reports for.")
        return

    st.markdown(
        f"<h2 style='font-size: 20px; font-weight: 800; color: {COLORS['graphite']}; margin-bottom: 12px;'>Institutional Reports & Quantitative Exports</h2>",
        unsafe_allow_html=True
    )

    with st.spinner("Compiling risk analytics dossier..."):
        risk_data = risk_service.analyze_portfolio_risk(portfolio_id)

    if "error" in risk_data:
        st.error(risk_data["error"])
        return

    col_pdf, col_csv = st.columns(2)

    # 1. PDF Risk Dossier Export
    with col_pdf:
        pdf_card_html = (
            f'<div style="background:{COLORS["white"]};border:1px solid {COLORS["border"]};border-radius:8px;padding:16px 18px;margin-bottom:12px;">'
            f'<div style="font-size:14px;font-weight:800;color:{COLORS["graphite"]};margin-bottom:4px;">PDF Portfolio Risk Dossier</div>'
            f'<p style="font-size:12px;color:{COLORS["secondary_text"]};margin-bottom:14px;">'
            f'Comprehensive multi-page audit report complete with executive KPI summaries, capital allocations, '
            f'Euler component volatility decomposition, Monte Carlo percentiles, and regulatory disclaimers.'
            f'</p></div>'
        )
        st.markdown(pdf_card_html, unsafe_allow_html=True)

        include_sim = st.checkbox("Include Monte Carlo Simulation Summary", value=True)
        sim_data = None
        if include_sim:
            try:
                sim_data = sim_service.run_simulation(portfolio_id, method="BOOTSTRAP", horizon_days=252, num_simulations=1000)
            except Exception:
                sim_data = None

        if st.button("Generate & Download PDF Report", type="primary", use_container_width=True):
            with st.spinner("Assembling ReportLab PDF document..."):
                pdf_bytes = report_service.generate_pdf_report(
                    portfolio_name=portfolio.portfolio_name,
                    risk_data=risk_data,
                    sim_data=sim_data
                )
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                fname = f"SIGMORA_Risk_Report_{portfolio.portfolio_name.replace(' ', '_')}_{ts}.pdf"
                st.download_button(
                    label="Click Here to Save PDF",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True
                )

    # 2. Raw CSV Matrix Exports
    with col_csv:
        csv_card_html = (
            f'<div style="background:{COLORS["white"]};border:1px solid {COLORS["border"]};border-radius:8px;padding:16px 18px;margin-bottom:12px;">'
            f'<div style="font-size:14px;font-weight:800;color:{COLORS["graphite"]};margin-bottom:4px;">Quantitative Data Exports (CSV)</div>'
            f'<p style="font-size:12px;color:{COLORS["secondary_text"]};margin-bottom:14px;">'
            f'Export raw mathematical models, aligned return series, and covariance matrices for use in Excel, R, or Python quantitative pipelines.'
            f'</p></div>'
        )
        st.markdown(csv_card_html, unsafe_allow_html=True)

        # Holdings CSV
        holdings_csv = report_service.export_holdings_csv(holdings)
        st.download_button(
            label="Download Current Holdings (CSV)",
            data=holdings_csv,
            file_name=f"{portfolio.portfolio_name}_holdings.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Correlation Matrix CSV
        corr_csv = report_service.export_correlation_csv(risk_data["correlation_matrix"])
        st.download_button(
            label="Download Pearson Correlation Matrix (CSV)",
            data=corr_csv,
            file_name=f"{portfolio.portfolio_name}_correlation_matrix.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Risk Contributions CSV
        rc_csv = risk_data["risk_contributions"].to_csv(index=True)
        st.download_button(
            label="Download Component Risk Contributions (CSV)",
            data=rc_csv,
            file_name=f"{portfolio.portfolio_name}_risk_contributions.csv",
            mime="text/csv",
            use_container_width=True
        )
