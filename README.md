# MusicMigrate

MusicMigrate is a web application that allows users to transfer their playlists between different music streaming platforms. 
**Currently, MusicMigrate primarily supports playlist transfers from Spotify to YouTube Music.** Support for other music platforms (such as Apple Music, Deezer, etc.) may be added in the future.

## Features

*   Transfer playlists from Spotify to YouTube Music.
*   Securely connect to your Spotify account using OAuth.
*   Select specific playlists for transfer.
*   View a summary of the transfer process, including any songs that could not be found on the destination platform.
*   Export a list of failed songs for manual review.
*   User-friendly interface.

## Setup and Run

This section covers how to get the MusicMigrate application running locally on your machine.

### Prerequisites

*   Python 3.8 or higher
*   pip (Python package installer)
*   Git (for cloning the repository)
*   A Spotify Developer application for API credentials (see [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/))
*   Credentials for YouTube Music (typically your Google account, handled via `ytmusicapi` setup if needed).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/MusicMigrate.git
    cd MusicMigrate
    ```
    *(Replace `your-username` with the actual repository path if forked or different)*

2.  **Set up Spotify API Credentials:**
    *   Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
    *   Create an app if you don't have one.
    *   Note your **Client ID** and **Client Secret**.
    *   In the app settings on the Spotify Dashboard, add a **Redirect URI**. For local development, this is typically `http://127.0.0.1:8000/callback` (assuming the Flask app runs on port 8000).
    *   You will need to set these as environment variables for the application to use. Create a `.env` file in the project root (add `.env` to your `.gitignore` file!) or set them directly in your shell:
        ```bash
        export SPOTIPY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID'
        export SPOTIPY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET'
        export SPOTIPY_REDIRECT_URI='http://127.0.0.1:8000/callback'
        export APP_SECRET='a_strong_random_secret_key_for_flask_sessions' 
        ```

3.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` is missing or incomplete, you might need to install packages like `Flask`, `spotipy`, `ytmusicapi`, `python-dotenv` manually using `pip install <package-name>`)*

### Running the Application

1.  **Ensure environment variables are set** (as described in Installation step 2).
2.  **Run the development server:**
    ```bash
    python backend/server.py 
    ```
    *(The main Flask application script is `server.py` inside the `backend` directory. Adjust if your project structure is different.)*

3.  Open your web browser and navigate to `http://127.0.0.1:8000/` (or the address shown in the terminal, typically the `/transfer` route is the starting page).

## How to Use MusicMigrate

Once the application is running, follow these steps to transfer your playlists:

1.  **Navigate to the Application:**
    *   Open your web browser and go to `http://127.0.0.1:8000/` (or the URL provided when you started the server). You should land on a page asking you to select your source and destination platforms.

2.  **Select Source Platform (Spotify):**
    *   On the main page, you'll see options to choose your music source.
    *   Select "Spotify" from the available source platforms.
    *   Click the "Connect with Spotify" (or similarly named) button.

3.  **Authenticate with Spotify:**
    *   You will be redirected to the Spotify login and authorization page.
    *   Log in with your Spotify credentials.
    *   Grant MusicMigrate permission to access your playlists and library.
    *   After successful authorization, Spotify will redirect you back to the MusicMigrate application.

4.  **Select Destination Platform (YouTube Music):**
    *   Once authenticated with Spotify, you'll typically be on a page showing your Spotify playlists.
    *   The application is currently configured to use YouTube Music as the destination platform.
    *   **YouTube Music Authentication:** The `ytmusicapi` library, used for interacting with YouTube Music, requires authentication to add songs to your playlists.
        *   When you initiate a transfer to YouTube Music for the first time, the application (specifically, the `backend/server.py` script) will attempt to authenticate.
        *   **Check your terminal:** The terminal window where `python backend/server.py` is running will display any necessary authentication instructions or links provided by `ytmusicapi`. This usually involves visiting a URL in your browser and entering a code.
        *   Follow these on-screen terminal prompts to authorize MusicMigrate to access your YouTube Music account. This is typically a one-time setup, and your credentials will be stored locally (often as `oauth.json`) for future use by `ytmusicapi`.
        *   If the terminal instructions are unclear, or if you encounter persistent authentication issues, you can consult the [ytmusicapi OAuth setup documentation](https://ytmusicapi.readthedocs.io/en/latest/setup/oauth.html) for more details on manual setup if needed.

5.  **Choose Playlists to Transfer:**
    *   A list of your Spotify playlists will be displayed.
    *   Select the checkboxes next to the playlists you wish to transfer.
    *   You can see a running count of selected playlists and total tracks.

6.  **Start the Transfer Process:**
    *   Once you've selected your playlists, click the "Transfer Playlists" (or similarly named) button.
    *   A progress bar or indicator will appear, showing the status of the transfer (e.g., "Transferring: Playlist Name...", "Song X of Y").

7.  **Understand the Results Page:**
    *   After the transfer is complete, you will be taken to a results page.
    *   This page summarizes the transfer:
        *   Total number of songs processed.
        *   Number of songs successfully transferred.
        *   Number of songs that could not be found or transferred (failed).
    *   A detailed list of songs that failed for each playlist will be shown. This typically includes the song title and artist, making it easier to find them manually if desired.
    *   **Export Failed Songs:** Look for an "Export List" or "Download Failed Songs" button. Clicking this will download a CSV file (`failed_songs.csv`) containing the details of all songs that could not be transferred. You can use this file for your records or to try adding the songs manually later.

## Contributing

Contributions are welcome

