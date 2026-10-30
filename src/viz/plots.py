"""Reusable plotting functions. Each returns the Matplotlib Figure."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

CUBS_COLOR = "#0E3386"
OTHER_COLOR = "#8c8c8c"


def plot_runs_to_wins(curve: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(
        curve["bucket"],
        curve["win_pct"],
        yerr=[curve["win_pct"] - curve["ci_lo"], curve["ci_hi"] - curve["win_pct"]],
        fmt="o-",
        color=CUBS_COLOR,
        capsize=3,
    )
    ax.axhline(0.5, color="k", lw=0.5, ls="--")
    ax.set_xlabel("Runs scored (10 = 10+)")
    ax.set_ylabel("Win %")
    ax.set_title("2026 MLB: win % by runs scored (95% Wilson CI)")
    fig.tight_layout()
    return fig


def scatter_with_fit(
    d: pd.DataFrame, x: str, y: str, xlabel: str, ylabel: str, title: str
) -> plt.Figure:
    """Team scatter with OLS line; Cubs highlighted and all teams labeled."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = np.where(d["team"] == "CHC", CUBS_COLOR, OTHER_COLOR)
    ax.scatter(d[x], d[y], c=colors, s=45)
    for _, r in d.iterrows():
        ax.annotate(r["team"], (r[x], r[y]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    slope, intercept = np.polyfit(d[x], d[y], 1)
    xs = np.linspace(d[x].min(), d[x].max(), 50)
    ax.plot(xs, intercept + slope * xs, color="firebrick", lw=1)
    r = np.corrcoef(d[x], d[y])[0, 1]
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} (r = {r:.2f}, n = {len(d)})")
    fig.tight_layout()
    return fig


def scatter_within_season(
    d: pd.DataFrame, x: str, y: str, xlabel: str, ylabel: str, title: str
) -> plt.Figure:
    """Panel scatter after removing season means from x and y; one color per season, Cubs ringed."""
    dm = d.copy()
    for col in (x, y):
        dm[col] = dm[col] - dm.groupby("season")[col].transform("mean")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for season, g in dm.groupby("season"):
        ax.scatter(g[x], g[y], s=30, alpha=0.75, label=str(season))
    cubs = dm[dm["team"] == "CHC"]
    ax.scatter(
        cubs[x], cubs[y], s=110, facecolors="none", edgecolors=CUBS_COLOR, lw=1.8, label="CHC"
    )
    slope, intercept = np.polyfit(dm[x], dm[y], 1)
    xs = np.linspace(dm[x].min(), dm[x].max(), 50)
    ax.plot(xs, intercept + slope * xs, color="firebrick", lw=1)
    r = np.corrcoef(dm[x], dm[y])[0, 1]
    ax.set_xlabel(f"{xlabel} (minus season mean)")
    ax.set_ylabel(f"{ylabel} (minus season mean)")
    ax.set_title(f"{title} (r = {r:.2f}, n = {len(dm)})")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_cv_intervals(d: pd.DataFrame) -> plt.Figure:
    """Team CV of runs scored with bootstrap 95% CIs, sorted by fly-ball rate."""
    s = d.sort_values("fb_pct").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7, 8))
    colors = np.where(s["team"] == "CHC", CUBS_COLOR, OTHER_COLOR)
    ax.hlines(s.index, s["runs_cv_lo"], s["runs_cv_hi"], color=colors)
    ax.scatter(s["runs_cv"], s.index, c=colors, zorder=3)
    ax.set_yticks(s.index)
    labels = [f"{t} ({f:.1%})" for t, f in zip(s["team"], s["fb_pct"], strict=True)]
    ax.set_yticklabels(labels, fontsize=8)
    ax.axvline(s["runs_cv"].mean(), color="k", lw=0.5, ls="--")
    ax.set_xlabel("CV of runs scored per game (bootstrap 95% CI)")
    ax.set_title("Run-scoring CV by team, ordered by fly-ball rate")
    fig.tight_layout()
    return fig
