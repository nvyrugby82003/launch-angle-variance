"""Tests for feature construction and (when data exists) processed-table validation."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.analysis import features as F

PROCESSED = Path("data/processed")


def _pitches() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "game_type": ["R", "R", "R", "S", "R"],
            "type": ["X", "X", "S", "X", "X"],
            "launch_angle": [5.0, 30.0, None, 30.0, None],
            "inning_topbot": ["Top", "Bot", "Top", "Top", "Top"],
            "away_team": ["AZ", "AZ", "AZ", "AZ", "AZ"],
            "home_team": ["CHC", "CHC", "CHC", "CHC", "CHC"],
        }
    )


def test_clean_batted_balls_filters_and_maps_team():
    bb = F.clean_batted_balls(_pitches())
    assert len(bb) == 2
    assert list(bb["batting_team"]) == ["ARI", "CHC"]


def test_profiles_bands_sum_to_one():
    bb = F.clean_batted_balls(_pitches())
    bb["launch_speed"] = 100.0
    bb["launch_speed_angle"] = 6
    bb["hc_x"], bb["hc_y"], bb["stand"] = 100.0, 100.0, "R"
    prof = F.team_lineup_profiles(bb).set_index("team")
    bands = prof[["gb_pct", "ld_pct", "fb_pct", "pu_pct"]].sum(axis=1)
    assert np.allclose(bands, 1.0)
    assert prof.loc["CHC", "fb_pct"] == 1.0 and prof.loc["ARI", "gb_pct"] == 1.0


def test_band_edges():
    bb = pd.DataFrame(
        {
            "launch_angle": [9.99, 10.0, 24.99, 25.0, 49.99, 50.0],
            "launch_speed": 90.0,
            "launch_speed_angle": 1,
            "hc_x": 125.42,
            "hc_y": 100.0,
            "stand": "R",
        }
    )
    f = F.add_batted_ball_flags(bb)
    assert list(f["is_gb"]) == [True, False, False, False, False, False]
    assert list(f["is_ld"]) == [False, True, True, False, False, False]
    assert list(f["is_fb"]) == [False, False, False, True, True, False]
    assert list(f["is_pu"]) == [False] * 5 + [True]


def test_pull_air_handedness():
    bb = pd.DataFrame(
        {
            "launch_angle": [20.0, 20.0, 20.0],
            "launch_speed": 90.0,
            "launch_speed_angle": 1,
            "hc_x": [50.0, 50.0, None],
            "hc_y": 100.0,
            "stand": ["R", "L", "R"],
        }
    )
    f = F.add_batted_ball_flags(bb)
    assert list(f["is_pull_air"]) == [True, False, False]


def test_bootstrap_cv_reproducible_and_brackets_estimate():
    runs = np.array([0, 2, 5, 3, 8, 1, 4, 6, 2, 3] * 10, dtype=float)
    a, b = F.bootstrap_cv(runs, 500, seed=1), F.bootstrap_cv(runs, 500, seed=1)
    assert a == b
    cv = runs.std(ddof=1) / runs.mean()
    assert a[2] < cv < a[3]


@pytest.mark.skipif(not (PROCESSED / "team_season.parquet").exists(), reason="no processed data")
def test_processed_tables_valid():
    season = pd.read_parquet(PROCESSED / "team_season.parquet")
    games = pd.read_parquet(PROCESSED / "team_games.parquet")
    assert len(season) == 30 and season["team"].is_unique
    assert season["games"].between(160, 162).all()
    assert season["park_factor"].notna().all() and season["fb_pct"].notna().all()
    assert games["runs"].sum() == games["runs_allowed"].sum()
    assert not games.duplicated(["team", "team_game"]).any()
    assert len(games) % 2 == 0
