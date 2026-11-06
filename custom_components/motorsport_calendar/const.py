"""Constants for Motorsport Calendar (MotoGP + F1)."""

from datetime import timedelta

DOMAIN = "motorsport_calendar"
UPDATE_INTERVAL = timedelta(hours=6)
STORAGE_KEY = f"{DOMAIN}.cache"
STORAGE_VERSION = 1

# Official MotoGP data (the feed behind motogp.com and the MotoGP app)
MOTOGP_EVENTS_URL = "https://api.motogp.pulselive.com/motogp/v1/events?seasonYear={year}"
# OpenF1 (open data from the official F1 timing feed)
F1_SESSIONS_URL = "https://api.openf1.org/v1/sessions?year={year}"
F1_MEETINGS_URL = "https://api.openf1.org/v1/meetings?year={year}"

CONF_LANGUAGE = "language"
LANGUAGES = {"en": "English", "fr": "Français"}

SERIES_MOTOGP = "motogp"
SERIES_F1 = "f1"

# MotoGP session code -> (French label, English label, type)
MOTOGP_SESSIONS = {
    "FP1": ("Essais libres 1", "Free Practice 1", "practice"),
    "FP2": ("Essais libres 2", "Free Practice 2", "practice"),
    "FP3": ("Essais libres 3", "Free Practice 3", "practice"),
    "FP4": ("Essais libres 4", "Free Practice 4", "practice"),
    "PR": ("Essais", "Practice", "practice"),
    "Q1": ("Qualif 1", "Qualifying 1", "qualifying"),
    "Q2": ("Qualif 2", "Qualifying 2", "qualifying"),
    "Q": ("Qualifications", "Qualifying", "qualifying"),
    "SPR": ("Sprint", "Sprint", "sprint"),
    "WUP": ("Warm-up", "Warm Up", "warm_up"),
    "RAC": ("Course", "Race", "race"),
    "RAC1": ("Course 1", "Race 1", "race"),
    "RAC2": ("Course 2", "Race 2", "race"),
}
# Default duration when the API gives end == start (races)
MOTOGP_DEFAULT_MINUTES = {"race": 45, "sprint": 25}

# OpenF1 session name -> (French label, English label, type)
F1_SESSIONS = {
    "Practice 1": ("Essais libres 1", "Practice 1", "practice"),
    "Practice 2": ("Essais libres 2", "Practice 2", "practice"),
    "Practice 3": ("Essais libres 3", "Practice 3", "practice"),
    "Qualifying": ("Qualifications", "Qualifying", "qualifying"),
    "Sprint Qualifying": ("Qualifs sprint", "Sprint Qualifying", "qualifying"),
    "Sprint Shootout": ("Qualifs sprint", "Sprint Shootout", "qualifying"),
    "Sprint": ("Sprint", "Sprint", "sprint"),
    "Race": ("Course", "Race", "race"),
}
