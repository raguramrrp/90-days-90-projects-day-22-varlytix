"""
Database Models & SQLAlchemy Schema for SIGMORA.
Supports SQLite with robust relationships, indexes, and constraints.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint, Index, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from config import DATABASE_URL

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(30), unique=True, nullable=False, index=True)
    provider_symbol = Column(String(50), nullable=True, index=True)
    exchange = Column(String(20), default="NSE", nullable=False)
    asset_name = Column(String(150), nullable=False)
    asset_type = Column(String(30), default="EQUITY")  # EQUITY, ETF, INDEX, CASH
    sector = Column(String(50), default="General", nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    country = Column(String(30), default="India", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    positions = relationship("PortfolioPosition", back_populates="asset", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="asset")
    prices = relationship("HistoricalPrice", back_populates="asset", cascade="all, delete-orphan")
    returns = relationship("DailyReturn", back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Asset {self.symbol} ({self.asset_name})>"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    base_currency = Column(String(10), default="INR", nullable=False)
    benchmark_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    risk_metrics = relationship("RiskMetric", back_populates="portfolio", cascade="all, delete-orphan")
    simulations = relationship("SimulationRun", back_populates="portfolio", cascade="all, delete-orphan")
    stress_results = relationship("StressTestResult", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio {self.portfolio_name}>"


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0.0)
    average_cost = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="uq_portfolio_asset"),
    )

    def __repr__(self):
        return f"<Position Asset={self.asset_id} Qty={self.quantity} AvgCost={self.average_cost}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)
    transaction_date = Column(Date, nullable=False)
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.quantity} @ {self.price}>"


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    price_date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0, nullable=True)
    data_source = Column(String(50), default="DEMO_SYNTHETIC", nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("asset_id", "price_date", name="uq_asset_price_date"),
        Index("idx_asset_date", "asset_id", "price_date"),
    )

    def __repr__(self):
        return f"<Price {self.asset_id} on {self.price_date}: {self.adjusted_close}>"


class DailyReturn(Base):
    __tablename__ = "daily_returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    return_date = Column(Date, nullable=False, index=True)
    simple_return = Column(Float, nullable=False)
    log_return = Column(Float, nullable=False)
    calculation_version = Column(String(20), default="v1.0", nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="returns")

    __table_args__ = (
        UniqueConstraint("asset_id", "return_date", name="uq_asset_return_date"),
    )


class RiskMetric(Base):
    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    calculation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    volatility = Column(Float, nullable=False)
    annualized_return = Column(Float, nullable=False)
    maximum_drawdown = Column(Float, nullable=False)
    average_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=False)
    sortino_ratio = Column(Float, nullable=False)
    beta = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=False)
    cvar_95 = Column(Float, nullable=False)
    calmar_ratio = Column(Float, nullable=True)

    portfolio = relationship("Portfolio", back_populates="risk_metrics")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    simulation_method = Column(String(50), nullable=False)  # BOOTSTRAP, PARAMETRIC
    initial_value = Column(Float, nullable=False)
    simulation_count = Column(Integer, nullable=False)
    horizon_days = Column(Integer, nullable=False)
    random_seed = Column(Integer, nullable=True)
    assumptions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    portfolio = relationship("Portfolio", back_populates="simulations")
    results = relationship("SimulationResult", back_populates="simulation", cascade="all, delete-orphan")


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False, index=True)
    percentile = Column(Float, nullable=False)  # e.g., 0.05, 0.25, 0.50, 0.75, 0.95
    ending_value = Column(Float, nullable=False)
    ending_return = Column(Float, nullable=False)

    simulation = relationship("SimulationRun", back_populates="results")


class StressTestScenario(Base):
    __tablename__ = "stress_test_scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_name = Column(String(100), nullable=False, unique=True)
    scenario_type = Column(String(50), nullable=False)  # UNIFORM, SECTOR, HISTORICAL, CUSTOM
    assumptions = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StressTestResult(Base):
    __tablename__ = "stress_test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("stress_test_scenarios.id"), nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    scenario_name = Column(String(100), nullable=False)
    original_value = Column(Float, nullable=False)
    stressed_value = Column(Float, nullable=False)
    portfolio_return = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    portfolio = relationship("Portfolio", back_populates="stress_results")


class BenchmarkData(Base):
    __tablename__ = "benchmark_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    close_price = Column(Float, nullable=False)
    data_source = Column(String(50), default="DEMO_SYNTHETIC", nullable=False)

    __table_args__ = (
        UniqueConstraint("asset_id", "observation_date", name="uq_benchmark_date"),
    )


class DataRefreshLog(Base):
    __tablename__ = "data_refresh_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True, index=True)
    provider = Column(String(50), nullable=False)
    refresh_started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    refresh_completed_at = Column(DateTime, nullable=True)
    records_received = Column(Integer, default=0, nullable=False)
    refresh_status = Column(String(20), nullable=False)  # SUCCESS, FAILED, PARTIAL, SKIPPED
    error_message = Column(Text, nullable=True)


# Database Engine & Session Factory
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def init_db():
    """Initializes all database tables safely."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yields a database session context."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
