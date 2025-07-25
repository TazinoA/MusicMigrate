from ytmusicapi import setup_oauth, YTMusic, OAuthCredentials
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
    
    def setup_oauth(self):
        setup_oauth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            filepath=f"./{self.auth_file}"
        )
    
    def get_client(self):
        if self._client is not None:
            return self._client
            
        try:
            with open(self.auth_file, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            auth_data = {}
        
        expires_at = auth_data.get("expires_at")
        refresh_token = auth_data.get("refresh_token")
        
        if not refresh_token:
            self.setup_oauth()
            with open(self.auth_file, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
                expires_at = auth_data.get("expires_at")
                refresh_token = auth_data.get("refresh_token")

        oauth_credentials = OAuthCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        now = time.time()
        if now > expires_at:
            new_token = oauth_credentials.refresh_token(refresh_token)

            auth_data["access_token"] = new_token["access_token"]
            auth_data["expires_at"] = now + new_token["expires_in"]        

            if "refresh_token" in new_token:
                auth_data["refresh_token"] = new_token["refresh_token"]
                refresh_token = new_token["refresh_token"]
                
            with open(self.auth_file, "w", encoding="utf-8") as f:
                json.dump(auth_data, f, indent=2)

        self._client = YTMusic(self.auth_file, oauth_credentials=oauth_credentials)
        return self._client

    def create_playlist(self, name, description="Made from MusicMigrate"):
        client = self.get_client()
        playlist_id = client.create_playlist(title=name, description=description)
        return playlist_id

    def add_songs_to_playlist(self, playlists, progress_callback=None):
        client = self.get_client()
        could_not_find = {}
        total_songs = sum([len(songs) for _, songs in playlists])
        total_playlists = len(playlists)
        
        for curr_playlist, (playlist_name, songs) in enumerate(playlists, 1):
            could_not_find[playlist_name] = [len(songs)]
            playlist_id = self.create_playlist(playlist_name)
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

    def get_playlists(self):
        client = self.get_client()
        return client.get_library_playlists(limit=50)