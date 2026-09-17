from flask import redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from dotenv import load_dotenv, find_dotenv
import time
import os


class SpotifyHandler:
    def __init__(self):
        load_dotenv(find_dotenv())
        self.client_id = (os.getenv("SP_CLIENT_ID") or "").strip("'\" ")
        self.client_secret = (os.getenv("SP_CLIENT_SECRET") or "").strip("'\" ")
        self.scope = "playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative ugc-image-upload user-top-read"
    
    def get_sp_oauth(self):
        cache_handler = FlaskSessionCacheHandler(session)
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=url_for("redirect_page", _external=True),
            scope=self.scope,
            cache_handler=cache_handler,
            show_dialog=True
        )
    
    def get_client(self):
        token_info = session.get("sp_token_info") or session.get("token_info")
        if not token_info or not isinstance(token_info, dict):
            return None
        
        start_time = session.get("sp_start_time", 0)
        expires_in = session.get("sp_expires_in", 3600)
        expiration_time = start_time + expires_in

        if time.time() > expiration_time:
            sp_oauth = self.get_sp_oauth()
            refresh_token = token_info.get("refresh_token")
            if refresh_token:
                try:
                    token_info = sp_oauth.refresh_access_token(refresh_token)
                    session["sp_token_info"] = token_info
                    session["token_info"] = token_info
                    session['sp_start_time'] = time.time()
                    session['sp_expires_in'] = token_info.get('expires_in', 3600)
                except Exception as e:
                    print(f"Error refreshing Spotify token: {e}")
                    return None
            else:
                return None

        access_token = token_info.get("access_token")
        if not access_token:
            return None

        return spotipy.Spotify(auth=access_token)

    def get_songs(self, playlists):
        sp = self.get_client()
        if not sp:
            return None
        
        fields = "items(track(name,artists(name),album(name),duration_ms)),next"
        playlists_list = []

        for playlist_id, playlist_name in playlists:
            try:
                result = sp.playlist_items(playlist_id=playlist_id, fields=fields)
            except Exception as e:
                print(f"Error fetching items for playlist {playlist_id}: {e}")
                continue

            songs = []

            while result:
                for item in result.get("items", []):
                    track = item.get("track")
                    if not track:
                        continue
                    data = {
                        "song": track.get("name", "Unknown Title"),
                        "artists": [artist.get("name", "") for artist in track.get("artists", []) if artist.get("name")],
                        "album": track.get("album", {}).get("name", ""),
                        "duration": track.get("duration_ms", 0)
                    }
                    songs.append(data)
                if result.get("next"):
                    result = sp.next(result)
                else:
                    break
            
            playlists_list.append([playlist_id, playlist_name, songs])
        
        return playlists_list

    def get_playlists(self):
        sp = self.get_client()
        if not sp:
            return []

        try:
            response = sp.current_user_playlists(limit=50)
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return []

        playlists = []

        while response:
            items = response.get("items") or []
            for data in items:
                if not isinstance(data, dict):
                    continue

                images = data.get("images") or []
                url = "https://kzmk6dbvewv371frmiwy.lite.vusercontent.net/placeholder.svg?height=60&width=60"
                if isinstance(images, list) and len(images) > 0 and isinstance(images[0], dict):
                    url = images[0].get("url") or url

                count = None
                tracks_data = data.get("tracks")
                if isinstance(tracks_data, dict):
                    count = tracks_data.get("total")
                    if count is None and isinstance(tracks_data.get("items"), list):
                        count = len(tracks_data["items"])
                elif isinstance(tracks_data, int):
                    count = tracks_data
                elif isinstance(tracks_data, list):
                    count = len(tracks_data)

                if count is None:
                    count = data.get("total_tracks", 0)

                playlists.append({
                    "logo": url,
                    "name": data.get("name", "Untitled Playlist"),
                    "id": data.get("id"),
                    "count": count or 0
                })

            if response.get("next"):
                try:
                    response = sp.next(response)
                except Exception as e:
                    print(f"Error paginating playlists: {e}")
                    break
            else:
                break

        return playlists

    def get_song_uri(self, song):
        sp = self.get_client()
        if not sp:
            return None
        response = sp.search(song, limit=1, type="track")
        if response and response.get("tracks", {}).get("items"):
            return response["tracks"]["items"][0]["uri"]
        return None

    def add_songs(self, playlist_id, tracks):
        sp = self.get_client()
        if sp:
            sp.playlist_add_items(playlist_id=playlist_id, items=tracks)

    def create_playlist(self, name, description="", public=True):
        sp = self.get_client()
        if not sp:
            return None
        
        user_id = sp.current_user()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            description=description
        )
        return playlist

    def search_tracks(self, query, limit=10):
        sp = self.get_client()
        if not sp:
            return []
        
        results = sp.search(q=query, type='track', limit=limit)
        return results.get('tracks', {}).get('items', [])
