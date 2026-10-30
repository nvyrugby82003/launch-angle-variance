# Data Sources

Track provenance here as data is pulled (source, date pulled, query/parameters, version of `pybaseball`).

Access check run 2026-10-29 with `pybaseball` 2.2.7 and pandas 2.3.3.

| Dataset | Source | Access status | Notes |
|---------|--------|---------------|-------|
| Statcast batted balls (2026) | Baseball Savant via `pybaseball.statcast` | Works | One-day pull (2026-06-02) returned 4,505 rows with launch angle and exit velocity. |
| Team game logs (2026) | Baseball Reference via `pybaseball.schedule_and_record` | Works | Cubs 2026 schedule returned with runs scored (`R`) and allowed (`RA`). Rate limit is about 20 requests/min; cache everything. |
| Park factors | FanGraphs | Blocked via `pybaseball` (HTTP 403) | Export manually from FanGraphs (Guts! > Park Factors) into `data/external/`. |
| Batted-ball splits | FanGraphs via `pybaseball.team_batting` | Blocked (HTTP 403) | Derive from Statcast instead, or export CSV manually. |

Notes:
- `pybaseball` 2.2.7 is incompatible with pandas 3.x (`schedule_and_record` fails on the "Unknown" attendance value), so `requirements.txt` pins `pandas<3`.
- Check each site's terms of use and rate limits before bulk pulls.
- Do not commit raw data; document how to reproduce it instead.
