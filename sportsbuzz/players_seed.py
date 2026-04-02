"""
players_seed.py — Initial list of players and sports sources to track.

Add/remove players here. Run `python players_seed.py` to (re)seed the DB.
Aliases let the crawler catch nicknames and shortened names in articles.
"""

from database import init_db, upsert_player, upsert_source

# ── Players ────────────────────────────────────────────────────────────────────
# Format: (full_name, sport, nationality, [aliases])

PLAYERS = [
    # Cricket
    ("Virat Kohli",       "Cricket",  "India",     ["Kohli", "King Kohli", "Chiku"]),
    ("Rohit Sharma",      "Cricket",  "India",     ["Rohit", "Hitman"]),
    ("Joe Root",          "Cricket",  "England",   ["Root", "The Don"]),
    ("Steve Smith",       "Cricket",  "Australia", ["Smith", "Smudge"]),
    ("Babar Azam",        "Cricket",  "Pakistan",  ["Babar"]),
    ("Ben Stokes",        "Cricket",  "England",   ["Stokes"]),
    ("Pat Cummins",       "Cricket",  "Australia", ["Cummins"]),
    ("Shubman Gill",      "Cricket",  "India",     ["Gill"]),
    ("Travis Head",       "Cricket",  "Australia", ["Head"]),
    ("Jasprit Bumrah",    "Cricket",  "India",     ["Bumrah"]),

    # Football / Soccer
    ("Lionel Messi",      "Football", "Argentina", ["Messi", "Leo Messi", "La Pulga", "GOAT"]),
    ("Cristiano Ronaldo", "Football", "Portugal",  ["Ronaldo", "CR7", "Siuuu"]),
    ("Erling Haaland",    "Football", "Norway",    ["Haaland", "The Terminator"]),
    ("Kylian Mbappé",     "Football", "France",    ["Mbappe", "Mbappé", "Donatello"]),
    ("Vinicius Junior",   "Football", "Brazil",    ["Vinicius", "Vini Jr", "Vini Junior"]),
    ("Jude Bellingham",   "Football", "England",   ["Bellingham"]),
    ("Rodri",             "Football", "Spain",     ["Rodrigo Hernandez"]),
    ("Mohamed Salah",     "Football", "Egypt",     ["Salah", "Mo Salah", "Egyptian King"]),
    ("Harry Kane",        "Football", "England",   ["Kane"]),
    ("Phil Foden",        "Football", "England",   ["Foden", "Boy from Stockport"]),

    # Basketball
    ("LeBron James",      "Basketball", "USA",     ["LeBron", "King James", "The King", "LBJ"]),
    ("Stephen Curry",     "Basketball", "USA",     ["Curry", "Steph Curry", "Chef Curry"]),
    ("Giannis Antetokounmpo", "Basketball", "Greece", ["Giannis", "Greek Freak"]),
    ("Nikola Jokić",      "Basketball", "Serbia",  ["Jokic", "Jokić", "The Joker"]),
    ("Luka Dončić",       "Basketball", "Slovenia",["Doncic", "Dončić", "Luka"]),
    ("Joel Embiid",       "Basketball", "Cameroon",["Embiid", "The Process"]),
    ("Kevin Durant",      "Basketball", "USA",     ["Durant", "KD", "Slim Reaper"]),
    ("Jayson Tatum",      "Basketball", "USA",     ["Tatum", "JT"]),
    ("Shai Gilgeous-Alexander", "Basketball", "Canada", ["SGA", "Shai"]),
    ("Anthony Davis",     "Basketball", "USA",     ["AD", "The Brow"]),

    # Tennis
    ("Novak Djokovic",    "Tennis",   "Serbia",    ["Djokovic", "Novak", "Nole", "GOAT"]),
    ("Carlos Alcaraz",    "Tennis",   "Spain",     ["Alcaraz", "Carlitos"]),
    ("Jannik Sinner",     "Tennis",   "Italy",     ["Sinner"]),
    ("Daniil Medvedev",   "Tennis",   "Russia",    ["Medvedev"]),
    ("Iga Świątek",       "Tennis",   "Poland",    ["Swiatek", "Świątek", "Iga"]),
    ("Aryna Sabalenka",   "Tennis",   "Belarus",   ["Sabalenka"]),
    ("Coco Gauff",        "Tennis",   "USA",       ["Gauff", "Coco"]),
    ("Rafael Nadal",      "Tennis",   "Spain",     ["Nadal", "Rafa", "King of Clay"]),
]


# ── Sports news / stats sources to crawl ──────────────────────────────────────
# Format: (display_name, base_url, sport_filter, source_type)
# sport_filter = None means it covers multiple sports

SOURCES = [
    # Multi-sport news
    ("ESPN",             "https://www.espn.com",          None,         "news"),
    ("BBC Sport",        "https://www.bbc.com/sport",     None,         "news"),
    ("Sky Sports",       "https://www.skysports.com",     None,         "news"),
    ("The Athletic",     "https://theathletic.com",       None,         "news"),
    ("Yahoo Sports",     "https://sports.yahoo.com",      None,         "news"),

    # Cricket
    ("Cricbuzz",         "https://www.cricbuzz.com",      "Cricket",    "news"),
    ("ESPNcricinfo",     "https://www.espncricinfo.com",  "Cricket",    "stats"),
    ("CricketWorld",     "https://www.cricketworld.com",  "Cricket",    "news"),

    # Football
    ("Goal.com",         "https://www.goal.com",          "Football",   "news"),
    ("Transfermarkt",    "https://www.transfermarkt.com", "Football",   "stats"),
    ("90min",            "https://www.90min.com",         "Football",   "news"),
    ("WhoScored",        "https://www.whoscored.com",     "Football",   "stats"),

    # Basketball
    ("NBA.com",          "https://www.nba.com",           "Basketball", "stats"),
    ("Bleacher Report",  "https://bleacherreport.com",    "Basketball", "news"),
    ("Basketball Reference", "https://www.basketball-reference.com", "Basketball", "stats"),

    # Tennis
    ("Tennis.com",       "https://www.tennis.com",        "Tennis",     "news"),
    ("ATP Tour",         "https://www.atptour.com",       "Tennis",     "stats"),
    ("WTA",              "https://www.wtatennis.com",     "Tennis",     "stats"),
]


# ── Entry point ────────────────────────────────────────────────────────────────

def seed():
    print("[Seed] Initialising database …")
    init_db()

    print(f"[Seed] Adding {len(PLAYERS)} players …")
    for name, sport, nationality, aliases in PLAYERS:
        pid = upsert_player(name, sport, nationality, aliases)
        print(f"  [{sport}] {name} -> id={pid}")

    print(f"[Seed] Adding {len(SOURCES)} sources …")
    for sname, base_url, sport, stype in SOURCES:
        sid = upsert_source(sname, base_url, sport, stype)
        print(f"  [{stype}] {sname} -> id={sid}")

    print("[Seed] Done ✓")


if __name__ == "__main__":
    seed()
