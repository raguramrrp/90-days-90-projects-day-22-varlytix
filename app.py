"""
VARLYTIX — Portfolio Risk Intelligence Platform
Main Streamlit Application Entrypoint.
Initializes the database, configures the modern stock market app (Midnight Pro) design system,
renders global navigation, and routes to quantitative analytical workspaces.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    BRAND_NAME, BRAND_DESCRIPTOR, BRAND_TAGLINE,
    COLORS, DATABASE_PATH
)
from models.database import init_db, SessionLocal
from services.portfolio_service import PortfolioService
from scripts.seed_demo_data import seed_all

# Set Page Config
st.set_page_config(
    page_title=f"{BRAND_NAME} — {BRAND_DESCRIPTOR}",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Stock Market App (Midnight Pro) Design System CSS
CUSTOM_CSS = f"""
<style>
    /* Hide Streamlit default sidebar and top toolbar */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 1.2rem !important;
    }}
    #MainMenu, footer {{
        visibility: hidden !important;
    }}

    /* Global Midnight Slate Canvas */
    .stApp {{
        background-color: {COLORS['application_background']} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: {COLORS['primary_text']} !important;
    }}

    /* Main Container Padding */
    .block-container {{
        padding-top: 0.6rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1440px !important;
    }}

    /* Stock Market Pro Buttons */
    .stButton > button {{
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 5px 14px !important;
        transition: all 0.12s ease-in-out !important;
        border: 1px solid {COLORS['border']} !important;
        background-color: {COLORS['primary_surface']} !important;
        color: {COLORS['primary_text']} !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }}
    .stButton > button:hover {{
        border-color: {COLORS['secondary_accent']} !important;
        color: {COLORS['secondary_accent']} !important;
        background-color: {COLORS['surface_tint']} !important;
    }}
    .stButton > button[kind="primary"] {{
        background-color: {COLORS['primary_accent']} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px !important;
        border-bottom: 1.5px solid {COLORS['border']} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 12.5px !important;
        font-weight: 600 !important;
        color: {COLORS['secondary_text']} !important;
        padding: 6px 14px !important;
        border-radius: 4px 4px 0 0 !important;
        background: transparent !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {COLORS['secondary_accent']} !important;
        border-bottom: 2.5px solid {COLORS['secondary_accent']} !important;
        font-weight: 700 !important;
    }}

    /* Segmented Control Styling — Sleek Dark Terminal Bar */
    div[data-testid="stSegmentedControl"] {{
        background-color: {COLORS['primary_surface']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 6px !important;
        padding: 3px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }}
    div[data-testid="stSegmentedControl"] button {{
        border-radius: 4px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        color: {COLORS['secondary_text']} !important;
        border: none !important;
        transition: all 0.12s ease !important;
        background-color: transparent !important;
        padding: 4px 10px !important;
    }}
    div[data-testid="stSegmentedControl"] button:hover {{
        color: #FFFFFF !important;
        background-color: {COLORS['surface_tint']} !important;
    }}
    div[data-testid="stSegmentedControl"] button[aria-checked="true"],
    div[data-testid="stSegmentedControl"] button[data-checked="true"] {{
        background-color: {COLORS['primary_accent']} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(37,99,235,0.35) !important;
    }}

    /* Inputs: Selectbox, Number Input, Text Input */
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput div[data-baseweb="input"] > div,
    .stTextInput div[data-baseweb="input"] > div {{
        background-color: {COLORS['surface_tint']} !important;
        border: 1px solid {COLORS['border']} !important;
        color: {COLORS['primary_text']} !important;
        border-radius: 6px !important;
    }}
    .stSelectbox div[data-baseweb="select"] > div:focus-within,
    .stNumberInput div[data-baseweb="input"] > div:focus-within,
    .stTextInput div[data-baseweb="input"] > div:focus-within {{
        border-color: {COLORS['secondary_accent']} !important;
        box-shadow: 0 0 0 1px {COLORS['secondary_accent']} !important;
    }}

    /* Sliders */
    .stSlider div[data-baseweb="slider"] {{
        color: {COLORS['secondary_accent']} !important;
    }}

    /* Expanders */
    div[data-testid="stExpander"] {{
        background-color: {COLORS['primary_surface']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }}
    div[data-testid="stExpander"] summary {{
        color: {COLORS['primary_text']} !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
    }}

    /* Dataframe tables */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {COLORS['border']} !important;
        border-radius: 6px !important;
        background-color: {COLORS['primary_surface']} !important;
    }}

    /* Custom Sleek Dark Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: {COLORS['application_background']};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['border']};
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['secondary_accent']};
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main():
    # Initialize Database
    init_db()
    db = SessionLocal()

    portfolio_service = PortfolioService(db)
    portfolios = portfolio_service.list_portfolios()

    # If first run with empty DB, auto-seed demo data
    if not portfolios:
        with st.spinner("Initializing VARLYTIX with demo portfolio universe..."):
            seed_all()
            portfolios = portfolio_service.list_portfolios()

    # Session State Initialization
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "overview"

    # Fallback if previous session state had deleted 'methodology' page
    if st.session_state.get("current_page") == "methodology":
        st.session_state["current_page"] = "overview"

    if "current_portfolio_id" not in st.session_state and portfolios:
        st.session_state["current_portfolio_id"] = portfolios[0].id

    current_portfolio_id = st.session_state.get("current_portfolio_id")

    # Components
    from components.navigation import render_global_header, render_horizontal_nav

    # 1. Global Header with Market Snapshot Ribbon
    render_global_header(portfolios, current_portfolio_id)

    # Update current_portfolio_id from session state in case it changed
    current_portfolio_id = st.session_state.get("current_portfolio_id", current_portfolio_id)

    # 2. Horizontal Navigation Bar (10 Workspaces)
    render_horizontal_nav()

    # 3. Page Router
    current_page = st.session_state["current_page"]

    if current_page == "overview":
        from pages.overview import render_overview_page
        render_overview_page(db, current_portfolio_id)

    elif current_page == "portfolio":
        from pages.portfolio import render_portfolio_page
        render_portfolio_page(db, current_portfolio_id)

    elif current_page == "risk_lab":
        from pages.risk_lab import render_risk_lab_page
        render_risk_lab_page(db, current_portfolio_id)

    elif current_page == "correlation":
        from pages.correlation import render_correlation_page
        render_correlation_page(db, current_portfolio_id)

    elif current_page == "simulation":
        from pages.simulation import render_simulation_page
        render_simulation_page(db, current_portfolio_id)

    elif current_page == "stress_test":
        from pages.stress_test import render_stress_test_page
        render_stress_test_page(db, current_portfolio_id)

    elif current_page == "optimizer":
        from pages.optimizer import render_optimizer_page
        render_optimizer_page(db, current_portfolio_id)

    elif current_page == "reports":
        from pages.reports import render_reports_page
        render_reports_page(db, current_portfolio_id)

    elif current_page == "data_centre":
        from pages.data_centre import render_data_centre_page
        render_data_centre_page(db, current_portfolio_id)

    elif current_page == "settings":
        from pages.settings import render_settings_page
        render_settings_page(db, current_portfolio_id)

    else:
        # Default route fallback
        from pages.overview import render_overview_page
        render_overview_page(db, current_portfolio_id)

    db.close()


if __name__ == "__main__":
    main()
