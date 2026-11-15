"""
4-Question Investor Risk Appetite Profiler for VARLYTIX.
Engages everyday investors with an intuitive 4-question behavioral assessment
and contrasts stated psychological risk tolerance against actual quantitative portfolio volatility.
"""

from typing import Dict, Any
import streamlit as st
from config import COLORS


def render_risk_profiler_section(actual_portfolio_vol: float):
    """
    Renders the 4-question risk profiler expander and provides instantaneous alignment feedback.
    """
    with st.expander("Investor Risk Appetite Profiler (4-Question Alignment Quiz)", expanded=False):
        st.markdown(
            f"<div style='font-size: 12px; color: {COLORS['secondary_text']}; margin-bottom: 12px;'>"
            f"Most investors do not realize whether their actual holdings match their psychological ability to withstand losses. "
            f"Answer these 4 quick questions to see if your portfolio aligns with your risk tolerance."
            f"</div>",
            unsafe_allow_html=True
        )

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            q1 = st.selectbox(
                "1. What is your planned investment horizon for this capital?",
                [
                    "Short Term (< 2 Years) — Need capital for known goals",
                    "Medium Term (2 to 5 Years) — Balanced wealth building",
                    "Long Term (5+ Years) — Compounding for retirement/wealth"
                ],
                index=1,
                key="quiz_q1"
            )
            q2 = st.selectbox(
                "2. If your portfolio dropped by -20% in 3 weeks, what would you do?",
                [
                    "Sell everything to cash to prevent further losses",
                    "Feel anxious and check prices daily, but hold without selling",
                    "View it as a festive sale and aggressively invest more money"
                ],
                index=1,
                key="quiz_q2"
            )

        with col_q2:
            q3 = st.selectbox(
                "3. What is your primary objective for this money?",
                [
                    "Capital Safety & beating bank FD returns",
                    "Balanced steady growth with moderate drawdowns",
                    "Maximum wealth growth, accepting sharp temporary swings"
                ],
                index=1,
                key="quiz_q3"
            )
            q4 = st.selectbox(
                "4. What is your monthly cash flow & emergency fund status?",
                [
                    "Tight cash flow, less than 3 months emergency savings",
                    "Stable income with 6 months living expenses parked safely",
                    "Strong recurring surplus and dedicated emergency liquidity"
                ],
                index=1,
                key="quiz_q4"
            )

        # Score calculation (1 to 3 pts per question)
        score = 0
        score += 1 if "Short" in q1 else (2 if "Medium" in q1 else 3)
        score += 1 if "Sell" in q2 else (2 if "Feel" in q2 else 3)
        score += 1 if "Capital Safety" in q3 else (2 if "Balanced" in q3 else 3)
        score += 1 if "Tight" in q4 else (2 if "Stable" in q4 else 3)

        if score <= 6:
            profile_name = "Conservative (Capital Preservation)"
            target_vol_min, target_vol_max = 0.05, 0.10
            badge_bg = COLORS["positive"]
        elif score <= 9:
            profile_name = "Moderate / Balanced Growth"
            target_vol_min, target_vol_max = 0.10, 0.16
            badge_bg = COLORS["deep_teal"]
        else:
            profile_name = "Aggressive / Maximum Compounding"
            target_vol_min, target_vol_max = 0.16, 0.28
            badge_bg = COLORS["amber"]

        actual_vol_pct = actual_portfolio_vol * 100.0

        # Diagnosis logic
        if actual_portfolio_vol > target_vol_max + 0.02:
            alignment = "MISMATCH: OVER-EXPOSED"
            align_color = COLORS["negative"]
            msg = (
                f"Your stated psychological profile is <b>{profile_name}</b> (comfortable with {target_vol_min*100:.0f}–{target_vol_max*100:.0f}% volatility), "
                f"but your portfolio's annualized volatility is <b>{actual_vol_pct:.1f}%</b>. "
                f"You are taking substantially more market turbulence than you can comfortably stomach. "
                f"During a market correction, you face elevated risk of emotional selling. Consider adding 15–20% allocation to Gold (GoldBeES) or liquid debt."
            )
        elif actual_portfolio_vol < target_vol_min - 0.02:
            alignment = "POTENTIAL UNDER-ALLOCATION"
            align_color = COLORS["slate"]
            msg = (
                f"Your stated profile is <b>{profile_name}</b>, but your portfolio volatility is just <b>{actual_vol_pct:.1f}%</b>. "
                f"You have the risk capacity and long-term horizon to take on more growth-oriented equity assets if higher returns are desired."
            )
        else:
            alignment = "WELL ALIGNED"
            align_color = COLORS["positive"]
            msg = (
                f"Excellent alignment! Your portfolio volatility of <b>{actual_vol_pct:.1f}%</b> fits comfortably within your "
                f"stated target range of {target_vol_min*100:.0f}–{target_vol_max*100:.0f}%. Your investment structure matches your behavioral temperament."
            )

        diagnosis_html = (
            f'<div style="background:{COLORS["white"]}; border:1px solid {COLORS["border"]}; border-radius:6px; padding:12px 16px; margin-top:10px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<span style="font-size:11px; font-weight:800; color:{COLORS["secondary_text"]}; text-transform:uppercase;">Stated Appetite:</span>'
            f'<span style="background:{badge_bg}; color:#FFFFFF; font-size:11px; font-weight:800; padding:2px 8px; border-radius:3px;">{profile_name}</span>'
            f'</div>'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<span style="font-size:11px; font-weight:800; color:{COLORS["secondary_text"]}; text-transform:uppercase;">Portfolio Volatility:</span>'
            f'<span style="font-size:13px; font-weight:800; color:{COLORS["graphite"]};">{actual_vol_pct:.1f}%</span>'
            f'<span style="background:rgba(0,0,0,0.06); color:{align_color}; font-size:10px; font-weight:800; padding:2px 6px; border-radius:3px;">{alignment}</span>'
            f'</div>'
            f'</div>'
            f'<div style="font-size:11.5px; color:{COLORS["graphite"]}; line-height:1.45; border-top:1px solid {COLORS["border"]}; padding-top:8px;">{msg}</div>'
            f'</div>'
        )
        st.markdown(diagnosis_html, unsafe_allow_html=True)
