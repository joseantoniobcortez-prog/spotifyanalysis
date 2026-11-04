"""
load_export.py

One-time loader for Spotify's Extended Streaming History export.
Reads every audio JSON file in data/, cleans the rows, and loads them
into the raw_streaming_history table in Supabase.

Safe to run more than once: rows already in the table are skipped.
"""

import glob  # finds files that match a name pattern
import json  # parses the export's JSON files
import os    # reads environment variables like DATABASE_URL

from dotenv import load_dotenv               # loads secrets from .env
import psycopg2                              # PostgreSQL driver
from psycopg2.extras import execute_values   # fast bulk inserts


# ---------------------------------------------------------------
# 1. Setup
# ---------------------------------------------------------------

# Load DATABASE_URL from .env so the password never appears in code.
load_dotenv()

# "**" with recursive=True searches data/ and every subfolder,
# so it finds the files inside "Spotify Extended Streaming History/".
EXPORT_PATTERN = "data/**/Streaming_History_Audio_*.json"


# ---------------------------------------------------------------
# 2. Read and clean the export
# ---------------------------------------------------------------

# Store plays in a dict keyed by (timestamp, track URI).
# Using a dict means duplicate keys collapse into a single entry.
plays = {}
dropped_no_uri = 0
dropped_duplicates = 0

for path in sorted(glob.glob(EXPORT_PATTERN, recursive=True)):
    with open(path, encoding="utf-8") as f:
        records = json.load(f)  # each file is a list of play records

    for r in records:
        uri = r.get("spotify_track_uri")

        # Rows without a track URI are podcasts, audiobooks or broken
        # entries. They aren't music plays, so skip them.
        if not uri:
            dropped_no_uri += 1
            continue

        key = (r["ts"], uri)

        # Duplicate check: if we've already seen this timestamp + track,
        # keep whichever copy has the longer listening time.
        if key in plays:
            dropped_duplicates += 1
            if plays[key]["ms_played"] >= r["ms_played"]:
                continue

        plays[key] = r


# ---------------------------------------------------------------
# 3. Shape the rows for the database
# ---------------------------------------------------------------

# Pick only the columns we need, in the same order as the INSERT below.
# ip_addr and conn_country are left out on purpose: they're personal
# data the analysis doesn't need.
rows = [
    (
        r["ts"],                                   # play time (UTC)
        r["spotify_track_uri"],                    # unique track ID
        r.get("master_metadata_track_name"),
        r.get("master_metadata_album_artist_name"),
        r.get("master_metadata_album_album_name"),
        r["ms_played"],                            # how long you listened
        r.get("platform"),                         # phone, desktop, etc.
        r.get("reason_start"),                     # why the track started
        r.get("reason_end"),                       # why it ended (skip etc.)
        r.get("shuffle"),
        r.get("skipped"),
    )
    for r in plays.values()
]


# ---------------------------------------------------------------
# 4. Load into Supabase
# ---------------------------------------------------------------

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# execute_values sends rows in batches of 1,000 instead of one at a
# time, which turns hours of inserts into a few minutes.
# "on conflict do nothing" skips rows already in the table, which is
# what makes the script safe to rerun.
execute_values(
    cur,
    """
    insert into raw_streaming_history
        (played_at, track_uri, track_name, artist_name, album_name,
         ms_played, platform, reason_start, reason_end, shuffle, skipped)
    values %s
    on conflict (played_at, track_uri) do nothing
    """,
    rows,
    page_size=1000,
)

conn.commit()  # nothing is saved until this runs
cur.close()
conn.close()


# ---------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------

print(f"Dropped {dropped_no_uri} rows with no track URI")
print(f"Resolved {dropped_duplicates} duplicate rows")
print(f"Sent {len(rows)} rows to the database")