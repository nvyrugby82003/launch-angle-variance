from pathlib import Path

import pandas as pd
import pytest
from src.ingestion import gamelogs


def _make_fetch(calls: list[str]):
    def fetch(season: int, team: str) -> pd.DataFrame:
        calls.append(team)
        return pd.DataFrame({"Date": ["Thursday, Mar 26"], "R": [3.0], "RA": [1.0]})

    return fetch


def test_download_all_is_idempotent(tmp_path: Path) -> None:
    calls: list[str] = []
    teams = ("CHC", "MIL")
    first = gamelogs.download_all(2026, teams, tmp_path, _make_fetch(calls), delay_s=0)
    assert first == {"cached": 0, "downloaded": 2}
    second = gamelogs.download_all(2026, teams, tmp_path, _make_fetch(calls), delay_s=0)
    assert second == {"cached": 2, "downloaded": 0}
    assert calls == ["CHC", "MIL"]


def test_load_gamelogs_adds_team_column(tmp_path: Path) -> None:
    gamelogs.download_all(2026, ("CHC", "MIL"), tmp_path, _make_fetch([]), delay_s=0)
    df = gamelogs.load_gamelogs(2026, tmp_path)
    assert sorted(df["team"].unique()) == ["CHC", "MIL"]


def test_empty_result_raises(tmp_path: Path) -> None:
    def fetch(season: int, team: str) -> pd.DataFrame:
        return pd.DataFrame()

    with pytest.raises(ValueError):
        gamelogs.download_team(2026, "CHC", tmp_path, fetch)


def test_all_30_teams_listed() -> None:
    assert len(set(gamelogs.TEAMS)) == 30


SAMPLE_HTML = """
<table id="team_schedule"><tbody>
<tr><th data-stat="team_game">1</th><td data-stat="date_game">Thursday, Mar 26</td>
<td data-stat="boxscore"><a href="/boxes/CHC/CHC202603260.shtml">boxscore</a></td>
<td data-stat="R">3</td><td data-stat="RA">1</td><td data-stat="extra_innings"></td></tr>
<tr class="thead"><th data-stat="team_game">Gm#</th><td data-stat="date_game">Date</td></tr>
<tr><th data-stat="team_game">2</th><td data-stat="date_game">Friday, Mar 27</td>
<td data-stat="boxscore"><a href="/boxes/CHC/CHC202603270.shtml">boxscore</a></td>
<td data-stat="R">0</td><td data-stat="RA">2</td><td data-stat="extra_innings"></td></tr>
<tr><th data-stat="team_game">3</th><td data-stat="date_game">Sunday, Sep 27</td>
<td data-stat="boxscore"><a href="/boxes/CHC/CHC202609270.shtml">boxscore</a></td>
<td data-stat="R">6</td><td data-stat="RA">2</td><td data-stat="extra_innings"></td></tr>
</tbody></table>
"""


def test_parse_keeps_every_game_row_including_last() -> None:
    df = gamelogs.parse_schedule_html(SAMPLE_HTML)
    assert len(df) == 3  # header row skipped, final row kept
    assert df["R"].tolist() == ["3", "0", "6"]
    assert df["boxscore_url"].iloc[-1].endswith("CHC202609270.shtml")
    assert df["extra_innings"].tolist() == ["", "", ""]  # blank cells do not shift columns


def test_parse_requires_schedule_table() -> None:
    with pytest.raises(ValueError):
        gamelogs.parse_schedule_html("<html></html>")
