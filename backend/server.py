from flask import Flask, redirect,url_for,render_template,session,request
import time
import os
from datetime import timedelta
from spotify_client import *
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

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


@app.route("/get-playlists")
def display_playlists():
   data = get_playlists()
   return render_template("playlists.html", playlists = data)


if __name__ == "__main__":
    app.run(debug=True, port = 8000)