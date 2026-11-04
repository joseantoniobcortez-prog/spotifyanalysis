"""
ingest.py

The main pipeline script. GitHub Actions runs it every two hours.

1. Logs in to Spotify and fetches your last 50 plays.
2. Saves each play into the raw_plays table in Supabase.
3. Skips plays that are already stored, so nothing is duplicated.
"""

import os                                  # reads environment variables
from dotenv import load_dotenv             # loads .env when running locally
import spotipy                             # Spotify Web API library
from spotipy.oauth2 import SpotifyOAuth    # handles the Spotify login
import psycopg2                            # PostgreSQL driver
from psycopg2.extras import Json           # converts a Python dict to JSONB

# ---------------------------------------------------------------
# 1. Setup
# ---------------------------------------------------------------

# Load credentials from .env when running on your laptop.
# On GitHub Actions there's no .env file; the same variables come from
# the repository secrets instead, and this line simply does nothing.
load_dotenv()

# ---------------------------------------------------------------
# 2. Fetch recent plays from Spotify
# ---------------------------------------------------------------

# Log in using the saved token in .cache. On GitHub Actions, the workflow
# recreates .cache from the SPOTIFY_CACHE secret before this script runs,
# so no browser login is needed.
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))

# Get up to 50 recent plays. This is Spotify's limit, which is why the job
# runs every two hours: anything older than your last 50 plays is gone.
items = sp.current_user_recently_played(limit=50)["items"]

# ---------------------------------------------------------------
# 3. Save the plays to the database
# ---------------------------------------------------------------

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

inserted = 0  # counts how many plays were actually new

for item in items:
    # Insert one play. The three %s placeholders are filled in safely by
    # psycopg2, which prevents SQL injection and handles quoting.
    #
    # - played_at: when the play happened
    # - track_uri: Spotify's ID for the track
    # - payload:   the whole play record stored as JSON, so no data is
    #              lost even if we decide later we need more fields
    #
    # "on conflict ... do nothing" skips the row if a play with the same
    # played_at and track_uri already exists. This is the dedupe that makes
    # the script safe to run every two hours.
    cur.execute(
        """
        insert into raw_plays (played_at, track_uri, payload)
        values (%s, %s, %s)
        on conflict (played_at, track_uri) do nothing
        """,
        (item["played_at"], item["track"]["uri"], Json(item)),
    )

    # rowcount is 1 if the row was inserted, 0 if it was skipped.
    inserted += cur.rowcount

# Save all the inserts. Without commit(), the changes are thrown away.
conn.commit()

cur.close()
conn.close()

# This line appears in the GitHub Actions log for each run.
print(f"Fetched {len(items)} plays, inserted {inserted} new")