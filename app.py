from flask import Flask, render_template, request, redirect, url_for, session
import requests
import json
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Fetch sensitive information from environment variables
app.secret_key = os.getenv('SECRET_KEY')

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Spotify API Endpoints
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# Scopes for user authentication
SCOPES = "user-read-private playlist-modify-public playlist-modify-private"


# Function to get Spotify token
def get_spotify_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(SPOTIFY_TOKEN_URL, data=data)
    return response.json()

# Function to fetch top tracks based on language/genre
def fetch_top_tracks(query, token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": "track", "limit": 10}
    response = requests.get(SPOTIFY_API_BASE_URL + "/search", headers=headers, params=params)
    if response.status_code == 200:
        tracks = response.json()['tracks']['items']
        return [{"name": track["name"], "artist": track["artists"][0]["name"], "uri": track["uri"]} for track in tracks]
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = get_spotify_token(code)
    session['token'] = token_data['access_token']
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    if 'token' not in session:
        # Redirect to Spotify authentication if no token
        params = {
            "client_id": SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "scope": SCOPES
        }
        auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
        return redirect(auth_url)

    token = session['token']
    language = request.form.get('language')
    query = request.form.get('query')
    search_query = f"{query} {language}"
    tracks = fetch_top_tracks(search_query, token)
    session['tracks'] = tracks  # Save tracks in session
    return render_template('track_list.html', tracks=tracks)

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    if 'token' not in session or 'tracks' not in session:
        return redirect(url_for('index'))

    token = session['token']
    user_data = requests.get(SPOTIFY_API_BASE_URL + "/me", headers={"Authorization": f"Bearer {token}"}).json()
    user_id = user_data['id']

    # Create a new playlist
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    playlist_data = {"name": "Moodify Playlist", "description": "Generated by Moodify", "public": True}
    playlist_response = requests.post(SPOTIFY_API_BASE_URL + f"/users/{user_id}/playlists", headers=headers, json=playlist_data)
    playlist = playlist_response.json()

    # Add tracks to the playlist
    track_uris = [track['uri'] for track in session['tracks']]
    add_tracks_response = requests.post(
        SPOTIFY_API_BASE_URL + f"/playlists/{playlist['id']}/tracks", 
        headers=headers, 
        json={"uris": track_uris}
    )

    return f"Playlist created! <a href='{playlist['external_urls']['spotify']}' target='_blank'>Open Playlist</a>"

if __name__ == '__main__':
    app.run(debug=True)
