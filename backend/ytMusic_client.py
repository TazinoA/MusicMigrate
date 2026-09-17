from ytmusicapi import YTMusic, OAuthCredentials
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
    
    def get_device_code(self):
        creds = OAuthCredentials(self.client_id, self.client_secret)
        return creds.get_code()

    def get_token_from_code(self, device_code):
        creds = OAuthCredentials(self.client_id, self.client_secret)
        token_info = creds.token_from_code(device_code)
        if "expires_in" in token_info and "expires_at" not in token_info:
            token_info["expires_at"] = time.time() + token_info["expires_in"]
        if "scope" not in token_info:
            token_info["scope"] = "https://www.googleapis.com/auth/youtube"
        return token_info

    def get_client(self, auth_info):
        if not auth_info or not isinstance(auth_info, dict):
            return None

        creds = OAuthCredentials(self.client_id, self.client_secret)
        now = time.time()
        expires_at = auth_info.get("expires_at", 0)
        refresh_token = auth_info.get("refresh_token")

        if refresh_token and now >= expires_at:
            try:
                new_token = creds.refresh_token(refresh_token)
                auth_info["access_token"] = new_token["access_token"]
                auth_info["expires_at"] = now + new_token.get("expires_in", 3600)
                if "refresh_token" in new_token:
                    auth_info["refresh_token"] = new_token["refresh_token"]
            except Exception as e:
                print(f"Error refreshing YouTube token: {e}")

        try:
            return YTMusic(auth=auth_info, oauth_credentials=creds)
        except Exception as e:
            print(f"Error initializing YTMusic: {e}")
            return None

    def create_playlist(self, client, name, description="Made from MusicMigrate"):
        try:
            playlist_id = client.create_playlist(title=name, description=description, privacy_status="PRIVATE")
            return playlist_id
        except Exception as e:
            print(f"Error creating playlist '{name}': {e}")
            return None

    def add_songs_to_playlist(self, playlists, auth_info, progress_callback=None):
        client = self.get_client(auth_info)
        if not client:
            raise ValueError("YouTube Music client could not be authenticated")

        could_not_find = {}
        total_songs = sum([len(item[2]) if len(item) == 3 else len(item[1]) for item in playlists])
        total_playlists = len(playlists)
        
        for curr_playlist, playlist_item in enumerate(playlists, 1):
            if len(playlist_item) == 3:
                _, playlist_name, songs = playlist_item
            else:
                playlist_name, songs = playlist_item

            dict_key = playlist_name
            if dict_key in could_not_find:
                dict_key = f"{playlist_name} (#{curr_playlist})"

            could_not_find[dict_key] = [len(songs)]

            playlist_id = self.create_playlist(client, playlist_name)
            if not playlist_id:
                for track in songs:
                    could_not_find[dict_key].append({
                        "song": track.get("song", "Unknown"),
                        "artists": track.get("artists", [])
                    })
                continue

            video_ids = []
            total = len(songs)

            for curr_count, track in enumerate(songs, 1):
                current_song = track.get("song", "Unknown")
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

                artists_list = track.get("artists", [])
                search_artists = ' '.join([a for a in artists_list if isinstance(a, str) and a.strip()])
                query = f"{current_song} {search_artists}".strip()

                matched_song = None
                for attempt in range(2):
                    try:
                        result = client.search(query=query, filter="songs", limit=5)[:5]
                        matched_song = self.match_song(result, track)
                        break
                    except Exception as e:
                        time.sleep(1)

                if not matched_song:
                    for attempt in range(2):
                        try:
                            result = client.search(query=query, filter="videos", limit=5)[:5]
                            matched_song = self.match_song(result, track)
                            break
                        except Exception as e:
                            time.sleep(1)
                
                if matched_song and "videoId" in matched_song:
                    video_ids.append(matched_song["videoId"])
                else:
                    could_not_find[dict_key].append({
                        "song": current_song,
                        "artists": track.get("artists", [])
                    })

                if len(video_ids) >= 50:
                    for attempt in range(2):
                        try:
                            client.add_playlist_items(
                                playlistId=playlist_id,
                                videoIds=video_ids,
                                duplicates=True
                            )
                            break
                        except Exception as e:
                            print(f"Error adding batch to YT playlist: {e}")
                            time.sleep(1)
                    video_ids = []
            
            if video_ids:
                for attempt in range(2):
                    try:
                        client.add_playlist_items(
                            playlistId=playlist_id,
                            videoIds=video_ids,
                            duplicates=True
                        )
                        break
                    except Exception as e:
                        print(f"Error adding final batch to YT playlist: {e}")
                        time.sleep(1)

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
