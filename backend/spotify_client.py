from flask import redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time
import os


class SpotifyHandler:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("SP_CLIENT_ID")
        self.client_secret = os.getenv("SP_CLIENT_SECRET")
        self.scope = "playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative ugc-image-upload user-top-read"
    
    def get_sp_oauth(self):
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=url_for("redirect_page", _external=True),
            scope=self.scope
        )
    
    def get_client(self, token_info):
        if not token_info:
            return redirect(self.get_sp_oauth().get_authorize_url())
        
        # Assuming token_info contains 'expires_at'
        if time.time() > token_info.get('expires_at', 0):
            sp_oauth = self.get_sp_oauth()
            refresh_token = token_info.get("refresh_token")
            if refresh_token:
                token_info = sp_oauth.refresh_access_token(refresh_token)

        return spotipy.Spotify(auth=token_info["access_token"])

    def get_songs(self, playlists, token_info):
        sp = self.get_client(token_info)
        if not isinstance(sp, spotipy.Spotify):
            return sp
        
        fields = "items(track(name,artists(name),album(name),duration_ms)),next"
        playlists_list = []

        for playlist_id, playlist_name in playlists:
            result = sp.playlist_items(playlist_id=playlist_id, fields=fields)
            songs = []

            while True:
                for item in result["items"]:
                    track = item["track"]
                    if not track:
                        continue
                    data = {
                        "song": track["name"],
                        "artists": [artist["name"] for artist in track["artists"]],
                        "album": track["album"]["name"],
                        "duration": track["duration_ms"]
                    }
                    songs.append(data)
                if result["next"]:
                    result = sp.next(result)
                else:
                    break
            
            playlists_list.append([playlist_name, songs])
        
        return playlists_list

    def get_playlists(self, token_info):
        sp = self.get_client(token_info)
        response = sp.current_user_playlists(limit=50)

        playlists = []

        for data in response["items"]:
            if data.get("images") and len(data["images"]) > 1:
                url = data["images"][0]["url"]
            else:
                url = "https://kzmk6dbvewv371frmiwy.lite.vusercontent.net/placeholder.svg?height=60&width=60"
            playlists.append({
                "logo": url,
                "name": data["name"],
                "id": data["id"],
                "count": data["tracks"]["total"]
            })
        return playlists

    def get_song_uri(self, song, token_info):
        sp = self.get_client(token_info)
        response = sp.search(song, limit=1, type="track")
        if response["tracks"]["items"]:
            return response["tracks"]["items"][0]["uri"]
        return None

    def add_songs(self, playlist_id, tracks, token_info):
        sp = self.get_client(token_info)
        sp.playlist_add_items(playlist_id=playlist_id, items=tracks)

    def create_playlist(self, name, token_info, description="", public=True):
        sp = self.get_client(token_info)
        if not isinstance(sp, spotipy.Spotify):
            return sp
        
        user_id = sp.current_user()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            description=description
        )
        return playlist

    def search_tracks(self, query, token_info, limit=10):
        sp = self.get_client(token_info)
        if not isinstance(sp, spotipy.Spotify):
            return sp
        
        results = sp.search(q=query, type='track', limit=limit)
        return results['tracks']['items']