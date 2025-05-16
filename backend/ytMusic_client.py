from ytmusicapi import setup_oauth, YTMusic, OAuthCredentials
import os
from dotenv import load_dotenv, find_dotenv
import json
import time

load_dotenv(find_dotenv())
client_id =os.getenv("YT_CLIENT_ID")
client_secret = os.getenv("YT_CLIENT_SECRET")
AUTH_FILE = "headers_auth.json"


def get_yt_auth():
    setup_oauth(client_id=client_id, client_secret=client_secret, filepath = f"./{AUTH_FILE}")


def get_ytClient():
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        auth_data = json.load(f)
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

    


def add_ytSongs(playlists):
    client = get_ytClient()
    for playlist_name, songs in playlists:
        playlist_id = create_playlist(playlist_name)
        video_ids = []
        for track in songs:
            result = client.search(query = f"{track["song"]} {track["artist"]}",filter = "songs", limit = 5)[:5]

            for song in result:
                artist = song["artists"][0]["name"]
                if song["title"] == track["song"] and artist == track["artist"]:
                    video_ids.append(song["videoId"])
                    break
        
        client.add_playlist_items(playlistId=playlist_id, videoIds=video_ids)
        


def create_playlist(name):
    client = get_ytClient()

    playlist_id = client.create_playlist(title = name, description = "Made from Tranfer Playlists")
    return playlist_id

