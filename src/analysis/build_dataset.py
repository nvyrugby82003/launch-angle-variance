"""Build processed tables: python -m src.analysis.build_dataset"""

from __future__ import annotations

from pathlib import Path

from src.analysis import config as C
from src.analysis import features as F
from src.ingestion.gamelogs import load_gamelogs
from src.ingestion.statcast import load_season

OUT_DIR = Path("data/processed")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bb = F.clean_batted_balls(load_season(C.SEASON))
    team_games = F.build_team_games(load_gamelogs(C.SEASON))
    profiles = F.team_lineup_profiles(bb)
    stats = F.team_run_stats(team_games)
    pf = F.load_park_factors()
    # Park factor of the team's own home park (proxy for its run environment)
    team_table = stats.merge(profiles, on="team", validate="1:1").merge(
        pf, on="team", validate="1:1"
    )
    team_games.to_parquet(OUT_DIR / "team_games.parquet", index=False)
    profiles.to_parquet(OUT_DIR / "team_profiles.parquet", index=False)
    team_table.to_parquet(OUT_DIR / "team_season.parquet", index=False)
    print(f"batted balls: {len(bb):,}; team-games: {len(team_games):,}; teams: {len(team_table)}")


if __name__ == "__main__":
    main()
