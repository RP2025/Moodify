from flask import Flask, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

# Spotify API credentials
SPOTIFY_CLIENT_ID = "a30e0e2e444a4eb3a101a92aba0a0724"
SPOTIFY_CLIENT_SECRET = "bebd2c70191845acac8e830920ebab14"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

# Setup Spotify Authentication
sp_auth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                       client_secret=SPOTIFY_CLIENT_SECRET,
                       redirect_uri=SPOTIFY_REDIRECT_URI,
                       scope="playlist-read-private")

sp = spotipy.Spotify(auth_manager=sp_auth)

@app.route("/generate_playlist", methods=["POST"])
def generate_playlist():
    data = request.json
    mood = data.get("mood")

    # Search Spotify for playlists related to mood
    results = sp.search(q=mood, type="playlist", limit=1)
    if results["playlists"]["items"]:
        playlist = results["playlists"]["items"][0]
        return jsonify({
            "name": playlist["name"],
            "url": playlist["external_urls"]["spotify"]
        })
    return jsonify({"error": "No playlist found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
