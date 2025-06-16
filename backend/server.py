from flask import Flask, redirect,url_for,render_template,session,request,jsonify, Response, stream_with_context
import time
import os
from datetime import timedelta
from spotify_client import SpotifyHandler
from flask_cors import CORS
from ytMusic_client import YouTubeMusicHandler
from soundcloud_client import SoundCloudHandler
from deezer_client import DeezerHandler
import queue
import json




app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("APP_SECRET")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
event_queue = queue.Queue()
sp_client = SpotifyHandler()
yt_client = YouTubeMusicHandler()

@app.route("/callback")
def redirect_page():
    session.permanent = True
    # session.clear() 
    code = request.args["code"]
    
    platform_name = session["source"] 

    if platform_name == "Spotify":
        token_info = sp_client.get_sp_oauth().get_access_token(code) 
        session["sp_token_info"] = token_info 
        session['sp_expires_in'] = token_info['expires_in']
        session['sp_start_time'] = time.time()
    
    session[f"{platform_name}_authenticated"] = True

    return render_template("auth_success.html", 
                           playlists_url=url_for("display_playlists"), 
                           authenticated_platform=platform_name)



@app.route("/transfer", methods = ["POST", "GET"])
def transfer():
    if request.method == "GET":
       path = os.path.join(app.static_folder, "cards.json")
       with open(path) as f:
           cards = json.load(f)
       return render_template("transfer.html", cards=cards)
  

@app.route("/get-playlists", methods = ["POST", "GET"])
def display_playlists():
   if request.method == "GET":
       source = session.get("source")
       data = sp_client.get_playlists()
       path = os.path.join(app.static_folder, "cards.json")
       with open(path) as f:
           cards = json.load(f)
       return render_template("playlists.html", playlists = data, cards=cards, source = source)
   else:
       data = request.get_json()
       playlists = data.get("playlists")
       result = sp_client.get_songs(playlists)
       
       if isinstance(result, Response):
           return result, 400
       
       unfound = yt_client.add_songs_to_playlist(result, progress_callback)
       session["results"] = unfound
       return jsonify({"redirect": url_for("results")})

@app.route("/results")
def results():
    results = session.get("results", [])
    print(results)
    total_songs = 0
    total_failed = 0
    for playlist in results.values():
        if playlist:
            total_songs += playlist[0] 
            total_failed += len(playlist) - 1 

    total_success = total_songs - total_failed
    return render_template(
    "results.html",
    results=results,
    total_songs=total_songs,
    total_success=total_success,
    total_failed=total_failed,
    source = "Spotify",
    destination = "YoutubeMusic"
    )
       

@app.route("/update-selected", methods = ["POST"])
def update():
    data = request.get_json()
    selected = data.get("selectedPlaylists")
    return render_template("/partials/selected-playlists.html", selectedPlaylists=selected)


def progress_callback(playlist_name, current_song, curr_count, total, total_songs, curr_playlist, total_playlists):
    data = {
        "playlist": playlist_name,
        "song": current_song,
        "currCount": curr_count,
        "total": total,
        "totalSongs": total_songs,
        "currPlaylist": curr_playlist,
        "totalPlaylists": total_playlists
    }
    event_queue.put(data)  


@app.route('/progress-stream')
def progress_stream():
    def event_stream():
        while True:
            data = event_queue.get()
            yield f"data: {json.dumps(data)}\n\n"
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@app.route("/save-source", methods = ["POST"])
def save():
    data = request.get_json()
    session["source"] = data.get("source")
    return "",204


@app.route("/check-auth-status", methods=["GET"])
def check_auth_status():
    platform_name = request.args.get("platform")
    is_authenticated = False

    if platform_name == "Spotify":
        if session.get("sp_token_info"):
            is_authenticated = True

    return jsonify({"is_authenticated": is_authenticated, "platform": platform_name})


@app.route("/auth/start")
def start_auth():
    platform_name = request.args.get("platform")
    auth_url = None

    if platform_name == "Spotify":
        auth_url = sp_client.get_sp_oauth().get_authorize_url()
    else:
        return "Unknown platform specified for authentication.", 400

    if auth_url:
        return redirect(auth_url)
    else:
        return f"Could not initiate authentication for {platform_name}. Configuration might be missing or platform not supported for direct auth.", 500


if __name__ == "__main__":
    app.run(debug=True, port = 8000)