from ytmusicapi import setup_oauth, YTMusic, OAuthCredentials
import os
from dotenv import load_dotenv, find_dotenv
import json
import time
from difflib import SequenceMatcher
import re

load_dotenv(find_dotenv())
client_id =os.getenv("YT_CLIENT_ID")
client_secret = os.getenv("YT_CLIENT_SECRET")
AUTH_FILE = "headers_auth.json"


def get_yt_auth():
    setup_oauth(client_id=client_id, client_secret=client_secret, filepath = f"./{AUTH_FILE}")


def get_ytClient():
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
    except json.JSONDecodeError:
        auth_data = {}
    
    expires_at = auth_data.get("expires_at")
    refresh_token = auth_data.get("refresh_token")
    
    if not refresh_token:
        get_yt_auth()

        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
            expires_at = auth_data.get("expires_at")
            refresh_token = auth_data.get("refresh_token")


    oauth_credentials = OAuthCredentials(client_id=client_id, client_secret=client_secret)

    now = time.time()
    if now > expires_at:
        new_token = oauth_credentials.refresh_token(refresh_token)

        auth_data["access_token"] = new_token["access_token"]
        auth_data["expires_at"] = now + new_token["expires_in"]        

        if "refresh_token" in new_token:
            auth_data["refresh_token"] = new_token["refresh_token"]
            refresh_token = new_token["refresh_token"]
            
        with open(AUTH_FILE, "w", encoding = "utf-8") as f:
            json.dump(auth_data, f, indent = 2)

    ytmusic = YTMusic(AUTH_FILE, oauth_credentials=oauth_credentials)
    return ytmusic


def create_playlist(name):
    client = get_ytClient()

    playlist_id = client.create_playlist(title = name, description = "Made from Tranfer Playlists")
    return playlist_id

def is_similar(a,b,threshold =0.8):
    if not a or not b:
        return False
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold


def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\(.*?\)|\[.*?\]|-.*", "", text) 
    text = re.sub(r"[^\w\s]", "", text) 
    return text.strip()


def add_ytSongs(playlists, progress_callback = None):
    print("start")
    client = get_ytClient()
    could_not_find = {}
    total_songs = sum([len(songs) for _, songs in playlists])
    total_playlists = len(playlists)
    for playlist_name, songs in playlists:
        could_not_find[playlist_name] = [0]
        could_not_find[playlist_name][0] = len(songs)
        playlist_id = create_playlist(playlist_name)
        video_ids = set()

       
        total = len(songs)
        curr_count = 0
        curr_playlist = 1
        for track in songs:
            current_song = track["song"]
            curr_count += 1
            progress_callback(playlist_name = playlist_name, current_song = current_song, total = total, curr_count = curr_count, curr_playlist = curr_playlist, total_songs = total_songs, total_playlists = total_playlists)

            search_artists = ' '.join([a for a in track["artists"] if isinstance(a, str) and a.strip()])
            result = client.search(query = f"{track['song']} {search_artists}", filter="songs", limit=5)[:5]

            matched_song = match_song(result, track)

            if not matched_song:
                result = client.search(query = f"{track['song']} {search_artists}", filter="videos", limit=5)[:5]
                matched_song = match_song(result, track)
            
            if matched_song and "videoId" in matched_song:
                videoId = matched_song["videoId"]
                #print(track)
                if videoId not in video_ids:
                    video_ids.add(videoId)
            else:
                could_not_find[playlist_name].append({
                    "song": track["song"],
                    "artists": track["artists"]
                })


            if len(video_ids) >= 50:
                 response = client.add_playlist_items(playlistId=playlist_id, videoIds=list(video_ids), duplicates = True)
                 #print(response["status"])
                 video_ids = set()
            
        
        if video_ids:
            response = client.add_playlist_items(playlistId=playlist_id, videoIds=list(video_ids), duplicates=True)
            #print(response["status"])
        
        curr_playlist += 1

    return could_not_find


def split_artists(name_str):
    parts = re.split(r'\s*,\s*|\s*&\s*|\s+and\s+', name_str)
    return [part.strip() for part in parts if part.strip()]

def get_result_artists(song):
    if "artists" in song:
        artists_list = song["artists"]
        if len(artists_list) == 1:   
            name_str = artists_list[0].get("name", "")
           
            if any(sep in name_str for sep in [",", "&", " and "]):
                return [clean_text(a) for a in split_artists(name_str)]
            else:
                return [clean_text(name_str)]
        else:
            return [clean_text(a.get("name", "")) for a in artists_list if a.get("name")]
    elif "artist" in song:
        return [clean_text(song["artist"])]
    else:
        return []
    

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


def match_song(results, track):
    target_title = clean_text(track["song"])
    target_artists = [clean_text(artist) for artist in track["artists"]]


    featured_from_title = extract_featured_artists(track["song"])
    target_artists += [clean_text(a) for a in featured_from_title]

    target_duration = int(track.get("duration") or 0) // 1000

    best_match = None
    best_score = 0

    for song in results:
        title = clean_text(song.get("title"))
        result_artists = get_result_artists(song)  

        featured_from_yt_title = extract_featured_artists(song.get("title", ""))
        result_artists += [clean_text(a) for a in featured_from_yt_title]

        if "duration_seconds" in song and song["duration_seconds"]:
            duration = song["duration_seconds"]
        elif "duration" in song and song["duration"]:
            duration = parse_duration(song["duration"])
        else:
            duration = 0

        title_score = SequenceMatcher(None, title, target_title).ratio()
        artist_matches = [1 for a in result_artists for b in target_artists if is_similar(a, b)]
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