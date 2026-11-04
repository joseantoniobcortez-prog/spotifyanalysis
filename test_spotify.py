"""
test_spotify.py

A quick test that the Spotify login works.
Prints your last 50 played tracks to the terminal.
Nothing is saved anywhere.
"""

from dotenv import load_dotenv            # reads variables from the .env file
import spotipy                            # Python library for the Spotify Web API
from spotipy.oauth2 import SpotifyOAuth   # handles the Spotify login flow

# Load SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET and SPOTIPY_REDIRECT_URI
# from .env into environment variables, where spotipy looks for them.
load_dotenv()

# Create a Spotify client that logs in as you.
# scope="user-read-recently-played" asks permission to read your listening
# history and nothing else.
# The first run opens a browser so you can approve access; after that the
# login token is saved in the .cache file and reused automatically.
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))

# Ask Spotify for your recently played tracks. 50 is the maximum it allows.
results = sp.current_user_recently_played(limit=50)

# The response is a dict; the plays are in the "items" list.
# Each item holds a played_at timestamp (UTC) and a "track" object
# with the song's details.
for item in results["items"]:
    print(
        item["played_at"],                    # when you played it, in UTC
        item["track"]["artists"][0]["name"],  # first listed artist
        "-",
        item["track"]["name"],                # song title
    )