"""
inspect_export.py

A one-off check of the Spotify export before loading it.
Reads all the audio history files and prints summary counts,
so you can spot problems before anything goes into the database.
"""

import glob          # finds files that match a name pattern
import json          # parses JSON files
import pandas as pd  # table-style data analysis

# Collect every play record from every audio history file.
rows = []

# "**" with recursive=True searches data/ and all its subfolders.
for path in glob.glob("data/**/Streaming_History_Audio_*.json", recursive=True):
    with open(path, encoding="utf-8") as f:
        # Each file holds a list of play records; add them all to rows.
        rows += json.load(f)

# Turn the list of records into a DataFrame (a table with named columns).
df = pd.DataFrame(rows)

# Total number of plays across all files.
print(len(df), "rows")

# Every column name, to check the format matches what the loader expects.
print(df.columns.tolist())

# Earliest and latest play. "ts" is the timestamp column, in UTC.
print("date range:", df["ts"].min(), "->", df["ts"].max())

# Rows with no track URI: podcasts, audiobooks or broken entries.
print("no track uri:", df["spotify_track_uri"].isna().sum())

# Plays shorter than 30 seconds: skips, which Spotify doesn't count as streams.
print("under 30s:", (df["ms_played"] < 30000).sum())

# Rows that repeat the same timestamp and track: duplicates in the export.
print("duplicates:", df.duplicated(["ts", "spotify_track_uri"]).sum())