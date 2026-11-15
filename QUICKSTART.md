# SIGMORA Quickstart Guide

Get up and running with SIGMORA in under 2 minutes.

---

## 1. Quick Launch (Windows)

Simply double-click `run.bat` in the project folder, or execute via PowerShell:

```powershell
cd "d:\90 days\90-days-90-projects-day-22-sigmora"
.\.venv\Scripts\activate.ps1
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 2. Exploring Key Screens

1. **Overview Tab:**
   - Review current portfolio valuation and total return.
   - Inspect the cumulative trajectory chart vs the NIFTY 50 benchmark.
   - Switch between **By Asset** and **By Sector** treemap views.
   - Review quantitative risk observations (concentration alerts, correlated clusters).

2. **Portfolio Tab:**
   - Switch between the 3 included demo portfolios via the top dropdown:
     - *Balanced Growth Portfolio*
     - *High-Beta Aggressive Portfolio*
     - *Defensive Dividend Portfolio*
   - Log a new BUY or SELL transaction to see Weighted Average Cost update automatically.

3. **Risk Lab Tab:**
   - Inspect the 10 quantitative risk metrics (Volatility, Sharpe, Sortino, VaR, CVaR, Beta, Calmar).
   - Check the **Euler Risk Contribution** chart and verify that the sum of component contributions matches total volatility.

4. **Correlation Tab:**
   - View the Pearson correlation heatmap across Daily, Weekly, and Monthly frequencies.
   - Select an asset pair to plot its moving 63-day rolling correlation.

5. **Simulation Tab:**
   - Run a 1,000 to 10,000 path Monte Carlo simulation.
   - Toggle between **Historical Bootstrap** and **Multivariate Parametric** modes.
   - Observe the 5th-95th percentile fan chart bands and the probability of ending below initial capital.

6. **Stress Test Tab:**
   - Compare capital losses across predefined macro shocks (-10%, -15%, -25%).
   - Adjust individual asset shock sliders in the **Custom Asset Shock Builder**.

7. **Optimizer Tab:**
   - Compare your current portfolio against the **Minimum Variance** and **Maximum Sharpe** allocations.
   - Trace the Markowitz Efficient Frontier curve.

8. **Reports Tab:**
   - Click **Generate & Download PDF Report** for an executive-ready multi-page dossier.
   - Download CSV exports of holdings, correlation matrices, and risk contributions.
