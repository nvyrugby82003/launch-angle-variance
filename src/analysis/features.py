"""Cleaning and feature construction for the team-level dataset (docs/metrics.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis import config as C


def clean_batted_balls(pitches: pd.DataFrame) -> pd.DataFrame:
    """Regular-season balls in play with a batting-team column and non-null launch angle."""
    df = pitches[(pitches["game_type"] == "R") & (pitches["type"] == "X")].copy()
    df = df.dropna(subset=["launch_angle"])
    batting = np.where(df["inning_topbot"] == "Top", df["away_team"], df["home_team"])
    df["batting_team"] = (
        pd.Series(batting, index=df.index).replace(C.STATCAST_TO_BR).replace(C.FRANCHISE_ALIASES)
    )
    return df


def spray_angle(hc_x: pd.Series, hc_y: pd.Series) -> pd.Series:
    """Spray angle in degrees; negative = left of center field, positive = right."""
    return np.degrees(np.arctan((hc_x - C.HC_X_HOME) / (C.HC_Y_HOME - hc_y)))


def add_batted_ball_flags(bb: pd.DataFrame) -> pd.DataFrame:
    """Add boolean band/flag columns used for aggregation."""
    la = bb["launch_angle"]
    out = bb.copy()
    out["is_gb"] = la < C.GB_MAX
    out["is_ld"] = (la >= C.GB_MAX) & (la < C.LD_MAX)
    out["is_fb"] = (la >= C.LD_MAX) & (la < C.FB_MAX)
    out["is_pu"] = la >= C.FB_MAX
    out["is_sweet"] = (la >= C.SWEET_SPOT_MIN) & (la <= C.SWEET_SPOT_MAX)
    out["is_barrel"] = out["launch_speed_angle"] == C.BARREL_CODE
    out["is_hard"] = out["launch_speed"] >= C.HARD_HIT_MPH
    # RHB pull = left side (negative angle); LHB pull = right side (positive angle)
    spray = spray_angle(out["hc_x"].astype(float), out["hc_y"].astype(float)).to_numpy(float)
    right = (out["stand"] == "R").to_numpy(bool)
    pull = np.where(right, spray < 0, spray > 0)  # NaN spray compares False
    has_stand = out["stand"].isin(["L", "R"]).to_numpy(bool)
    out["is_pull_air"] = (la >= C.GB_MAX).to_numpy(bool) & pull & has_stand
    return out


def team_lineup_profiles(bb: pd.DataFrame) -> pd.DataFrame:
    """One row per batting team. Pooled over all batted balls (BBE-weighted)."""
    flagged = add_batted_ball_flags(bb)
    g = flagged.groupby("batting_team")
    prof = pd.DataFrame(
        {
            "batted_balls": g.size(),
            "mean_la": g["launch_angle"].mean(),
            "gb_pct": g["is_gb"].mean(),
            "ld_pct": g["is_ld"].mean(),
            "fb_pct": g["is_fb"].mean(),
            "pu_pct": g["is_pu"].mean(),
            "sweet_spot_pct": g["is_sweet"].mean(),
            "barrel_pct": g["is_barrel"].mean(),
            "hard_hit_pct": g["is_hard"].mean(),
            "pull_air_pct": g["is_pull_air"].mean(),
        }
    )
    prof["gb_fb_ratio"] = g["is_gb"].sum() / g["is_fb"].sum()
    prof.index.name = "team"
    return prof.reset_index()


def build_team_games(gamelogs: pd.DataFrame, season: int = C.SEASON) -> pd.DataFrame:
    """Typed team-game table: one row per team per game (regular season)."""
    df = gamelogs.copy()
    df["date"] = pd.to_datetime(
        df["date_game"].str.replace(r"\s*\(\d\)", "", regex=True) + f" {season}",
        format="%A, %b %d %Y",
    )
    df["team"] = df["team"].replace(C.FRANCHISE_ALIASES)
    df["opp_ID"] = df["opp_ID"].replace(C.FRANCHISE_ALIASES)
    df["runs"] = pd.to_numeric(df["R"])
    df["runs_allowed"] = pd.to_numeric(df["RA"])
    df["home"] = df["homeORvis"] != "@"
    df["win"] = df["win_loss_result"].str.startswith("W")
    df["park"] = np.where(df["home"], df["team"], df["opp_ID"])
    df["opponent"] = df["opp_ID"]
    df["team_game"] = pd.to_numeric(df["team_game"])
    cols = ["team", "team_game", "date", "opponent", "home", "park", "runs", "runs_allowed", "win"]
    return df[cols].sort_values(["team", "date"], kind="stable").reset_index(drop=True)


def bootstrap_cv(
    runs: np.ndarray, n_boot: int = 5000, seed: int = 2026
) -> tuple[float, float, float, float]:
    """Bootstrap (resample games) 95% CIs; returns (sd_lo, sd_hi, cv_lo, cv_hi)."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(runs), size=(n_boot, len(runs)))
    samp = runs[idx]
    sd = samp.std(axis=1, ddof=1)
    cv = sd / samp.mean(axis=1)
    return (*np.percentile(sd, [2.5, 97.5]), *np.percentile(cv, [2.5, 97.5]))


def team_run_stats(team_games: pd.DataFrame, n_boot: int = 5000, seed: int = 2026) -> pd.DataFrame:
    """Per-team mean/variance/CV of runs scored and allowed, with bootstrap CIs."""
    rows = []
    for i, (team, g) in enumerate(team_games.groupby("team")):
        rs = g["runs"].to_numpy(dtype=float)
        ra = g["runs_allowed"].to_numpy(dtype=float)
        sd_lo, sd_hi, cv_lo, cv_hi = bootstrap_cv(rs, n_boot, seed + i)
        w, games = int(g["win"].sum()), len(g)
        rpg = (rs.sum() + ra.sum()) / games
        x = rpg**0.287
        pyth = rs.sum() ** x / (rs.sum() ** x + ra.sum() ** x)
        rows.append(
            {
                "team": team,
                "games": games,
                "wins": w,
                "win_pct": w / games,
                "runs_per_game": rs.mean(),
                "runs_var": rs.var(ddof=1),
                "runs_sd": rs.std(ddof=1),
                "runs_cv": rs.std(ddof=1) / rs.mean(),
                "runs_sd_lo": sd_lo,
                "runs_sd_hi": sd_hi,
                "runs_cv_lo": cv_lo,
                "runs_cv_hi": cv_hi,
                "dispersion_index": rs.var(ddof=1) / rs.mean(),
                "shutout_rate": float((rs == 0).mean()),
                "big_game_rate": float((rs >= C.BIG_GAME_RUNS).mean()),
                "runs_allowed_per_game": ra.mean(),
                "runs_allowed_cv": ra.std(ddof=1) / ra.mean(),
                "home_share": float(g["home"].mean()),
                "pythagenpat_win_pct": pyth,
                "win_residual": w / games - pyth,
            }
        )
    return pd.DataFrame(rows)


def load_park_factors(path: str = "data/external/fangraphs-guts-data.csv") -> pd.DataFrame:
    """Run park factor (FanGraphs 'Basic (5yr)', 100 = neutral) keyed by team code."""
    pf = pd.read_csv(path)
    pf["team"] = pf["Team"].map(C.FANGRAPHS_NAME_TO_CODE)
    if pf["team"].isna().any():
        raise ValueError(
            f"Unmapped park-factor teams: {pf.loc[pf['team'].isna(), 'Team'].tolist()}"
        )
    return pf[["team", "Basic (5yr)"]].rename(columns={"Basic (5yr)": "park_factor"})
