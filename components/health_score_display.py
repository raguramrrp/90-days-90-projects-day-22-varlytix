"""
Health Score & Executive Summary UI Component for SIGMORA.
Renders an editorial card featuring:
- 0–100 Circular-style Health Score with Grade & Badge
- 4 Horizontal Progress Bars for each Pillar (Diversification, Downside, Efficiency, Tail-Risk)
- Plain-English 3-Bullet Executive Intelligence Summary (The Strength, The Blindspot, The Stress Reality)
"""

from typing import Dict, Any
from config import COLORS


def render_health_score_card(health_data: Dict[str, Any]) -> str:
    """
    Renders minified, zero-indentation HTML for the Portfolio Health Score card.
    """
    total = health_data["total_score"]
    grade = health_data["grade"]
    grade_label = health_data["grade_label"]
    grade_desc = health_data["grade_desc"]
    status_col = health_data["status_color"]
    exec_summary = health_data["executive_summary"]
    pillars = health_data["pillars"]

    # Pillar bars HTML
    pillar_bars_html = ""
    for k, p in pillars.items():
        pct = (p["score"] / p["max"]) * 100.0
        bar_col = COLORS["deep_teal"] if pct >= 70 else (COLORS["amber"] if pct >= 50 else COLORS["negative"])
        pillar_bars_html += (
            f'<div style="margin-bottom: 8px;">'
            f'<div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">'
            f'<span style="font-weight:600; color:{COLORS["graphite"]};">{p["name"]}</span>'
            f'<span style="font-weight:700; color:{bar_col};">{p["score"]:.0f} / {p["max"]} <span style="font-size:10px; color:{COLORS["slate"]}; font-weight:400;">({p["detail"]})</span></span>'
            f'</div>'
            f'<div style="background:{COLORS["border"]}; height:5px; border-radius:3px; overflow:hidden;">'
            f'<div style="background:{bar_col}; width:{pct:.1f}%; height:100%; border-radius:3px;"></div>'
            f'</div>'
            f'</div>'
        )

    card_html = (
        f'<div style="background:{COLORS["white"]}; border:1px solid {COLORS["border"]}; border-radius:8px; padding:16px 20px; margin-bottom:14px; box-shadow: 0 4px 18px rgba(0,0,0,0.35);">'
        f'<div style="display:flex; flex-wrap:wrap; gap:20px; align-items:flex-start;">'
        f'<div style="flex: 0 0 210px; border-right:1px solid {COLORS["border"]}; padding-right:18px;">'
        f'<div style="font-size:10px; font-weight:800; color:{COLORS["secondary_text"]}; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:6px;">PORTFOLIO HEALTH SCORE</div>'
        f'<div style="display:flex; align-items:baseline; gap:6px;">'
        f'<span style="font-size:42px; font-weight:900; color:#FFFFFF; font-family:\'Roboto Mono\',sans-serif; line-height:1;">{total}</span>'
        f'<span style="font-size:15px; font-weight:600; color:{COLORS["slate"]};">/ 100</span>'
        f'<span style="background:{status_col}; color:#0B0E14; font-size:11px; font-weight:900; padding:2px 8px; border-radius:4px; margin-left:auto; letter-spacing:0.5px;">GRADE {grade}</span>'
        f'</div>'
        f'<div style="font-size:13px; font-weight:800; color:{status_col}; margin-top:4px;">{grade_label}</div>'
        f'<div style="font-size:11px; color:{COLORS["secondary_text"]}; line-height:1.4; margin-top:4px;">{grade_desc}</div>'
        f'</div>'
        f'<div style="flex: 1 1 320px; border-right:1px solid {COLORS["border"]}; padding-right:18px;">'
        f'<div style="font-size:10px; font-weight:800; color:{COLORS["secondary_text"]}; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:10px;">QUANTITATIVE PILLAR BREAKDOWN</div>'
        f'{pillar_bars_html}'
        f'</div>'
        f'<div style="flex: 1 1 360px;">'
        f'<div style="font-size:10px; font-weight:800; color:{COLORS["secondary_text"]}; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:8px;">PLAIN-ENGLISH EXECUTIVE INTELLIGENCE</div>'
        f'<div style="margin-bottom:8px; display:flex; gap:8px;">'
        f'<span style="background:rgba(0,210,106,0.15); border:1px solid rgba(0,210,106,0.3); color:{COLORS["positive"]}; font-weight:800; font-size:9.5px; padding:2px 6px; border-radius:3px; height:fit-content; white-space:nowrap; font-family:\'Roboto Mono\',monospace;">STRENGTH</span>'
        f'<span style="font-size:11.5px; color:{COLORS["graphite"]}; line-height:1.4;">{exec_summary["strength"]}</span>'
        f'</div>'
        f'<div style="margin-bottom:8px; display:flex; gap:8px;">'
        f'<span style="background:rgba(251,191,36,0.15); border:1px solid rgba(251,191,36,0.3); color:{COLORS["amber"]}; font-weight:800; font-size:9.5px; padding:2px 6px; border-radius:3px; height:fit-content; white-space:nowrap; font-family:\'Roboto Mono\',monospace;">BLINDSPOT</span>'
        f'<span style="font-size:11.5px; color:{COLORS["graphite"]}; line-height:1.4;">{exec_summary["blindspot"]}</span>'
        f'</div>'
        f'<div style="display:flex; gap:8px;">'
        f'<span style="background:rgba(244,63,94,0.15); border:1px solid rgba(244,63,94,0.3); color:{COLORS["negative"]}; font-weight:800; font-size:9.5px; padding:2px 6px; border-radius:3px; height:fit-content; white-space:nowrap; font-family:\'Roboto Mono\',monospace;">STRESS REALITY</span>'
        f'<span style="font-size:11.5px; color:{COLORS["graphite"]}; line-height:1.4;">{exec_summary["stress_reality"]}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return card_html
