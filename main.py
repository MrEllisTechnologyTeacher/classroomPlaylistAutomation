"""
classroomPlaylistAutomation
Reads songs from a Google Sheet and adds them to a Spotify playlist.

Columns expected in the sheet: "Song Title", "Song Artist"
"""

import os
import sys
import gspread
import spotipy
from google.oauth2.service_account import Credentials
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

SCOPES_SHEETS = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private"


def get_sheet_songs() -> list[dict]:
    """Return a list of {title, artist} dicts from the Google Sheet."""
    service_account_path = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    gid = os.environ.get("GOOGLE_SHEET_GID", "0")

    creds = Credentials.from_service_account_file(service_account_path, scopes=SCOPES_SHEETS)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(sheet_id)
    # Find worksheet by gid
    worksheet = None
    for ws in spreadsheet.worksheets():
        if str(ws.id) == str(gid):
            worksheet = ws
            break
    if worksheet is None:
        raise ValueError(f"Worksheet with gid={gid} not found.")

    records = worksheet.get_all_records()
    songs = []
    for row in records:
        title = str(row.get("Song Title", "")).strip()
        artist = str(row.get("Song Artist", "")).strip()
        if title:
            songs.append({"title": title, "artist": artist})
    return songs


def search_spotify(sp: spotipy.Spotify, title: str, artist: str) -> str | None:
    """Search Spotify for a track and return its URI, or None if not found."""
    query = f"track:{title}"
    if artist:
        query += f" artist:{artist}"
    results = sp.search(q=query, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    if items:
        return items[0]["uri"]
    # Retry with a looser query if strict search fails
    results = sp.search(q=f"{title} {artist}", type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    if items:
        return items[0]["uri"]
    return None


def get_existing_track_uris(sp: spotipy.Spotify, playlist_id: str) -> set:
    """Return the set of track URIs already in the playlist."""
    uris = set()
    results = sp.playlist_items(playlist_id, fields="items.track.uri,next", limit=100)
    while results:
        for item in results.get("items", []):
            track = item.get("track")
            if track and track.get("uri"):
                uris.add(track["uri"])
        next_page = results.get("next")
        if not next_page:
            break
        results = sp.next(results)
    return uris


def add_songs_to_playlist():
    # --- Google Sheets ---
    print("Fetching songs from Google Sheet...")
    songs = get_sheet_songs()
    print(f"  Found {len(songs)} song(s).")

    # --- Spotify ---
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
            scope=SPOTIFY_SCOPE,
        )
    )
    playlist_id = os.environ["SPOTIFY_PLAYLIST_ID"]

    print("Checking existing playlist tracks...")
    existing_uris = get_existing_track_uris(sp, playlist_id)
    print(f"  Playlist already has {len(existing_uris)} track(s).")

    to_add = []
    not_found = []
    already_in = []

    for song in songs:
        uri = search_spotify(sp, song["title"], song["artist"])
        if uri is None:
            not_found.append(song)
            print(f"  [NOT FOUND]  {song['title']} — {song['artist']}")
        elif uri in existing_uris:
            already_in.append(song)
            print(f"  [SKIP/DUP]   {song['title']} — {song['artist']}")
        else:
            to_add.append(uri)
            print(f"  [QUEUED]     {song['title']} — {song['artist']}")

    if to_add:
        # Spotify allows max 100 tracks per request
        for i in range(0, len(to_add), 100):
            sp.playlist_add_items(playlist_id, to_add[i : i + 100])
        print(f"\nAdded {len(to_add)} new track(s) to the playlist.")
    else:
        print("\nNo new tracks to add.")

    if not_found:
        print(f"\nCould not find {len(not_found)} song(s) on Spotify:")
        for s in not_found:
            print(f"  - {s['title']} — {s['artist']}")


if __name__ == "__main__":
    required_env = [
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REDIRECT_URI",
        "SPOTIFY_PLAYLIST_ID",
        "GOOGLE_SHEET_ID",
        "GOOGLE_SERVICE_ACCOUNT_JSON",
    ]
    missing = [k for k in required_env if not os.environ.get(k)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    add_songs_to_playlist()
