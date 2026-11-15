# SIGMORA — Market Data Sources & Provider Architecture

## Architecture Overview
SIGMORA adheres to a provider-independent adapter architecture. No single data provider is hardcoded into the business logic.

```
                  ┌──────────────────────────────┐
                  │    Market Data Service       │
                  └──────────────┬───────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┐
         │                       │                        │
         ▼                       ▼                        ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│  Demo Synthetic  │   │ Yahoo-Compatible │   │ Manual CSV Import    │
│  Provider        │   │ Provider         │   │ Provider             │
└──────────────────┘   └──────────────────┘   └──────────────────────┘
```

---

## 1. Demo Synthetic Provider (Deterministic Market Simulation)
- **Role:** Immediate local development, offline operation, and deterministic demonstration.
- **Coverage:** 10 Indian assets across Financials, Technology, Conglomerates, Healthcare, Utilities, and the NIFTY 50 benchmark index.
- **Generation Method:** Correlated Geometric Brownian Motion (GBM) with calibrated sector covariance matrices and fixed random seeds.
- **Observation Count:** 650 continuous trading days (~2.5 calendar years).
- **Labeling:** Clearly disclosed with a prominent "DEMO DATA — SYNTHETIC MARKET SERIES" banner to eliminate any ambiguity.

---

## 2. Yahoo-Compatible Provider Adapter
- **Role:** Retrieval of public historical quotes for NSE and BSE equities and ETFs.
- **Ticker Format:** 
  - NSE Equities: Appends `.NS` (e.g., `TCS.NS`, `RELIANCE.NS`, `HDFCBANK.NS`).
  - BSE Equities: Appends `.BO` (e.g., `500325.BO`).
  - Benchmark Index: `^NSEI` (NIFTY 50).
- **Adjusted Prices:** Prioritizes dividend- and split-adjusted closing prices.
- **Error Handling:** Gracefully falls back if rate limits, timeouts, or network disconnects occur, preserving previously downloaded cached records.

---

## 3. CSV Import Provider
- **Role:** Fallback and custom institution file imports.
- **Validation Pipeline:**
  1. Header normalization (`date`, `close`, `adjusted_close`, `open`, `high`, `low`, `volume`).
  2. Date parsing and sorting.
  3. Duplicate timestamp rejection.
  4. Positive price verification ($P_t > 0$).
  5. Interactive preview prior to database ingestion.
