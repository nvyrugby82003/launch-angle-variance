import numpy as np
import pandas as pd
from src.analysis import hypotheses as H


def _games() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    runs = rng.poisson(4.5, 3000)
    win = rng.random(3000) < 1 / (1 + np.exp(-(runs - 4.5) * 0.5))
    return pd.DataFrame({"team": ["A", "B", "C"] * 1000, "runs": runs, "win": win})


def test_runs_to_wins_buckets_and_ci():
    c = H.runs_to_wins(_games())
    assert c["bucket"].max() == H.MAX_RUNS_BUCKET
    assert c["games"].sum() == 3000
    assert (c["ci_lo"] <= c["win_pct"]).all() and (c["win_pct"] <= c["ci_hi"]).all()


def test_jensen_gap_is_negative_for_concave_region():
    g = pd.DataFrame({"team": ["X"] * 4, "runs": [0, 10, 0, 10], "win": [0, 1, 0, 1]})
    curve = pd.DataFrame(
        {"bucket": list(range(11)), "win_pct": [min(1.0, r / 5) for r in range(11)]}
    )
    curve["win_pct"] = np.sqrt(curve["win_pct"])  # concave
    gap = H.jensen_gap(g, curve).iloc[0]["jensen_gap"]
    assert gap < 0


def test_h3_picks_top_quintile():
    rng = np.random.default_rng(1)
    d = pd.DataFrame(
        {
            "team": [f"T{i}" for i in range(30)],
            "fb_pct": np.linspace(0.2, 0.3, 30),
            "runs_per_game": rng.normal(4.5, 0.3, 30),
            "runs_cv": rng.normal(0.7, 0.03, 30),
            "runs_allowed_cv": rng.normal(0.7, 0.03, 30),
            "win_pct": rng.normal(0.5, 0.05, 30),
            "win_residual": rng.normal(0, 0.02, 30),
        }
    )
    out = H.run_h3(d)
    assert out["top_teams"].iloc[0].split(",") == sorted(f"T{i}" for i in range(24, 30))
    assert (out["ci_lo"] <= out["diff"]).all()


def test_ols_recovers_slope():
    rng = np.random.default_rng(2)
    x = rng.normal(size=200)
    df = pd.DataFrame({"x": x, "y": 2 * x + rng.normal(scale=0.1, size=200)})
    res = H.fit_ols(df, "y ~ x")
    assert abs(res.params["x"] - 2) < 0.05
