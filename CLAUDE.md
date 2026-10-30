# CLAUDE.md

Context for AI coding assistants working in this repository.

## Project

Baseball analytics portfolio project (GitHub, aimed at sports analytics roles).

**Research question:** Do MLB lineups over-indexed on launch-angle / fly-ball hitters produce higher run-scoring variance that hurts win expectancy more than it helps? Primary case study: the 2026 Chicago Cubs.

**Core idea:** Win probability is a concave function of runs scored, so at a fixed mean, higher run-scoring variance should lower win %. Test whether fly-ball-heavy lineups are higher variance and whether that costs wins beyond what mean run production predicts.

## Phases

1. **League-wide analysis** — all 30 teams, 2026 season.
2. **Cubs deep dive** — player contributions, game-level splits, peer comparison.
3. **Monte Carlo counterfactual** — simulate alternative Cubs lineups.

## Current status

Scaffolding only. **No analysis code exists yet.** Do not write analysis code unless asked; check README "Project Status" for the current phase.

## Data sources

- Baseball Savant / Statcast (batted-ball data) via `pybaseball`
- Baseball Reference (game logs, standings)
- FanGraphs (park factors, batted-ball splits)

Conventions:
- `data/raw/` is immutable — never edit raw files; write cleaned output to `data/processed/`.
- `data/raw/` and `data/processed/` are gitignored. Never commit large data files.
- `data/external/` holds small reference tables (e.g., park factors) that may be committed.
- Ingestion code should cache downloads and be idempotent (re-running must not re-hit sources unnecessarily). Respect site rate limits and terms of use.

## Layout

- `src/ingestion/` — pulls and caching
- `src/analysis/` — features, statistics, regressions
- `src/modeling/` — PA outcome models, Monte Carlo simulation
- `src/viz/` — reusable plotting functions
- `notebooks/` — exploration and narrative; keep logic in `src/` and import it
- `output/` — figures and tables; `docs/` — methodology and data notes

## Coding conventions

- Python 3.11+, type hints on public functions, docstrings for non-trivial logic.
- Format with `black`, lint with `ruff`, test with `pytest` (tests go in `tests/`).
- Use `pandas` + `pyarrow`/parquet for processed data.
- Set random seeds explicitly and record them; simulations must be reproducible.
- Prefer functions that take and return DataFrames over notebook-only code.

## Analytical guidance

- Control for mean runs per game, park factors, and league run environment when examining variance.
- Be explicit about limitations: single season, n=30 teams, confounding (park, weather, opposing pitching).
- Report uncertainty (confidence/credible/simulation intervals); don't overstate causal claims.
- Null results are acceptable; don't tune analyses to reach the hypothesis.
- Define metrics clearly (e.g., fly-ball %, barrel %, launch-angle thresholds) in `docs/` and use them consistently.

## Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
