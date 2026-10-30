# Data Sources

Track provenance here as data is pulled (source, date pulled, query/parameters, version of `pybaseball`).

Access check run 2026-10-29 with `pybaseball` 2.2.7 and pandas 2.3.3.

| Dataset | Source | Access status | Notes |
|---------|--------|---------------|-------|
| Statcast batted balls (2026) | Baseball Savant via `pybaseball.statcast` | Works | Cached by day in `data/raw/statcast/2026/` (gitignored) via `python -m src.ingestion.statcast`, which resumes safely. Window 2026-03-15 to 2026-10-05; filter to `game_type == 'R'` later. |
| Team game logs (2026) | Baseball Reference, parsed directly (`requests` + BeautifulSoup) | Works | `pybaseball.schedule_and_record` was dropped: it discards the final row and can shift columns on blank cells. Runs scored (`R`) and allowed (`RA`) for all 30 teams. Rate limit is about 20 requests/min; cache everything. |
| Park factors | FanGraphs Guts! (manual CSV export, 2026-10-29) | Done, **2025 only** | [data/external/fangraphs-guts-data.csv](../data/external/fangraphs-guts-data.csv): 30 teams, columns Basic (5yr), 3yr, 1yr, plus 1B/2B/3B/HR/SO/BB/GB/FB/LD/IFFB/FIP factors. 2026 was not available, so 2025 factors are used as a proxy; note this as a limitation. |
| Playoff teams (2026) | Wikipedia, 2026 MLB postseason page (manual, 2026-10-29) | Done | [data/external/playoff-teams-2026.csv](../data/external/playoff-teams-2026.csv): the 12 qualifiers. Used only for descriptive comparisons. |
| Batted-ball splits | FanGraphs (manual CSV export, 2026-10-29) | Done | [data/external/fangraphs-team-batted-ball-2026.csv](../data/external/fangraphs-team-batted-ball-2026.csv): 30 teams, GB/FB, LD%, GB%, FB%, IFFB%, HR/FB, Pull/Cent/Oppo%, Soft/Med/Hard%. Cross-check only; the primary fly-ball rate is derived from Statcast launch angle (see `docs/metrics.md`). `pybaseball.team_batting` is blocked (HTTP 403). |

## Site rules to follow

- **Baseball Reference:** `robots.txt` crawl-delay is 3 seconds and the bot policy caps requests at about 20/min. Sleep at least 3 seconds between requests and cache every response. Terms: https://www.sports-reference.com/termsofuse.html
- **FanGraphs:** no `robots.txt` restriction on the leaderboard and Guts! pages, but automated requests get a 403. Use manual exports only. Do not redistribute large exports.
- **Baseball Savant:** `robots.txt` is fully open. Keep pulls to day-sized chunks and cache them.
- Raw data stays out of git. Small reference tables in `data/external/` may be committed.
- robots.txt and terms reviewed 2026-10-29.

Notes:
- `pybaseball` 2.2.7 is incompatible with pandas 3.x (`schedule_and_record` fails on the "Unknown" attendance value), so `requirements.txt` pins `pandas<3`.
- Check each site's terms of use and rate limits before bulk pulls.
- Do not commit raw data; document how to reproduce it instead.
