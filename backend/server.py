from flask import Flask, redirect,url_for,render_template,session,request,jsonify, Response, stream_with_context
import time
import os
from datetime import timedelta
from spotify_client import *
from flask_cors import CORS
from ytMusic_client import *
import queue
import json




app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
event_queue = queue.Queue()

@app.route("/")
def get_auth():
    return redirect(get_sp().get_authorize_url())

@app.route("/callback")
def redirect_page():
    source_backup = session.get("source")
    session.permanent = True
    session.clear()
    session["source"] = source_backup
    code = request.args["code"]
    token_info = get_sp().get_access_token(code)

    session["token_info"] = token_info
    session['expires_in'] = token_info['expires_in']
    session['start_time'] = time.time()
    return redirect(url_for("display_playlists"))



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
       data = get_playlists()
       path = os.path.join(app.static_folder, "cards.json")
       with open(path) as f:
           cards = json.load(f)
       return render_template("playlists.html", playlists = data, cards=cards, source = source)
   else:
       data = request.get_json()
       playlists = data.get("playlists")
       result = get_songs(playlists)
       
       if isinstance(result, Response):
           return result, 400
       
       unfound = add_ytSongs(result, progress_callback)
       session["results"] = unfound
       return jsonify({"redirect": url_for("results")})

@app.route("/results")
def results():
    results = session.get("results", [])
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
    total_failed=total_failed
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


if __name__ == "__main__":
    app.run(debug=True, port = 8000)