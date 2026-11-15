"""
Professional PDF and CSV Reporting Service for SIGMORA.
Generates comprehensive quantitative risk reports using ReportLab with editorial styling
and clean CSV data exports.
"""

from io import BytesIO
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from config import BRAND_NAME, BRAND_DESCRIPTOR, BRAND_TAGLINE, COLORS

# High-contrast institutional print palette for publication PDF output
PDF_PALETTE = {
    "title": "#0F172A",
    "subtitle": "#2563EB",
    "heading": "#0F172A",
    "body": "#334155",
    "secondary": "#64748B",
    "border": "#E2E8F0",
    "header_bg": "#F1F5F9",
    "stripe_bg": "#F8FAFC",
    "primary": "#2563EB",
    "positive": "#00A854",
    "negative": "#DC2626",
    "table_header": "#0F172A",
}


class ReportService:
    def __init__(self):
        self.colors = PDF_PALETTE

    def generate_pdf_report(
        self,
        portfolio_name: str,
        risk_data: Dict[str, Any],
        sim_data: Optional[Dict[str, Any]] = None,
        stress_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Builds a multi-page professional quantitative risk research report in PDF.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Editorial Styles for PDF
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor(self.colors["title"])
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor(self.colors["subtitle"])
        )
        section_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor(self.colors["heading"]),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor(self.colors["body"])
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor(self.colors["secondary"])
        )

        story = []

        # Header Block
        story.append(Paragraph(f"<b>{BRAND_NAME}</b> — {BRAND_DESCRIPTOR}", title_style))
        story.append(Paragraph(f"Quantitative Portfolio Risk Audit & Simulation Dossier | {portfolio_name}", subtitle_style))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(self.colors["primary"])))
        story.append(Spacer(1, 10))

        # Meta Info
        as_of = datetime.now().strftime("%d %B %Y, %H:%M IST")
        period_str = f"{risk_data.get('period_start', 'N/A')} to {risk_data.get('period_end', 'N/A')} ({risk_data.get('observation_days', 0)} trading days)"
        meta_text = f"<b>Generated:</b> {as_of} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Historical Window:</b> {period_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Base Currency:</b> INR (₹)"
        story.append(Paragraph(meta_text, body_style))
        story.append(Spacer(1, 12))

        # Executive Summary Table
        story.append(Paragraph("1. Executive Portfolio Risk Summary", section_style))
        summary_data = [
            ["Metric", "Value", "Metric", "Value"],
            [
                "Current Portfolio Value", f"₹ {risk_data.get('current_value', 0):,.2f}",
                "Annualized Return (CAGR)", f"{risk_data.get('annualized_return', 0) * 100:.2f}%"
            ],
            [
                "Total Invested Capital", f"₹ {risk_data.get('starting_value', 0):,.2f}",
                "Annualized Volatility (σ)", f"{risk_data.get('annualized_volatility', 0) * 100:.2f}%"
            ],
            [
                "Unrealized Gain / Loss", f"₹ {risk_data.get('total_pnl', 0):,.2f}",
                "Sharpe Ratio (Rf=6.5%)", f"{risk_data.get('sharpe_ratio', 0):.2f}"
            ],
            [
                "Cumulative Return", f"{risk_data.get('cumulative_return', 0) * 100:.2f}%",
                "Sortino Ratio", f"{risk_data.get('sortino_ratio', 0):.2f}"
            ],
            [
                "Maximum Drawdown (MDD)", f"{risk_data.get('max_drawdown', 0) * 100:.2f}%",
                "Benchmark Beta (NIFTY 50)", f"{risk_data.get('beta', 1.0):.2f}"
            ],
            [
                "Value at Risk (95% 1-Day)", f"{risk_data.get('var_95', 0) * 100:.2f}%",
                "Conditional VaR (CVaR 95%)", f"{risk_data.get('cvar_95', 0) * 100:.2f}%"
            ],
        ]

        t_summary = Table(summary_data, colWidths=[150, 120, 150, 120])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors["header_bg"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.colors["title"])),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.colors["border"])),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(self.colors["stripe_bg"])]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 14))

        # Current Holdings Breakdown
        holdings = risk_data.get("holdings", pd.DataFrame())
        if isinstance(holdings, pd.DataFrame) and not holdings.empty:
            story.append(Paragraph("2. Portfolio Holdings & Capital Allocations", section_style))
            h_header = ["Symbol", "Sector", "Qty", "Avg Cost (₹)", "Price (₹)", "Current Value (₹)", "Weight (%)", "Return (%)"]
            h_rows = [h_header]
            for _, r in holdings.iterrows():
                h_rows.append([
                    str(r["symbol"]),
                    str(r.get("sector", "General")),
                    f"{r['quantity']:,.0f}",
                    f"₹{r['average_cost']:,.1f}",
                    f"₹{r['latest_price']:,.1f}",
                    f"₹{r['current_value']:,.0f}",
                    f"{r['weight'] * 100:.1f}%",
                    f"{r['return_pct'] * 100:+.1f}%",
                ])

            t_holdings = Table(h_rows, colWidths=[70, 95, 45, 60, 60, 85, 55, 70])
            t_holdings.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors["table_header"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.colors["border"])),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(self.colors["stripe_bg"])]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t_holdings)
            story.append(Spacer(1, 14))

        # Component Risk Contribution
        rc_df = risk_data.get("risk_contributions", pd.DataFrame())
        if isinstance(rc_df, pd.DataFrame) and not rc_df.empty:
            story.append(Paragraph("3. Component Volatility Risk Contributions (Euler Allocation)", section_style))
            story.append(Paragraph(
                "Calculated using <i>σ_p = √(w^T Σ w)</i> and Component Contribution <i>RC_i = w_i (Σ w)_i / σ_p</i>. "
                f"Sum of component contributions strictly equals total portfolio volatility (Identity check: {risk_data.get('sum_rc_identity', 0)*100:.2f}% ≈ {risk_data.get('annualized_volatility', 0)*100:.2f}%).",
                body_style
            ))
            story.append(Spacer(1, 5))

            rc_header = ["Asset", "Weight (w_i)", "Marginal Risk (MRC)", "Component Risk (RC_i)", "Risk Contribution (%)"]
            rc_rows = [rc_header]
            for idx, r in rc_df.iterrows():
                rc_rows.append([
                    str(idx),
                    f"{r['weight'] * 100:.2f}%",
                    f"{r['marginal_risk'] * 100:.2f}%",
                    f"{r['component_risk'] * 100:.2f}%",
                    f"{r['percentage_risk_contribution'] * 100:.2f}%",
                ])

            t_rc = Table(rc_rows, colWidths=[110, 100, 110, 110, 110])
            t_rc.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors["header_bg"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.colors["title"])),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.colors["border"])),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ]))
            story.append(t_rc)
            story.append(Spacer(1, 14))

        # Monte Carlo Simulation Section
        if sim_data:
            story.append(Paragraph("4. Monte Carlo Simulation Outcomes", section_style))
            p_dict = sim_data.get("summary_percentiles", {})
            sim_table_data = [
                ["Percentile / Scenario", "Ending Portfolio Value", "Implied Return", "Risk Profile"],
                ["5th Percentile (Severe Bear)", f"₹ {p_dict.get(5, 0):,.2f}", f"{(p_dict.get(5, 0)/risk_data.get('current_value', 1) - 1)*100:+.2f}%", "Lower tail loss threshold"],
                ["25th Percentile (Underperforming)", f"₹ {p_dict.get(25, 0):,.2f}", f"{(p_dict.get(25, 0)/risk_data.get('current_value', 1) - 1)*100:+.2f}%", "Moderate market drag"],
                ["50th Percentile (Median Path)", f"₹ {p_dict.get(50, 0):,.2f}", f"{(p_dict.get(50, 0)/risk_data.get('current_value', 1) - 1)*100:+.2f}%", "Central expected trajectory"],
                ["75th Percentile (Favorable)", f"₹ {p_dict.get(75, 0):,.2f}", f"{(p_dict.get(75, 0)/risk_data.get('current_value', 1) - 1)*100:+.2f}%", "Above-average compounding"],
                ["95th Percentile (Strong Bull)", f"₹ {p_dict.get(95, 0):,.2f}", f"{(p_dict.get(95, 0)/risk_data.get('current_value', 1) - 1)*100:+.2f}%", "Upper tail expansion"],
            ]
            t_sim = Table(sim_table_data, colWidths=[140, 130, 110, 160])
            t_sim.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors["header_bg"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.colors["title"])),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.colors["border"])),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ]))
            story.append(t_sim)
            story.append(Spacer(1, 5))
            loss_p = sim_data.get("loss_probability", 0) * 100
            story.append(Paragraph(
                f"<b>Simulation Parameters:</b> Method: {sim_data.get('method', 'Bootstrap')} | Horizon: {sim_data.get('horizon_days', 252)} days | Simulated Paths: {sim_data.get('num_simulations', 1000):,} | <b>Probability of Capital Loss:</b> {loss_p:.1f}%",
                body_style
            ))
            story.append(Spacer(1, 14))

        # Risk Observations
        obs_list = risk_data.get("observations", [])
        if obs_list:
            story.append(Paragraph("5. Quantitative Risk Observations", section_style))
            for obs in obs_list:
                story.append(Paragraph(f"• <b>[{obs['type']}]</b> {obs['text']}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 10))

        # Disclaimer
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(self.colors["border"])))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "<b>REGULATORY AND STATISTICAL DISCLAIMER:</b> SIGMORA is an analytical portfolio risk exploration platform. "
            "All metrics, ratios, simulations, and stress tests are hypothetical quantitative representations based on historical price series and statistical models. "
            "They do not constitute investment advice, guarantees of future returns, or trade recommendations. "
            "Past performance and historical correlation structures do not guarantee future market behavior.",
            disclaimer_style
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def export_holdings_csv(self, holdings_df: pd.DataFrame) -> str:
        """Converts holdings summary into downloadable CSV string."""
        if holdings_df.empty:
            return ""
        return holdings_df.to_csv(index=False)

    def export_returns_csv(self, returns_df: pd.DataFrame) -> str:
        """Converts returns matrix to CSV string."""
        if returns_df.empty:
            return ""
        return returns_df.to_csv(index=True)

    def export_correlation_csv(self, corr_df: pd.DataFrame) -> str:
        """Converts correlation matrix to CSV string."""
        if corr_df.empty:
            return ""
        return corr_df.to_csv(index=True)
