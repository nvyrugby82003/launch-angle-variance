"""Cached, idempotent Statcast downloader.

Each game day is stored as its own parquet file under ``data/raw/statcast/<season>/``.
Re-running skips days that are already cached, so interrupted pulls resume where they
stopped. Days with no games get an ``.empty`` marker so they are not re-requested.
Raw files are never modified once written.
"""

from __future__ import annotations

import argparse
import logging
import time
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/statcast")
# Wide window around the 2026 regular season; spring training and postseason rows
# are filtered later using the `game_type` column (R = regular season).
DEFAULT_START = date(2026, 3, 15)
DEFAULT_END = date(2026, 10, 5)
REQUEST_DELAY_S = 1.0
MAX_RETRIES = 4
# Pull windows (start of the earliest regular-season game to the last regular-season day).
SEASON_WINDOWS: dict[int, tuple[date, date]] = {
    2023: (date(2023, 3, 30), date(2023, 10, 1)),
    2024: (date(2024, 3, 20), date(2024, 9, 30)),
    2025: (date(2025, 3, 18), date(2025, 9, 28)),
}


def _fetch_day(day: date) -> pd.DataFrame:
    """Download one day of Statcast pitch-level data via pybaseball."""
    from pybaseball import statcast

    iso = day.isoformat()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return statcast(start_dt=iso, end_dt=iso, verbose=False)
        except Exception as exc:  # dropped connections surface as several exception types
            if attempt == MAX_RETRIES:
                raise
            logger.warning("%s: attempt %d failed (%s); retrying", day, attempt, type(exc).__name__)
            time.sleep(10 * attempt)
    raise AssertionError("unreachable")


def _day_path(day: date, raw_dir: Path) -> Path:
    return raw_dir / str(day.year) / f"{day.isoformat()}.parquet"


def _marker_path(day: date, raw_dir: Path) -> Path:
    return _day_path(day, raw_dir).with_suffix(".empty")


def is_cached(day: date, raw_dir: Path = RAW_DIR) -> bool:
    """Return True if the day has already been downloaded (data or empty marker)."""
    return _day_path(day, raw_dir).exists() or _marker_path(day, raw_dir).exists()


def download_day(
    day: date,
    raw_dir: Path = RAW_DIR,
    fetch: Callable[[date], pd.DataFrame] = _fetch_day,
) -> str:
    """Download and cache a single day. Returns 'cached', 'empty', or 'downloaded'.

    Days on or after today are never cached because their data may be incomplete.
    """
    if is_cached(day, raw_dir):
        return "cached"

    df = fetch(day)
    path = _day_path(day, raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    if df is None or df.empty:
        if day < date.today():
            _marker_path(day, raw_dir).touch()
        return "empty"

    if day >= date.today():
        logger.warning("%s is not a completed day; skipping cache write", day)
        return "downloaded"

    # Write to a temp file then rename so an interrupted run never leaves a partial file.
    tmp = path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)
    return "downloaded"


def download_range(
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    raw_dir: Path = RAW_DIR,
    fetch: Callable[[date], pd.DataFrame] = _fetch_day,
    delay_s: float = REQUEST_DELAY_S,
) -> dict[str, int]:
    """Download every day in [start, end], skipping cached days. Returns status counts."""
    counts = {"cached": 0, "empty": 0, "downloaded": 0}
    day = start
    while day <= end:
        status = download_day(day, raw_dir, fetch)
        counts[status] += 1
        if status != "cached":
            logger.info("%s: %s", day, status)
            time.sleep(delay_s)
        day += timedelta(days=1)
    return counts


def load_season(season: int, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load all cached days for a season into one DataFrame (raw, unfiltered)."""
    files = sorted((raw_dir / str(season)).glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No cached Statcast files for {season} in {raw_dir}")
    return pd.concat((pd.read_parquet(f) for f in files), ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and cache Statcast data by day.")
    parser.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START)
    parser.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END)
    parser.add_argument(
        "--season",
        type=int,
        nargs="+",
        help="Pull full regular-season windows for these seasons (overrides --start/--end).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.season:
        for season in args.season:
            start, end = SEASON_WINDOWS[season]
            print(season, download_range(start, end))
    else:
        print(download_range(args.start, args.end))


if __name__ == "__main__":
    main()
