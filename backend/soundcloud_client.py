import os
from flask import redirect, url_for, session
from dotenv import load_dotenv, find_dotenv
import json
import time
from difflib import SequenceMatcher
import re


class SoundCloudHandler:
    def init(self):
        load_dotenv(find_dotenv())
        self.client_id = os.getenv("SC_CLIENT_ID")
        self.client_secret = os.getenv("SC_CLIENT_SECRET")
        self._client = None

    def get_auth_url(self):
        return f"https://secure.soundcloud.com/authorize\?client_id={self.client_id}\&redirect_uri={url_for("redirect_page")}\&response_type=code\&code_challenge=CODE_CHALLENGE\&code_challenge_method=S256\&state=STATE"