"""
Unit Tests for VARLYTIX Broker Statement Import Engine.
"""

import pytest
import pandas as pd
from services.broker_import_service import (
    BrokerImportService, SAMPLE_ZERODHA_DATA, SAMPLE_GROWW_DATA,
    SAMPLE_ANGEL_ONE_DATA, SAMPLE_UPSTOX_DATA
)


def test_broker_format_detection_and_parsing():
    service = BrokerImportService(db=None)

    # 1. Zerodha
    broker_name, df_z = service.parse_statement(SAMPLE_ZERODHA_DATA.encode("utf-8"), "zerodha.csv")
    assert "Zerodha" in broker_name
    assert len(df_z) == 8
    assert "RELIANCE" in df_z["raw_symbol"].values
    assert "GOLDBEES" in df_z["raw_symbol"].values
    assert df_z["quantity"].sum() > 0

    # 2. Groww
    broker_name, df_g = service.parse_statement(SAMPLE_GROWW_DATA.encode("utf-8"), "groww.csv")
    assert "Groww" in broker_name
    assert len(df_g) == 6
    assert "TCS" in df_g["raw_symbol"].values

    # 3. Angel One
    broker_name, df_a = service.parse_statement(SAMPLE_ANGEL_ONE_DATA.encode("utf-8"), "angel.csv")
    assert "Angel One" in broker_name
    assert len(df_a) == 5

    # 4. Upstox
    broker_name, df_u = service.parse_statement(SAMPLE_UPSTOX_DATA.encode("utf-8"), "upstox.csv")
    assert "Upstox" in broker_name
    assert len(df_u) == 5
