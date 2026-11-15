"""
Portfolio Health Score & Plain-English Executive Intelligence Engine for SIGMORA.
Calculates a holistic 0–100 score across 4 quantitative pillars:
1. Diversification Pillar (Effective N, concentration penalty, multi-asset hedge)
2. Downside Resilience Pillar (Maximum Drawdown & recovery cushion)
3. Risk Efficiency Pillar (Sharpe Ratio relative to Indian risk-free rate 6.5%)
4. Tail-Risk Safety Pillar (95% 1-Day CVaR / Expected Shortfall)

Also generates the 3-Bullet Plain-English Executive Summary:
- The Strength: Primary portfolio advantage
- The Blindspot: Hidden risks or concentration traps
- The Stress Reality: Estimated ₹ loss in severe market shock
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


def compute_health_score(risk_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a comprehensive 0–100 Portfolio Health Score and plain-English summary.
    """
    holdings = risk_data.get("holdings", pd.DataFrame())
    mdd = abs(risk_data.get("max_drawdown", 0.0))
    sharpe = risk_data.get("sharpe_ratio", 0.0)
    cvar_95 = abs(risk_data.get("cvar_95", 0.0))
    ann_vol = risk_data.get("annualized_volatility", 0.15)
    current_value = risk_data.get("current_value", 1000000.0)

    # ----------------------------------------------------
    # PILLAR 1: Diversification & Concentration (Max 25 pts)
    # ----------------------------------------------------
    if not holdings.empty and "weight" in holdings.columns:
        weights = holdings["weight"].values
        weights = weights / weights.sum()
        hhi = float(np.sum(weights ** 2))
        effective_n = 1.0 / hhi if hhi > 0 else 1.0
        max_w = float(np.max(weights))
        num_assets = len(holdings)

        # Check for multi-asset presence (Gold / Debt / Cash)
        sectors = holdings["sector"].str.lower().tolist() if "sector" in holdings.columns else []
        has_hedge = any("gold" in s or "commodity" in s or "debt" in s or "cash" in s for s in sectors)

        div_pts = 0.0
        # Effective N contribution (max 15)
        if effective_n >= 5.0:
            div_pts += 15.0
        elif effective_n >= 3.5:
            div_pts += 12.0
        elif effective_n >= 2.5:
            div_pts += 9.0
        elif effective_n >= 1.5:
            div_pts += 5.0
        else:
            div_pts += 2.0

        # Concentration penalty / reward (max 7)
        if max_w <= 0.25:
            div_pts += 7.0
        elif max_w <= 0.35:
            div_pts += 5.0
        elif max_w <= 0.50:
            div_pts += 2.0

        # Multi-asset hedge bonus (max 3)
        if has_hedge:
            div_pts += 3.0
        elif num_assets >= 5:
            div_pts += 1.0

        div_score = min(25.0, max(2.0, div_pts))
    else:
        div_score = 10.0
        effective_n = 1.0
        max_w = 1.0
        has_hedge = False

    # ----------------------------------------------------
    # PILLAR 2: Downside Resilience / Drawdown (Max 25 pts)
    # ----------------------------------------------------
    if mdd <= 0.10:
        downside_score = 25.0
    elif mdd <= 0.16:
        downside_score = 21.0
    elif mdd <= 0.22:
        downside_score = 17.0
    elif mdd <= 0.30:
        downside_score = 12.0
    elif mdd <= 0.40:
        downside_score = 8.0
    else:
        downside_score = 4.0

    # ----------------------------------------------------
    # PILLAR 3: Risk Efficiency / Sharpe Ratio (Max 25 pts)
    # ----------------------------------------------------
    if sharpe >= 1.25:
        efficiency_score = 25.0
    elif sharpe >= 0.90:
        efficiency_score = 21.0
    elif sharpe >= 0.50:
        efficiency_score = 16.0
    elif sharpe >= 0.20:
        efficiency_score = 11.0
    elif sharpe >= 0.00:
        efficiency_score = 7.0
    else:
        efficiency_score = 3.0

    # ----------------------------------------------------
    # PILLAR 4: Tail-Risk Safety / CVaR (Max 25 pts)
    # ----------------------------------------------------
    if cvar_95 <= 0.015:
        tail_score = 25.0
    elif cvar_95 <= 0.022:
        tail_score = 21.0
    elif cvar_95 <= 0.030:
        tail_score = 16.0
    elif cvar_95 <= 0.040:
        tail_score = 11.0
    elif cvar_95 <= 0.055:
        tail_score = 6.0
    else:
        tail_score = 3.0

    total_score = int(round(div_score + downside_score + efficiency_score + tail_score))
    total_score = max(5, min(100, total_score))

    # Grade determination
    if total_score >= 82:
        grade = "A"
        grade_label = "Institutional Grade"
        grade_desc = "Outstanding risk-adjusted structure with resilient shock absorption."
        status_color = "#00E5FF"  # Electric cyan
    elif total_score >= 68:
        grade = "B"
        grade_label = "Well Balanced"
        grade_desc = "Healthy allocation with robust returns and manageable exposure."
        status_color = "#00D26A"  # Positive bull green
    elif total_score >= 50:
        grade = "C"
        grade_label = "Moderate Risk"
        grade_desc = "Reasonable portfolio but carries concentration or drawdown blindspots."
        status_color = "#FBBF24"  # Amber warning
    else:
        grade = "D"
        grade_label = "High Risk Exposure"
        grade_desc = "Elevated tail-risk vulnerabilities and sharp drawdown sensitivity."
        status_color = "#F43F5E"  # Negative red

    # ----------------------------------------------------
    # PLAIN-ENGLISH 3-BULLET EXECUTIVE SUMMARY GENERATION
    # ----------------------------------------------------
    # 1. The Strength
    if sharpe >= 0.8:
        strength_text = f"High Risk-Adjusted Productivity: Your portfolio delivers a Sharpe ratio of {sharpe:.2f}, generating substantial excess returns above the 6.5% Indian sovereign risk-free rate per unit of risk taken."
    elif mdd <= 0.15:
        strength_text = f"Capital Preservation Shield: Your maximum historical drawdown is tightly contained at just {mdd*100:.1f}%, indicating strong capital defence during market pullbacks."
    elif len(holdings) >= 5 and max_w <= 0.30:
        strength_text = f"Balanced Capital Dispersion: With {len(holdings)} holdings and no single stock exceeding {max_w*100:.1f}%, your capital is not over-dependent on a single company."
    else:
        strength_text = f"Growth Momentum: Portfolio has generated positive cumulative return ({risk_data.get('cumulative_return', 0.0)*100:+.1f}%) with active participation in market upside."

    # 2. The Blindspot
    if max_w >= 0.35:
        top_asset = holdings.sort_values("weight", ascending=False).iloc[0]["name"] if not holdings.empty else "Top Asset"
        blindspot_text = f"Single-Stock Concentration: {top_asset} represents {max_w*100:.1f}% of your portfolio. An idiosyncratic earnings shock or regulatory shift in this single stock could drag down your total wealth."
    elif not has_hedge:
        blindspot_text = f"Zero Multi-Asset Hedge: Your portfolio is 100% correlated to equity market swings. Adding a 10–15% allocation to Gold (e.g. GoldBeES) or liquid debt would historically smooth out drawdowns."
    elif ann_vol >= 0.20:
        blindspot_text = f"Elevated Annualized Volatility ({ann_vol*100:.1f}%): Your portfolio fluctuates significantly wider than the benchmark NIFTY 50 (~14% vol), requiring a long holding horizon."
    elif effective_n < 3.0:
        blindspot_text = f"Low Effective Diversification: Although you hold {len(holdings)} assets, their co-movement means you effectively behave like holding only {effective_n:.1f} independent assets."
    else:
        blindspot_text = f"Macro Sector Correlation: Core holdings share moderate cyclical sensitivity to broader domestic economic growth and RBI interest rate policies."

    # 3. The Stress Reality
    # Calculate hypothetical crash drop
    crash_scenario_pct = min(0.35, max(0.18, ann_vol * 1.5))
    crash_rupee_loss = current_value * crash_scenario_pct
    stress_reality_text = f"Real-World Stress Reality: In a severe market drawdown of -{crash_scenario_pct*100:.0f}% (comparable to March 2020 or 2008), this portfolio is mathematically expected to drop by approximately ₹ {crash_rupee_loss:,.0f} before reaching a cyclical bottom."

    return {
        "total_score": total_score,
        "grade": grade,
        "grade_label": grade_label,
        "grade_desc": grade_desc,
        "status_color": status_color,
        "pillars": {
            "diversification": {
                "name": "Diversification & Balance",
                "score": round(div_score, 1),
                "max": 25,
                "detail": f"Effective N: {effective_n:.1f} assets | Max Weight: {max_w*100:.1f}%"
            },
            "downside_resilience": {
                "name": "Downside Resilience",
                "score": round(downside_score, 1),
                "max": 25,
                "detail": f"Max Drawdown: -{mdd*100:.1f}%"
            },
            "risk_efficiency": {
                "name": "Risk Efficiency (Sharpe)",
                "score": round(efficiency_score, 1),
                "max": 25,
                "detail": f"Sharpe Ratio: {sharpe:.2f} (Rf=6.5%)"
            },
            "tail_risk": {
                "name": "Tail-Risk Safety (CVaR)",
                "score": round(tail_score, 1),
                "max": 25,
                "detail": f"95% 1-Day CVaR: {cvar_95*100:.2f}%"
            },
        },
        "executive_summary": {
            "strength": strength_text,
            "blindspot": blindspot_text,
            "stress_reality": stress_reality_text,
        }
    }
