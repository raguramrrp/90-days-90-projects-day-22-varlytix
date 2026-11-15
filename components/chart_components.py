"""
Plotly Interactive Chart Components for SIGMORA.
Modern Stock Market App (Midnight Pro) visual design:
- Deep Midnight Surface (#121826) & Slate dividers (#1E293B)
- Electric Cobalt (#2563EB) & Tech Sky Cyan (#38BDF8) primary trajectory series
- Neutral Slate (#64748B) benchmark comparison
- Market Bear Crimson (#F43F5E) drawdown / downside series
- Market Bull Green (#00D26A) positive performance
- Amber Gold (#F59E0B) uncertainty bounds
- Crisp typography (#F8FAFC) and responsive tooltips.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from config import COLORS


def _apply_sigmora_layout(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Applies modern stock market pro terminal styling to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        title={
            "text": title,
            "font": {"size": 13, "color": COLORS["primary_text"], "family": "Inter, sans-serif"},
            "x": 0.01,
            "xanchor": "left"
        },
        paper_bgcolor=COLORS["primary_surface"],
        plot_bgcolor=COLORS["primary_surface"],
        margin=dict(l=45, r=25, t=42, b=38),
        height=height,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(size=10.5, color=COLORS["primary_text"]),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS["border"],
            gridwidth=0.8,
            linecolor=COLORS["border"],
            tickfont=dict(size=10, color=COLORS["secondary_text"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS["border"],
            gridwidth=0.8,
            linecolor=COLORS["border"],
            tickfont=dict(size=10, color=COLORS["secondary_text"]),
        ),
    )
    return fig


def plot_portfolio_performance(
    port_values: pd.Series,
    benchmark_prices: Optional[pd.DataFrame] = None,
    normalize: bool = True
) -> go.Figure:
    """
    Renders cumulative portfolio performance vs benchmark with market pro styling.
    If normalize=True, scales both series to base 100.
    """
    fig = go.Figure()

    if normalize:
        port_series = (port_values / port_values.iloc[0]) * 100.0
        y_title = "Index (Base = 100)"
    else:
        port_series = port_values
        y_title = "Portfolio Value (₹)"

    fig.add_trace(go.Scatter(
        x=port_series.index,
        y=port_series.values,
        mode="lines",
        name="Portfolio Value",
        line=dict(color=COLORS["secondary_accent"], width=2.4),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.10)",
        hovertemplate="%{x|%d %b %Y}: <b>%{y:,.2f}</b><extra></extra>"
    ))

    # Add benchmark if available
    if benchmark_prices is not None and not benchmark_prices.empty:
        bench_col = benchmark_prices.columns[0]
        aligned = pd.concat([port_values, benchmark_prices[bench_col]], axis=1, join="inner").dropna()
        if not aligned.empty:
            bench_norm = (aligned[bench_col] / aligned[bench_col].iloc[0]) * 100.0 if normalize else aligned[bench_col]
            fig.add_trace(go.Scatter(
                x=aligned.index,
                y=bench_norm.values,
                mode="lines",
                name="NIFTY 50 Benchmark",
                line=dict(color=COLORS["neutral"], width=1.5, dash="dash"),
                hovertemplate="%{x|%d %b %Y}: <b>%{y:,.2f}</b><extra></extra>"
            ))

    fig = _apply_sigmora_layout(fig, title="Historical Trajectory & Benchmark Comparison", height=380)
    fig.update_layout(yaxis_title=y_title)
    return fig


def plot_drawdown_curve(drawdown_df: pd.DataFrame) -> go.Figure:
    """Renders underwater drawdown visualization with vivid bear crimson fill."""
    fig = go.Figure()

    dd_pct = drawdown_df["drawdown"] * 100.0

    fig.add_trace(go.Scatter(
        x=drawdown_df.index,
        y=dd_pct,
        mode="lines",
        name="Drawdown",
        line=dict(color=COLORS["negative"], width=1.8),
        fill="tozeroy",
        fillcolor="rgba(244, 63, 94, 0.16)",
        hovertemplate="%{x|%d %b %Y}: <b>%{y:.2f}%</b><extra></extra>"
    ))

    fig = _apply_sigmora_layout(fig, title="Historical Underwater Drawdown Curve", height=280)
    fig.update_layout(yaxis_title="Drawdown (%)", hovermode="x unified")
    return fig


def plot_correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    """Renders Pearson correlation matrix with dark market diverging palette."""
    symbols = list(corr_matrix.columns)
    z_vals = corr_matrix.values

    # Diverging colorscale: Red (-1) -> Elevated Slate (0) -> Bull Green (+1)
    colorscale = [
        [0.0, COLORS["negative"]],
        [0.5, "#182234"],
        [1.0, COLORS["positive"]]
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=symbols,
        y=symbols,
        colorscale=colorscale,
        zmin=-1.0,
        zmax=1.0,
        text=np.round(z_vals, 2),
        texttemplate="%{text}",
        textfont={"size": 10.5, "family": "Inter, sans-serif", "color": "#FFFFFF"},
        hoverongaps=False,
        hovertemplate="Pair: %{x} vs %{y}<br>Correlation: <b>%{z:.3f}</b><extra></extra>"
    ))

    fig = _apply_sigmora_layout(fig, title="Multi-Asset Correlation Matrix", height=440)
    fig.update_layout(xaxis_tickangle=-35)
    return fig


def plot_monte_carlo_fan_chart(sim_data: Dict[str, Any]) -> go.Figure:
    """
    Renders Monte Carlo Fan Chart with market pro percentile bands:
    - 5th to 95th percentile (Market amber uncertainty envelope)
    - 25th to 75th percentile (Electric cobalt core)
    - Median path (Cyan line)
    - Initial capital line
    - Optional sample trajectories
    """
    fig = go.Figure()

    pct = sim_data["percentiles_over_time"]
    steps = np.arange(len(pct["p50"]))
    initial_val = sim_data["initial_value"]

    # 5th-95th Band (Uncertainty envelope)
    fig.add_trace(go.Scatter(
        x=steps,
        y=pct["p95"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=steps,
        y=pct["p05"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(245, 158, 11, 0.12)",
        name="5th – 95th Percentile Band",
        hoverinfo="skip"
    ))

    # 25th-75th Band (Core Interquartile)
    fig.add_trace(go.Scatter(
        x=steps,
        y=pct["p75"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=steps,
        y=pct["p25"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(37, 99, 235, 0.22)",
        name="25th – 75th Percentile Core",
        hoverinfo="skip"
    ))

    # Sample paths (first 6 paths for texture)
    if "sample_paths" in sim_data:
        for p in sim_data["sample_paths"][:6]:
            fig.add_trace(go.Scatter(
                x=steps,
                y=p,
                mode="lines",
                line=dict(color="rgba(148, 163, 184, 0.18)", width=0.8),
                showlegend=False,
                hoverinfo="skip"
            ))

    # Median Path
    fig.add_trace(go.Scatter(
        x=steps,
        y=pct["p50"],
        mode="lines",
        name="Median Path (50th Percentile)",
        line=dict(color=COLORS["secondary_accent"], width=2.6),
        hovertemplate="Day %{x}: <b>₹ %{y:,.0f}</b><extra></extra>"
    ))

    # Baseline capital
    total_inv = sim_data.get("total_invested", initial_val)
    if total_inv > initial_val:
        fig.add_trace(go.Scatter(
            x=[0, steps[-1]],
            y=[total_inv, total_inv],
            mode="lines",
            name=f"Total Invested with SIP (₹ {total_inv:,.0f})",
            line=dict(color=COLORS["secondary_text"], width=1.4, dash="dashdot"),
            hovertemplate="Total Capital with SIP: ₹ %{y:,.0f}<extra></extra>"
        ))
    else:
        fig.add_trace(go.Scatter(
            x=[0, steps[-1]],
            y=[initial_val, initial_val],
            mode="lines",
            name=f"Starting Capital (₹ {initial_val:,.0f})",
            line=dict(color=COLORS["secondary_text"], width=1.2, dash="dash"),
            hovertemplate="Starting Capital: ₹ %{y:,.0f}<extra></extra>"
        ))

    # Financial Goal Target Line (if specified)
    goal_val = sim_data.get("goal_target_value")
    goal_prob = sim_data.get("goal_probability")
    if goal_val is not None and goal_val > 0:
        prob_str = f" ({goal_prob * 100:.1f}% Probability)" if goal_prob is not None else ""
        fig.add_trace(go.Scatter(
            x=[0, steps[-1]],
            y=[goal_val, goal_val],
            mode="lines",
            name=f"Goal Target: ₹ {goal_val:,.0f}{prob_str}",
            line=dict(color=COLORS["warning"], width=1.8, dash="dot"),
            hovertemplate=f"Goal Target: ₹ %{{y:,.0f}}{prob_str}<extra></extra>"
        ))

    fig = _apply_sigmora_layout(fig, title="Monte Carlo Uncertainty Fan Chart (Simulated Portfolio Paths)", height=420)
    fig.update_layout(xaxis_title="Trading Days into Future", yaxis_title="Simulated Portfolio Value (₹)")
    return fig


def plot_simulation_distribution(sim_data: Dict[str, Any]) -> go.Figure:
    """Renders histogram of simulated ending portfolio values with markers."""
    fig = go.Figure()

    ending_vals = sim_data["ending_values"]
    initial_val = sim_data["initial_value"]
    median_val = sim_data["summary_percentiles"][50]
    p05_val = sim_data["summary_percentiles"][5]

    fig.add_trace(go.Histogram(
        x=ending_vals,
        nbinsx=40,
        marker=dict(color=COLORS["primary_accent"], opacity=0.8, line=dict(color="#121826", width=0.5)),
        name="Simulated Outcomes",
        hovertemplate="Range: ₹ %{x:,.0f}<br>Count: %{y}<extra></extra>"
    ))

    # Vertical line for Initial Value
    fig.add_vline(
        x=initial_val,
        line_width=1.6,
        line_dash="dash",
        line_color=COLORS["secondary_text"],
        annotation_text="Starting Capital",
        annotation_position="top left",
        annotation_font_size=10
    )

    # Vertical line for Median
    fig.add_vline(
        x=median_val,
        line_width=2.0,
        line_color=COLORS["secondary_accent"],
        annotation_text=f"Median (₹{median_val:,.0f})",
        annotation_position="top right",
        annotation_font_size=10
    )

    # Vertical line for 5th Percentile
    fig.add_vline(
        x=p05_val,
        line_width=1.5,
        line_dash="dot",
        line_color=COLORS["negative"],
        annotation_text=f"5th %ile (₹{p05_val:,.0f})",
        annotation_position="bottom left",
        annotation_font_size=9.5
    )

    fig = _apply_sigmora_layout(fig, title="Distribution of Terminal Portfolio Outcomes", height=320)
    fig.update_layout(xaxis_title="Ending Value (₹)", yaxis_title="Simulation Frequency", showlegend=False)
    return fig


def plot_risk_contribution_bars(risk_contrib_df: pd.DataFrame) -> go.Figure:
    """Renders horizontal component risk contribution comparison."""
    df = risk_contrib_df.sort_values(by="percentage_risk_contribution", ascending=True)

    fig = go.Figure()

    # Weight bar
    fig.add_trace(go.Bar(
        y=df.index,
        x=df["weight"] * 100.0,
        name="Capital Weight (%)",
        orientation="h",
        marker=dict(color=COLORS["neutral"], opacity=0.75),
        hovertemplate="%{y}: <b>%{x:.1f}%</b> capital<extra></extra>"
    ))

    # Risk contribution bar
    fig.add_trace(go.Bar(
        y=df.index,
        x=df["percentage_risk_contribution"] * 100.0,
        name="Volatility Contribution (%)",
        orientation="h",
        marker=dict(color=COLORS["secondary_accent"]),
        hovertemplate="%{y}: <b>%{x:.1f}%</b> of risk<extra></extra>"
    ))

    fig = _apply_sigmora_layout(fig, title="Euler Risk Contribution vs Capital Weight", height=320)
    fig.update_layout(barmode="group", xaxis_title="Percentage (%)")
    return fig


def plot_allocation_treemap(holdings_df: pd.DataFrame, by_sector: bool = False) -> go.Figure:
    """Renders dark market portfolio allocation treemap."""
    if holdings_df.empty:
        return go.Figure()

    df = holdings_df.copy()
    treemap_scale = [
        [0.0, COLORS["negative"]],
        [0.5, "#182234"],
        [1.0, COLORS["positive"]]
    ]

    if by_sector:
        fig = px.treemap(
            df,
            path=["sector", "symbol"],
            values="current_value",
            color="return_pct",
            color_continuous_scale=treemap_scale,
            color_continuous_midpoint=0.0
        )
    else:
        fig = px.treemap(
            df,
            path=["symbol"],
            values="current_value",
            color="return_pct",
            color_continuous_scale=treemap_scale,
            color_continuous_midpoint=0.0
        )

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=30, b=10),
        height=320,
        paper_bgcolor=COLORS["primary_surface"],
        font=dict(family="Inter, sans-serif", color=COLORS["primary_text"])
    )
    return fig


def plot_rolling_volatility(rolling_vol: pd.Series) -> go.Figure:
    """Renders 21-day rolling annualized volatility time series."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rolling_vol.index,
        y=rolling_vol.values * 100.0,
        mode="lines",
        name="21-Day Annualized Volatility",
        line=dict(color=COLORS["secondary_accent"], width=2.0),
        hovertemplate="%{x|%d %b %Y}: <b>%{y:.1f}%</b><extra></extra>"
    ))

    fig = _apply_sigmora_layout(fig, title="Historical Rolling Volatility (21-Day Annualized Window)", height=280)
    fig.update_layout(yaxis_title="Annualized Volatility (%)")
    return fig


def plot_efficient_frontier(
    frontier_df: pd.DataFrame,
    current_profile: Dict[str, Any],
    min_var: Dict[str, Any],
    max_sharpe: Dict[str, Any]
) -> go.Figure:
    """Renders Markowitz Efficient Frontier curve with key portfolio benchmarks."""
    fig = go.Figure()

    if not frontier_df.empty:
        fig.add_trace(go.Scatter(
            x=frontier_df["volatility"] * 100.0,
            y=frontier_df["return"] * 100.0,
            mode="lines",
            name="Efficient Frontier",
            line=dict(color=COLORS["secondary_accent"], width=2.2),
            hovertemplate="Vol: %{x:.1f}% | Exp Return: %{y:.1f}%<extra></extra>"
        ))

    # Current Portfolio
    fig.add_trace(go.Scatter(
        x=[current_profile["volatility"] * 100.0],
        y=[current_profile["expected_return"] * 100.0],
        mode="markers+text",
        name="Current Portfolio",
        text=["Current"],
        textposition="top center",
        marker=dict(color=COLORS["primary_text"], size=10, symbol="circle"),
        hovertemplate="Current: Vol %{x:.1f}%, Ret %{y:.1f}%<extra></extra>"
    ))

    # Min Variance
    if min_var.get("success"):
        fig.add_trace(go.Scatter(
            x=[min_var["volatility"] * 100.0],
            y=[min_var["expected_return"] * 100.0],
            mode="markers+text",
            name="Minimum Variance",
            text=["Min Var"],
            textposition="bottom right",
            marker=dict(color=COLORS["muted_highlight"], size=11, symbol="diamond"),
            hovertemplate="Min Var: Vol %{x:.1f}%, Ret %{y:.1f}%<extra></extra>"
        ))

    # Max Sharpe
    if max_sharpe.get("success"):
        fig.add_trace(go.Scatter(
            x=[max_sharpe["volatility"] * 100.0],
            y=[max_sharpe["expected_return"] * 100.0],
            mode="markers+text",
            name="Maximum Sharpe",
            text=["Max Sharpe"],
            textposition="top left",
            marker=dict(color=COLORS["positive"], size=12, symbol="star"),
            hovertemplate="Max Sharpe: Vol %{x:.1f}%, Ret %{y:.1f}%<extra></extra>"
        ))

    fig = _apply_sigmora_layout(fig, title="Markowitz Efficient Frontier (Risk vs Expected Return)", height=380)
    fig.update_layout(xaxis_title="Annualized Volatility (%)", yaxis_title="Expected Annual Return (%)")
    return fig


def plot_stress_comparison(stress_results: List[Dict[str, Any]]) -> go.Figure:
    """Renders scenario stress test comparison."""
    if not stress_results:
        return go.Figure()

    scenarios = [s["scenario_name"] for s in stress_results]
    orig_vals = [s["original_value"] for s in stress_results]
    stressed_vals = [s["stressed_value"] for s in stress_results]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scenarios,
        y=orig_vals,
        name="Original Capital",
        marker=dict(color=COLORS["neutral"], opacity=0.75)
    ))
    fig.add_trace(go.Bar(
        x=scenarios,
        y=stressed_vals,
        name="Stressed Value",
        marker=dict(color=COLORS["negative"], opacity=0.85)
    ))

    fig = _apply_sigmora_layout(fig, title="Capital Impact across Macro Scenarios", height=320)
    fig.update_layout(barmode="group", yaxis_title="Portfolio Value (₹)")
    return fig
