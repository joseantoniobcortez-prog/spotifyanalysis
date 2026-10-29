import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import psycopg2
from psycopg2.extras import Json

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))
items = sp.current_user_recently_played(limit=50)["items"]

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

inserted = 0
for item in items:
    cur.execute(
        """
        insert into raw_plays (played_at, track_uri, payload)
        values (%s, %s, %s)
        on conflict (played_at, track_uri) do nothing
        """,
        (item["played_at"], item["track"]["uri"], Json(item)),
    )
    inserted += cur.rowcount

conn.commit()
cur.close()
conn.close()
print(f"Fetched {len(items)} plays, inserted {inserted} new")