# Launch Angle, Scoring Variance, and Win Expectancy

> Do MLB lineups over-indexed on launch-angle / fly-ball hitters produce higher run-scoring variance, and does that variance hurt win expectancy more than the extra power helps?

**Status:** 🚧 Scaffolding complete — no analysis code written yet. See [Project Status](#project-status).

## Overview

Modern hitting philosophy prizes elevating the baseball: more fly balls, more barrels, more home runs. But fly-ball-heavy offenses may be "boom-or-bust" — more extreme single-game outcomes (high variance) — and in baseball the relationship between runs scored and wins is concave over the relevant range (Pythagorean expectation). Extra variance in runs scored for a given mean can therefore cost wins. This project tests whether that tradeoff is real, how large it is, and whether it shows up for the 2026 Chicago Cubs.

## Research Question

**Primary:** Do lineups with higher team-level launch-angle / fly-ball tendencies show higher game-to-game run-scoring variance, and does that variance reduce win expectancy relative to what their mean run production would predict?

**Sub-questions**
1. League-wide (30 teams, 2026): Is fly-ball rate / mean launch angle associated with run-scoring variance after controlling for mean runs per game?
2. Does residual win-% (actual vs. Pythagorean, or vs. a variance-adjusted expectation) correlate with run-scoring variance?
3. Cubs: Where does the 2026 Cubs lineup sit on the launch-angle/variance spectrum, and which hitters drive it?
4. Counterfactual: How would the Cubs' expected wins change under alternative lineup constructions (e.g., more contact/ground-ball-oriented bats in place of high-launch bats)?

## Hypotheses

- **H1:** Team fly-ball rate / mean launch angle is positively associated with per-game run-scoring variance (holding mean runs constant).
- **H2:** Higher run-scoring variance at a fixed mean is associated with lower win % than Pythagorean expectation predicts.
- **H3:** The net effect (power gain minus variance penalty) is small or negative for the most launch-angle-heavy lineups.

These are hypotheses, not conclusions; a null or opposite result is a valid outcome.

## Methodology

### Phase 1 — League-wide analysis (30 teams, 2026)
- Build team-level lineup profiles: mean launch angle, fly-ball %, pull-air %, barrel %, GB/FB ratio, weighted by plate appearances.
- Build per-team game logs: runs scored/allowed per game, mean and variance, distribution shape (e.g., share of shutouts / 8+ run games).
- Regress run-scoring variance on lineup profile controlling for mean runs, park factors, and league run environment.
- Compare actual win % to Pythagorean win % and test whether variance explains the residual.

### Phase 2 — Cubs deep dive
- Player-level contribution to lineup launch-angle profile and to team variance.
- Game-level splits (home/away, Wrigley wind and weather conditions, opponent quality).
- Compare Cubs to league peers with similar mean offense but different profiles.

### Phase 3 — Monte Carlo counterfactual simulation
- Model per-plate-appearance outcome distributions for individual hitters (Statcast-based, with shrinkage toward league/batted-ball-type priors).
- Simulate games and seasons under the actual lineup and alternative lineups; estimate the distribution of runs per game and expected wins.
- Quantify uncertainty with simulation intervals; run sensitivity analyses on key assumptions.

## Data Sources

| Source | Use | Access |
|--------|-----|--------|
| Baseball Savant / Statcast | Pitch- and batted-ball-level data (launch angle, exit velocity, barrels) | `pybaseball` |
| Baseball Reference | Team game logs, standings, run totals | `pybaseball` / scraping within ToS |
| FanGraphs | Park factors, batted-ball splits, wRC+, team stats | `pybaseball` / CSV exports |

Raw data is **not** committed to the repository. See [docs/data_sources.md](docs/data_sources.md) for provenance notes and reproduction steps.

## Repository Structure

```
.
├── data/
│   ├── raw/          # Untouched downloads (gitignored)
│   ├── processed/    # Cleaned / feature-engineered data (gitignored)
│   └── external/     # Park factors, lookup tables, third-party reference data
├── notebooks/        # Exploratory and narrative notebooks
├── src/
│   ├── ingestion/    # Data pulls and caching
│   ├── analysis/     # Feature engineering, statistics, regressions
│   ├── modeling/     # PA outcome models, Monte Carlo simulation
│   └── viz/          # Reusable plotting code
├── output/           # Figures, tables, final artifacts
├── docs/             # Methodology notes, data dictionary, write-ups
├── CLAUDE.md         # Context for AI coding assistants
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11+ (3.12 recommended)
- Git

### Environment setup

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name launch-angle-variance
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name launch-angle-variance
```

Verify:
```bash
python -c "import pybaseball, pandas, statsmodels; print('ok')"
```

## Project Status

- [x] Project scaffolding and documentation
- [ ] Phase 1: League-wide analysis
  - [ ] Data ingestion (Statcast, game logs, park factors)
  - [ ] Lineup profile features
  - [ ] Variance / win-expectancy modeling
- [ ] Phase 2: Cubs deep dive
- [ ] Phase 3: Monte Carlo counterfactual simulation
- [ ] Final write-up and visuals

## Limitations (anticipated)

- Single-season sample (30 teams) limits statistical power; consider adding prior seasons as a robustness check.
- Run-scoring variance is confounded by park, weather, opposing pitching, and bullpen usage.
- Team-level launch-angle tendencies are correlated with overall offensive quality and roster construction.
- Simulation results depend on modeling assumptions (independence of PAs, lineup-order effects, baserunning).

## License

TBD.

## Acknowledgments

Data courtesy of Baseball Savant / MLB, Baseball-Reference, and FanGraphs. Not affiliated with MLB or any team.
