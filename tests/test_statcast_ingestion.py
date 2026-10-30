from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from src.ingestion import statcast


def _make_fetch(calls: list[date], empty_days: set[date] | None = None):
    empty_days = empty_days or set()

    def fetch(day: date) -> pd.DataFrame:
        calls.append(day)
        if day in empty_days:
            return pd.DataFrame()
        return pd.DataFrame({"game_date": [day.isoformat()], "launch_angle": [20.0]})

    return fetch


def test_download_range_is_idempotent(tmp_path: Path) -> None:
    start = date(2026, 4, 1)
    end = date(2026, 4, 3)
    calls: list[date] = []
    fetch = _make_fetch(calls, empty_days={date(2026, 4, 2)})

    first = statcast.download_range(start, end, tmp_path, fetch, delay_s=0)
    assert first == {"cached": 0, "empty": 1, "downloaded": 2}
    assert len(calls) == 3

    second = statcast.download_range(start, end, tmp_path, fetch, delay_s=0)
    assert second == {"cached": 3, "empty": 0, "downloaded": 0}
    assert len(calls) == 3  # no new requests


def test_load_season_concatenates_cached_days(tmp_path: Path) -> None:
    calls: list[date] = []
    statcast.download_range(
        date(2026, 4, 1), date(2026, 4, 2), tmp_path, _make_fetch(calls), delay_s=0
    )
    df = statcast.load_season(2026, tmp_path)
    assert len(df) == 2


def test_today_is_not_cached(tmp_path: Path) -> None:
    calls: list[date] = []
    today = date.today()
    statcast.download_day(today, tmp_path, _make_fetch(calls))
    statcast.download_day(today, tmp_path, _make_fetch(calls))
    assert len(calls) == 2
    assert not statcast.is_cached(today, tmp_path)


def test_future_empty_day_not_marked(tmp_path: Path) -> None:
    calls: list[date] = []
    future = date.today() + timedelta(days=1)
    statcast.download_day(future, tmp_path, _make_fetch(calls, empty_days={future}))
    assert not statcast.is_cached(future, tmp_path)


def test_load_season_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        statcast.load_season(2026, tmp_path)
