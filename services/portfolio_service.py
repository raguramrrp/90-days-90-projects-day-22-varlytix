"""
Portfolio Service for SIGMORA.
Handles portfolio CRUD, transactions, weighted-average cost accounting,
position management, and portfolio switching.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timezone
import pandas as pd
from sqlalchemy.orm import Session
from models.database import Portfolio, PortfolioPosition, Transaction, Asset, HistoricalPrice
from config import BASE_CURRENCY, DEFAULT_BENCHMARK_SYMBOL


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def list_portfolios(self) -> List[Portfolio]:
        """Returns all portfolios ordered by updated_at descending."""
        return self.db.query(Portfolio).order_by(Portfolio.updated_at.desc()).all()

    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Retrieves a single portfolio by ID."""
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def get_portfolio_by_name(self, name: str) -> Optional[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.portfolio_name == name).first()

    def create_portfolio(
        self,
        name: str,
        description: str = "",
        base_currency: str = BASE_CURRENCY,
        is_demo: bool = False
    ) -> Portfolio:
        """Creates a new portfolio entity."""
        existing = self.get_portfolio_by_name(name)
        if existing:
            return existing

        portfolio = Portfolio(
            portfolio_name=name.strip(),
            description=description.strip(),
            base_currency=base_currency,
            is_demo=is_demo,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def rename_portfolio(self, portfolio_id: int, new_name: str) -> bool:
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return False
        portfolio.portfolio_name = new_name.strip()
        portfolio.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def delete_portfolio(self, portfolio_id: int) -> bool:
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return False
        self.db.delete(portfolio)
        self.db.commit()
        return True

    def get_or_create_asset(
        self,
        symbol: str,
        name: Optional[str] = None,
        sector: str = "General",
        exchange: str = "NSE",
        asset_type: str = "EQUITY"
    ) -> Asset:
        """Finds or creates an asset record in the assets master table."""
        clean_sym = symbol.strip().upper()
        asset = self.db.query(Asset).filter(Asset.symbol == clean_sym).first()
        if not asset:
            asset = Asset(
                symbol=clean_sym,
                asset_name=name or clean_sym,
                sector=sector,
                exchange=exchange,
                asset_type=asset_type,
                currency=BASE_CURRENCY,
                country="India",
                is_active=True,
            )
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)
        return asset

    def record_transaction(
        self,
        portfolio_id: int,
        symbol: str,
        transaction_type: str,  # BUY or SELL
        quantity: float,
        price: float,
        fees: float = 0.0,
        tx_date: Optional[date] = None,
        notes: str = ""
    ) -> Transaction:
        """
        Records a transaction and updates the portfolio position using
        Weighted Average Cost accounting:
        New Avg Cost = (Old Qty * Old Cost + New Qty * Price + Fees) / (Old Qty + New Qty)
        """
        if quantity <= 0:
            raise ValueError("Transaction quantity must be positive.")
        if price <= 0:
            raise ValueError("Transaction price must be positive.")

        asset = self.get_or_create_asset(symbol)
        tx_date = tx_date or datetime.now().date()
        tx_type = transaction_type.upper()

        # Find or create position
        position = self.db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.asset_id == asset.id
        ).first()

        if tx_type == "BUY":
            if not position:
                # First purchase
                total_cost = (quantity * price) + fees
                avg_cost = total_cost / quantity
                position = PortfolioPosition(
                    portfolio_id=portfolio_id,
                    asset_id=asset.id,
                    quantity=quantity,
                    average_cost=avg_cost,
                )
                self.db.add(position)
            else:
                old_val = position.quantity * position.average_cost
                new_val = (quantity * price) + fees
                new_qty = position.quantity + quantity
                position.quantity = new_qty
                position.average_cost = (old_val + new_val) / new_qty if new_qty > 0 else 0.0
                position.updated_at = datetime.now(timezone.utc)

        elif tx_type == "SELL":
            if not position or position.quantity < quantity:
                raise ValueError(f"Cannot sell {quantity} shares of {symbol}. Current holding is {position.quantity if position else 0}.")
            position.quantity -= quantity
            # Average cost remains unchanged under standard weighted average cost for partial sells
            position.updated_at = datetime.now(timezone.utc)
            if position.quantity <= 1e-6:
                self.db.delete(position)
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}. Must be BUY or SELL.")

        # Create transaction log
        tx = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            transaction_type=tx_type,
            quantity=quantity,
            price=price,
            fees=fees,
            transaction_date=tx_date,
            notes=notes,
        )
        self.db.add(tx)

        # Update portfolio timestamp
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio:
            portfolio.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        return tx

    def get_holdings_summary(self, portfolio_id: int) -> pd.DataFrame:
        """
        Returns a rich DataFrame of current portfolio positions with:
        Symbol, Name, Sector, Exchange, Quantity, Avg Cost, Latest Price,
        Invested Value, Current Value, Unrealized P&L, Return %, Weight %.
        """
        positions = self.db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.quantity > 0
        ).all()

        if not positions:
            return pd.DataFrame()

        rows = []
        for pos in positions:
            asset = pos.asset
            # Get latest price
            latest_price_rec = self.db.query(HistoricalPrice).filter(
                HistoricalPrice.asset_id == asset.id
            ).order_by(HistoricalPrice.price_date.desc()).first()

            latest_price = latest_price_rec.adjusted_close if latest_price_rec else pos.average_cost
            invested_val = pos.quantity * pos.average_cost
            current_val = pos.quantity * latest_price
            pnl = current_val - invested_val
            ret_pct = (pnl / invested_val) if invested_val > 0 else 0.0

            rows.append({
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "name": asset.asset_name,
                "sector": asset.sector,
                "exchange": asset.exchange,
                "quantity": pos.quantity,
                "average_cost": pos.average_cost,
                "latest_price": latest_price,
                "invested_value": invested_val,
                "current_value": current_val,
                "unrealized_pnl": pnl,
                "return_pct": ret_pct,
            })

        df = pd.DataFrame(rows)
        total_market_value = df["current_value"].sum()
        if total_market_value > 0:
            df["weight"] = df["current_value"] / total_market_value
        else:
            df["weight"] = 1.0 / len(df)

        return df.sort_values(by="current_value", ascending=False)
