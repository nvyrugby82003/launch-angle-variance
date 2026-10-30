# Project TODO

Step-by-step plan. Check items off as you go and keep the README "Project Status" in sync.

## Phase 0 — Setup
- [x] Scaffold repo structure, README, CLAUDE.md, requirements, .gitignore
- [x] Finish `pip install -r requirements.txt`; verify imports (`pybaseball`, `pandas`, `statsmodels`)
- [x] Register venv as Jupyter kernel (`python -m ipykernel install --user --name launch-angle-variance`)
- [x] First git commit
- [x] Create GitHub repo and push
- [x] Add `tests/` directory and a `pyproject.toml` (black / ruff / pytest config)
- [x] Decide license (MIT)
- [x] Confirm 2026 data access in `pybaseball`: Statcast and Baseball Reference work; FanGraphs is blocked (403), so use manual CSV exports (see `docs/data_sources.md`)
- [x] Read terms of use / robots.txt for Baseball Reference, FanGraphs, Baseball Savant (summarized in `docs/data_sources.md`)

## Phase 1 — League-wide analysis (30 teams, 2026)

### 1a. Definitions (write before coding)
- [x] `docs/metrics.md` drafted: batted-ball metrics (needs your review before they're final)
- [x] Variance metrics drafted (CV is the primary outcome)
- [x] Win-expectancy baseline drafted (Pythagenpat residual)
- [x] Hypotheses H1–H3 and primary regression spec drafted
- [x] Review and approve `docs/metrics.md`, then freeze it (commit with message "Freeze metric definitions")

### 1b. Ingestion (`src/ingestion/`)
- [x] Statcast pull for 2026 in date chunks, cached to `data/raw/` (idempotent): 759,679 pitches, 2,429 regular-season games (one short of 2,430; confirmed by game logs), 0 duplicates
- [x] Team game logs (runs scored/allowed, W/L, park, date) for all 30 teams: 4,858 team-games = 2,429 games (matches Statcast; two teams have 161, so one scheduled game was likely never played); league RS = RA = 21,769
- [x] Park factors from FanGraphs into `data/external/` (2025 only; 2026 not yet published)
- [x] FanGraphs team batted-ball splits (cross-check against Statcast-derived values)
- [ ] Log provenance in `docs/data_sources.md`
- [x] Tests for caching and idempotency (Statcast; game logs parser tests included)

### 1c. Cleaning and features (`src/analysis/`)
- [x] Clean Statcast: batted balls only, handle missing launch angle, map batter team correctly (home/away by inning half)
- [x] Build team lineup profiles (mean LA, FB%, barrel%, GB/FB, pull-air%); pooled over batted balls (BBE-weighted), not PA-weighted by hitter
- [x] Build team-game table: runs, opponent, park, home/away
- [x] Compute per-team mean and variance of runs per game
- [x] Write cleaned tables to `data/processed/` as parquet
- [x] Data validation tests (30 teams, game counts, no duplicate games)

### 1d. Analysis
- [x] EDA notebook (`notebooks/01_eda.ipynb`): distributions, correlations, sanity checks
- [x] Verify the mechanism: runs-to-win-probability concavity (empirical win% by runs scored)
- [x] H1: regress run variance on fly-ball profile, controlling for mean runs, park factor, league environment
- [x] H2: test whether variance explains win% minus Pythagorean residual
- [x] H3: net effect for the most launch-angle-heavy lineups
- [x] Robustness: NB2 moment dispersion, dispersion index, exclude CHC, leave-one-out, alt exposures (mean LA, barrel, pull-air, sweet-spot); alternative LA band cutoffs still to do
- [x] Optional: ingest 2023–2025 (Statcast + game logs, cached in `data/raw/`; 2,430 / 2,429 / 2,430 games, matching game logs). Still to do: extend `src/analysis` to build a multi-season team-season panel (n=120) with park factors per season
- [x] Report effect sizes with confidence intervals; note n=30 power limits
- [x] Figures in `src/viz/` and `output/figures/`

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
