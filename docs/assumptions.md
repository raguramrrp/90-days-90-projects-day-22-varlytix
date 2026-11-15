# SIGMORA — Quantitative Assumptions & Limitations

## 1. Baseline Assumptions

1. **Base Currency:** Indian Rupee (INR / ₹) is the standard numeraire.
2. **Trading Calendar:** 252 sessions per year, matching standard National Stock Exchange (NSE) and Bombay Stock Exchange (BSE) equity trading schedules.
3. **Risk-Free Hurdle Rate ($R_f$):** 6.50% annualized, referencing the sovereign 10-Year Indian Government Benchmark Bond (G-Sec).
4. **Weighted-Average Cost Basis:** Used across all transaction accounting. Partial liquidations reduce position quantities without altering the existing average cost basis.
5. **Buy-and-Hold Portfolio Trajectory:** By default, portfolio performance accounts for dynamic weight drift driven by asset price divergence. Daily rebalanced weighting is provided as a configurable alternative.
6. **Stationarity:** Volatility, correlations, and betas are computed over the selected historical lookback window.

---

## 2. Model Limitations & Disclosures

### A. Non-Stationarity of Asset Correlations
Historical correlations estimated during tranquil market regimes frequently break down during crisis periods. Diversification benefits derived from historical correlation matrices may evaporate during systemic liquidity crunches when correlations converge toward 1.0.

### B. Distributional Assumptions (Monte Carlo)
Parametric Monte Carlo models assume multivariate normally distributed returns. In real-world financial markets, asset returns exhibit negative skewness and excess kurtosis (fat tails). The Historical Bootstrap method is recommended when fat-tailed empirical distributions need to be preserved.

### C. Markowitz Mean-Variance Sensitivity
The Portfolio Optimizer utilizes historical sample mean returns and covariance estimates. Markowitz optimization is sensitive to small changes in input estimates. Candidate allocations should be explored as diagnostic benchmarks rather than guaranteed future return trajectories.

---

## 3. Regulatory Disclaimer
SIGMORA is an educational and analytical research simulator. It does not provide automated trading, guaranteed returns, or certified financial advice. Users should consult licensed financial advisors before committing capital.
