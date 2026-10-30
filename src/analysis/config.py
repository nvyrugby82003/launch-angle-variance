"""Single source of truth for metric thresholds (see docs/metrics.md, frozen)."""

SEASON = 2026

# Launch-angle bands (degrees): GB < 10, LD [10, 25), FB [25, 50), PU >= 50
GB_MAX = 10.0
LD_MAX = 25.0
FB_MAX = 50.0

SWEET_SPOT_MIN = 8.0
SWEET_SPOT_MAX = 32.0
HARD_HIT_MPH = 95.0
BARREL_CODE = 6  # Statcast launch_speed_angle == 6

# Spray-angle conversion (standard Statcast home-plate coordinates in hc_x / hc_y)
HC_X_HOME = 125.42
HC_Y_HOME = 198.27

BIG_GAME_RUNS = 8

# Statcast team codes that differ from Baseball Reference codes
STATCAST_TO_BR = {
    "AZ": "ARI",
    "CWS": "CHW",
    "KC": "KCR",
    "SD": "SDP",
    "SF": "SFG",
    "TB": "TBR",
    "WSH": "WSN",
}

# One code per franchise across seasons (the Athletics were OAK through 2024).
FRANCHISE_ALIASES = {"OAK": "ATH"}

SEASONS = (2023, 2024, 2025, 2026)

# FanGraphs park-factor file uses full team names; map to Baseball Reference codes.
FANGRAPHS_NAME_TO_CODE = {
    "Angels": "LAA",
    "Orioles": "BAL",
    "Red Sox": "BOS",
    "White Sox": "CHW",
    "Guardians": "CLE",
    "Tigers": "DET",
    "Royals": "KCR",
    "Twins": "MIN",
    "Yankees": "NYY",
    "Athletics": "ATH",
    "Mariners": "SEA",
    "Rays": "TBR",
    "Rangers": "TEX",
    "Blue Jays": "TOR",
    "Diamondbacks": "ARI",
    "Braves": "ATL",
    "Cubs": "CHC",
    "Reds": "CIN",
    "Rockies": "COL",
    "Dodgers": "LAD",
    "Marlins": "MIA",
    "Brewers": "MIL",
    "Mets": "NYM",
    "Phillies": "PHI",
    "Pirates": "PIT",
    "Padres": "SDP",
    "Giants": "SFG",
    "Cardinals": "STL",
    "Nationals": "WSN",
    "Astros": "HOU",
}
