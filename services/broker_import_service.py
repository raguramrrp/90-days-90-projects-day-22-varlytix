"""
Broker Statement Import Service for VARLYTIX.
Supports 1-click auto-detection and parsing of portfolio holdings from:
- Zerodha Kite / Console (.csv, .xlsx)
- Groww (.csv, .xlsx)
- Angel One (.csv)
- Upstox (.csv)
- Generic CSV with fuzzy header matching

Provides ready-to-test sample broker statements for instant demonstration.
"""

from typing import Dict, Any, List, Tuple, Optional
import io
import pandas as pd
from datetime import date, timedelta
from sqlalchemy.orm import Session
from models.database import Portfolio, Asset
from services.portfolio_service import PortfolioService
from services.market_data_service import MarketDataService


# Sample Broker Templates for instant 1-click test drive
SAMPLE_ZERODHA_DATA = """Instrument,Qty.,Avg. cost,Cur. val,P&L,Net chg.
RELIANCE,150,2780.50,426000.00,9000.00,+2.15%
TCS,80,3640.00,308000.00,16800.00,+5.77%
HDFCBANK,250,1490.00,395000.00,22500.00,+6.04%
INFY,200,1540.00,324000.00,16000.00,+5.19%
ITC,1000,418.00,435000.00,17000.00,+4.07%
GOLDBEES,4000,61.20,262000.00,17200.00,+7.03%
LIQUIDBEES,300,996.00,300000.00,1200.00,+0.40%
TATAMOTORS,300,890.00,288000.00,21000.00,+7.87%"""

SAMPLE_GROWW_DATA = """Stock Name,Symbol,Quantity,Average Price,Current Value,Total Returns
Reliance Industries,RELIANCE,120,2810.00,340800.00,+3600.00
Tata Consultancy Services,TCS,60,3710.00,231000.00,+8400.00
HDFC Bank,HDFCBANK,200,1510.00,316000.00,+14000.00
Sun Pharma,SUNPHARMA,250,1460.00,385000.00,+20000.00
NTPC,NTPC,1200,335.00,432000.00,+30000.00
Nippon India ETF Gold BeES,GOLDBEES,3500,62.50,229250.00,+10500.00"""

SAMPLE_ANGEL_ONE_DATA = """Stock Symbol,Company Name,Quantity,Buy Average Price,LTP,Total Investment
RELIANCE,Reliance Industries Ltd,100,2750.00,2840.00,275000.00
ICICIBANK,ICICI Bank Ltd,350,960.00,1050.00,336000.00
INFY,Infosys Ltd,180,1520.00,1620.00,273600.00
ITC,ITC Ltd,800,422.00,435.00,337600.00
GOLDBEES,Nippon India Gold ETF,2500,61.80,65.50,154500.00"""

SAMPLE_UPSTOX_DATA = """Scrip Name,Symbol,Quantity,Cost Price,LTP,Cur. Value
TCS,TCS,75,3680.00,3850.00,288750.00
HDFCBANK,HDFCBANK,180,1475.00,1580.00,284400.00
TATAMOTORS,TATAMOTORS,400,880.00,960.00,384000.00
NTPC,NTPC,1000,325.00,360.00,360000.00
LIQUIDBEES,LIQUIDBEES,250,998.00,1000.00,250000.00"""

# Mapping standard Indian tickers to demo assets or synthetic counterparts
INDIAN_SYMBOL_MAPPING = {
    "RELIANCE": ("DEMO_CONSUMER_RELIANCE", "Reliance Industries", "Conglomerate / Energy"),
    "TCS": ("DEMO_TECH_TCS", "Tata Consultancy Services", "Technology"),
    "HDFCBANK": ("DEMO_BANK_HDFC", "HDFC Bank", "Financial Services"),
    "HDFC": ("DEMO_BANK_HDFC", "HDFC Bank", "Financial Services"),
    "ICICIBANK": ("DEMO_BANK_ICICI", "ICICI Bank", "Financial Services"),
    "INFY": ("DEMO_TECH_INFY", "Infosys Ltd", "Technology"),
    "ITC": ("DEMO_CONSUMER_ITC", "ITC Ltd", "Consumer Defensive"),
    "TATAMOTORS": ("DEMO_AUTO_TATAMOTORS", "Tata Motors", "Automobile"),
    "SUNPHARMA": ("DEMO_PHARMA_SUN", "Sun Pharma", "Healthcare"),
    "NTPC": ("DEMO_ENERGY_NTPC", "NTPC Ltd", "Utilities / Power"),
    "GOLDBEES": ("DEMO_COMMODITY_GOLDBEES", "Nippon India ETF Gold BeES", "Commodity / Gold ETF"),
    "LIQUIDBEES": ("DEMO_DEBT_LIQUIDBEES", "Nippon India ETF Liquid BeES", "Debt / Cash Alternative"),
}


class BrokerImportService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.market_service = MarketDataService(db)

    def detect_broker_format(self, df: pd.DataFrame) -> str:
        """Identifies the broker export format based on column headers."""
        cols = [str(c).strip().lower() for c in df.columns]

        if any("instrument" in c for c in cols) and any("avg. cost" in c or "avg cost" in c for c in cols):
            return "Zerodha (Kite / Console)"
        elif any("stock name" in c for c in cols) and any("average price" in c for c in cols):
            return "Groww"
        elif any("stock symbol" in c for c in cols) and any("buy average" in c for c in cols):
            return "Angel One"
        elif any("scrip name" in c for c in cols) and any("cost price" in c for c in cols):
            return "Upstox"
        else:
            return "Generic Indian Broker CSV"

    def parse_statement(self, file_content: bytes, filename: str) -> Tuple[str, pd.DataFrame]:
        """
        Parses raw CSV or Excel content and normalizes into a clean holdings DataFrame:
        Columns: symbol, name, sector, quantity, avg_cost, target_symbol
        """
        try:
            if filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                try:
                    df = pd.read_csv(io.BytesIO(file_content))
                except Exception:
                    df = pd.read_csv(io.BytesIO(file_content), encoding="latin1")
        except Exception as e:
            raise ValueError(f"Could not read broker file: {str(e)}")

        broker_name = self.detect_broker_format(df)
        cols_lower = {str(c).strip().lower(): c for c in df.columns}

        # Find Symbol Column
        sym_col = None
        for candidate in ["symbol", "stock symbol", "instrument", "scrip name", "ticker"]:
            if candidate in cols_lower:
                sym_col = cols_lower[candidate]
                break

        # Find Quantity Column
        qty_col = None
        for candidate in ["qty.", "qty", "quantity", "shares", "units", "holdings"]:
            if candidate in cols_lower:
                qty_col = cols_lower[candidate]
                break

        # Find Average Cost Column
        price_col = None
        for candidate in ["avg. cost", "avg cost", "average price", "buy average price", "cost price", "buy price", "rate"]:
            if candidate in cols_lower:
                price_col = cols_lower[candidate]
                break

        if not sym_col or not qty_col or not price_col:
            raise ValueError(f"Unable to detect required columns (Symbol, Quantity, Average Price). Available columns: {list(df.columns)}")

        records = []
        for _, row in df.iterrows():
            raw_sym = str(row[sym_col]).strip().upper()
            if not raw_sym or raw_sym == "NAN":
                continue

            # Strip exchange suffixes if present (e.g. RELIANCE-EQ, RELIANCE.NS)
            clean_sym = raw_sym.split("-")[0].split(".")[0].strip()

            try:
                # Clean numerical values
                raw_qty = str(row[qty_col]).replace(",", "").replace(" ", "").strip()
                raw_price = str(row[price_col]).replace(",", "").replace("₹", "").replace("INR", "").replace(" ", "").strip()
                qty = float(raw_qty)
                price = float(raw_price)
            except Exception:
                continue

            if qty <= 0 or price <= 0:
                continue

            # Map to known universe or create asset
            if clean_sym in INDIAN_SYMBOL_MAPPING:
                target_sym, name, sector = INDIAN_SYMBOL_MAPPING[clean_sym]
            else:
                target_sym = f"{clean_sym}.NS"
                name = f"{clean_sym} Ltd"
                sector = "Diversified Equities"

            records.append({
                "raw_symbol": clean_sym,
                "target_symbol": target_sym,
                "name": name,
                "sector": sector,
                "quantity": qty,
                "avg_cost": price,
                "invested_value": qty * price
            })

        parsed_df = pd.DataFrame(records)
        if parsed_df.empty:
            raise ValueError("No valid holdings could be parsed from the provided statement.")

        return broker_name, parsed_df

    def import_parsed_holdings(
        self,
        portfolio_id: int,
        holdings_df: pd.DataFrame,
        notes: str = "Broker Statement Import"
    ) -> int:
        """
        Records weighted average cost transactions into the designated portfolio.
        Returns the number of positions imported.
        """
        imported_count = 0
        tx_date = date.today() - timedelta(days=90)

        for _, row in holdings_df.iterrows():
            target_sym = row["target_symbol"]
            qty = float(row["quantity"])
            price = float(row["avg_cost"])

            # Ensure asset exists in DB
            asset = self.portfolio_service.get_or_create_asset(
                symbol=target_sym,
                name=row["name"],
                sector=row["sector"],
                exchange="NSE",
                asset_type="EQUITY" if "ETF" not in row["sector"] and "Commodity" not in row["sector"] and "Debt" not in row["sector"] else "ETF"
            )

            # Sync prices if needed
            self.market_service.sync_asset_prices(asset)

            # Record buy transaction
            self.portfolio_service.record_transaction(
                portfolio_id=portfolio_id,
                symbol=target_sym,
                transaction_type="BUY",
                quantity=qty,
                price=price,
                fees=max(20.0, price * qty * 0.001),  # Estimated brokerage/STT
                tx_date=tx_date,
                notes=notes
            )
            imported_count += 1

        return imported_count
