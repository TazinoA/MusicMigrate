import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure backend directory is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["APP_SECRET"] = "test_secret_key"

import server
from spotify_client import SpotifyHandler
from ytMusic_client import YouTubeMusicHandler


class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True

    def test_save_source_and_destination(self):
        res = self.app.post("/save-source", json={"source": "Spotify"})
        self.assertEqual(res.status_code, 204)

        res = self.app.post("/save-destination", json={"destination": "YouTube Music"})
        self.assertEqual(res.status_code, 204)

    def test_check_auth_status(self):
        res = self.app.get("/check-auth-status?platform=Spotify")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("is_authenticated", data)
        self.assertFalse(data["is_authenticated"])

    def test_empty_playlist_submission(self):
        res = self.app.post("/get-playlists", json={"playlists": []})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)

    def test_callback_missing_code(self):
        res = self.app.get("/callback")
        self.assertEqual(res.status_code, 400)


class TestSpotifyHandler(unittest.TestCase):
    @patch.object(SpotifyHandler, "get_client")
    def test_get_playlists_pagination(self, mock_get_client):
        mock_sp = MagicMock()
        mock_get_client.return_value = mock_sp

        page1 = {
            "items": [
                {"id": "pl1", "name": "Playlist 1", "tracks": {"total": 10}, "images": []}
            ],
            "next": "https://api.spotify.com/v1/me/playlists?offset=1&limit=50"
        }
        page2 = {
            "items": [
                {"id": "pl2", "name": "Playlist 2", "tracks": {"total": 20}, "images": []}
            ],
            "next": None
        }

        mock_sp.current_user_playlists.return_value = page1
        mock_sp.next.return_value = page2

        handler = SpotifyHandler()
        playlists = handler.get_playlists()

        self.assertEqual(len(playlists), 2)
        self.assertEqual(playlists[0]["name"], "Playlist 1")
        self.assertEqual(playlists[1]["name"], "Playlist 2")


class TestYouTubeMusicHandler(unittest.TestCase):
    def test_helpers(self):
        handler = YouTubeMusicHandler()
        self.assertEqual(handler.clean_text("Song Title (feat. Artist)"), "song title")
        self.assertEqual(handler.parse_duration("03:45"), 225)
        self.assertTrue(handler.is_similar("Artist", "artist"))

    def test_extract_featured_artists(self):
        handler = YouTubeMusicHandler()
        featured = handler.extract_featured_artists("Track Title (feat. Drake & Future)")
        self.assertIn("Drake", featured)
        self.assertIn("Future", featured)


if __name__ == "__main__":
    unittest.main()
