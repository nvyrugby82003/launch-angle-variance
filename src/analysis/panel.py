"""Multi-season (2023-2026) versions of H1-H3 and robustness, with team-clustered errors.

Every model includes season fixed effects (league-wide launch-angle and run-environment
drift). Standard errors are clustered by team because the same franchise appears in up to
four seasons. With only 30 clusters, cluster-robust CIs are approximate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from src.analysis.hypotheses import coef_table, prepare

SEASON_FE = " + C(season)"
P1 = "runs_cv ~ fb_pts + park_factor + runs_per_game" + SEASON_FE
P1_TEAM_FE = "runs_cv ~ fb_pts + runs_per_game + C(team)" + SEASON_FE  # park factor absorbed
P2 = "win_residual ~ runs_cv + runs_allowed_cv" + SEASON_FE
KEY_TERMS = ("fb_pts", "runs_cv", "runs_allowed_cv")


def fit_cluster(df: pd.DataFrame, formula: str):
    """OLS with standard errors clustered by team."""
    return smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df["team"]})


def prepare_panel(panel: pd.DataFrame) -> pd.DataFrame:
    return prepare(panel)


def _key_rows(res, model: str) -> pd.DataFrame:
    t = coef_table(res, model)
    return t[~t["term"].str.startswith("C(")].reset_index(drop=True)


def run_p1(d: pd.DataFrame) -> pd.DataFrame:
    return _key_rows(fit_cluster(d, P1), "P1")


def run_p2(d: pd.DataFrame) -> pd.DataFrame:
    return _key_rows(fit_cluster(d, P2), "P2")


def run_p3(d: pd.DataFrame) -> pd.DataFrame:
    """Top-quintile FB% team-seasons (top 6 within each season) vs the rest, season FE."""
    d = d.copy()
    d["top_fb"] = (d.groupby("season")["fb_pct"].rank(ascending=False, method="first") <= 6).astype(
        int
    )
    rows = []
    for col in ["fb_pct", "runs_per_game", "runs_cv", "runs_allowed_cv", "win_pct", "win_residual"]:
        res = fit_cluster(d, f"{col} ~ top_fb" + SEASON_FE)
        ci = res.conf_int().loc["top_fb"]
        rows.append(
            {
                "metric": col,
                "top_mean": d.loc[d.top_fb == 1, col].mean(),
                "rest_mean": d.loc[d.top_fb == 0, col].mean(),
                "adj_diff": res.params["top_fb"],
                "ci_lo": ci[0],
                "ci_hi": ci[1],
                "p": res.pvalues["top_fb"],
                "n_top": int(d.top_fb.sum()),
            }
        )
    return pd.DataFrame(rows)


def run_panel_robustness(d: pd.DataFrame) -> pd.DataFrame:
    """Secondary specs for the exposure coefficient; per-season and leave-one-team-out."""
    base = "park_factor + runs_per_game" + SEASON_FE
    specs = {
        "P1 primary": (d, P1, "fb_pts"),
        "P1 team fixed effects": (d, P1_TEAM_FE, "fb_pts"),
        "P1 exclude CHC": (d[d.team != "CHC"], P1, "fb_pts"),
        "P1 mean LA": (d, f"runs_cv ~ mean_la + {base}", "mean_la"),
        "P1 barrel %": (d, f"runs_cv ~ barrel_pts + {base}", "barrel_pts"),
        "P1 pull-air %": (d, f"runs_cv ~ pull_air_pts + {base}", "pull_air_pts"),
        "P1 sweet-spot %": (d, f"runs_cv ~ sweet_pts + {base}", "sweet_pts"),
        "P1 dispersion index": (d, f"dispersion_index ~ fb_pts + {base}", "fb_pts"),
        "P1 NB2 alpha": (d, f"nb_alpha ~ fb_pts + {base}", "fb_pts"),
    }
    rows = []
    for name, (data, formula, term) in specs.items():
        res = fit_cluster(data, formula)
        ci = res.conf_int().loc[term]
        rows.append(_robust_row(name, term, res.params[term], ci[0], ci[1], res.pvalues[term], res))
    for season, g in d.groupby("season"):
        res = smf.ols("runs_cv ~ fb_pts + park_factor + runs_per_game", data=g).fit(cov_type="HC3")
        ci = res.conf_int().loc["fb_pts"]
        rows.append(
            _robust_row(
                f"P1 season {season} only", "fb_pts", res.params["fb_pts"], ci[0], ci[1],
                res.pvalues["fb_pts"], res,
            )
        )  # fmt: skip
    loo = [fit_cluster(d[d.team != t], P1).params["fb_pts"] for t in d["team"].unique()]
    rows.append(
        {
            "spec": "P1 leave-one-team-out (min / max coef)",
            "term": "fb_pts",
            "coef": float(np.median(loo)),
            "ci_lo": float(np.min(loo)),
            "ci_hi": float(np.max(loo)),
            "p": np.nan,
            "n": len(d) - 4,
        }
    )
    return pd.DataFrame(rows)


def _robust_row(name, term, coef, lo, hi, p, res) -> dict:
    return {
        "spec": name,
        "term": term,
        "coef": coef,
        "ci_lo": lo,
        "ci_hi": hi,
        "p": p,
        "n": int(res.nobs),
    }


def persistence(d: pd.DataFrame) -> pd.DataFrame:
    """Year-to-year correlation of each metric across consecutive seasons (same team).

    Low persistence of run CV means much of it is sampling noise, which limits any
    exposure -> CV relationship regardless of sample size.
    """
    rows = []
    for col in ["fb_pct", "runs_cv", "runs_per_game", "win_residual"]:
        wide = d.pivot(index="team", columns="season", values=col)
        pairs = [(a, b) for a, b in zip(wide.columns[:-1], wide.columns[1:], strict=True)]
        x = np.concatenate([wide[a].to_numpy() for a, _ in pairs])
        y = np.concatenate([wide[b].to_numpy() for _, b in pairs])
        r, p = stats.pearsonr(x, y)
        rows.append({"metric": col, "year_to_year_r": r, "p": p, "n_pairs": len(x)})
    return pd.DataFrame(rows)
