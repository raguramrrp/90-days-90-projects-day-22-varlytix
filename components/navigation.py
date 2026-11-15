"""
Horizontal Navigation and Global Header Component for VARLYTIX.
Modern Stock Market App (Midnight Pro) layout:
- Deep midnight header with subtle dark slate borders (#1E293B)
- Clean brand identity
- Active portfolio selector
- Transparent Market Data Snapshot service integration (NIFTY 50, SENSEX, BANK NIFTY, INDIA VIX, GOLD, USD/INR)
- 10-item horizontal navigation bar (Methodology permanently removed)
"""

import streamlit as st
from config import BRAND_NAME, BRAND_DESCRIPTOR, COLORS
from components.brand import get_header_brand_html
from services.market_snapshot_service import MarketSnapshotService

# Exactly 10 navigation workspaces — Methodology permanently removed
NAV_MAP = {
    "Overview": "overview",
    "Portfolio": "portfolio",
    "Risk Lab": "risk_lab",
    "Correlation": "correlation",
    "Simulation": "simulation",
    "Stress Test": "stress_test",
    "Optimizer": "optimizer",
    "Reports": "reports",
    "Data Centre": "data_centre",
    "Settings": "settings",
}
REV_NAV_MAP = {v: k for k, v in NAV_MAP.items()}


def render_market_snapshot_ribbon():
    """
    Renders the modern Indian market benchmark ribbon:
    NIFTY 50, SENSEX, BANK NIFTY, INDIA VIX, GOLD, USD/INR.
    Displays clear provider attribution and observation timestamp without status tags.
    """
    service = MarketSnapshotService()
    snapshot = service.get_snapshot()

    items = snapshot.get("items", [])
    provider = snapshot.get("provider", "NSE/BSE Reference EOD")
    obs_time = snapshot.get("observation_time", "")

    items_html = []
    for item in items:
        price = item.get("price", 0.0)
        chg = item.get("change", 0.0)
        chg_pct = item.get("change_pct", 0.0)
        is_pos = chg >= 0

        color = COLORS["positive"] if is_pos else COLORS["negative"]
        arrow = "▲" if is_pos else "▼"
        prefix = "+" if is_pos else ""

        # Format price
        if price > 1000:
            price_str = f"{price:,.2f}"
        else:
            price_str = f"{price:.2f}"

        item_str = (
            f'<div style="display:inline-flex;align-items:baseline;gap:6px;font-size:11.5px;padding-right:16px;border-right:1px solid {COLORS["border"]};white-space:nowrap;">'
            f'<span style="font-weight:600;color:{COLORS["secondary_text"]};font-size:11px;">{item["name"]}</span>'
            f'<span style="font-weight:700;color:{COLORS["primary_text"]};font-variant-numeric:tabular-nums;">{price_str}</span>'
            f'<span style="font-weight:700;color:{color};font-size:10.5px;font-variant-numeric:tabular-nums;">{arrow} {prefix}{chg_pct:.2f}%</span>'
            f'</div>'
        )
        items_html.append(item_str)

    ribbon_html = (
        f'<div style="background:{COLORS["primary_surface"]};border:1px solid {COLORS["border"]};border-radius:6px;padding:7px 14px;margin-top:6px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 1px 3px rgba(0,0,0,0.2);overflow-x:auto;">'
        f'<div style="display:flex;align-items:center;gap:12px;overflow-x:auto;">'
        f'{"".join(items_html)}'
        f'</div>'
        f'<div style="font-size:10.5px;color:{COLORS["secondary_text"]};white-space:nowrap;padding-left:14px;display:flex;gap:6px;align-items:center;">'
        f'<span>{provider}</span>'
        f'<span>•</span>'
        f'<span>{obs_time}</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(ribbon_html, unsafe_allow_html=True)


def render_global_header(portfolios, current_portfolio_id: int):
    """
    Renders top application header:
    - Left: Brand Logo, Wordmark, and Descriptor, with compact Active Portfolio Selector directly underneath
    - Right: Market Data Attribution & Scope, with small Demo notice
    """
    col_left, col_right = st.columns([5.5, 6.5])

    with col_left:
        st.markdown(get_header_brand_html(), unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)

        if portfolios:
            p_names = [p.portfolio_name for p in portfolios]
            name_to_id = {p.portfolio_name: p.id for p in portfolios}
            id_to_name = {p.id: p.portfolio_name for p in portfolios}

            current_name = id_to_name.get(current_portfolio_id, p_names[0] if p_names else "")
            current_idx = p_names.index(current_name) if current_name in p_names else 0

            def _handle_portfolio_switch():
                chosen = st.session_state.get("active_portfolio_dropdown")
                if chosen and chosen in name_to_id:
                    st.session_state["current_portfolio_id"] = name_to_id[chosen]

            # Compact selector width under VARLYTIX title
            c_sel, _ = st.columns([5.2, 6.8])
            with c_sel:
                st.selectbox(
                    "Active Portfolio",
                    options=p_names,
                    index=current_idx,
                    label_visibility="collapsed",
                    key="active_portfolio_dropdown",
                    on_change=_handle_portfolio_switch
                )

    with col_right:
        # Check if active portfolio is a demo portfolio
        is_demo = False
        if portfolios:
            for p in portfolios:
                if p.id == current_portfolio_id and getattr(p, "is_demo", False):
                    is_demo = True
                    break

        demo_badge_html = ""
        if is_demo:
            demo_badge_html = (
                f'<div style="background:{COLORS["surface_tint"]};border:1px solid {COLORS["border"]};border-radius:4px;padding:3px 8px;text-align:right;">'
                f'<div style="font-size:10px;font-weight:600;color:{COLORS["muted_highlight"]};">Demo Portfolio Active</div>'
                f'<div style="font-size:9px;color:{COLORS["secondary_text"]};">Deterministic Simulation Series</div>'
                f'</div>'
            )

        status_html = (
            f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:12px;height:100%;margin-top:6px;">'
            f'<div style="text-align:right;">'
            f'<div style="font-size:11px;font-weight:700;color:{COLORS["secondary_accent"]};letter-spacing:0.4px;">INDIA MARKET SCOPE</div>'
            f'<div style="font-size:10px;color:{COLORS["secondary_text"]};">NSE & BSE Equities / ETFs</div>'
            f'</div>'
            f'{demo_badge_html}'
            f'</div>'
        )
        st.markdown(status_html, unsafe_allow_html=True)

    # Render Market Snapshot Ribbon
    render_market_snapshot_ribbon()


def render_horizontal_nav():
    """
    Renders the compact horizontal navigation bar across the top of the workspace.
    Uses st.segmented_control with exactly 10 navigation workspaces.
    """
    current_key = st.session_state.get("current_page", "overview")
    current_label = REV_NAV_MAP.get(current_key, "Overview")

    selected_label = st.segmented_control(
        "Navigation",
        options=list(NAV_MAP.keys()),
        default=current_label,
        label_visibility="collapsed",
        key="main_horizontal_segmented_nav"
    )

    if selected_label and NAV_MAP.get(selected_label) != current_key:
        st.session_state["current_page"] = NAV_MAP[selected_label]
        st.rerun()

    # Refined subtle dark slate divider
    st.markdown(
        f'<div style="border-bottom:1px solid {COLORS["border"]};margin-top:4px;margin-bottom:14px;"></div>',
        unsafe_allow_html=True
    )
