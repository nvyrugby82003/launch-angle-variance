"""Build the multi-season panel: python -m src.analysis.build_panel

Writes data/processed/panel_team_games.parquet and panel_team_season.parquet (one row per
team-season, 2023-2026). Bootstrap seed for each season is ``season * 100`` (+ team index).
Park factors are a single 2025 FanGraphs 5-year value per team, used for every season.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import config as C
from src.analysis import features as F
from src.ingestion.gamelogs import load_gamelogs
from src.ingestion.statcast import load_season

OUT_DIR = Path("data/processed")


def build_panel(seasons: tuple[int, ...] = C.SEASONS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (team_games, team_season) stacked over seasons, each with a `season` column."""
    pf = F.load_park_factors()
    games_all, season_all = [], []
    for season in seasons:
        bb = F.clean_batted_balls(load_season(season))
        games = F.build_team_games(load_gamelogs(season), season)
        table = (
            F.team_run_stats(games, seed=season * 100)
            .merge(F.team_lineup_profiles(bb), on="team", validate="1:1")
            .merge(pf, on="team", validate="1:1")
        )
        games.insert(0, "season", season)
        table.insert(0, "season", season)
        games_all.append(games)
        season_all.append(table)
    return pd.concat(games_all, ignore_index=True), pd.concat(season_all, ignore_index=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    games, table = build_panel()
    games.to_parquet(OUT_DIR / "panel_team_games.parquet", index=False)
    table.to_parquet(OUT_DIR / "panel_team_season.parquet", index=False)
    print(f"team-games: {len(games):,}; team-seasons: {len(table)}")
    print(table.groupby("season").size().to_dict())


if __name__ == "__main__":
    main()
