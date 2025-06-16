import os
from flask import redirect, url_for, session
from dotenv import load_dotenv, find_dotenv
import json
import time
from difflib import SequenceMatcher
import re
import requests


class DeezerHandler:
    def init(self):
        load_dotenv(find_dotenv())
        self.client_id = os.getenv("DZ_CLIENT_ID")
        self.client_secret = os.getenv("DZ_CLIENT_SECRET")
        self._client = None

    def get_auth_url(self):
       return f"https://connect.deezer.com/oauth/auth.php?app_id={self.client_id}&redirect_uri={url_for("redirect_page")}&perms=basic_access,email"
    
    def get_access_token(self, code):
        params = {
            "app_id":self.client_id,
            "secret":self.client_secret,
            "code":code,
            "output":"json"
        }
        response = requests.get("https://connect.deezer.com/oauth/access_token.php",params=params)
