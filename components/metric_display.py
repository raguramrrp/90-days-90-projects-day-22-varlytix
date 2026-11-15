"""
Metric Display and Quantitative Observation Components for SIGMORA.
Modern stock market app design system with elevated dark surfaces (#121826),
crisp slate borders (#1E293B), tabular numerals, and vibrant bull-bear indicators.
Strictly generated as single-line HTML without indentation to eliminate any
CommonMark markdown parsing collisions.
"""

from typing import Optional, List, Dict, Any
from config import COLORS


def render_metric_card(
    label: str,
    value: str,
    subvalue: Optional[str] = None,
    delta: Optional[str] = None,
    delta_positive: Optional[bool] = None,
    help_text: Optional[str] = None
) -> str:
    """
    Renders a stock market pro quantitative metric card.
    Zero indentation ensures markdown never renders content as a code block.
    """
    delta_html = ""
    if delta is not None:
        if delta_positive:
            delta_color = COLORS["positive"]
            delta_bg = "rgba(0, 210, 106, 0.12)"
            arrow = "▲"
        else:
            delta_color = COLORS["negative"]
            delta_bg = "rgba(244, 63, 94, 0.12)"
            arrow = "▼"
        delta_html = f'<span style="background:{delta_bg};color:{delta_color};font-size:11px;font-weight:700;padding:2px 6px;border-radius:4px;font-variant-numeric:tabular-nums;margin-left:6px;display:inline-block;">{arrow} {delta}</span>'

    subvalue_html = ""
    if subvalue:
        subvalue_html = f'<div style="font-size:11.5px;color:{COLORS["secondary_text"]};margin-top:4px;font-variant-numeric:tabular-nums;">{subvalue}</div>'

    help_icon = ""
    if help_text:
        help_icon = f'<span title="{help_text}" style="cursor:help;color:{COLORS["secondary_text"]};font-size:11px;font-weight:normal;margin-left:4px;">ℹ</span>'

    # Pure single-line HTML with inline styles
    card_html = (
        f'<div style="background:{COLORS["primary_surface"]};border:1px solid {COLORS["border"]};border-radius:8px;padding:12px 14px;box-shadow:0 2px 8px rgba(0,0,0,0.25);min-height:86px;display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
        f'<span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:{COLORS["secondary_text"]};">{label} {help_icon}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:4px;">'
        f'<span style="font-size:20px;font-weight:800;color:{COLORS["primary_text"]};font-variant-numeric:tabular-nums;letter-spacing:-0.3px;">{value}</span>'
        f'{delta_html}'
        f'</div>'
        f'{subvalue_html}'
        f'</div>'
    )
    return card_html


def render_observation_banner(obs_list: List[Dict[str, Any]]) -> str:
    """
    Renders portfolio risk insights in a clean, professional financial layout.
    Clean typography and subtle dividers without noisy card borders or shouting tags.
    """
    if not obs_list:
        return ""

    rows_html = []
    for i, obs in enumerate(obs_list):
        lvl = obs.get("level", "info")
        dot_color = COLORS["muted_highlight"] if lvl == "warning" else (COLORS["positive"] if lvl == "positive" else COLORS["secondary_accent"])

        obs_type = obs.get("type", "Observation")
        clean_title = obs_type.replace("_", " ").title()
        obs_text = obs.get("text", "")

        border_bottom = f"border-bottom:1px solid {COLORS['border']};" if i < len(obs_list) - 1 else ""

        row = (
            f'<div style="padding:10px 0;{border_bottom}">'
            f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:3px;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{dot_color};display:inline-block;"></span>'
            f'<span style="font-size:12px;font-weight:700;color:{COLORS["primary_text"]};">{clean_title}</span>'
            f'</div>'
            f'<div style="font-size:11.5px;color:{COLORS["secondary_text"]};line-height:1.45;padding-left:13px;">{obs_text}</div>'
            f'</div>'
        )
        rows_html.append(row)

    container_html = (
        f'<div style="background:{COLORS["primary_surface"]};border:1px solid {COLORS["border"]};border-radius:6px;padding:8px 14px;box-shadow:0 1px 3px rgba(0,0,0,0.15);">'
        f'{"".join(rows_html)}'
        f'</div>'
    )
    return container_html
