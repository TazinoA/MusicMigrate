from ytmusicapi import setup_oauth, YTMusic, OAuthCredentials
from google_auth_oauthlib.flow import Flow
import os
from dotenv import load_dotenv, find_dotenv
import json
import time
from difflib import SequenceMatcher
import re

class YouTubeMusicHandler:
    def __init__(self):
        load_dotenv(find_dotenv())
        self.client_id = os.getenv("YT_CLIENT_ID")
        self.client_secret = os.getenv("YT_CLIENT_SECRET")
        self.auth_file = "headers_auth.json"
        self._client = None


    def get_auth_url(self):
        flow = Flow.from_client_config(
        {
            "web":{
                "client_id":self.client_id,
                "client_secret":self.client_secret,
                "redirect_uris":["http://localhost:8000/callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=["https://www.googleapis.com/auth/youtube"]
    )
        flow.redirect_uri = "http://localhost:8000/callback"
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
        self.flow = flow
        return flow, auth_url
    
    def get_auth_token(self, flow, code):
        flow.fetch_token(code=code)
        return flow.credentials

    def setup_oauth(self, code):
        return self.get_auth_token(flow = self.flow, code = code)
    
    def get_client(self, token_info):
        if self._client is not None:
            return self._client

        if token_info is None:
            raise RuntimeError("YouTube Music token info is missing.")

        oauth_credentials = OAuthCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        now = time.time()
        access_token = token_info["token"]
        expires_at = token_info["expires_at"]
        refresh_token = token_info["refresh_token"]

        if now >= expires_at:
            new_token = oauth_credentials.refresh_token(refresh_token)
            access_token = new_token["access_token"]
            expires_at = now + new_token["expires_in"]
            refresh_token = new_token.get("refresh_token", refresh_token)

            token_info["token"] = access_token
            token_info["expires_at"] = expires_at
            token_info["refresh_token"] = refresh_token

        self._client = YTMusic(
            OAuthCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=access_token,
                refresh_token=refresh_token
            )
        )

        return self._client


    def create_playlist(self, name, token_info ,description="Made from MusicMigrate"):
        client = self.get_client(token_info=token_info)
        playlist_id = client.create_playlist(title=name, description=description)
        return playlist_id

    def add_songs_to_playlist(self, playlists, token_info,progress_callback=None):
        client = self.get_client(token_info=token_info)
        could_not_find = {}
        total_songs = sum([len(songs) for _, songs in playlists])
        total_playlists = len(playlists)
        
        for curr_playlist, (playlist_name, songs) in enumerate(playlists, 1):
            could_not_find[playlist_name] = [len(songs)]
            playlist_id = self.create_playlist(playlist_name, token_info)
            video_ids = set()

            total = len(songs)
            for curr_count, track in enumerate(songs, 1):
                current_song = track["song"]
                if progress_callback:
                    progress_callback(
                        playlist_name=playlist_name,
                        current_song=current_song,
                        total=total,
                        curr_count=curr_count,
                        curr_playlist=curr_playlist,
                        total_songs=total_songs,
                        total_playlists=total_playlists
                    )

                search_artists = ' '.join([a for a in track["artists"] if isinstance(a, str) and a.strip()])
                
                # Search for songs first
                result = client.search(query=f"{track['song']} {search_artists}", filter="songs", limit=5)[:5]
                matched_song = self.match_song(result, track)

                # If no match, search videos
                if not matched_song:
                    result = client.search(query=f"{track['song']} {search_artists}", filter="videos", limit=5)[:5]
                    matched_song = self.match_song(result, track)
                
                if matched_song and "videoId" in matched_song:
                    video_id = matched_song["videoId"]
                    if video_id not in video_ids:
                        video_ids.add(video_id)
                else:
                    could_not_find[playlist_name].append({
                        "song": track["song"],
                        "artists": track["artists"]
                    })

                # Add songs in batches of 50
                if len(video_ids) >= 50:
                    client.add_playlist_items(
                        playlistId=playlist_id,
                        videoIds=list(video_ids),
                        duplicates=True
                    )
                    video_ids = set()
            
           
            if video_ids:
                client.add_playlist_items(
                    playlistId=playlist_id,
                    videoIds=list(video_ids),
                    duplicates=True
                )

        return could_not_find

    @staticmethod
    def is_similar(a, b, threshold=0.8):
        """Check if two strings are similar based on threshold"""
        if not a or not b:
            return False
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold

    @staticmethod
    def clean_text(text):
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"\(.*?\)|\[.*?\]|-.*", "", text) 
        text = re.sub(r"[^\w\s]", "", text) 
        return text.strip()

    @staticmethod
    def split_artists(name_str):
        parts = re.split(r'\s*,\s*|\s*&\s*|\s+and\s+', name_str)
        return [part.strip() for part in parts if part.strip()]

    def get_result_artists(self, song):
        if "artists" in song:
            artists_list = song["artists"]
            if len(artists_list) == 1:   
                name_str = artists_list[0].get("name", "")
                if any(sep in name_str for sep in [",", "&", " and "]):
                    return [self.clean_text(a) for a in self.split_artists(name_str)]
                else:
                    return [self.clean_text(name_str)]
            else:
                return [self.clean_text(a.get("name", "")) for a in artists_list if a.get("name")]
        elif "artist" in song:
            return [self.clean_text(song["artist"])]
        else:
            return []

    @staticmethod
    def extract_featured_artists(title):
        featured_artists = []
        feat_pattern = re.compile(r"\(feat\.? ([^)]+)\)|\[feat\.? ([^\]]+)\]", re.IGNORECASE)
        matches = feat_pattern.findall(title)
        for match in matches:
            feat_text = match[0] or match[1]
            if feat_text:
                artists = re.split(r'\s*,\s*|\s*&\s*|\s+and\s+', feat_text)
                featured_artists.extend([a.strip() for a in artists if a.strip()])
        return featured_artists

    @staticmethod
    def parse_duration(duration_str):
        if not duration_str:
            return 0
        parts = duration_str.split(':')
        parts = [int(p) for p in parts]
        if len(parts) == 2: 
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3: 
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return 0

    def match_song(self, results, track):
        target_title = self.clean_text(track["song"])
        target_artists = [self.clean_text(artist) for artist in track["artists"]]

        featured_from_title = self.extract_featured_artists(track["song"])
        target_artists += [self.clean_text(a) for a in featured_from_title]

        target_duration = int(track.get("duration") or 0) // 1000

        best_match = None
        best_score = 0

        for song in results:
            title = self.clean_text(song.get("title"))
            result_artists = self.get_result_artists(song)  

          
            featured_from_yt_title = self.extract_featured_artists(song.get("title", ""))
            result_artists += [self.clean_text(a) for a in featured_from_yt_title]

            
            if "duration_seconds" in song and song["duration_seconds"]:
                duration = song["duration_seconds"]
            elif "duration" in song and song["duration"]:
                duration = self.parse_duration(song["duration"])
            else:
                duration = 0

            
            title_score = SequenceMatcher(None, title, target_title).ratio()
            artist_matches = [1 for a in result_artists for b in target_artists if self.is_similar(a, b)]
            artist_score = len(artist_matches) / max(len(target_artists), 1)

            duration_score = 1.0
            if target_duration and duration:
                diff = abs(duration - target_duration)
                if diff > 10:
                    duration_score = max(0, 1 - (diff / 30))

            total_score = (title_score * 0.5) + (artist_score * 0.3) + (duration_score * 0.2)

            if total_score > best_score and total_score > 0.65:
                best_score = total_score
                best_match = song

        return best_match

    def search_songs(self, query, limit=10):
        client = self.get_client()
        return client.search(query=query, filter="songs", limit=limit)

    def get_playlists(self, token_info):
        client = self.get_client(token_info)
        return client.get_library_playlists(limit=50)