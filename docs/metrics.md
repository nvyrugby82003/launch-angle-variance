# Metric Definitions

**Status: FROZEN (approved 2026-10-29).** These definitions are fixed before analysis begins; changing them after seeing results is not allowed without documenting the change here with a dated note. All code should import thresholds from a single config module (to be created in `src/analysis/`).

## 1. Batted-ball metrics (Statcast)

Computed from Statcast rows where `type == 'X'` (ball in play) and `launch_angle` is not null, using the **batting team's** hitters. Batting team = `away_team` when `inning_topbot == 'Top'`, else `home_team`.

| Metric | Definition |
|--------|------------|
| Mean launch angle (LA) | Mean `launch_angle` over batted balls, PA-weighted by hitter when aggregating to a lineup |
| Ground ball (GB) | LA < 10° |
| Line drive (LD) | 10° ≤ LA < 25° |
| Fly ball (FB) | 25° ≤ LA < 50° |
| Pop-up (PU) | LA ≥ 50° |
| GB % / FB % / LD % / PU % | Share of batted balls in each band |
| GB/FB ratio | GB count / FB count |
| **Fly-ball rate (primary exposure)** | FB / all batted balls, with FB = 25° ≤ LA < 50° |
| Pull-air % | Share of batted balls with LA ≥ 10° hit to the pull side (use `hc_x` and batter handedness; requires a documented spray-angle conversion) |
| Barrel % | Statcast `launch_speed_angle == 6` / batted balls (use MLB's official classification) |
| Sweet-spot % | 8° ≤ LA ≤ 32° / batted balls |
| Hard-hit % | `launch_speed` ≥ 95 mph / batted balls (secondary control) |

Notes:
- Bands follow common conventions and are not identical to FanGraphs' (which uses batted-ball type from stringer/video). Cross-checking to FanGraphs FB% is a sanity check, not an expectation of equality.
- Primary exposure variable: **team fly-ball rate**. Mean LA and pull-air % are secondary and used for robustness checks. Do not pick whichever fits best after the fact.

## 2. Run-scoring variance metrics (team-game level)

Unit of observation: one team-game (regular season only, 2026). Extra-inning runs are included as scored. Suspended or tied/shortened games are handled per the rule in the data-cleaning step and documented there.

| Metric | Definition |
|--------|------------|
| Mean runs per game (μ) | Mean of runs scored |
| Variance (σ²) / SD (σ) | Sample variance (ddof=1) / SD of runs scored per game |
| **Coefficient of variation (primary outcome)** | σ / μ. Needed because variance mechanically rises with the mean in count data |
| Dispersion index | σ² / μ (equals 1 for a Poisson process) |
| Shutout rate | Share of games with 0 runs scored |
| Big-inning-game rate | Share of games with ≥ 8 runs scored |
| Uncertainty | Bootstrap (resample games) 95% CIs for σ and CV per team |

Notes:
- Variance must always be analyzed **conditional on mean**. Raw σ² differences between teams are mostly mean differences.
- League run environment: compare to the league mean CV and to the mean-variance relationship across all teams.

## 3. Win-expectancy baseline

| Metric | Definition |
|--------|------------|
| Pythagorean win % | RS^x / (RS^x + RA^x) with x = 1.83 |
| Pythagenpat | x = ((RS + RA) / G)^0.287 |
| **Win residual (primary)** | Actual win % − Pythagenpat win % |
| Empirical runs-to-wins curve | League-wide win % by runs scored (0, 1, 2, ... 10+), used to demonstrate concavity |

Notes:
- Pythagorean expectation already uses totals, so it does not directly encode variance. The residual tests whether the *distribution* of runs, not just its total, shifts wins.
- Run **allowed** variance is a control, since it also affects wins.

## 4. Controls

| Control | Source |
|---------|--------|
| Mean runs per game | Game logs |
| Park factor (run environment) | FanGraphs park factors in `data/external/` (2025 values used as a proxy for 2026; documented limitation) |
| League run environment | League mean runs per game, 2026 |
| Home/away mix | Share of games at home |
| Opponent pitching quality | Opponent mean runs allowed or FIP (to be decided) |

## 5. Primary analysis specification (pre-registered)

- **H1:** CV of runs scored ~ team fly-ball rate + park factor + mean runs per game (OLS, n = 30, robust SEs). Report coefficient, 95% CI and R².
- **H2:** Win residual ~ CV of runs scored + CV of runs allowed. Report coefficient and 95% CI.
- **H3:** Descriptive comparison of the top-quintile fly-ball-rate lineups versus the rest on mean runs, CV and win residual.
- Secondary / robustness only: mean LA, barrel %, pull-air %, dispersion index, negative binomial models of runs per game, dropping individual teams, excluding the Cubs.

## 6. Known limitations

- n = 30 teams in a single season gives low power; null results are acceptable and will be reported as such.
- Team batted-ball profile reflects the whole season's roster, including injuries, trades and platoons; the lineup on a given day differs.
- Park, weather, opposing pitching and bullpen usage confound run variance.
- Statcast launch-angle bands are an approximation of batted-ball type.
