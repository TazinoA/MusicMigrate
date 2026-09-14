from flask import Flask, redirect, url_for, render_template, session, request, jsonify, Response, stream_with_context
from flask_session import Session
from flask_cors import CORS
import time
import os
import uuid
import queue
import json
from datetime import timedelta
from spotify_client import SpotifyHandler
from ytMusic_client import YouTubeMusicHandler

app = Flask(__name__)

app_secret = os.getenv("APP_SECRET")
if not app_secret:
    raise RuntimeError("APP_SECRET environment variable is required")

app.secret_key = app_secret

# Configure server-side session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(app.root_path, "flask_session")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
Session(app)

CORS(app, supports_credentials=True, origins=[
    "http://localhost:8000", "http://127.0.0.1:8000",
    "http://localhost:3000", "http://127.0.0.1:3000"
])

sp_client = SpotifyHandler()
yt_client = YouTubeMusicHandler()

event_queues = {}

def get_session_queue():
    if "session_id" not in session:
        session["session_id"] = uuid.uuid4().hex
    sid = session["session_id"]
    if sid not in event_queues:
        event_queues[sid] = queue.Queue()
    return event_queues[sid]


@app.route("/callback")
def redirect_page():
    session.permanent = True
    code = request.args.get("code")
    error = request.args.get("error")
    state = request.args.get("state")
    expected_state = session.get("oauth_state")

    if error:
        return f"Authentication error: {error}", 400
    if not code:
        return "Missing authorization code", 400
    if expected_state and state != expected_state:
        return "Invalid OAuth state parameter", 400

    platform_name = session.get("source") or session.get("auth_platform") or "Spotify"

    if platform_name == "Spotify":
        try:
            token_info = sp_client.get_sp_oauth().get_access_token(code)
            session["sp_token_info"] = token_info
            session["sp_expires_in"] = token_info.get("expires_in", 3600)
            session["sp_start_time"] = time.time()
            session["Spotify_authenticated"] = True
        except Exception as e:
            return f"Failed to exchange token with Spotify: {str(e)}", 400
    else:
        session[f"{platform_name}_authenticated"] = True

    return render_template("auth_success.html", 
                           playlists_url=url_for("display_playlists"), 
                           authenticated_platform=platform_name)


@app.route("/auth/start")
def start_auth():
    platform_name = request.args.get("platform")
    if not platform_name:
        return "Missing platform parameter", 400

    if "youtube" in platform_name.lower():
        platform_name = "YouTube Music"
    elif "spotify" in platform_name.lower():
        platform_name = "Spotify"

    session["auth_platform"] = platform_name

    if platform_name == "Spotify":
        state = uuid.uuid4().hex
        session["oauth_state"] = state
        auth_url = sp_client.get_sp_oauth().get_authorize_url(state=state)
        return redirect(auth_url)
    elif platform_name == "YouTube Music":
        try:
            code_dict = yt_client.get_device_code()
            session["yt_device_code"] = code_dict.get("device_code")
            return render_template("yt_auth.html",
                                   user_code=code_dict.get("user_code"),
                                   verification_url=code_dict.get("verification_url"))
        except Exception as e:
            return f"Error starting YouTube Music auth: {str(e)}", 500

    return f"Unsupported platform: {platform_name}", 400


@app.route("/auth/ytmusic/confirm")
def confirm_yt_auth():
    device_code = session.get("yt_device_code")
    if not device_code:
        return "No pending YouTube Music authentication found. Please start auth again.", 400

    try:
        token_info = yt_client.get_token_from_code(device_code)
        session["yt_auth_info"] = token_info
        session["YouTube Music_authenticated"] = True
        session["yt_device_code"] = None
        return render_template("auth_success.html",
                               playlists_url=url_for("display_playlists"),
                               authenticated_platform="YouTube Music")
    except Exception as e:
        return f"YouTube Music authorization failed or pending. Ensure you entered the code on Google, then try again. Error: {str(e)}", 400


@app.route("/check-auth-status", methods=["GET"])
def check_auth_status():
    platform_name = request.args.get("platform")
    is_authenticated = False

    if platform_name == "Spotify":
        if session.get("sp_token_info"):
            is_authenticated = True
    elif platform_name in ["YouTube Music", "YoutubeMusic"]:
        if session.get("yt_auth_info"):
            is_authenticated = True

    return jsonify({"is_authenticated": is_authenticated, "platform": platform_name})


@app.route("/transfer", methods=["POST", "GET"])
def transfer():
    if request.method in ["GET", "HEAD"]:
        source = request.args.get("platform") or session.get("source") or "Spotify"
        session["source"] = source
        path = os.path.join(app.static_folder, "cards.json")
        with open(path) as f:
            cards = json.load(f)
            cards = [card for card in cards if card["name"] == source]
        return render_template("transfer.html", cards=cards)
    return "", 405


@app.route("/get-playlists", methods=["POST", "GET"])
def display_playlists():
    if request.method == "GET":
        source = session.get("source", "Spotify")
        if source == "Spotify":
            sp = sp_client.get_client()
            if not sp:
                state = uuid.uuid4().hex
                session["oauth_state"] = state
                return redirect(sp_client.get_sp_oauth().get_authorize_url(state=state))
            data = sp_client.get_playlists()
        else:
            data = []

        path = os.path.join(app.static_folder, "cards.json")
        with open(path) as f:
            cards = json.load(f)
        return render_template("playlists.html", playlists=data, cards=cards, source=source)
    else:
        data = request.get_json() or {}
        playlists = data.get("playlists", [])

        if not playlists:
            return jsonify({"error": "No playlists selected for transfer"}), 400

        result = sp_client.get_songs(playlists)

        if not result or isinstance(result, Response):
            return jsonify({"error": "Failed to fetch songs from Spotify or unauthenticated"}), 400

        yt_auth = session.get("yt_auth_info")
        if not yt_auth:
            return jsonify({"error": "Destination YouTube Music account not authenticated"}), 400

        q = get_session_queue()

        def progress_cb(playlist_name, current_song, curr_count, total, total_songs, curr_playlist, total_playlists):
            msg = {
                "playlist": playlist_name,
                "song": current_song,
                "currCount": curr_count,
                "total": total,
                "totalSongs": total_songs,
                "currPlaylist": curr_playlist,
                "totalPlaylists": total_playlists
            }
            q.put(msg)

        unfound = yt_client.add_songs_to_playlist(result, yt_auth, progress_callback=progress_cb)
        session["results"] = unfound
        q.put("DONE")
        return jsonify({"redirect": url_for("results")})


@app.route("/results")
def results():
    res_data = session.get("results", {})
    total_songs = 0
    total_failed = 0

    for playlist, items in res_data.items():
        if items and isinstance(items, list):
            total_songs += items[0]
            total_failed += len(items) - 1

    total_success = total_songs - total_failed
    source = session.get("source", "Spotify")
    destination = session.get("destination", "YouTube Music")

    return render_template(
        "results.html",
        results=res_data,
        total_songs=total_songs,
        total_success=total_success,
        total_failed=total_failed,
        source=source,
        destination=destination
    )


@app.route("/update-selected", methods=["POST"])
def update():
    data = request.get_json() or {}
    selected = data.get("selectedPlaylists")
    return render_template("/partials/selected-playlists.html", selectedPlaylists=selected)


@app.route('/progress-stream')
def progress_stream():
    q = get_session_queue()

    def event_stream():
        while True:
            try:
                data = q.get(timeout=30)
                if data == "DONE":
                    yield f"data: {json.dumps({'complete': True})}\n\n"
                    break
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'ping': True})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@app.route("/save-source", methods=["POST"])
def save():
    data = request.get_json() or {}
    session["source"] = data.get("source")
    return "", 204


@app.route("/save-destination", methods=["POST"])
def save_destination():
    data = request.get_json() or {}
    session["destination"] = data.get("destination")
    return "", 204


if __name__ == "__main__":
    debug_flag = os.getenv("FLASK_DEBUG", "false").lower() in ["true", "1"]
    app.run(debug=debug_flag, port=8000)
