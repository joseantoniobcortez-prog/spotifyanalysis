from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))
results = sp.current_user_recently_played(limit=50)

for item in results["items"]:
    print(item["played_at"], item["track"]["artists"][0]["name"], "-", item["track"]["name"])