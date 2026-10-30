"""Cached, idempotent Baseball Reference team game-log downloader.

One parquet file per team under ``data/raw/gamelogs/<season>/<TEAM>.parquet``. Existing
files are never re-downloaded. Baseball Reference's robots.txt asks for a 3 second crawl
delay, which is enforced between live requests.
"""

from __future__ import annotations

import argparse
import logging
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/gamelogs")
SEASON = 2026
REQUEST_DELAY_S = 3.0  # Baseball Reference robots.txt crawl-delay
USER_AGENT = "Mozilla/5.0 (compatible; launch-angle-variance research project)"

# Baseball Reference team codes (match the FanGraphs exports in data/external).
TEAMS: tuple[str, ...] = (
    "ARI", "ATH", "ATL", "BAL", "BOS", "CHC", "CHW", "CIN", "CLE", "COL",
    "DET", "HOU", "KCR", "LAA", "LAD", "MIA", "MIL", "MIN", "NYM", "NYY",
    "PHI", "PIT", "SDP", "SEA", "SFG", "STL", "TBR", "TEX", "TOR", "WSN",
)  # fmt: skip


def teams_for_season(season: int) -> tuple[str, ...]:
    """Baseball Reference team codes for a season (the Athletics were OAK before 2025)."""
    return tuple("OAK" if t == "ATH" and season < 2025 else t for t in TEAMS)


def parse_schedule_html(html: str) -> pd.DataFrame:
    """Parse a Baseball Reference team schedule page into a text DataFrame.

    Every column is kept as text, keyed by the page's ``data-stat`` names; the box-score
    link is kept in ``boxscore_url``. Unplayed games have an empty ``R``.
    """
    from bs4 import BeautifulSoup

    table = BeautifulSoup(html, "lxml").find("table", id="team_schedule")
    if table is None:
        raise ValueError("No team_schedule table found in page")

    records = []
    for tr in table.find("tbody").find_all("tr"):
        if "thead" in (tr.get("class") or []):
            continue  # repeated mid-table header rows
        record = {c["data-stat"]: c.get_text(strip=True) for c in tr.find_all(["th", "td"])}
        link = tr.find("a", href=lambda h: h and "/boxes/" in h)
        record["boxscore_url"] = link["href"] if link else ""
        records.append(record)
    return pd.DataFrame(records).astype("string")


def _fetch_team(season: int, team: str) -> pd.DataFrame:
    """Download and parse one team's season schedule/results from Baseball Reference.

    Parsed directly rather than via ``pybaseball.schedule_and_record``, which silently
    drops the final row of the table and shifts columns when a cell is blank.
    """
    import requests

    url = f"https://www.baseball-reference.com/teams/{team}/{season}-schedule-scores.shtml"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return parse_schedule_html(resp.text)


def _team_path(season: int, team: str, raw_dir: Path) -> Path:
    return raw_dir / str(season) / f"{team}.parquet"


def download_team(
    season: int,
    team: str,
    raw_dir: Path = RAW_DIR,
    fetch: Callable[[int, str], pd.DataFrame] = _fetch_team,
) -> str:
    """Download and cache one team. Returns 'cached' or 'downloaded'."""
    path = _team_path(season, team, raw_dir)
    if path.exists():
        return "cached"

    df = fetch(season, team)
    if df is None or df.empty:
        raise ValueError(f"No game log returned for {team} {season}")

    path.parent.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype("string")
    tmp = path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)
    return "downloaded"


def download_all(
    season: int = SEASON,
    teams: tuple[str, ...] | None = None,
    raw_dir: Path = RAW_DIR,
    fetch: Callable[[int, str], pd.DataFrame] = _fetch_team,
    delay_s: float = REQUEST_DELAY_S,
) -> dict[str, int]:
    """Download every team's game log, skipping cached teams. Returns status counts."""
    counts = {"cached": 0, "downloaded": 0}
    for team in teams or teams_for_season(season):
        status = download_team(season, team, raw_dir, fetch)
        counts[status] += 1
        if status == "downloaded":
            logger.info("%s: downloaded", team)
            time.sleep(delay_s)
    return counts


def load_gamelogs(season: int = SEASON, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load all cached team game logs into one DataFrame with a `team` column."""
    frames = []
    for path in sorted((raw_dir / str(season)).glob("*.parquet")):
        df = pd.read_parquet(path)
        df.insert(0, "team", path.stem)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No cached game logs for {season} in {raw_dir}")
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and cache team game logs.")
    parser.add_argument("--season", type=int, nargs="+", default=[SEASON])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    for season in args.season:
        print(season, download_all(season))


if __name__ == "__main__":
    main()
