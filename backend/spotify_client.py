from flask import Flask, redirect,url_for,session,request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time
import os


load_dotenv()

def get_sp():
    sp_oauth = SpotifyOAuth(client_id=os.getenv("CLIENT_ID"), client_secret=os.getenv("CLIENT_SECRET"),
                            redirect_uri=url_for("redirect_page", _external=True),
                            scope="playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative ugc-image-upload user-top-read")
    return sp_oauth

def get_client():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(get_sp().get_authorize_url())
    
    expiration_time = session['start_time'] + session['expires_in']

    if time.time() > expiration_time:
        sp_oauth = get_sp()
        refresh_token = token_info["refresh_token"]
        token_info = sp_oauth.refresh_access_token(refresh_token)
        session["token_info"] = token_info
        session['start_time'] = time.time()


    return spotipy.Spotify(auth = token_info["access_token"])


def get_songs(playlists):
    sp = get_client()
    if not isinstance(sp, spotipy.Spotify):
        return sp
    

    fields = "items(track(name,artists(name),album(name),duration_ms)),next"
    playlists_list = []

    for playlist_id, playlist_name in playlists:
        result = sp.playlist_items(playlist_id=playlist_id, fields = fields)
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



def get_playlists():
    sp = get_client()
    response = sp.current_user_playlists(limit = 50)

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



def get_song_uri(song):
    sp = get_client()
    response = sp.search(song, limit = 1, type = "track")
    return response["tracks"]["items"][0]["uri"]

def add_songs(playlist_id, tracks):
    sp = get_client()
    sp.playlist_add_items(playlist_id=playlist_id, items=tracks)
