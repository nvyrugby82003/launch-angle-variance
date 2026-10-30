"""Tests for the multi-season panel (src/analysis/panel.py and build_panel.py)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.analysis import panel as P
from src.analysis.hypotheses import prepare


def _synthetic_panel(n_teams: int = 30, seasons=(2023, 2024, 2025), seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for s in seasons:
        for i in range(n_teams):
            rpg = rng.normal(4.5, 0.3)
            rows.append(
                {
                    "season": s,
                    "team": f"T{i:02d}",
                    "fb_pct": rng.normal(0.24, 0.02),
                    "mean_la": rng.normal(12, 1),
                    "barrel_pct": rng.normal(0.07, 0.01),
                    "pull_air_pct": rng.normal(0.2, 0.02),
                    "sweet_spot_pct": rng.normal(0.35, 0.02),
                    "park_factor": rng.normal(100, 3),
                    "runs_per_game": rpg,
                    "runs_var": rng.normal(10, 1),
                    "runs_cv": rng.normal(0.71, 0.04),
                    "runs_allowed_cv": rng.normal(0.71, 0.04),
                    "dispersion_index": rng.normal(2.2, 0.2),
                    "win_pct": rng.normal(0.5, 0.05),
                    "win_residual": rng.normal(0, 0.02),
                }
            )
    return prepare(pd.DataFrame(rows))


def test_panel_models_run_and_return_key_terms():
    d = _synthetic_panel()
    assert "fb_pts" in set(P.run_p1(d)["term"])
    assert not P.run_p1(d)["term"].str.startswith("C(").any()
    assert {"runs_cv", "runs_allowed_cv"} <= set(P.run_p2(d)["term"])


def test_p3_flags_six_per_season():
    d = _synthetic_panel()
    assert (P.run_p3(d)["n_top"] == 6 * d["season"].nunique()).all()


def test_persistence_detects_stable_metric():
    d = _synthetic_panel()
    team_effect = d["team"].str[1:].astype(float)
    d["fb_pct"] = 0.2 + team_effect / 1000  # identical each season
    pers = P.persistence(d).set_index("metric")
    assert pers.loc["fb_pct", "year_to_year_r"] == pytest.approx(1.0)
    assert abs(pers.loc["runs_cv", "year_to_year_r"]) < 0.5


PANEL = Path("data/processed/panel_team_season.parquet")


@pytest.mark.skipif(not PANEL.exists(), reason="processed panel not built")
def test_processed_panel_is_complete():
    d = pd.read_parquet(PANEL)
    assert len(d) == 120
    assert d.groupby("season").size().eq(30).all()
    assert not d.duplicated(["season", "team"]).any()
    assert "OAK" not in set(d["team"])
    assert d["games"].between(161, 162).all()
    assert d.notna().all().all()
