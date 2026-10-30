"""Run the multi-season analysis: python -m src.analysis.run_panel"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import hypotheses as H
from src.analysis import panel as P
from src.viz import plots

PROCESSED = Path("data/processed")
TABLES = Path("output/tables")
FIGS = Path("output/figures")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)

    games = pd.read_parquet(PROCESSED / "panel_team_games.parquet")
    d = P.prepare_panel(pd.read_parquet(PROCESSED / "panel_team_season.parquet"))

    curve = H.runs_to_wins(games)
    jg = H.jensen_gap(games, curve)
    p1, p2, p3 = P.run_p1(d), P.run_p2(d), P.run_p3(d)
    rob, pers = P.run_panel_robustness(d), P.persistence(d)
    for name, t in {
        "panel_runs_to_wins": curve,
        "panel_p1": p1,
        "panel_p2": p2,
        "panel_p3": p3,
        "panel_robustness": rob,
        "panel_persistence": pers,
    }.items():
        t.to_csv(TABLES / f"{name}.csv", index=False)

    plots.scatter_within_season(
        d,
        "fb_pct",
        "runs_cv",
        "Fly-ball rate",
        "CV of runs scored",
        "Panel: fly-ball rate vs run CV",
    ).savefig(FIGS / "panel_fb_vs_cv.png", dpi=150)
    plots.scatter_within_season(
        d, "runs_cv", "win_residual", "CV of runs scored", "Win % - Pythagenpat",
        "Panel: run CV vs win residual",
    ).savefig(FIGS / "panel_cv_vs_win_residual.png", dpi=150)  # fmt: skip

    print(curve.round(3).to_string(index=False))
    print(H.concavity_summary(curve))
    print("mean Jensen gap (pooled curve):", round(jg["jensen_gap"].mean(), 4))
    for t in (p1, p2):
        print("\n", t.round(4).to_string(index=False))
    print("\n", p3.round(4).to_string(index=False))
    print("\n", rob.round(4).to_string(index=False))
    print("\n", pers.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
