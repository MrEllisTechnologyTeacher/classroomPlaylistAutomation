# Classroom Playlist Automation

Reads songs from a Google Sheet and automatically adds them to a Spotify playlist. Skips duplicates and reports any songs that couldn't be found.

---

## Prerequisites

- Python 3.10+
- A [Spotify Developer App](https://developer.spotify.com/dashboard)
- A Google Cloud project with the **Google Sheets API** and **Google Drive API** enabled, plus a **Service Account** key

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in all values.

### 3. Spotify credentials

1. Go to [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and create an app.
2. Set the **Redirect URI** to `http://localhost:8888/callback` (must match `.env`).
3. Copy the **Client ID** and **Client Secret** into `.env`.
4. Get your **Playlist ID** from the playlist URL:
   `https://open.spotify.com/playlist/<PLAYLIST_ID>`

### 4. Google Sheets credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account**, download the JSON key, and save it as `service_account.json` in this folder.
4. Share your Google Sheet with the service account email (found in the JSON key — looks like `something@project.iam.gserviceaccount.com`).

---

## Google Sheet format

The sheet must have these column headers:

| Song Title | Song Artist |
|------------|-------------|
| Blinding Lights | The Weeknd |
| … | … |

---

## Running

```bash
python main.py
```

On first run, Spotify will open a browser window to authorize. After that, a `.cache` file stores the token automatically.

The script will:
- Fetch all songs from the sheet
- Search each one on Spotify
- Skip songs already in the playlist
- Add new songs in batches
- Report any songs it couldn't find

---

## `.env` reference

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | From Spotify Developer Dashboard |
| `SPOTIFY_CLIENT_SECRET` | From Spotify Developer Dashboard |
| `SPOTIFY_REDIRECT_URI` | Must match what's set in the Spotify app |
| `SPOTIFY_PLAYLIST_ID` | ID of the target playlist |
| `GOOGLE_SHEET_ID` | ID portion of the sheet URL |
| `GOOGLE_SHEET_GID` | Tab/worksheet gid (default: `751801221`) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to your service account key file |