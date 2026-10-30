# Project TODO

Step-by-step plan. Check items off as you go and keep the README "Project Status" in sync.

## Phase 0 — Setup
- [x] Scaffold repo structure, README, CLAUDE.md, requirements, .gitignore
- [x] Finish `pip install -r requirements.txt`; verify imports (`pybaseball`, `pandas`, `statsmodels`)
- [x] Register venv as Jupyter kernel (`python -m ipykernel install --user --name launch-angle-variance`)
- [x] First git commit
- [x] Create GitHub repo and push
- [x] Add `tests/` directory and a `pyproject.toml` (black / ruff / pytest config)
- [ ] Decide license (README says TBD)
- [ ] Confirm data access: check 2026 data availability in `pybaseball`, plus Baseball Reference / FanGraphs terms of use and rate limits

## Phase 1 — League-wide analysis (30 teams, 2026)

### 1a. Definitions (write before coding)
- [ ] `docs/metrics.md`: define fly-ball %, launch-angle bands (e.g., GB <10°, LD 10–25°, FB 25–50°, PU >50°), barrel %, pull-air %, sweet-spot %
- [ ] Define variance metrics: SD / variance of runs scored per game, coefficient of variation, shutout rate, 8+ run rate
- [ ] Define win-expectancy baseline: Pythagorean (and/or Pythagenpat) and the residual to test
- [ ] Pre-register hypotheses H1–H3 and the primary regression spec (avoids tuning to the hypothesis)

### 1b. Ingestion (`src/ingestion/`)
- [ ] Statcast pull for 2026 in date chunks, cached to `data/raw/` (idempotent)
- [ ] Team game logs (runs scored/allowed, W/L, park, date) for all 30 teams
- [ ] Park factors from FanGraphs into `data/external/`
- [ ] FanGraphs team batted-ball splits (cross-check against Statcast-derived values)
- [ ] Log provenance in `docs/data_sources.md`
- [ ] Tests for caching and idempotency

### 1c. Cleaning and features (`src/analysis/`)
- [ ] Clean Statcast: batted balls only, handle missing launch angle, map batter team correctly (home/away by inning half)
- [ ] Build PA-weighted team lineup profiles (mean LA, FB%, barrel%, GB/FB, pull-air%)
- [ ] Build team-game table: runs, opponent, park, home/away
- [ ] Compute per-team mean and variance of runs per game
- [ ] Write cleaned tables to `data/processed/` as parquet
- [ ] Data validation tests (30 teams, game counts, no duplicate games)

### 1d. Analysis
- [ ] EDA notebook: distributions, correlations, sanity checks
- [ ] Verify the mechanism: runs-to-win-probability concavity (empirical win% by runs scored)
- [ ] H1: regress run variance on fly-ball profile, controlling for mean runs, park factor, league environment
- [ ] H2: test whether variance explains win% minus Pythagorean residual
- [ ] H3: net effect for the most launch-angle-heavy lineups
- [ ] Robustness: negative binomial / overdispersion models, drop outlier teams, alternative LA thresholds
- [ ] Optional: add 2023–2025 seasons to increase n beyond 30
- [ ] Report effect sizes with confidence intervals; note n=30 power limits
- [ ] Figures in `src/viz/` and `output/figures/`

## Phase 2 — Cubs deep dive
- [ ] Cubs lineup profile vs. league percentile (LA, FB%, barrel%)
- [ ] Player-level contributions to lineup launch-angle profile and to game-level variance
- [ ] Game-level splits: home/away, Wrigley wind/weather, opponent quality, starter handedness
- [ ] Identify peer teams (similar mean offense, different profile) and compare
- [ ] Rolling-window variance and win% over the season
- [ ] Cubs notebook with narrative and figures

## Phase 3 — Monte Carlo counterfactual (`src/modeling/`)
- [ ] Choose PA outcome model (multinomial outcome probabilities per hitter, shrunk toward priors)
- [ ] Fit and validate against actual 2026 team run distributions (calibration check)
- [ ] Build game simulator (base/out states, baserunning assumptions documented)
- [ ] Set and record random seeds; make runs reproducible
- [ ] Validate: simulated Cubs mean and variance of runs vs. actual
- [ ] Define alternative lineups (more contact/GB-oriented vs. current; platoon changes)
- [ ] Simulate seasons; report expected wins with simulation intervals
- [ ] Sensitivity analysis on key assumptions (lineup order, park, opposing pitching)

## Phase 4 — Write-up and polish
- [ ] Final write-up in `docs/` (methodology, results, limitations)
- [ ] Clean notebooks: logic in `src/`, narrative in notebooks, run top to bottom
- [ ] README: add headline findings, key figures, reproduction steps
- [ ] Run `black`, `ruff`, `pytest`; make sure CI (optional GitHub Actions) is green
- [ ] Publish and share (LinkedIn / blog post / portfolio site)
