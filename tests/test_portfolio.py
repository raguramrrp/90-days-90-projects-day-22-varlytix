"""
Unit Tests for Portfolio Accounting, Weighted Average Cost, and Position Valuation.
"""

import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, Portfolio, Asset, PortfolioPosition
from services.portfolio_service import PortfolioService


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_portfolio_creation_and_retrieval(in_memory_db):
    service = PortfolioService(in_memory_db)
    p = service.create_portfolio("Test Portfolio", "Description of test")
    assert p.id is not None
    assert p.portfolio_name == "Test Portfolio"

    retrieved = service.get_portfolio(p.id)
    assert retrieved.portfolio_name == "Test Portfolio"


def test_weighted_average_cost_accounting(in_memory_db):
    service = PortfolioService(in_memory_db)
    p = service.create_portfolio("Core Equities")

    # Transaction 1: Buy 100 shares @ 1000 with 50 fee -> Cost = (100 * 1000 + 50) / 100 = 1000.5
    tx1 = service.record_transaction(
        portfolio_id=p.id,
        symbol="TCS",
        transaction_type="BUY",
        quantity=100.0,
        price=1000.0,
        fees=50.0
    )
    pos1 = in_memory_db.query(PortfolioPosition).filter_by(portfolio_id=p.id).first()
    assert pos1.quantity == 100.0
    assert pytest.approx(pos1.average_cost, 0.01) == 1000.5

    # Transaction 2: Buy 50 shares @ 1200 with 25 fee
    # Total val before = 100 * 1000.5 = 100050
    # New val = 50 * 1200 + 25 = 60025
    # Total Qty = 150 -> New Avg Cost = 160075 / 150 = 1067.167
    tx2 = service.record_transaction(
        portfolio_id=p.id,
        symbol="TCS",
        transaction_type="BUY",
        quantity=50.0,
        price=1200.0,
        fees=25.0
    )
    in_memory_db.refresh(pos1)
    assert pos1.quantity == 150.0
    assert pytest.approx(pos1.average_cost, 0.01) == 1067.167

    # Transaction 3: Partial Sell 50 shares
    # Under weighted-average cost, average cost remains unchanged
    tx3 = service.record_transaction(
        portfolio_id=p.id,
        symbol="TCS",
        transaction_type="SELL",
        quantity=50.0,
        price=1300.0
    )
    in_memory_db.refresh(pos1)
    assert pos1.quantity == 100.0
    assert pytest.approx(pos1.average_cost, 0.01) == 1067.167


def test_invalid_transactions_raise_error(in_memory_db):
    service = PortfolioService(in_memory_db)
    p = service.create_portfolio("Error Testing")

    # Negative quantity
    with pytest.raises(ValueError):
        service.record_transaction(p.id, "INFY", "BUY", -10, 500)

    # Selling non-existent holding
    with pytest.raises(ValueError):
        service.record_transaction(p.id, "INFY", "SELL", 10, 500)
