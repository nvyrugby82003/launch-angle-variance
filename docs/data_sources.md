# Data Sources

Track provenance here as data is pulled (source, date pulled, query/parameters, version of `pybaseball`).

| Dataset | Source | Date pulled | Notes |
|---------|--------|-------------|-------|
| Statcast batted balls (2026) | Baseball Savant via `pybaseball.statcast` | TBD | |
| Team game logs (2026) | Baseball Reference | TBD | |
| Park factors | FanGraphs | TBD | Store in `data/external/` |
| Batted-ball splits | FanGraphs | TBD | |

Notes:
- Check each site's terms of use and rate limits before bulk pulls.
- Do not commit raw data; document how to reproduce it instead.
