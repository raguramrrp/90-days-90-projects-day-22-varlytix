"""
Unit test to verify that all 10 VARLYTIX pages import correctly and exposure functions exist,
and that Methodology is completely removed.
"""

import pytest


def test_ten_pages_exist_and_import():
    from pages.overview import render_overview_page
    from pages.portfolio import render_portfolio_page
    from pages.risk_lab import render_risk_lab_page
    from pages.correlation import render_correlation_page
    from pages.simulation import render_simulation_page
    from pages.stress_test import render_stress_test_page
    from pages.optimizer import render_optimizer_page
    from pages.reports import render_reports_page
    from pages.data_centre import render_data_centre_page
    from pages.settings import render_settings_page

    assert callable(render_overview_page)
    assert callable(render_portfolio_page)
    assert callable(render_risk_lab_page)
    assert callable(render_correlation_page)
    assert callable(render_simulation_page)
    assert callable(render_stress_test_page)
    assert callable(render_optimizer_page)
    assert callable(render_reports_page)
    assert callable(render_data_centre_page)
    assert callable(render_settings_page)


def test_methodology_page_removed():
    with pytest.raises(ImportError):
        import pages.methodology  # type: ignore


def test_navigation_map_has_ten_items():
    from components.navigation import NAV_MAP
    assert len(NAV_MAP) == 10
    assert "Methodology" not in NAV_MAP
    assert list(NAV_MAP.keys()) == [
        "Overview", "Portfolio", "Risk Lab", "Correlation", "Simulation",
        "Stress Test", "Optimizer", "Reports", "Data Centre", "Settings"
    ]


def test_market_snapshot_service():
    from services.market_snapshot_service import MarketSnapshotService
    service = MarketSnapshotService()
    snap = service.get_snapshot()
    assert "items" in snap
    assert len(snap["items"]) == 6
    assert "provider" in snap
    assert "status" in snap
    assert "observation_time" in snap
