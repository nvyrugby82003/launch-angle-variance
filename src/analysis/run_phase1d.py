"""Run Phase 1d: python -m src.analysis.run_phase1d  (writes output/tables and output/figures)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import hypotheses as H
from src.viz import plots

PROCESSED = Path("data/processed")
TABLES = Path("output/tables")
FIGS = Path("output/figures")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)

    games = pd.read_parquet(PROCESSED / "team_games.parquet")
    d = H.prepare(pd.read_parquet(PROCESSED / "team_season.parquet"))

    curve = H.runs_to_wins(games)
    jg = H.jensen_gap(games, curve).merge(d[["team", "runs_cv", "fb_pct"]], on="team")
    h1, h2, h3, rob = H.run_h1(d), H.run_h2(d), H.run_h3(d), H.run_robustness(d)

    for name, t in {
        "runs_to_wins": curve,
        "jensen_gap": jg,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "robustness": rob,
        "correlations": d[
            ["fb_pct", "mean_la", "barrel_pct", "runs_per_game", "runs_cv", "win_residual"]
        ].corr(),
    }.items():
        t.to_csv(TABLES / f"{name}.csv", index=name == "correlations")

    plots.plot_runs_to_wins(curve).savefig(FIGS / "runs_to_wins.png", dpi=150)
    plots.scatter_with_fit(
        d, "fb_pct", "runs_cv", "Fly-ball rate", "CV of runs scored", "Fly-ball rate vs run CV"
    ).savefig(FIGS / "fb_vs_cv.png", dpi=150)
    plots.scatter_with_fit(
        d,
        "runs_cv",
        "win_residual",
        "CV of runs scored",
        "Win % - Pythagenpat",
        "Run CV vs win residual",
    ).savefig(FIGS / "cv_vs_win_residual.png", dpi=150)
    plots.plot_cv_intervals(d).savefig(FIGS / "cv_intervals.png", dpi=150)

    print(curve.round(3).to_string(index=False))
    print(H.concavity_summary(curve))
    print("\nJensen gap vs CV corr:", round(jg["jensen_gap"].corr(jg["runs_cv"]), 3))
    print("mean Jensen gap:", round(jg["jensen_gap"].mean(), 4))
    for t in (h1, h2):
        print("\n", t.round(4).to_string(index=False))
    print("\n", h3.round(4).to_string(index=False))
    print("\n", rob.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
