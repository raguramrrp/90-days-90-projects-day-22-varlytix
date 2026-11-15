"""
Seed Script for SIGMORA.
Initializes the database, generates 650+ trading days of correlated synthetic market data,
and creates 3 realistic sample portfolios with multi-asset holdings and transactions.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from models.database import init_db, SessionLocal, Asset, Portfolio
from providers.demo_provider import DemoSyntheticProvider, DEMO_ASSETS
from services.market_data_service import MarketDataService
from services.portfolio_service import PortfolioService
from datetime import date, timedelta


def seed_all():
    print("=" * 60)
    print("SIGMORA — SEEDING DEMO MARKET UNIVERSE & SAMPLE PORTFOLIOS")
    print("=" * 60)

    # Initialize tables
    init_db()
    db = SessionLocal()

    market_service = MarketDataService(db)
    portfolio_service = PortfolioService(db)

    print("\n1. Registering Assets & Generating Historical Price Histories...")
    # Seed Assets and Prices
    for symbol, meta in DEMO_ASSETS.items():
        asset = portfolio_service.get_or_create_asset(
            symbol=symbol,
            name=meta["name"],
            sector=meta["sector"],
            exchange=meta["exchange"],
            asset_type=meta["type"]
        )
        rec_count = market_service.sync_asset_prices(asset, provider_name="DEMO_SYNTHETIC")
        print(f"  [+] {symbol:<24} | {meta['sector']:<22} | {rec_count} daily prices synced.")

    print("\n2. Creating Sample Portfolios & Positions...")

    # Portfolio 1: Balanced Growth
    p1 = portfolio_service.create_portfolio(
        name="Balanced Growth Portfolio",
        description="Core multi-sector diversified portfolio balancing secular tech, financial compounding, and defensive cashflows.",
        is_demo=True
    )
    p1_allocations = [
        ("DEMO_BANK_HDFC", 300, 1480.0, 150.0),
        ("DEMO_TECH_TCS", 120, 3620.0, 200.0),
        ("DEMO_CONSUMER_RELIANCE", 180, 2690.0, 250.0),
        ("DEMO_CONSUMER_ITC", 1200, 410.0, 100.0),
        ("DEMO_PHARMA_SUN", 350, 1420.0, 120.0),
        ("DEMO_ENERGY_NTPC", 1500, 320.0, 80.0),
    ]
    for sym, qty, price, fees in p1_allocations:
        portfolio_service.record_transaction(
            portfolio_id=p1.id,
            symbol=sym,
            transaction_type="BUY",
            quantity=qty,
            price=price,
            fees=fees,
            tx_date=date.today() - timedelta(days=200),
            notes="Initial allocation"
        )
    print(f"  [✓] Created: {p1.portfolio_name} ({len(p1_allocations)} positions)")

    # Portfolio 2: High-Beta Aggressive
    p2 = portfolio_service.create_portfolio(
        name="High-Beta Aggressive Portfolio",
        description="High-growth, cyclical momentum portfolio concentrated in technology and automotive expansion.",
        is_demo=True
    )
    p2_allocations = [
        ("DEMO_AUTO_TATAMOTORS", 800, 820.0, 150.0),
        ("DEMO_TECH_INFY", 450, 1480.0, 180.0),
        ("DEMO_BANK_ICICI", 600, 940.0, 200.0),
        ("DEMO_TECH_TCS", 100, 3700.0, 160.0),
    ]
    for sym, qty, price, fees in p2_allocations:
        portfolio_service.record_transaction(
            portfolio_id=p2.id,
            symbol=sym,
            transaction_type="BUY",
            quantity=qty,
            price=price,
            fees=fees,
            tx_date=date.today() - timedelta(days=150),
            notes="Aggressive expansion"
        )
    print(f"  [✓] Created: {p2.portfolio_name} ({len(p2_allocations)} positions)")

    # Portfolio 3: Defensive Dividend
    p3 = portfolio_service.create_portfolio(
        name="Defensive Dividend Portfolio",
        description="Resilient capital preservation portfolio focused on low-volatility consumer staples, healthcare, and utilities.",
        is_demo=True
    )
    p3_allocations = [
        ("DEMO_CONSUMER_ITC", 2200, 420.0, 150.0),
        ("DEMO_PHARMA_SUN", 500, 1450.0, 160.0),
        ("DEMO_ENERGY_NTPC", 2500, 330.0, 120.0),
        ("DEMO_BANK_HDFC", 200, 1520.0, 100.0),
    ]
    for sym, qty, price, fees in p3_allocations:
        portfolio_service.record_transaction(
            portfolio_id=p3.id,
            symbol=sym,
            transaction_type="BUY",
            quantity=qty,
            price=price,
            fees=fees,
            tx_date=date.today() - timedelta(days=280),
            notes="Defensive yield positioning"
        )
    print(f"  [✓] Created: {p3.portfolio_name} ({len(p3_allocations)} positions)")

    # Portfolio 4: All-Weather Multi-Asset (Equities + Gold + Liquid Debt)
    p4 = portfolio_service.create_portfolio(
        name="All-Weather Multi-Asset Portfolio",
        description="Balanced multi-asset allocation combining Indian bluechip equities, Gold ETF (GoldBeES safe-haven hedge), and Liquid ETF (LiquidBeES cash yield).",
        is_demo=True
    )
    p4_allocations = [
        ("DEMO_BANK_HDFC", 200, 1500.0, 120.0),
        ("DEMO_TECH_TCS", 90, 3650.0, 150.0),
        ("DEMO_CONSUMER_ITC", 1000, 415.0, 100.0),
        ("DEMO_COMMODITY_GOLDBEES", 5000, 62.0, 80.0),
        ("DEMO_DEBT_LIQUIDBEES", 400, 995.0, 50.0),
    ]
    for sym, qty, price, fees in p4_allocations:
        portfolio_service.record_transaction(
            portfolio_id=p4.id,
            symbol=sym,
            transaction_type="BUY",
            quantity=qty,
            price=price,
            fees=fees,
            tx_date=date.today() - timedelta(days=220),
            notes="Multi-asset risk parity positioning"
        )
    print(f"  [✓] Created: {p4.portfolio_name} ({len(p4_allocations)} positions)")

    db.close()
    print("\n[SUCCESS] Seed complete. SIGMORA is fully initialized with realistic synthetic demo data.")


if __name__ == "__main__":
    seed_all()
