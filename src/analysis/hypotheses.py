"""Phase 1d: concavity check, pre-registered H1-H3 and robustness (see docs/metrics.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint

MAX_RUNS_BUCKET = 10


def runs_to_wins(team_games: pd.DataFrame) -> pd.DataFrame:
    """League-wide win % by runs scored (0..10+), with Wilson 95% CIs and marginal gain per run."""
    g = team_games.assign(bucket=team_games["runs"].clip(upper=MAX_RUNS_BUCKET).astype(int))
    out = g.groupby("bucket")["win"].agg(games="size", wins="sum").reset_index()
    out["win_pct"] = out["wins"] / out["games"]
    lo, hi = proportion_confint(out["wins"], out["games"], method="wilson")
    out["ci_lo"], out["ci_hi"] = lo, hi
    out["marginal_gain"] = out["win_pct"].diff()
    return out


def concavity_summary(curve: pd.DataFrame) -> dict[str, float]:
    """Mean marginal win-% gain from the first vs last half of the 0..10 range."""
    gains = curve["marginal_gain"].dropna().to_numpy()
    half = len(gains) // 2
    return {
        "mean_gain_low_runs": float(gains[:half].mean()),
        "mean_gain_high_runs": float(gains[half:].mean()),
    }


def jensen_gap(team_games: pd.DataFrame, curve: pd.DataFrame) -> pd.DataFrame:
    """Per team: expected win % from its actual runs distribution (E[f(R)]) vs f(mean R).

    f is the league empirical runs-to-wins curve (linearly interpolated). A negative gap
    means the team's dispersion costs wins relative to a team scoring its mean every game.
    """
    xs, ys = curve["bucket"].to_numpy(float), curve["win_pct"].to_numpy(float)
    rows = []
    for team, g in team_games.groupby("team"):
        r = g["runs"].clip(upper=MAX_RUNS_BUCKET).to_numpy(float)
        rows.append(
            {
                "team": team,
                "exp_win_from_distribution": float(np.interp(r, xs, ys).mean()),
                "exp_win_from_mean": float(np.interp(r.mean(), xs, ys)),
            }
        )
    out = pd.DataFrame(rows)
    out["jensen_gap"] = out["exp_win_from_distribution"] - out["exp_win_from_mean"]
    return out


def fit_ols(df: pd.DataFrame, formula: str):
    """OLS with HC3 robust standard errors."""
    return smf.ols(formula, data=df).fit(cov_type="HC3")


def coef_table(res, model: str) -> pd.DataFrame:
    ci = res.conf_int()
    t = pd.DataFrame(
        {
            "model": model,
            "term": res.params.index,
            "coef": res.params.values,
            "se": res.bse.values,
            "p": res.pvalues.values,
            "ci_lo": ci[0].values,
            "ci_hi": ci[1].values,
        }
    )
    t["r2"] = res.rsquared
    t["n"] = int(res.nobs)
    return t


def prepare(team_season: pd.DataFrame) -> pd.DataFrame:
    """Add the analysis columns: FB% in points, NB2 moment dispersion, z-scores."""
    d = team_season.copy()
    d["fb_pts"] = d["fb_pct"] * 100
    d["barrel_pts"] = d["barrel_pct"] * 100
    d["pull_air_pts"] = d["pull_air_pct"] * 100
    d["sweet_pts"] = d["sweet_spot_pct"] * 100
    d["nb_alpha"] = (d["runs_var"] - d["runs_per_game"]) / d["runs_per_game"] ** 2
    return d


H1 = "runs_cv ~ fb_pts + park_factor + runs_per_game"
H2 = "win_residual ~ runs_cv + runs_allowed_cv"


def run_h1(d: pd.DataFrame) -> pd.DataFrame:
    return coef_table(fit_ols(d, H1), "H1")


def run_h2(d: pd.DataFrame) -> pd.DataFrame:
    return coef_table(fit_ols(d, H2), "H2")


def run_h3(d: pd.DataFrame) -> pd.DataFrame:
    """Top-quintile FB% lineups (top 6 of 30) vs the other 24, with Welch t-test p-values."""
    from scipy import stats

    k = int(round(len(d) * 0.2))
    top_teams = d.nlargest(k, "fb_pct")["team"]
    d = d.assign(top_fb=d["team"].isin(top_teams))
    rows = []
    for col in ["fb_pct", "runs_per_game", "runs_cv", "runs_allowed_cv", "win_pct", "win_residual"]:
        a, b = d.loc[d.top_fb, col], d.loc[~d.top_fb, col]
        diff = a.mean() - b.mean()
        t = stats.ttest_ind(a, b, equal_var=False)
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        df_w = t.df
        crit = stats.t.ppf(0.975, df_w)
        rows.append(
            {
                "metric": col,
                "top_mean": a.mean(),
                "rest_mean": b.mean(),
                "diff": diff,
                "ci_lo": diff - crit * se,
                "ci_hi": diff + crit * se,
                "p": t.pvalue,
                "top_teams": ",".join(sorted(top_teams)),
            }
        )
    return pd.DataFrame(rows)


PLAYOFF_PATH = "data/external/playoff-teams-2026.csv"
PLAYOFF_METRICS = [
    "win_pct",
    "runs_per_game",
    "runs_allowed_per_game",
    "runs_cv",
    "runs_allowed_cv",
    "fb_pct",
    "shutout_rate",
    "win_residual",
]


def load_playoff_teams(path: str = PLAYOFF_PATH) -> list[str]:
    return pd.read_csv(path)["team"].tolist()


def compare_playoff(d: pd.DataFrame, playoff_teams: list[str]) -> pd.DataFrame:
    """Playoff vs non-playoff team means with Welch 95% CIs. Descriptive only."""
    from scipy import stats

    is_po = d["team"].isin(playoff_teams)
    rows = []
    for col in PLAYOFF_METRICS:
        a, b = d.loc[is_po, col], d.loc[~is_po, col]
        t = stats.ttest_ind(a, b, equal_var=False)
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        crit = stats.t.ppf(0.975, t.df)
        diff = a.mean() - b.mean()
        rows.append(
            {
                "metric": col,
                "playoff_mean": a.mean(),
                "non_playoff_mean": b.mean(),
                "diff": diff,
                "ci_lo": diff - crit * se,
                "ci_hi": diff + crit * se,
                "p": t.pvalue,
                "n_playoff": int(is_po.sum()),
            }
        )
    return pd.DataFrame(rows)


def run_robustness(d: pd.DataFrame) -> pd.DataFrame:
    """Secondary specs only; the exposure coefficient is reported for each."""
    specs = {
        "H1 primary": (d, H1, "fb_pts"),
        "H1 exclude CHC": (d[d.team != "CHC"], H1, "fb_pts"),
        "H1 mean LA": (d, "runs_cv ~ mean_la + park_factor + runs_per_game", "mean_la"),
        "H1 barrel %": (d, "runs_cv ~ barrel_pts + park_factor + runs_per_game", "barrel_pts"),
        "H1 pull-air %": (
            d,
            "runs_cv ~ pull_air_pts + park_factor + runs_per_game",
            "pull_air_pts",
        ),
        "H1 sweet-spot %": (d, "runs_cv ~ sweet_pts + park_factor + runs_per_game", "sweet_pts"),
        "H1 dispersion index": (
            d,
            "dispersion_index ~ fb_pts + park_factor + runs_per_game",
            "fb_pts",
        ),
        "H1 NB2 alpha": (
            d,
            "nb_alpha ~ fb_pts + park_factor + runs_per_game",
            "nb_alpha_placeholder",
        ),
    }
    specs["H1 NB2 alpha"] = (d, specs["H1 NB2 alpha"][1], "fb_pts")
    rows = []
    for name, (data, formula, term) in specs.items():
        res = fit_ols(data, formula)
        ci = res.conf_int().loc[term]
        rows.append(
            {
                "spec": name,
                "term": term,
                "coef": res.params[term],
                "ci_lo": ci[0],
                "ci_hi": ci[1],
                "p": res.pvalues[term],
                "n": int(res.nobs),
            }
        )
    # Leave-one-team-out range for the primary FB% coefficient
    loo = [fit_ols(d[d.team != t], H1).params["fb_pts"] for t in d["team"]]
    rows.append(
        {
            "spec": "H1 leave-one-out (min / max coef)",
            "term": "fb_pts",
            "coef": float(np.median(loo)),
            "ci_lo": float(np.min(loo)),
            "ci_hi": float(np.max(loo)),
            "p": np.nan,
            "n": len(d) - 1,
        }
    )
    return pd.DataFrame(rows)
