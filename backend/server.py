from flask import Flask, redirect,url_for,render_template,session,request,jsonify, Response, stream_with_context
import time
import os
from datetime import timedelta
from spotify_client import *
from flask_cors import CORS
from ytMusic_client import *
import queue


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
    session.permanent = True
    session.clear()
    code = request.args["code"]
    token_info = get_sp().get_access_token(code)

    session["token_info"] = token_info
    session['expires_in'] = token_info['expires_in']
    session['start_time'] = time.time()
    return redirect(url_for("display_playlists"))


@app.route("/get-playlists", methods = ["POST", "GET"])
def display_playlists():
   if request.method == "GET":
       data = get_playlists()
       return render_template("playlists.html", playlists = data)
   else:
       data = request.get_json()
       playlists = data.get("playlists")
       result = get_songs(playlists)
       
       if isinstance(result, Response):
           return result, 400
       
       unfound = add_ytSongs(result, progress_callback)
       print(unfound)
       return "success", 200
       

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
            data = event_queue.get()  # Waits for new progress data
            yield f"data: {json.dumps(data)}\n\n"
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, port = 8000)