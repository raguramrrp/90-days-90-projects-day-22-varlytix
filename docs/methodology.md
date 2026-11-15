# SIGMORA — Mathematical Methodology & Analytical Formulations

## Executive Summary
SIGMORA evaluates investment portfolio risk from a multi-dimensional perspective, transcending simple profit and loss. It models return distributions, volatility clustering, tail risk, and structural co-movements for Indian listed equities and ETFs.

---

## 1. Capital Valuation and Return Compounding

### Position Valuation
For asset $i$ with quantity $q_i$ and latest closing price $P_{i,t}$:
$$V_{i,t} = q_i \times P_{i,t}$$

Total portfolio market value:
$$V_t = \sum_{i=1}^N V_{i,t}$$

### Simple vs Log Returns
- **Simple Returns ($r_t$):** Used for linear portfolio asset weighting and capital aggregation.
  $$r_{i,t} = \frac{P_{i,t} - P_{i,t-1}}{P_{i,t-1}}$$
- **Log Returns:** Continuously compounded returns, useful for time-series additivity.

### Buy-and-Hold Drift
In real-world personal portfolios without algorithmic daily rebalancing, position weights drift dynamically as relative market prices diverge:
$$w_{i,t} = \frac{V_{i,t}}{V_t}$$
Portfolio returns reflect actual capital changes:
$$r_{p,t} = \frac{V_t - V_{t-1}}{V_{t-1}}$$

### Compound Annual Growth Rate (CAGR)
Computed geometrically over $N$ active trading days (NSE convention: 252 sessions/year):
$$\text{CAGR} = \left( \frac{V_{\text{end}}}{V_{\text{start}}} \right)^{\frac{252}{N}} - 1$$

---

## 2. Volatility and Risk-Adjusted Ratios

### Annualized Volatility ($\sigma_p$)
Sample standard deviation with Bessel's correction ($N-1$ degrees of freedom):
$$\sigma_{\text{daily}} = \sqrt{\frac{1}{N-1} \sum_{t=1}^N (r_{p,t} - \bar{r}_p)^2}$$
$$\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{252}$$

### Sharpe Ratio
Measures excess return over the risk-free hurdle rate ($R_f = 6.5\%$ for Indian 10-Year Sovereign G-Secs) per unit of total annualized volatility:
$$\text{Sharpe} = \frac{\text{CAGR} - R_f}{\sigma_{\text{ann}}}$$

### Sortino Ratio & Downside Semi-Deviation
Penalizes only downside return volatility below the hurdle rate:
$$\text{DD} = \sqrt{\frac{1}{N} \sum_{t=1}^N \min(r_{p,t} - r_{\text{target}}, 0)^2} \times \sqrt{252}$$
$$\text{Sortino} = \frac{\text{CAGR} - R_f}{\text{DD}}$$

### Drawdown Analysis
Running peak is computed as:
$$\text{Peak}_t = \max_{s \le t} V_s$$
$$\text{Drawdown}_t = \frac{V_t}{\text{Peak}_t} - 1$$
$$\text{Maximum Drawdown (MDD)} = \min_t (\text{Drawdown}_t)$$
$$\text{Calmar Ratio} = \frac{\text{CAGR}}{|\text{MDD}|}$$

---

## 3. Euler Risk Decomposition (Risk Contribution)

Using Euler's homogeneous function theorem, total portfolio volatility is decomposed into exact component contributions:
$$\sigma_p = \sqrt{w^T \Sigma w}$$

### Marginal Risk Contribution (MRC)
$$\text{MRC} = \frac{\Sigma w}{\sigma_p}$$

### Component Risk Contribution (RC)
$$\text{RC}_i = w_i \times \text{MRC}_i = \frac{w_i (\Sigma w)_i}{\sigma_p}$$

### Mathematical Identity Check
$$\sum_{i=1}^N \text{RC}_i = \sigma_p$$
This ensures zero unexplained variance allocation.

---

## 4. Value at Risk (VaR) & Conditional VaR (CVaR)

### Historical Quantile VaR
For confidence level $c$ (e.g. 95%), VaR represents the threshold loss exceeded $(1-c)\%$ of the time:
$$\text{VaR}_c = -\text{Quantile}(r_p, 1-c)$$

### Conditional VaR (Expected Shortfall)
The expected average loss conditional upon returns breaching the VaR threshold:
$$\text{CVaR}_c = -\mathbb{E}[r_p \mid r_p \le -\text{VaR}_c]$$

---

## 5. Monte Carlo Simulation Engine

### Method A: Joint Historical Bootstrap
Resamples complete daily empirical return vectors $[r_{1,t}, r_{2,t}, \dots, r_{N,t}]$ from historical observation dates. By sampling joint rows rather than independent single-asset returns, the empirical cross-asset covariance and fat-tail distributions are preserved without imposing parametric assumptions.

### Method B: Multivariate Parametric Simulation
Draws from a multivariate normal distribution $\mathcal{N}(\mu, \Sigma)$:
1. Decomposes covariance matrix $\Sigma = L L^T$ via Cholesky factorization.
2. If $\Sigma$ has negative eigenvalues due to sample estimation gaps, applies Higham's nearest positive semi-definite projection.
3. Generates correlated return vectors $r_{\text{sim}} = \mu + L \cdot Z$, where $Z \sim \mathcal{N}(0, I)$.
